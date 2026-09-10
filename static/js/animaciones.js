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

/* "Anatomía de Las Musas": el despiece funciona con :hover en CSS, pero algunos
   navegadores (Brave con escudos, Firefox en ciertos casos) no propagan bien
   el :hover a los <g> del SVG — así que también lo movemos con JS. Click fija /
   suelta; en pantallas táctiles se abre solo al entrar en el viewport. */
(function () {
  var burger = document.querySelector(".anat-burger");
  if (!burger) return;

  var mm = window.matchMedia;
  // Con "reducir movimiento" el CSS ya muestra la lista de ingredientes armada:
  // no montamos ninguna interacción de despiece.
  if (mm && mm("(prefers-reduced-motion: reduce)").matches) return;

  var fijado = false;

  function marcar(abierto) {
    burger.classList.toggle("abierto", abierto);
    burger.setAttribute("aria-pressed", abierto ? "true" : "false");
  }

  burger.addEventListener("click", function () {
    fijado = !burger.classList.contains("abierto");
    marcar(fijado);
  });
  burger.addEventListener("mouseenter", function () { marcar(true); });
  burger.addEventListener("mouseleave", function () { if (!fijado) marcar(false); });

  var tactil = mm && mm("(hover: none)").matches;
  if (tactil && "IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        marcar(true);
        fijado = true;
        io.disconnect();
      });
    }, { threshold: 0.55 });
    io.observe(burger);
  }
})();
