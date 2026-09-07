/* Mis pedidos: filtros, ver palabra clave, repetir pedido. */
(function () {
  var root = document.getElementById("mis-pedidos");
  if (!root) return;

  // --- Filtros ---
  var chips = root.querySelectorAll("[data-filtro]");
  var cards = root.querySelectorAll(".mp-card");
  var avisoVacio = root.querySelector(".mp-vacio-filtro");

  chips.forEach(function (c) {
    c.addEventListener("click", function () {
      chips.forEach(function (x) {
        x.classList.toggle("is-active", x === c);
      });
      var f = c.dataset.filtro;
      var visibles = 0;
      cards.forEach(function (card) {
        var ok = f === "todos" || card.dataset.estado === f;
        card.hidden = !ok;
        if (ok) visibles++;
      });
      if (avisoVacio) avisoVacio.hidden = visibles !== 0;
    });
  });

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
      window.MusasCarrito.guardar(items);
      window.location.href = "/carrito";
    });
  });
})();
