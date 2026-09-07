/* Checkout: resumen desde localStorage + serializa el carrito al form. */
(function () {
  var form = document.getElementById("checkout-form");
  if (!form) return;

  var IMG = "/static/img/";
  var resumenLista = document.getElementById("ck-items");
  var elConteo = document.getElementById("ck-conteo");
  var elNeto = document.getElementById("ck-subtotal");
  var elIgv = document.getElementById("ck-igv");
  var elTotal = document.getElementById("ck-total");
  var btnTexto = document.getElementById("ck-btn-texto");
  var inputCarrito = document.getElementById("carrito_json");
  var vacioAviso = document.getElementById("ck-vacio");
  var contenido = document.getElementById("ck-contenido");

  function money(n) {
    return "S/ " + Number(n).toFixed(2);
  }

  function pintarResumen() {
    var items = window.MusasCarrito.leer();

    if (!items.length) {
      if (contenido) contenido.hidden = true;
      if (vacioAviso) vacioAviso.hidden = false;
      return;
    }
    if (contenido) contenido.hidden = false;
    if (vacioAviso) vacioAviso.hidden = true;

    inputCarrito.value = JSON.stringify(
      items.map(function (it) {
        return {
          idProducto: it.idProducto,
          cantidad: it.cantidad,
          cremas: (it.cremas || []).map(function (c) {
            return c.idProducto;
          }),
        };
      })
    );

    resumenLista.innerHTML = "";
    items.forEach(function (it) {
      var row = document.createElement("div");
      row.className = "ck-item";
      var media = it.imagen
        ? '<img src="' + IMG + it.imagen + '" alt="">'
        : '<span class="producto-card__ph"><i class="bi bi-fire"></i></span>';
      var chips = (it.cremas || [])
        .map(function (c) {
          return '<span class="cart-chip">' + c.nombre + "</span>";
        })
        .join("");
      row.innerHTML =
        '<div class="ck-item__img">' + media + '<span class="ck-item__q">x' + it.cantidad + "</span></div>" +
        '<div class="ck-item__body">' +
        '<div class="ck-item__top"><strong>' + it.nombre + "</strong><span>" +
        money(window.MusasCarrito.subtotalLinea(it)) + "</span></div>" +
        (chips ? '<div class="ck-item__chips">' + chips + "</div>" : "") +
        "</div>";
      resumenLista.appendChild(row);
    });

    var total = window.MusasCarrito.total();
    var neto = total / 1.18;
    var n = window.MusasCarrito.cantidadTotal();
    if (elConteo) elConteo.textContent = n + (n === 1 ? " ítem" : " ítems");
    if (elNeto) elNeto.textContent = money(neto);
    if (elIgv) elIgv.textContent = money(total - neto);
    if (elTotal) elTotal.textContent = money(total);
    if (btnTexto) btnTexto.textContent = "Confirmar pedido — " + money(total);
  }

  // Selector de franja de recojo
  var inputHora = document.getElementById("hora_recojo");
  document.querySelectorAll(".ck-hora:not([disabled])").forEach(function (b) {
    b.addEventListener("click", function () {
      if (inputHora) inputHora.value = b.dataset.hora;
      document.querySelectorAll(".ck-hora").forEach(function (x) {
        x.classList.toggle("is-active", x === b);
      });
    });
  });

  // método de pago (radios estilizados)
  document.querySelectorAll('input[name="pago"]').forEach(function (r) {
    r.addEventListener("change", function () {
      var yape = document.getElementById("ck-yape-info");
      if (yape) yape.hidden = document.querySelector('input[name="pago"]:checked').value !== "digital";
    });
  });

  form.addEventListener("submit", function (e) {
    if (!window.MusasCarrito.leer().length) {
      e.preventDefault();
      alert("Tu carrito está vacío.");
      return;
    }
    pintarResumen(); // asegura carrito_json actualizado
  });

  pintarResumen();
})();
