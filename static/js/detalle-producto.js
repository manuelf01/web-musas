/* Detalle de producto: stepper de cantidad, total en vivo y agregar al carrito. */
(function () {
  var root = document.getElementById("detalle-producto");
  if (!root) return;

  var base = Number(root.dataset.precio) || 0;
  var qtyEl = document.getElementById("dp-qty");
  var mobPrecio = document.getElementById("dp-mob-precio");
  var mobQty = document.getElementById("dp-mob-qty");
  var qty = 1;

  function btnTextos() {
    return document.querySelectorAll("[data-dp-btn-texto]");
  }

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
    var t = total().toFixed(2);
    if (qtyEl) qtyEl.textContent = qty;
    btnTextos().forEach(function (el) {
      el.textContent = "Agregar al carrito — S/ " + t;
    });
    if (mobPrecio) mobPrecio.textContent = "S/ " + t;
    if (mobQty) mobQty.textContent = qty;
  }

  document.querySelectorAll("[data-step]").forEach(function (b) {
    b.addEventListener("click", function () {
      qty = Math.max(1, qty + Number(b.dataset.step));
      render();
    });
  });

  document.querySelectorAll(".crema-check").forEach(function (c) {
    c.addEventListener("change", render);
  });

  var agregando = false;
  document.querySelectorAll("[data-agregar]").forEach(function (b) {
    b.addEventListener("click", function () {
      if (agregando) return;
      agregando = true;

      var unidades = qty;
      window.MusasCarrito.agregarConAnim(
        {
          idProducto: Number(root.dataset.id),
          nombre: root.dataset.nombre,
          precio: base,
          imagen: root.dataset.imagen || null,
          cantidad: unidades,
          cremas: cremasSeleccionadas(),
        },
        b,
        {
          href: root.dataset.carritoUrl,
          mensaje: unidades + "× " + root.dataset.nombre + " en el carrito",
        }
      );

      // Estado de confirmación del botón (sin sacar al cliente de la página).
      var span = b.querySelector("[data-dp-btn-texto]");
      var icono = b.querySelector("i");
      var icoPrev = icono ? icono.className : null;
      b.classList.add("is-ok");
      if (icono) icono.className = "bi bi-check-lg";
      if (span) span.textContent = "¡Agregado!";
      setTimeout(function () {
        b.classList.remove("is-ok");
        if (icono && icoPrev) icono.className = icoPrev;
        qty = 1;
        render();
        agregando = false;
      }, 1400);
    });
  });

  render();
})();
