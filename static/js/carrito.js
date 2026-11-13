/* Carrito de la tienda — almacenamiento en localStorage (sin dependencias).
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

  function reemplazar(indice, item) {
    var items = leer();
    indice = Number(indice);
    if (!Number.isInteger(indice) || indice < 0 || indice >= items.length) return false;
    items.splice(indice, 1);
    var existente = items.find(function (linea) { return _mismaLinea(linea, item); });
    if (existente) {
      existente.cantidad = Math.max(1, Math.min(99,
        (Number(existente.cantidad) || 1) + (Number(item.cantidad) || 1)));
    } else {
      items.splice(Math.min(indice, items.length), 0, item);
    }
    guardar(items);
    return true;
  }

  function actualizarNav() {
    var n = cantidadTotal();
    var t = total();
    document.querySelectorAll("[data-carrito-count]").forEach(function (el) {
      el.textContent = n;
      if (el.classList.contains("musa-tabbar__badge")) el.hidden = n === 0;
    });
    document.querySelectorAll("[data-carrito-total]").forEach(function (el) {
      var importe = "S/ " + t.toFixed(2);
      el.textContent = importe;
      if (el.hasAttribute("data-carrito-total-label")) {
        var enlace = el.closest("a");
        if (enlace) enlace.setAttribute("aria-label", "Carrito, total " + importe);
      }
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
    var duracion = opciones.duracion || (opciones.deshacer ? 8000 : 4200);
    var el = document.createElement("div");
    el.className = "musa-toast";
    el.setAttribute("role", "status");

    var icono = document.createElement("span");
    icono.className = "musa-toast__icono";
    icono.innerHTML = '<i class="bi bi-check-lg"></i>';
    el.appendChild(icono);

    var cuerpo = document.createElement("div");
    cuerpo.className = "musa-toast__cuerpo";
    var titulo = document.createElement("strong");
    titulo.textContent = opciones.titulo || (opciones.deshacer ? "Agregado al carrito" : "Listo");
    var texto = document.createElement("span");
    texto.textContent = mensaje;
    cuerpo.appendChild(titulo);
    cuerpo.appendChild(texto);

    var acciones = document.createElement("div");
    acciones.className = "musa-toast__acciones";
    if (typeof opciones.deshacer === "function") {
      var deshacer = document.createElement("button");
      deshacer.type = "button";
      deshacer.className = "musa-toast__deshacer";
      deshacer.innerHTML = '<i class="bi bi-arrow-counterclockwise"></i> Deshacer';
      acciones.appendChild(deshacer);
    }
    if (opciones.href) {
      var a = document.createElement("a");
      a.href = opciones.href;
      a.className = "musa-toast__accion";
      a.textContent = opciones.accion || "Ver";
      acciones.appendChild(a);
    }
    if (acciones.children.length) cuerpo.appendChild(acciones);
    el.appendChild(cuerpo);

    var botonCerrar = document.createElement("button");
    botonCerrar.type = "button";
    botonCerrar.className = "musa-toast__cerrar";
    botonCerrar.setAttribute("aria-label", "Cerrar aviso");
    botonCerrar.innerHTML = '<i class="bi bi-x-lg"></i>';
    el.appendChild(botonCerrar);

    var tiempo = document.createElement("span");
    tiempo.className = "musa-toast__tiempo";
    tiempo.style.animationDuration = duracion + "ms";
    el.appendChild(tiempo);

    contenedorToasts().appendChild(el);
    requestAnimationFrame(function () {
      el.classList.add("is-visible");
    });
    var cerrado = false;
    var timer = null;
    var inicio = 0;
    var restante = duracion;
    var cerrar = function () {
      if (cerrado) return;
      cerrado = true;
      clearTimeout(timer);
      el.classList.remove("is-visible");
      setTimeout(function () {
        el.remove();
      }, 300);
    };
    function iniciarTimer() {
      inicio = Date.now();
      timer = setTimeout(cerrar, restante);
    }
    function pausarTimer() {
      clearTimeout(timer);
      restante = Math.max(0, restante - (Date.now() - inicio));
    }
    botonCerrar.addEventListener("click", cerrar);
    el.addEventListener("mouseenter", pausarTimer);
    el.addEventListener("mouseleave", function () {
      if (!cerrado && restante > 0) iniciarTimer();
    });
    if (deshacer) {
      deshacer.addEventListener("click", function () {
        if (cerrado) return;
        var resultado = opciones.deshacer();
        cerrar();
        toast(resultado === false ? "El producto ya no estaba en el carrito." : "El producto fue retirado del carrito.", {
          titulo: resultado === false ? "Sin cambios" : "Acción deshecha",
          duracion: 2600,
        });
      });
    }
    iniciarTimer();
    return el;
  }

  function cantidadDeLinea(items, item) {
    for (var i = 0; i < items.length; i++) {
      if (_mismaLinea(items[i], item)) return Math.max(0, Number(items[i].cantidad) || 0);
    }
    return 0;
  }

  function deshacerAgregado(item, cantidadAgregada) {
    if (Number(cantidadAgregada) <= 0) return false;
    var items = leer();
    var indice = -1;
    for (var i = 0; i < items.length; i++) {
      if (_mismaLinea(items[i], item)) { indice = i; break; }
    }
    if (indice < 0) return false;
    var agregadas = Math.max(1, Number(cantidadAgregada) || 1);
    var actuales = Math.max(1, Number(items[indice].cantidad) || 1);
    if (actuales > agregadas) items[indice].cantidad = actuales - agregadas;
    else items.splice(indice, 1);
    guardar(items);
    window.dispatchEvent(new CustomEvent("musas:carrito-deshacer"));
    return true;
  }

  function agregarConAnim(item, origen, opciones) {
    opciones = opciones || {};
    var cantidadAntes = cantidadDeLinea(leer(), item);
    agregar(item);
    var cantidadAgregada = Math.max(0, cantidadDeLinea(leer(), item) - cantidadAntes);
    volar(origen);
    var opcionesAviso = {
      href: opciones.href || "/carrito",
      accion: opciones.accion || "Ver carrito",
      duracion: opciones.duracion || (cantidadAgregada ? 8000 : 4200),
    };
    if (cantidadAgregada) {
      opcionesAviso.deshacer = function () {
        var ok = deshacerAgregado(item, cantidadAgregada);
        if (ok && typeof opciones.onDeshacer === "function") opciones.onDeshacer();
        return ok;
      };
    } else {
      opcionesAviso.titulo = "Límite alcanzado";
    }
    toast(
      cantidadAgregada ? (opciones.mensaje || "Agregado al carrito") : "Ya tienes 99 unidades de esta combinación.",
      opcionesAviso
    );
  }

  window.MusasCarrito = {
    leer: leer,
    guardar: guardar,
    subtotalLinea: subtotalLinea,
    total: total,
    cantidadTotal: cantidadTotal,
    agregar: agregar,
    reemplazar: reemplazar,
    agregarConAnim: agregarConAnim,
    vaciar: vaciar,
    actualizarNav: actualizarNav,
    toast: toast,
    rebotar: rebotar,
    volar: volar,
  };
})();
