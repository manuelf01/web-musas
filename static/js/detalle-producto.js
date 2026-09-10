/* Detalle de producto: stepper de cantidad, total en vivo y agregar al carrito. */
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
          : "Agregar al carrito — S/ " + t;
      }
    });
    if (verCarrito) verCarrito.hidden = !enCarrito;
  }

  // Cambiar cantidad o cremas = otra combinación -> se puede volver a agregar.
  function reactivar() {
    if (enCarrito) enCarrito = false;
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
          href: carritoUrl,
          mensaje: unidades + "× " + root.dataset.nombre + " en el carrito",
        }
      );
      enCarrito = true;
      render();
    });
  });

  render();
})();
