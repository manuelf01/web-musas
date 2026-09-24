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

  function validarPersonalizacion() {
    if (!admitePersonalizacion) return true;
    var ok = true;
    document.querySelectorAll("[data-grupo-req]").forEach(function (grupo) {
      var req = grupo.dataset.grupoReq;
      var marcados = grupo.querySelectorAll(".crema-check:checked").length;
      var valido = marcados >= 1;
      grupo.classList.toggle("is-invalido", !valido);
      var error = grupo.querySelector("[data-grupo-error]");
      if (error) error.hidden = valido;
      if (!valido) ok = false;
    });
    return ok;
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
  }

  // Cambiar cantidad o cremas = otra combinación -> se puede volver a agregar.
  function reactivar() {
    if (enCarrito) enCarrito = false;
    guardarBorrador();
    render();
  }

  document.querySelectorAll("[data-step]").forEach(function (b) {
    b.addEventListener("click", function () {
      qty = Math.max(1, qty + Number(b.dataset.step));
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
        if (primero) primero.scrollIntoView({ block: "center", behavior: "smooth" });
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
        }
      );
      borrarBorrador();
      enCarrito = true;
      render();
    });
  });

  render();
})();
