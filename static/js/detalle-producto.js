/* Detalle de producto: stepper de cantidad, total en vivo y agregar al carrito.
   La personalización a medias se guarda como borrador (localStorage) para que no se
   pierda si el cliente cierra la pestaña o se va a otra página. */
(function () {
  var root = document.getElementById("detalle-producto");
  if (!root) return;

  var base = Number(root.dataset.precio) || 0;
  var carritoUrl = root.dataset.carritoUrl || "/carrito";
  var qtyEl = document.getElementById("dp-qty");
  var mobPrecio = document.getElementById("dp-mob-precio");
  var mobQty = document.getElementById("dp-mob-qty");
  var verCarrito = document.getElementById("dp-ver-carrito");
  var qty = 1;
  var enCarrito = false; // ya se agregó esta combinación
  var editarIndice = root.dataset.editarIndice === "" ? null : Number(root.dataset.editarIndice);
  var modoEditar = Number.isInteger(editarIndice) && editarIndice >= 0;

  if (modoEditar) {
    var lineaEditar = window.MusasCarrito.leer()[editarIndice];
    if (!lineaEditar || Number(lineaEditar.idProducto) !== Number(root.dataset.id)) {
      modoEditar = false;
    } else {
      qty = Math.max(1, Number(lineaEditar.cantidad) || 1);
      var idsEditar = (lineaEditar.cremas || []).map(function (c) {
        return Number(c.idProducto);
      });
      document.querySelectorAll(".crema-check").forEach(function (c) {
        c.checked = idsEditar.indexOf(Number(c.value)) !== -1;
      });
    }
  }

  var admitePersonalizacion = root.dataset.admiteCremas === "1";
  var pasosPersonalizacion = Array.prototype.slice.call(root.querySelectorAll("[data-dp-paso]"));
  var indicadoresPersonalizacion = Array.prototype.slice.call(root.querySelectorAll("[data-dp-indicador]"));
  var pasoPersonalizacionActual = 1;
  var pasoPersonalizacionMaximo = 1;

  // --- Borrador de la personalización ---------------------------------
  var CLAVE_BORRADOR = "musas_borrador_" + root.dataset.id;
  var VIGENCIA_BORRADOR = 24 * 60 * 60 * 1000;

  function guardarBorrador() {
    if (modoEditar) return;
    try {
      var ids = Array.prototype.map.call(
        document.querySelectorAll(".crema-check:checked"),
        function (c) { return Number(c.value); }
      );
      if (!ids.length && qty === 1) {
        localStorage.removeItem(CLAVE_BORRADOR);
      } else {
        localStorage.setItem(CLAVE_BORRADOR, JSON.stringify({ ids: ids, qty: qty, t: Date.now() }));
      }
    } catch (e) {}
  }

  function borrarBorrador() {
    try { localStorage.removeItem(CLAVE_BORRADOR); } catch (e) {}
  }

  if (!modoEditar) {
    try {
      var borrador = JSON.parse(localStorage.getItem(CLAVE_BORRADOR) || "null");
      if (borrador && Date.now() - borrador.t < VIGENCIA_BORRADOR) {
        var idsBorrador = (borrador.ids || []).map(Number);
        var restauradas = 0;
        document.querySelectorAll(".crema-check").forEach(function (c) {
          c.checked = idsBorrador.indexOf(Number(c.value)) !== -1;
          if (c.checked) restauradas++;
        });
        qty = Math.max(1, Math.min(99, Number(borrador.qty) || 1));
        if ((restauradas || qty > 1) && window.MusasCarrito && window.MusasCarrito.toast) {
          window.MusasCarrito.toast("Recuperamos tu personalización");
        }
      } else if (borrador) {
        localStorage.removeItem(CLAVE_BORRADOR);
      }
    } catch (e) {}
  }

  function validarGrupo(grupo) {
    var panel = document.querySelector('[data-grupo-req="' + grupo + '"]');
    if (!panel) return true;
    var valido = panel.querySelectorAll(".crema-check:checked").length >= 1;
    panel.classList.toggle("is-invalido", !valido);
    var error = panel.querySelector("[data-grupo-error]");
    if (error) error.hidden = valido;
    return valido;
  }

  function validarPersonalizacion() {
    if (!admitePersonalizacion) return true;
    var salsaOk = validarGrupo("salsa");
    var papasOk = validarGrupo("papas");
    return salsaOk && papasOk;
  }

  document.querySelectorAll("[data-grupo-req] .crema-check").forEach(function (c) {
    c.addEventListener("change", function () {
      var grupo = c.closest("[data-grupo-req]");
      if (grupo && grupo.classList.contains("is-invalido")) validarPersonalizacion();
    });
  });

  function cremasSeleccionadas() {
    return Array.prototype.map.call(
      document.querySelectorAll(".crema-check:checked"),
      function (c) {
        return {
          idProducto: Number(c.value),
          nombre: c.dataset.nombre,
          precio: Number(c.dataset.precio) || 0,
        };
      }
    );
  }

  function total() {
    var cremas = cremasSeleccionadas().reduce(function (s, c) {
      return s + c.precio;
    }, 0);
    return (base + cremas) * qty;
  }

  function renderResumenPersonalizacion() {
    var resumen = root.querySelector("[data-dp-resumen]");
    if (!resumen) return;
    resumen.innerHTML = "";
    [
      { grupo: "salsa", titulo: "Salsas", vacio: "Sin seleccionar" },
      { grupo: "papas", titulo: "Papas", vacio: "Sin seleccionar" },
      { grupo: "agregado", titulo: "Agregados", vacio: "Sin agregados" },
    ].forEach(function (seccion) {
      var elegidos = Array.prototype.slice.call(
        root.querySelectorAll('.crema-check[data-grupo="' + seccion.grupo + '"]:checked')
      );
      var fila = document.createElement("div");
      var titulo = document.createElement("strong");
      var detalle = document.createElement("span");
      titulo.textContent = seccion.titulo;
      detalle.textContent = elegidos.length
        ? elegidos.map(function (item) {
            var precio = Number(item.dataset.precio) || 0;
            return item.dataset.nombre + (precio ? " (+ S/ " + precio.toFixed(2) + ")" : "");
          }).join(", ")
        : seccion.vacio;
      fila.appendChild(titulo);
      fila.appendChild(detalle);
      resumen.appendChild(fila);
    });
  }

  function render() {
    if (qtyEl) qtyEl.textContent = qty;
    if (mobQty) mobQty.textContent = qty;
    var t = total().toFixed(2);
    if (mobPrecio) mobPrecio.textContent = "S/ " + t;
    document.querySelectorAll("[data-agregar]").forEach(function (b) {
      var span = b.querySelector("[data-dp-btn-texto]");
      var icono = b.querySelector("i");
      b.classList.toggle("is-ok", enCarrito);
      b.disabled = enCarrito;
      if (icono) icono.className = enCarrito ? "bi bi-check-lg" : "bi bi-bag-plus";
      if (span) {
        span.textContent = enCarrito
          ? "Agregado al carrito"
          : (modoEditar ? "Guardar cambios — S/ " + t : "Agregar al carrito — S/ " + t);
      }
    });
    if (verCarrito) verCarrito.hidden = !enCarrito;
    renderResumenPersonalizacion();
  }

  function mostrarPasoPersonalizacion(numero, moverFoco) {
    numero = Number(numero);
    if (!admitePersonalizacion || numero < 1 || numero > 4 || numero > pasoPersonalizacionMaximo) return;
    pasoPersonalizacionActual = numero;
    pasosPersonalizacion.forEach(function (panel) {
      var activo = Number(panel.dataset.dpPaso) === numero;
      panel.hidden = !activo;
      panel.classList.toggle("is-active", activo);
    });
    indicadoresPersonalizacion.forEach(function (item) {
      var n = Number(item.dataset.dpIndicador);
      var boton = item.querySelector("button");
      item.classList.toggle("is-active", n === numero);
      item.classList.toggle("is-complete", n !== numero && (n < numero || n < pasoPersonalizacionMaximo));
      if (boton) {
        boton.disabled = n > pasoPersonalizacionMaximo;
        if (n === numero) boton.setAttribute("aria-current", "step");
        else boton.removeAttribute("aria-current");
      }
    });
    if (numero === 4) renderResumenPersonalizacion();
    if (moverFoco) {
      var panelActivo = root.querySelector('[data-dp-paso="' + numero + '"]');
      if (panelActivo) {
        panelActivo.scrollIntoView({ block: "start", behavior: "smooth" });
        panelActivo.setAttribute("tabindex", "-1");
        window.setTimeout(function () { panelActivo.focus({ preventScroll: true }); }, 250);
      }
    }
  }

  function validarPasoPersonalizacion(numero) {
    if (numero === 1) return validarGrupo("salsa");
    if (numero === 2) return validarGrupo("papas");
    return true;
  }

  root.querySelectorAll("[data-dp-siguiente]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      if (!validarPasoPersonalizacion(pasoPersonalizacionActual)) return;
      var destino = Number(boton.dataset.dpSiguiente);
      pasoPersonalizacionMaximo = Math.max(pasoPersonalizacionMaximo, destino);
      mostrarPasoPersonalizacion(destino, true);
    });
  });
  root.querySelectorAll("[data-dp-anterior]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      mostrarPasoPersonalizacion(Number(boton.dataset.dpAnterior), true);
    });
  });
  root.querySelectorAll("[data-dp-ir]").forEach(function (boton) {
    boton.addEventListener("click", function () {
      mostrarPasoPersonalizacion(Number(boton.dataset.dpIr), true);
    });
  });

  // Cambiar cantidad o cremas = otra combinación -> se puede volver a agregar.
  function reactivar() {
    if (enCarrito) enCarrito = false;
    guardarBorrador();
    render();
  }

  document.querySelectorAll("[data-step]").forEach(function (b) {
    b.addEventListener("click", function () {
      qty = Math.max(1, Math.min(99, qty + Number(b.dataset.step)));
      reactivar();
    });
  });

  document.querySelectorAll(".crema-check").forEach(function (c) {
    function pintar() {
      // Fallback de :has() para navegadores viejos (Firefox < 121).
      var card = c.closest(".crema-card");
      if (card) card.classList.toggle("is-sel", c.checked);
    }
    c.addEventListener("change", function () {
      pintar();
      reactivar();
    });
    pintar();
  });

  document.querySelectorAll("[data-agregar]").forEach(function (b) {
    b.addEventListener("click", function () {
      if (enCarrito) return;
      if (!validarPersonalizacion()) {
        var primero = document.querySelector(".dp-personaliza__grupo.is-invalido");
        if (primero) {
          var pasoInvalido = Number(primero.dataset.dpPaso) || 1;
          pasoPersonalizacionMaximo = Math.max(pasoPersonalizacionMaximo, pasoInvalido);
          mostrarPasoPersonalizacion(pasoInvalido, true);
        }
        return;
      }
      var unidades = qty;
      var item = {
          idProducto: Number(root.dataset.id),
          nombre: root.dataset.nombre,
          precio: base,
          imagen: root.dataset.imagen || null,
          cantidad: unidades,
          cremas: cremasSeleccionadas(),
          admiteCremas: root.dataset.admiteCremas === "1",
        };
      if (modoEditar) {
        window.MusasCarrito.reemplazar(editarIndice, item);
        window.location.href = carritoUrl;
        return;
      }
      window.MusasCarrito.agregarConAnim(
        item,
        b,
        {
          href: carritoUrl,
          mensaje: unidades + "× " + root.dataset.nombre + " en el carrito",
          onDeshacer: function () {
            enCarrito = false;
            render();
          },
        }
      );
      borrarBorrador();
      enCarrito = true;
      render();
    });
  });

  render();
  if (admitePersonalizacion) mostrarPasoPersonalizacion(1, false);
})();
