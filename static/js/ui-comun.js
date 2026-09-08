/* UI comun: mostrar/ocultar contrasena + filtrado en vivo de listas. */
(function () {
  "use strict";

  // --- Mostrar / ocultar contrasena --------------------------------
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-toggle-pass]");
    if (!btn) return;
    var input = document.getElementById(btn.dataset.togglePass);
    if (!input) return;
    var oculto = input.type === "password";
    input.type = oculto ? "text" : "password";
    var icono = btn.querySelector("i");
    if (icono) icono.className = oculto ? "bi bi-eye-slash" : "bi bi-eye";
    btn.setAttribute("aria-pressed", oculto ? "true" : "false");
  });

  // --- Filtrado en vivo (sin Enter) --------------------------------
  // <input data-filtro-vivo="#scope"> filtra los [data-filtro-item] dentro de #scope
  // opcional: [data-filtro-seccion] (se oculta si no le quedan items visibles)
  //           [data-filtro-vacio]   (se muestra si no hay ningun resultado)
  //           data-filtro-texto en el item para acotar que texto se busca
  var COMBINABLES = new RegExp("[\\u0300-\\u036f]", "g");

  function normalizar(s) {
    return (s || "").toString().toLowerCase().normalize("NFD").replace(COMBINABLES, "");
  }

  function conectar(input) {
    var scope = document.querySelector(input.getAttribute("data-filtro-vivo"));
    if (!scope) return;
    var items = scope.querySelectorAll("[data-filtro-item]");
    var secciones = scope.querySelectorAll("[data-filtro-seccion]");
    var vacio = scope.querySelector("[data-filtro-vacio]");

    function aplicar() {
      var q = normalizar(input.value.trim());
      var visibles = 0;
      items.forEach(function (el) {
        var txt = normalizar(el.getAttribute("data-filtro-texto") || el.textContent);
        var ok = !q || txt.indexOf(q) !== -1;
        el.hidden = !ok;
        if (ok) visibles++;
      });
      secciones.forEach(function (sec) {
        sec.hidden = !!q && !sec.querySelector("[data-filtro-item]:not([hidden])");
      });
      if (vacio) vacio.hidden = !(q && visibles === 0);
    }

    input.addEventListener("input", aplicar);
    input.addEventListener("search", aplicar);
    aplicar();
  }

  document.querySelectorAll("[data-filtro-vivo]").forEach(conectar);
})();
