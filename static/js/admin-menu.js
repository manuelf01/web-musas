/* Menú lateral del panel: la hamburguesa de la marca lo contrae/expande.
   Escritorio: se recuerda la elección. Pantallas angostas: el menú está
   contraído y al pulsar se abre encima del contenido (se cierra al tocar fuera). */
(function () {
  "use strict";
  var html = document.documentElement;
  var boton = document.querySelector("[data-adm-toggle]");
  if (!boton) return;
  var angosta = window.matchMedia("(max-width: 900px)");

  function compacto() {
    return angosta.matches ? !html.classList.contains("adm-abierto") : html.classList.contains("adm-colapsado");
  }

  function pintar() {
    var c = compacto();
    boton.setAttribute("aria-expanded", c ? "false" : "true");
    var texto = c ? "Expandir menú" : "Contraer menú";
    boton.setAttribute("aria-label", texto);
    boton.title = texto;
  }

  boton.addEventListener("click", function () {
    if (angosta.matches) {
      html.classList.toggle("adm-abierto");
    } else {
      var contraido = html.classList.toggle("adm-colapsado");
      try { localStorage.setItem("musa.adm.menu", contraido ? "colapsado" : "expandido"); } catch (e) {}
    }
    pintar();
  });

  document.addEventListener("click", function (e) {
    if (angosta.matches && html.classList.contains("adm-abierto") && !e.target.closest(".adm-side")) {
      html.classList.remove("adm-abierto");
      pintar();
    }
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && html.classList.contains("adm-abierto")) {
      html.classList.remove("adm-abierto");
      pintar();
      boton.focus();
    }
  });
  var cambio = function () { html.classList.remove("adm-abierto"); pintar(); };
  if (angosta.addEventListener) angosta.addEventListener("change", cambio);
  else if (angosta.addListener) angosta.addListener(cambio);

  // ---- Módulos: acordeón (barra expandida) y ventana flotante (barra contraída)
  var GUARDADO = "musa.adm.grupos";
  var grupos = document.querySelectorAll(".adm-grupo");
  var recordados = [];
  try { recordados = JSON.parse(localStorage.getItem(GUARDADO) || "[]"); } catch (e) {}
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
