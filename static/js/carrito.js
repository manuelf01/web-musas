/* Carrito de Las Musas — almacenamiento en localStorage (sin dependencias).
   Clave:  musas_carrito
   Valor:  [ { idProducto, nombre, precio, imagen, cantidad,
               cremas: [ { idProducto, nombre, precio } ] } ]
   El subtotal de una línea = (precio + suma cremas) * cantidad
*/
(function () {
  var CLAVE = "musas_carrito";

  function leer() {
    try {
      var v = JSON.parse(localStorage.getItem(CLAVE));
      return Array.isArray(v) ? v : [];
    } catch (e) {
      return [];
    }
  }

  function guardar(items) {
    try {
      localStorage.setItem(CLAVE, JSON.stringify(items));
    } catch (e) {}
    actualizarNav();
  }

  function subtotalLinea(it) {
    var cremas = (it.cremas || []).reduce(function (s, c) {
      return s + Number(c.precio || 0);
    }, 0);
    return (Number(it.precio || 0) + cremas) * Number(it.cantidad || 1);
  }

  function total() {
    return leer().reduce(function (s, it) {
      return s + subtotalLinea(it);
    }, 0);
  }

  function cantidadTotal() {
    return leer().reduce(function (s, it) {
      return s + Number(it.cantidad || 1);
    }, 0);
  }

  function _firmaCremas(cremas) {
    return (cremas || [])
      .map(function (c) { return Number(c.idProducto || c); })
      .sort(function (a, b) { return a - b; })
      .join(",");
  }

  function _mismaLinea(a, b) {
    return (
      Number(a.idProducto) === Number(b.idProducto) &&
      _firmaCremas(a.cremas) === _firmaCremas(b.cremas)
    );
  }

  function agregar(item) {
    var items = leer();
    var existente = null;
    for (var i = 0; i < items.length; i++) {
      if (_mismaLinea(items[i], item)) { existente = items[i]; break; }
    }
    if (existente) {
      // Mismo producto y mismas cremas -> suma a la línea que ya está.
      var suma = (Number(existente.cantidad) || 1) + (Number(item.cantidad) || 1);
      existente.cantidad = Math.max(1, Math.min(suma, 99));
    } else {
      items.push(item);
    }
    guardar(items);
  }

  function vaciar() {
    guardar([]);
  }

  function actualizarNav() {
    var n = cantidadTotal();
    var t = total();
    document.querySelectorAll("[data-carrito-count]").forEach(function (el) {
      el.textContent = n;
      if (el.classList.contains("musa-tabbar__badge")) el.hidden = n === 0;
    });
    document.querySelectorAll("[data-carrito-total]").forEach(function (el) {
      el.textContent = "S/ " + t.toFixed(2);
    });
  }

  document.addEventListener("DOMContentLoaded", actualizarNav);

  // ---------------------------------------------------------------
  //  Micro-interacción "agregar al carrito": rebote del pill, una
  //  bolsita que vuela hasta el carrito y un aviso (toast).
  // ---------------------------------------------------------------
  var SIN_MOVIMIENTO =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function objetivoCarrito() {
    var pill = document.querySelector(".musa-cart-pill");
    if (pill && pill.getClientRects().length) return pill;
    return document.querySelector('.musa-tabbar a[href*="carrito"]');
  }

  function rebotar() {
    var t = objetivoCarrito();
    if (!t) return;
    t.classList.remove("is-bump");
    void t.offsetWidth;
    t.classList.add("is-bump");
    setTimeout(function () {
      t.classList.remove("is-bump");
    }, 650);
  }

  function volar(origen) {
    var destino = objetivoCarrito();
    if (SIN_MOVIMIENTO || !destino || !origen) {
      rebotar();
      return;
    }
    var o = origen.getBoundingClientRect();
    var d = destino.getBoundingClientRect();
    var burbuja = document.createElement("span");
    burbuja.className = "musa-fly";
    burbuja.innerHTML = '<i class="bi bi-bag-fill"></i>';
    burbuja.style.left = o.left + o.width / 2 + "px";
    burbuja.style.top = o.top + o.height / 2 + "px";
    document.body.appendChild(burbuja);
    var dx = d.left + d.width / 2 - (o.left + o.width / 2);
    var dy = d.top + d.height / 2 - (o.top + o.height / 2);
    requestAnimationFrame(function () {
      burbuja.style.transform =
        "translate(" + dx + "px," + dy + "px) scale(0.25)";
      burbuja.style.opacity = "0.2";
    });
    var quitar = function () {
      burbuja.remove();
      rebotar();
    };
    burbuja.addEventListener("transitionend", quitar, { once: true });
    setTimeout(quitar, 900);
  }

  function contenedorToasts() {
    var c = document.querySelector(".musa-toasts");
    if (!c) {
      c = document.createElement("div");
      c.className = "musa-toasts";
      c.setAttribute("aria-live", "polite");
      document.body.appendChild(c);
    }
    return c;
  }

  function toast(mensaje, opciones) {
    opciones = opciones || {};
    var el = document.createElement("div");
    el.className = "musa-toast";
    var texto = document.createElement("span");
    texto.innerHTML = '<i class="bi bi-check-circle-fill"></i> ' + mensaje;
    el.appendChild(texto);
    if (opciones.href) {
      var a = document.createElement("a");
      a.href = opciones.href;
      a.className = "musa-toast__accion";
      a.textContent = opciones.accion || "Ver";
      el.appendChild(a);
    }
    contenedorToasts().appendChild(el);
    requestAnimationFrame(function () {
      el.classList.add("is-visible");
    });
    var cerrar = function () {
      el.classList.remove("is-visible");
      setTimeout(function () {
        el.remove();
      }, 300);
    };
    setTimeout(cerrar, opciones.duracion || 3600);
  }

  function agregarConAnim(item, origen, opciones) {
    opciones = opciones || {};
    agregar(item);
    volar(origen);
    toast(opciones.mensaje || "Agregado al carrito", {
      href: opciones.href || "/carrito",
      accion: opciones.accion || "Ver carrito",
    });
  }

  window.MusasCarrito = {
    leer: leer,
    guardar: guardar,
    subtotalLinea: subtotalLinea,
    total: total,
    cantidadTotal: cantidadTotal,
    agregar: agregar,
    agregarConAnim: agregarConAnim,
    vaciar: vaciar,
    actualizarNav: actualizarNav,
    toast: toast,
    rebotar: rebotar,
    volar: volar,
  };
})();
