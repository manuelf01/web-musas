/* Preferencia visual compartida entre tienda y panel. */
(function () {
  "use strict";
  var clave = "musa.tema";
  var raiz = document.documentElement;

  function aplicar(preferencia) {
    if (preferencia !== "claro" && preferencia !== "oscuro" && preferencia !== "sistema") preferencia = "sistema";
    var oscuro = preferencia === "oscuro" ||
      (preferencia === "sistema" && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    raiz.dataset.themePreference = preferencia;
    raiz.dataset.theme = oscuro ? "dark" : "light";
    document.querySelectorAll("[data-theme-switch]").forEach(function (control) {
      control.checked = oscuro;
      control.setAttribute("aria-checked", oscuro ? "true" : "false");
    });
  }

  var inicial = "sistema";
  try { inicial = localStorage.getItem(clave) || "sistema"; } catch (e) {}
  aplicar(inicial);

  document.addEventListener("change", function (evento) {
    var control = evento.target.closest("[data-theme-switch]");
    if (!control) return;
    var preferencia = control.checked ? "oscuro" : "claro";
    try { localStorage.setItem(clave, preferencia); } catch (e) {}
    aplicar(preferencia);
  });

  if (window.matchMedia) {
    var media = window.matchMedia("(prefers-color-scheme: dark)");
    var actualizarSistema = function () {
      if ((raiz.dataset.themePreference || inicial) === "sistema") aplicar("sistema");
    };
    if (media.addEventListener) media.addEventListener("change", actualizarSistema);
    else if (media.addListener) media.addListener(actualizarSistema);
  }
})();
