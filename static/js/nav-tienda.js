/* Cabecera de tienda: en escritorio se compacta al avanzar por la carta.
   En móvil manda la barra inferior y no se aplica este comportamiento. */
(function () {
  var raiz = document.documentElement;
  var escritorio = window.matchMedia("(min-width: 769px)");
  var pendiente = false;

  function actualizar() {
    raiz.classList.toggle("musa-nav-compacta", escritorio.matches && window.scrollY > 48);
    pendiente = false;
  }

  function solicitarActualizacion() {
    if (pendiente) return;
    pendiente = true;
    window.requestAnimationFrame(actualizar);
  }

  window.addEventListener("scroll", solicitarActualizacion, { passive: true });
  window.addEventListener("resize", solicitarActualizacion);
  window.addEventListener("pageshow", actualizar);
  actualizar();
})();
