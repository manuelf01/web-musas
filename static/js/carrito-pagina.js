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

  var PH_ICO = {
    Bebidas: "bi-cup-straw", Postres: "bi-cake2-fill", Combos: "bi-bag-heart-fill",
    Salchipapas: "bi-fire", Hamburguesas: "bi-fire", Piqueos: "bi-egg-fried",
    Acompañamientos: "bi-basket-fill",
  };

  function tarjetaSugerida(s) {
    var card = document.createElement("div");
    card.className = "cart-sug";
    var media = s.imagen
      ? '<img src="' + IMG + s.imagen + '" alt="">'
      : '<span class="cart-sug__ph"><i class="bi ' + (PH_ICO[s.categoria] || "bi-fire") + '"></i></span>';
    card.innerHTML =
      '<div class="cart-sug__media">' + media + "</div>" +
      '<div class="cart-sug__body">' +
        '<span class="cart-sug__motivo">' + s.motivo + "</span>" +
        "<strong>" + s.nombre + "</strong>" +
        '<span class="cart-sug__precio">+ ' + money(s.precio) + "</span>" +
      "</div>" +
      '<button class="cart-sug__add btn-contorno" type="button"><i class="bi bi-plus-lg"></i> Agregar</button>';
    card.querySelector(".cart-sug__add").addEventListener("click", function () {
      window.MusasCarrito.agregarConAnim(
        {
          idProducto: s.idProducto, nombre: s.nombre, precio: s.precio,
          imagen: s.imagen || null, cantidad: 1, cremas: [],
        },
        this,
        { mensaje: s.nombre + " agregado" }
      );
      render();
    });
    return card;
  }

  function renderSugeridos(items) {
    var sec = document.getElementById("carrito-sugeridos");
    var lista = document.getElementById("carrito-sugeridos-lista");
    if (!sec || !lista) return;
    var ids = items
      .map(function (it) { return it.idProducto; })
      .filter(function (x) { return x; })
      .join(",");
    fetch("/carrito/sugeridos?ids=" + encodeURIComponent(ids), { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : { sugeridos: [] }; })
      .then(function (d) {
        var sug = (d && d.sugeridos) || [];
        if (!sug.length) { sec.hidden = true; return; }
        lista.innerHTML = "";
        sug.forEach(function (s) { lista.appendChild(tarjetaSugerida(s)); });
        sec.hidden = false;
      })
      .catch(function () { sec.hidden = true; });
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
    renderSugeridos(items);
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
