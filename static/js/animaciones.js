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
