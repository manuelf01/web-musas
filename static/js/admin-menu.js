/* Admin navigation: desktop collapse and Bootstrap responsive offcanvas on mobile. */
(function () {
  "use strict";
  var html = document.documentElement;
  var boton = document.querySelector("[data-adm-toggle]");
  if (!boton) return;
  var movil = window.matchMedia("(max-width: 991.98px)");

  function compacto() {
    return !movil.matches && html.classList.contains("adm-colapsado");
  }

  function pintar() {
    var c = compacto();
    boton.setAttribute("aria-expanded", c ? "false" : "true");
    var texto = c ? "Expandir menú" : "Contraer menú";
    boton.setAttribute("aria-label", texto);
    boton.title = texto;
  }

  boton.addEventListener("click", function () {
    var contraido = html.classList.toggle("adm-colapsado");
    try { localStorage.setItem("musa.adm.menu", contraido ? "colapsado" : "expandido"); } catch (e) {}
    pintar();
  });

  // ---- Módulos: acordeón (barra expandida) y ventana flotante (barra contraída)
  var GUARDADO = "musa.adm.grupos";
  var grupos = document.querySelectorAll(".adm-grupo");
  var recordados = [];
  try {
    var gruposGuardados = JSON.parse(localStorage.getItem(GUARDADO) || "[]");
    if (Array.isArray(gruposGuardados)) recordados = gruposGuardados;
  } catch (e) {}
  function recordar() {
    var abiertos = [];
    grupos.forEach(function (g) { if (g.classList.contains("is-abierto")) abiertos.push(g.dataset.grupo); });
    try { localStorage.setItem(GUARDADO, JSON.stringify(abiertos)); } catch (e) {}
  }
  function cerrarFlotantes(salvo) {
    grupos.forEach(function (g) { if (g !== salvo) g.classList.remove("is-flyout"); });
  }
  grupos.forEach(function (g) {
    var cab = g.querySelector(".adm-grupo__cab");
    if (recordados.indexOf(g.dataset.grupo) !== -1) g.classList.add("is-abierto");
    cab.setAttribute("aria-expanded", g.classList.contains("is-abierto") ? "true" : "false");
    cab.addEventListener("click", function (e) {
      e.stopPropagation();
      if (compacto()) {
        cerrarFlotantes(g);
        g.classList.toggle("is-flyout");
      } else {
        var abierto = g.classList.toggle("is-abierto");
        cab.setAttribute("aria-expanded", abierto ? "true" : "false");
        recordar();
      }
    });
  });
  document.addEventListener("click", function () { cerrarFlotantes(null); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") cerrarFlotantes(null); });

  pintar();
  // Las transiciones se activan tras el primer pintado para que no "salte" al cargar.
  requestAnimationFrame(function () { requestAnimationFrame(function () { html.classList.add("adm-anima"); }); });
})();
