/* Mis pedidos: ver palabra clave, repetir pedido (los filtros y la paginación los resuelve el servidor). */
(function () {
  var root = document.getElementById("mis-pedidos");
  if (!root) return;

  // --- Ver palabra clave ---
  var modalEl = document.getElementById("modalClave");
  var modal = modalEl && window.bootstrap ? new bootstrap.Modal(modalEl) : null;
  root.querySelectorAll(".mp-verclave").forEach(function (b) {
    b.addEventListener("click", function () {
      document.getElementById("clave-num").textContent = b.dataset.clave;
      document.getElementById("clave-hora").textContent = b.dataset.hora;
      if (modal) modal.show();
    });
  });

  // --- Repetir pedido ---
  root.querySelectorAll(".mp-repetir").forEach(function (b) {
    b.addEventListener("click", function () {
      var items;
      try {
        items = JSON.parse(b.dataset.repetir);
      } catch (e) {
        return;
      }
      if (!items || !items.length) return;
      // Se suma al carrito actual (no lo reemplaza) y se queda en la página.
      var actual = window.MusasCarrito.leer();
      window.MusasCarrito.guardar(actual.concat(items));
      window.MusasCarrito.volar(b);
      var n = items.reduce(function (s, it) {
        return s + Number(it.cantidad || 1);
      }, 0);
      window.MusasCarrito.toast(n + " producto(s) agregado(s) al carrito", {
        href: "/carrito",
        accion: "Ver carrito",
      });
    });
  });
})();
