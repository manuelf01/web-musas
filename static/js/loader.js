/* Loader global: primera carga, enlaces internos y envíos de formularios. */
(function () {
  "use strict";

  var loader = document.querySelector("[data-musa-loader]");
  if (!loader) return;

  var inicio = Date.now();
  var minimoInicial = 320;
  var temporizadorEspera;
  var temporizadorOcultar;
  var temporizadorSeguridad;

  function mostrar() {
    clearTimeout(temporizadorEspera);
    clearTimeout(temporizadorOcultar);
    clearTimeout(temporizadorSeguridad);
    loader.hidden = false;
    loader.setAttribute("aria-hidden", "false");
    document.documentElement.classList.add("musa-cargando");
    requestAnimationFrame(function () {
      loader.classList.remove("is-oculto");
    });
    // Si una descarga o un navegador evita la navegación, la UI no queda bloqueada.
    temporizadorSeguridad = setTimeout(function () { ocultar(0); }, 10000);
  }

  function ocultar(espera) {
    clearTimeout(temporizadorEspera);
    clearTimeout(temporizadorOcultar);
    clearTimeout(temporizadorSeguridad);
    temporizadorEspera = setTimeout(function () {
      loader.classList.add("is-oculto");
      loader.setAttribute("aria-hidden", "true");
      document.documentElement.classList.remove("musa-cargando");
      temporizadorOcultar = setTimeout(function () { loader.hidden = true; }, 360);
    }, Math.max(0, espera || 0));
  }

  function ocultarInicial() {
    ocultar(Math.max(0, minimoInicial - (Date.now() - inicio)));
  }

  function enlaceNavegable(evento, enlace) {
    if (!enlace || evento.defaultPrevented || evento.button !== 0) return false;
    if (evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey) return false;
    if (enlace.hasAttribute("download") || enlace.dataset.loaderSkip !== undefined) return false;
    if (enlace.target && enlace.target.toLowerCase() !== "_self") return false;
    if (enlace.hasAttribute("data-confirm")) return false;
    var destino;
    try { destino = new URL(enlace.href, window.location.href); } catch (error) { return false; }
    if (destino.origin !== window.location.origin) return false;
    if (destino.protocol !== "http:" && destino.protocol !== "https:") return false;
    return !(destino.pathname === window.location.pathname &&
      destino.search === window.location.search && destino.hash);
  }

  document.addEventListener("click", function (evento) {
    var enlace = evento.target.closest && evento.target.closest("a[href]");
    if (enlaceNavegable(evento, enlace)) mostrar();
  }, true);

  document.addEventListener("submit", function (evento) {
    var formulario = evento.target;
    if (!formulario || formulario.nodeName !== "FORM" || evento.defaultPrevented) return;
    var confirmable = formulario.hasAttribute("data-confirm") ||
      (evento.submitter && evento.submitter.hasAttribute("data-confirm"));
    if (confirmable && formulario.dataset.confirmHecho !== "1") return;
    setTimeout(function () {
      if (!evento.defaultPrevented) mostrar();
    }, 0);
  }, true);

  window.addEventListener("load", ocultarInicial, { once: true });
  window.addEventListener("pageshow", function (evento) {
    if (evento.persisted) ocultar(0);
  });
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) ocultar(0);
  });

  window.MusasLoader = { mostrar: mostrar, ocultar: ocultar };
})();
