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
  var pasos = Array.prototype.slice.call(form.querySelectorAll("[data-ck-paso]"));
  var indicadores = Array.prototype.slice.call(form.querySelectorAll("[data-ck-indicador]"));
  var pasoActual = 1;
  var pasoMaximo = 1;

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

    pintarTotales(window.MusasCarrito.total());
  }

  function pintarTotales(total) {
    var neto = total / 1.18;
    var n = window.MusasCarrito.cantidadTotal();
    if (elConteo) elConteo.textContent = n + (n === 1 ? " ítem" : " ítems");
    if (elNeto) elNeto.textContent = money(neto);
    if (elIgv) elIgv.textContent = money(total - neto);
    if (elTotal) elTotal.textContent = money(total);
    if (btnTexto) btnTexto.textContent = "Confirmar pedido — " + money(total);
  }

  // El total de arriba se calcula con los precios guardados en localStorage.
  // El servidor manda; si un precio cambió, se re-cotiza y se avisa al cliente.
  function reconciliarConServidor() {
    var csrf = form.querySelector('[name="_csrf"]');
    var cuerpo = new URLSearchParams();
    cuerpo.set("carrito_json", inputCarrito.value || "[]");
    if (csrf) cuerpo.set("_csrf", csrf.value);
    fetch("/compra/cotizar", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: cuerpo.toString(),
    })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || !data.total) return;
        var servidor = Number(data.total);
        var local = window.MusasCarrito.total();
        if (!isFinite(servidor) || Math.abs(servidor - local) < 0.005) return;
        pintarTotales(servidor);
        var aviso = document.getElementById("ck-aviso-precio");
        if (aviso) {
          aviso.textContent =
            "Actualizamos el precio de algún producto. El total a pagar es " +
            money(servidor) + ".";
          aviso.hidden = false;
        }
      })
      .catch(function () { /* sin conexión: se queda el total local */ });
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
  function syncYape() {
    var yape = document.getElementById("ck-yape-info");
    var sel = document.querySelector('input[name="pago"]:checked');
    if (yape && sel) yape.hidden = sel.dataset.tipo !== "billetera";
    // Fallback de :has() (Firefox < 121): marca la opción elegida.
    document.querySelectorAll(".ck-opcion").forEach(function (op) {
      var input = op.querySelector("input");
      op.classList.toggle("is-sel", !!(input && input.checked));
    });
  }
  document.querySelectorAll('input[name="pago"]').forEach(function (r) {
    r.addEventListener("change", syncYape);
  });
  syncYape();

  function mostrarErrorPaso(numero, mensaje) {
    var error = form.querySelector('[data-ck-error="' + numero + '"]');
    if (!error) return;
    error.textContent = mensaje || "";
    error.hidden = !mensaje;
  }

  function validarPaso(numero) {
    mostrarErrorPaso(numero, "");
    var panel = form.querySelector('[data-ck-paso="' + numero + '"]');
    if (!panel) return false;

    var campos = panel.querySelectorAll("input[required], textarea[required], select[required]");
    for (var i = 0; i < campos.length; i++) {
      if (!campos[i].checkValidity()) {
        campos[i].reportValidity();
        mostrarErrorPaso(numero, "Revisa el campo indicado antes de continuar.");
        return false;
      }
    }

    if (numero === 1 && (!inputHora || !inputHora.value)) {
      mostrarErrorPaso(numero, "Selecciona una hora de recojo disponible para continuar.");
      return false;
    }
    if (numero === 2 && !panel.querySelector('input[name="pago"]:checked')) {
      mostrarErrorPaso(numero, "Elige cómo prefieres pagar al recoger tu pedido.");
      return false;
    }
    return true;
  }

  function mostrarPaso(numero, moverFoco) {
    numero = Number(numero);
    if (numero < 1 || numero > 3 || numero > pasoMaximo) return;
    pasoActual = numero;

    pasos.forEach(function (panel) {
      var activo = Number(panel.dataset.ckPaso) === numero;
      panel.hidden = !activo;
      panel.classList.toggle("is-active", activo);
    });
    indicadores.forEach(function (item) {
      var n = Number(item.dataset.ckIndicador);
      var boton = item.querySelector("button");
      item.classList.toggle("is-active", n === numero);
      item.classList.toggle("is-complete", n !== numero && (n < numero || n < pasoMaximo));
      if (boton) {
        boton.disabled = n > pasoMaximo;
        if (n === numero) boton.setAttribute("aria-current", "step");
        else boton.removeAttribute("aria-current");
      }
    });

    if (moverFoco) {
      var actual = form.querySelector('[data-ck-paso="' + numero + '"]');
      if (actual) {
        actual.scrollIntoView({ behavior: "smooth", block: "start" });
        var titulo = actual.querySelector("h2");
        if (titulo) {
          titulo.setAttribute("tabindex", "-1");
          window.setTimeout(function () { titulo.focus({ preventScroll: true }); }, 250);
        }
      }
    }
  }

  form.querySelectorAll("[data-ck-siguiente]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      if (!validarPaso(pasoActual)) return;
      var destino = Number(boton.dataset.ckSiguiente);
      pasoMaximo = Math.max(pasoMaximo, destino);
      mostrarPaso(destino, true);
    });
  });
  form.querySelectorAll("[data-ck-anterior]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      mostrarPaso(Number(boton.dataset.ckAnterior), true);
    });
  });
  form.querySelectorAll("[data-ck-ir]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      mostrarPaso(Number(boton.dataset.ckIr), true);
    });
  });

  form.addEventListener("submit", function (e) {
    if (!window.MusasCarrito.leer().length) {
      e.preventDefault();
      alert("Tu carrito está vacío.");
      return;
    }
    if (!validarPaso(1)) {
      e.preventDefault();
      mostrarPaso(1, true);
      return;
    }
    if (!validarPaso(2)) {
      e.preventDefault();
      pasoMaximo = Math.max(pasoMaximo, 2);
      mostrarPaso(2, true);
      return;
    }
    pintarResumen(); // asegura carrito_json actualizado
  });

  pintarResumen();
  mostrarPaso(1, false);
  if (window.MusasCarrito.leer().length) reconciliarConServidor();
})();
