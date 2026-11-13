/* Accesibilidad común para los modales propios del panel administrativo. */
(function () {
  var ultimoFoco = null;

  function visibles(panel) {
    return Array.prototype.filter.call(
      panel.querySelectorAll('button:not([disabled]), [href], input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'),
      function (el) { return el.offsetParent !== null; }
    );
  }

  function alAbrir(panel) {
    ultimoFoco = document.activeElement;
    panel.setAttribute("aria-hidden", "false");
    window.setTimeout(function () {
      var foco = panel.querySelector("[data-enfocar]") || visibles(panel)[0];
      if (foco) foco.focus();
    }, 80);
  }

  function alCerrar(panel) {
    panel.setAttribute("aria-hidden", "true");
    if (ultimoFoco && document.contains(ultimoFoco)) ultimoFoco.focus();
    ultimoFoco = null;
  }

  document.querySelectorAll(".adm-panel").forEach(function (panel) {
    new MutationObserver(function () {
      if (panel.classList.contains("abierto")) alAbrir(panel);
      else alCerrar(panel);
    }).observe(panel, { attributes: true, attributeFilter: ["class"] });

    panel.addEventListener("keydown", function (ev) {
      if (ev.key !== "Tab") return;
      var elementos = visibles(panel);
      if (!elementos.length) return;
      var primero = elementos[0];
      var ultimo = elementos[elementos.length - 1];
      if (ev.shiftKey && document.activeElement === primero) {
        ev.preventDefault(); ultimo.focus();
      } else if (!ev.shiftKey && document.activeElement === ultimo) {
        ev.preventDefault(); primero.focus();
      }
    });
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Escape") return;
    var panel = document.querySelector(".adm-panel.abierto");
    if (!panel) return;
    var cerrar = panel.querySelector("[data-panel-cerrar], [data-cat-cerrar], [data-user-cerrar], [data-medio-cerrar], .adm-panel__cerrar");
    if (cerrar) cerrar.click();
  });
})();
