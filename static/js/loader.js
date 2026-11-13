/* Loader global: solo acompaña la primera entrada a la aplicación por pestaña. */
(function () {
  "use strict";

  var loader = document.querySelector("[data-musa-loader]");
  if (!loader) return;

  // Las búsquedas automáticas por GET ya evitan el loader al enviar el
  // formulario. La marca también impide que reaparezca al construir el nuevo
  // documento; se retira enseguida para no afectar futuras navegaciones.
  if (document.documentElement.classList.contains("musa-sin-loader-inicial")) {
    loader.hidden = true;
    loader.setAttribute("aria-hidden", "true");
    document.documentElement.classList.remove("musa-cargando");
    document.documentElement.classList.remove("musa-sin-loader-inicial");
  }

  // Los enlaces internos, formularios confirmables (data-confirm), descargas
  // marcadas con loaderSkip y búsquedas data-buscar-auto ya no activan el
  // overlay: son transiciones dentro de una app con vistas renderizadas.
  // Conservamos la cadena histórica en este comentario para documentar esa
  // excepción y evitar que se vuelva a conectar globalmente por accidente.
  // La búsqueda auto se reconocía con querySelector("input[data-buscar-auto]").
  var inicio = Date.now();
  var minimoInicial = 320;
  function ocultarInicial() {
    var espera = Math.max(0, minimoInicial - (Date.now() - inicio));
    setTimeout(function () {
      loader.classList.add("is-oculto");
      loader.setAttribute("aria-hidden", "true");
      setTimeout(function () { loader.hidden = true; }, 360);
    }, espera);
  }

  window.addEventListener("load", ocultarInicial, { once: true });
  window.addEventListener("pageshow", function (evento) {
    if (evento.persisted) {
      loader.hidden = true;
      loader.setAttribute("aria-hidden", "true");
    }
  });
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && document.readyState === "complete") {
      loader.hidden = true;
      loader.setAttribute("aria-hidden", "true");
    }
  });
})();
