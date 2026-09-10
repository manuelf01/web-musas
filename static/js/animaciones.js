/* Aparición suave al hacer scroll. Sin dependencias.
   Marca [data-reveal] como .is-visible cuando entran al viewport. */
(function () {
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var elementos = document.querySelectorAll("[data-reveal]");
  if (!elementos.length) return;

  if (reduce || !("IntersectionObserver" in window)) {
    elementos.forEach(function (el) { el.classList.add("is-visible"); });
    return;
  }

  var io = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("is-visible");
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.12, rootMargin: "0px 0px -8% 0px" }
  );

  elementos.forEach(function (el) { io.observe(el); });

  // Failsafe: si algo falla, no dejar contenido invisible.
  setTimeout(function () {
    document.querySelectorAll("[data-reveal]:not(.is-visible)").forEach(function (el) {
      var r = el.getBoundingClientRect();
      if (r.top < window.innerHeight) el.classList.add("is-visible");
    });
  }, 2500);
})();

/* "Anatomía de Las Musas": el despiece de la hamburguesa sigue el scroll de la
   sección (efecto "scroll-scrub"). En desktop, pasar el cursor / enfocar la fija
   abierta; un clic la deja fija (útil en táctil). El separado real lo hace el CSS
   con la variable --sep (0 = armada, 1 = despiezada); aquí solo la calculamos.
   Con "reducir movimiento" no se monta nada: el CSS la deja armada. */
(function () {
  var scene = document.querySelector("[data-anat-scene]");
  var burger = scene && scene.querySelector(".anat-burger");
  var seccion = burger && burger.closest(".anatomia");
  if (!scene || !burger || !seccion) return;

  var mm = window.matchMedia;
  if (mm && mm("(prefers-reduced-motion: reduce)").matches) return;

  var fijado = false;      // el cursor/foco/clic manda por encima del scroll
  var pendiente = false;

  function aplicar(v) {
    v = v < 0 ? 0 : v > 1 ? 1 : v;
    scene.style.setProperty("--sep", v.toFixed(3));
    var abierto = v > 0.04;
    burger.classList.toggle("abierto", abierto);
    burger.setAttribute("aria-pressed", v > 0.5 ? "true" : "false");
  }

  function porScroll() {
    if (fijado) return;
    if (pendiente) return;
    pendiente = true;
    requestAnimationFrame(function () {
      pendiente = false;
      var r = seccion.getBoundingClientRect();
      var vh = window.innerHeight || document.documentElement.clientHeight;
      // 0 cuando la sección asoma por abajo; 1 cuando su centro cruza el del viewport.
      var avance = (vh - r.top) / (vh * 0.5 + r.height * 0.5);
      aplicar((avance - 0.12) * 1.35);
    });
  }

  window.addEventListener("scroll", porScroll, { passive: true });
  window.addEventListener("resize", porScroll);
  porScroll();

  if (mm && mm("(hover: hover)").matches) {
    burger.addEventListener("mouseenter", function () { fijado = true; aplicar(1); });
    burger.addEventListener("mouseleave", function () { fijado = false; porScroll(); });
    burger.addEventListener("focus", function () { fijado = true; aplicar(1); });
    burger.addEventListener("blur", function () { fijado = false; porScroll(); });
  }

  burger.addEventListener("click", function () {
    fijado = !burger.classList.contains("abierto");
    aplicar(fijado ? 1 : 0);
  });
})();
