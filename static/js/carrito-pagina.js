/* Página del carrito: renderiza desde localStorage (window.MusasCarrito). */
(function () {
  var cont = document.getElementById("carrito-pagina");
  if (!cont) return;

  var IMG = "/static/img/";
  var lleno = document.getElementById("carrito-lleno");
  var vacio = document.getElementById("carrito-vacio");
  var lista = document.getElementById("carrito-items");
  var elConteo = document.getElementById("resumen-conteo");
  var elNeto = document.getElementById("resumen-subtotal");
  var elIgv = document.getElementById("resumen-igv");
  var elTotal = document.getElementById("resumen-total");
  var btnComprar = document.getElementById("carrito-continuar");

  function money(n) {
    return "S/ " + Number(n).toFixed(2);
  }

  function chip(txt) {
    var s = document.createElement("span");
    s.className = "cart-chip";
    s.textContent = txt;
    return s;
  }

  function tarjeta(it, idx) {
    var art = document.createElement("div");
    art.className = "cart-item";

    var media = document.createElement("div");
    media.className = "cart-item__img";
    if (it.imagen) {
      var img = document.createElement("img");
      img.src = IMG + it.imagen;
      img.alt = it.nombre;
      media.appendChild(img);
    } else {
      media.innerHTML = '<span class="producto-card__ph"><i class="bi bi-fire"></i></span>';
    }
    var badge = document.createElement("span");
    badge.className = "cart-item__qtybadge";
    badge.textContent = "x" + it.cantidad;
    media.appendChild(badge);

    var body = document.createElement("div");
    body.className = "cart-item__body";

    var top = document.createElement("div");
    top.className = "cart-item__top";
    top.innerHTML =
      '<div><h3>' + it.nombre + "</h3>" +
      '<p>Precio base: ' + money(it.precio) + "</p></div>";
    var quitar = document.createElement("button");
    quitar.className = "cart-item__quitar";
    quitar.setAttribute("aria-label", "Quitar " + it.nombre);
    quitar.innerHTML = '<i class="bi bi-trash"></i>';
    quitar.addEventListener("click", function () {
      var items = window.MusasCarrito.leer();
      items.splice(idx, 1);
      window.MusasCarrito.guardar(items);
      render();
    });
    top.appendChild(quitar);
    body.appendChild(top);

    if (it.cremas && it.cremas.length) {
      var chips = document.createElement("div");
      chips.className = "cart-item__chips";
      it.cremas.forEach(function (c) {
        chips.appendChild(chip(c.nombre + " (+ " + money(c.precio) + ")"));
      });
      body.appendChild(chips);
    }

    var foot = document.createElement("div");
    foot.className = "cart-item__foot";

    var stepper = document.createElement("div");
    stepper.className = "cart-stepper";
    stepper.innerHTML =
      '<button data-d="-1" aria-label="Quitar uno">−</button>' +
      "<span>" + it.cantidad + "</span>" +
      '<button data-d="1" aria-label="Agregar uno">+</button>';
    stepper.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        var items = window.MusasCarrito.leer();
        items[idx].cantidad = Math.max(1, items[idx].cantidad + Number(b.dataset.d));
        window.MusasCarrito.guardar(items);
        render();
      });
    });
    foot.appendChild(stepper);

    var sub = document.createElement("div");
    sub.className = "cart-item__sub";
    sub.innerHTML =
      '<span>Subtotal</span><strong>' +
      money(window.MusasCarrito.subtotalLinea(it)) +
      "</strong>";
    foot.appendChild(sub);

    body.appendChild(foot);
    art.appendChild(media);
    art.appendChild(body);
    return art;
  }

  function render() {
    var items = window.MusasCarrito.leer();

    if (!items.length) {
      lleno.hidden = true;
      vacio.hidden = false;
      window.MusasCarrito.actualizarNav();
      return;
    }
    lleno.hidden = false;
    vacio.hidden = true;

    lista.innerHTML = "";
    items.forEach(function (it, i) {
      lista.appendChild(tarjeta(it, i));
    });

    var total = window.MusasCarrito.total();
    var neto = total / 1.18;
    var igv = total - neto;
    var n = window.MusasCarrito.cantidadTotal();

    if (elConteo) elConteo.textContent = n + (n === 1 ? " producto" : " productos");
    if (elNeto) elNeto.textContent = money(neto);
    if (elIgv) elIgv.textContent = money(igv);
    if (elTotal) elTotal.textContent = money(total);
    window.MusasCarrito.actualizarNav();
  }

  var btnVaciar = document.getElementById("carrito-vaciar");
  if (btnVaciar) {
    btnVaciar.addEventListener("click", function () {
      if (confirm("¿Vaciar el carrito?")) {
        window.MusasCarrito.vaciar();
        render();
      }
    });
  }

  render();
})();
