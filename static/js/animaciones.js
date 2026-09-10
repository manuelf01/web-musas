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

/* Hero: la hamburguesa se despieza. ARRANCA ARMADA (--sep 0). Se abre al pasar
   el cursor / enfocar (desktop) y con un toque (móvil); vuelve a armarse al
   salir. Al cargar hace UNA demo: se abre y se vuelve a cerrar sola, para que
   se note que es interactiva. El separado lo hace el CSS con la var --sep
   (0 = armada, 1 = despiezada). Con "reducir movimiento" no se monta nada. */
(function () {
  var scene = document.querySelector("[data-anat-scene]");
  var burger = scene && scene.querySelector(".anat-burger");
  if (!scene || !burger) return;

  var mm = window.matchMedia;
  if (mm && mm("(prefers-reduced-motion: reduce)").matches) return;

  var hover = mm && mm("(hover: hover)").matches;
  var fijado = false;       // clic: deja la hamburguesa fija abierta/cerrada
  var interactuo = false;   // el usuario ya tocó/pasó el cursor -> se corta la demo

  function aplicar(v) {
    v = v < 0 ? 0 : v > 1 ? 1 : v;
    scene.style.setProperty("--sep", v.toFixed(3));
    burger.classList.toggle("abierto", v > 0.04);
    burger.setAttribute("aria-pressed", v > 0.5 ? "true" : "false");
  }

  function abrir()  { aplicar(1); }
  function cerrar() { if (!fijado) aplicar(0); }

  if (hover) {
    burger.addEventListener("mouseenter", function () { interactuo = true; abrir(); });
    burger.addEventListener("mouseleave", cerrar);
  }
  burger.addEventListener("focus", function () { interactuo = true; abrir(); });
  burger.addEventListener("blur", cerrar);

  burger.addEventListener("click", function () {
    interactuo = true;
    fijado = !burger.classList.contains("abierto");
    aplicar(fijado ? 1 : 0);
  });

  // Pista distinta según el dispositivo.
  var pista = scene.querySelector("[data-anat-hint-txt]");
  if (pista && !hover) pista.textContent = "Toca para ver las capas";

  // Demo automática al cargar (una sola vez, si el usuario no interactuó antes).
  setTimeout(function () {
    if (interactuo || fijado) return;
    aplicar(1);
    setTimeout(function () { if (!interactuo && !fijado) aplicar(0); }, 2200);
  }, 1100);
})();
