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
   el cursor / enfocar / tocar; vuelve a armarse al salir; un clic la deja fija.
   El separado lo hace el CSS con la var --sep (0 = armada, 1 = despiezada).
   Con "reducir movimiento": la interacción SIGUE funcionando (es a pedido del
   usuario), solo se salta la demo automática y las transiciones son instantáneas
   (eso lo hace el CSS). */
(function () {
  var scene = document.querySelector("[data-anat-scene]");
  var burger = scene && scene.querySelector(".anat-burger");
  if (!scene || !burger) return;

  var mm = window.matchMedia;
  var pocaMotion = mm && mm("(prefers-reduced-motion: reduce)").matches;
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

  burger.addEventListener("mouseenter", function () { interactuo = true; abrir(); });
  burger.addEventListener("mouseleave", cerrar);
  burger.addEventListener("focus", function () { interactuo = true; abrir(); });
  burger.addEventListener("blur", cerrar);
  // En táctil (o cuando el navegador manda click sin hover) alterna fijo.
  burger.addEventListener("click", function () {
    interactuo = true;
    fijado = !burger.classList.contains("abierto");
    aplicar(fijado ? 1 : 0);
  });

  // Texto de la pista según el dispositivo.
  var pista = scene.querySelector("[data-anat-hint-txt]");
  if (pista) {
    pista.textContent = hover
      ? "Pasa el cursor para ver las capas"
      : "Toca para ver las capas";
  }

  // Demo automática al cargar (una vez). Se salta si hay "reducir movimiento"
  // o si el usuario ya interactuó.
  if (!pocaMotion) {
    setTimeout(function () {
      if (interactuo || fijado) return;
      aplicar(1);
      setTimeout(function () { if (!interactuo && !fijado) aplicar(0); }, 2200);
    }, 1100);
  }
})();
