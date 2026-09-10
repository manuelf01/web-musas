/* UI comun: mostrar/ocultar contrasena + filtrado en vivo + modal de confirmacion. */
(function () {
  "use strict";

  // --- Mostrar / ocultar contrasena --------------------------------
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-toggle-pass]");
    if (!btn) return;
    var input = document.getElementById(btn.dataset.togglePass);
    if (!input) return;
    var oculto = input.type === "password";
    input.type = oculto ? "text" : "password";
    var icono = btn.querySelector("i");
    if (icono) icono.className = oculto ? "bi bi-eye-slash" : "bi bi-eye";
    btn.setAttribute("aria-pressed", oculto ? "true" : "false");
  });

  // --- Filtrado en vivo (sin Enter) --------------------------------
  // <input data-filtro-vivo="#scope"> filtra los [data-filtro-item] dentro de #scope
  // opcional: [data-filtro-seccion] (se oculta si no le quedan items visibles)
  //           [data-filtro-vacio]   (se muestra si no hay ningun resultado)
  //           data-filtro-texto en el item para acotar que texto se busca
  var COMBINABLES = new RegExp("[\\u0300-\\u036f]", "g");

  function normalizar(s) {
    return (s || "").toString().toLowerCase().normalize("NFD").replace(COMBINABLES, "");
  }

  function conectar(input) {
    var sel = input.getAttribute("data-filtro-vivo");
    if (!document.querySelector(sel)) return;

    function aplicar() {
      // Se re-consulta el DOM en cada tecla: así el filtro sigue funcionando
      // aunque la lista se haya vuelto a renderizar (p. ej. cocina en vivo).
      var scope = document.querySelector(sel);
      if (!scope) return;
      var items = scope.querySelectorAll("[data-filtro-item]");
      var secciones = scope.querySelectorAll("[data-filtro-seccion]");
      var vacio = scope.querySelector("[data-filtro-vacio]");
      var q = normalizar(input.value.trim());
      var visibles = 0;
      items.forEach(function (el) {
        var txt = normalizar(el.getAttribute("data-filtro-texto") || el.textContent);
        var ok = !q || txt.indexOf(q) !== -1;
        el.hidden = !ok;
        if (ok) visibles++;
      });
      secciones.forEach(function (sec) {
        sec.hidden = !!q && !sec.querySelector("[data-filtro-item]:not([hidden])");
      });
      if (vacio) vacio.hidden = !(q && visibles === 0);
    }

    input.addEventListener("input", aplicar);
    input.addEventListener("search", aplicar);
    aplicar();
  }

  document.querySelectorAll("[data-filtro-vivo]").forEach(conectar);

  // --- Modal de confirmacion (todos los CRUD + cancelaciones) ------
  // Uso: en un <form>, en su <button type="submit"> o en un <a>:
  //   data-confirm="texto que explica lo que va a pasar"
  //   data-confirm-titulo="..."   data-confirm-ok="..."   data-confirm-cancelar="..."
  //   data-confirm-tono="peligro"   data-confirm-icono="bi-..."
  var overlay, card, elIcono, elTitulo, elTexto, btnSi, btnNo, resolver, ultimoFoco;

  function construir() {
    overlay = document.createElement("div");
    overlay.className = "musa-confirm";
    overlay.hidden = true;
    overlay.innerHTML =
      '<div class="musa-confirm__backdrop" data-no></div>' +
      '<div class="musa-confirm__card" role="alertdialog" aria-modal="true" aria-labelledby="musaConfirmTitulo">' +
      '<span class="musa-confirm__icono"><i class="bi bi-question-lg"></i></span>' +
      '<h3 class="musa-confirm__titulo" id="musaConfirmTitulo"></h3>' +
      '<p class="musa-confirm__texto"></p>' +
      '<div class="musa-confirm__botones">' +
      '<button type="button" class="musa-confirm__no" data-no></button>' +
      '<button type="button" class="musa-confirm__si"></button>' +
      "</div></div>";
    document.body.appendChild(overlay);
    card = overlay.querySelector(".musa-confirm__card");
    elIcono = overlay.querySelector(".musa-confirm__icono i");
    elTitulo = overlay.querySelector(".musa-confirm__titulo");
    elTexto = overlay.querySelector(".musa-confirm__texto");
    btnSi = overlay.querySelector(".musa-confirm__si");
    btnNo = overlay.querySelector(".musa-confirm__no");

    btnSi.addEventListener("click", function () { cerrar(true); });
    overlay.addEventListener("click", function (e) {
      if (e.target.hasAttribute("data-no")) cerrar(false);
    });
    document.addEventListener("keydown", function (e) {
      if (overlay.hidden) return;
      if (e.key === "Escape") { e.preventDefault(); cerrar(false); }
      // Enter activa el botón enfocado: también debe respetar "Cancelar".
      else if (e.key === "Tab") {
        e.preventDefault();
        (document.activeElement === btnSi ? btnNo : btnSi).focus();
      }
    });
  }

  function cerrar(ok) {
    if (!overlay || overlay.hidden) return;
    overlay.classList.remove("is-abierto");
    var terminado = false;
    var fin = function () {
      if (terminado) return;
      terminado = true;
      overlay.hidden = true;
      overlay.removeEventListener("transitionend", fin);
      if (ultimoFoco && ultimoFoco.focus) { try { ultimoFoco.focus(); } catch (e) {} }
      var r = resolver; resolver = null;
      if (r) r(ok);
    };
    overlay.addEventListener("transitionend", fin);
    setTimeout(fin, 340);
  }

  function pedir(opts) {
    opts = opts || {};
    if (!overlay) construir();
    ultimoFoco = document.activeElement;
    elTitulo.textContent = opts.titulo || "¿Confirmar acción?";
    elTexto.textContent = opts.texto || "";
    elTexto.hidden = !opts.texto;
    btnSi.textContent = opts.ok || "Sí, continuar";
    btnNo.textContent = opts.cancelar || "Cancelar";
    var peligro = opts.tono === "peligro";
    card.classList.toggle("es-peligro", peligro);
    btnSi.classList.toggle("es-peligro", peligro);
    elIcono.className = "bi " + (opts.icono || (peligro ? "bi-exclamation-triangle" : "bi-question-lg"));
    overlay.hidden = false;
    void overlay.offsetWidth;
    overlay.classList.add("is-abierto");
    (peligro ? btnNo : btnSi).focus();
    return new Promise(function (res) { resolver = res; });
  }

  function opcionesDe(el) {
    return {
      texto: el.getAttribute("data-confirm") || "",
      titulo: el.getAttribute("data-confirm-titulo"),
      ok: el.getAttribute("data-confirm-ok"),
      cancelar: el.getAttribute("data-confirm-cancelar"),
      tono: el.getAttribute("data-confirm-tono"),
      icono: el.getAttribute("data-confirm-icono"),
    };
  }

  document.addEventListener("submit", function (e) {
    var form = e.target;
    if (!form || form.nodeName !== "FORM") return;
    if (form.dataset.confirmHecho === "1") { delete form.dataset.confirmHecho; return; }

    var sub = e.submitter || null;
    var disparador = null;
    var desdeBoton = sub && sub.closest ? sub.closest("[data-confirm]") : null;
    if (desdeBoton && form.contains(desdeBoton)) disparador = desdeBoton;
    else if (form.hasAttribute("data-confirm")) disparador = form;
    if (!disparador) return;

    e.preventDefault();
    e.stopPropagation();
    pedir(opcionesDe(disparador)).then(function (ok) {
      if (!ok) return;
      form.dataset.confirmHecho = "1";
      if (sub && form.requestSubmit) form.requestSubmit(sub);
      else if (form.requestSubmit) form.requestSubmit();
      else form.submit();
    });
  }, true);

  document.addEventListener("click", function (e) {
    var a = e.target.closest("a[data-confirm]");
    if (!a) return;
    if (a.dataset.confirmHecho === "1") { delete a.dataset.confirmHecho; return; }
    e.preventDefault();
    e.stopPropagation();
    pedir(opcionesDe(a)).then(function (ok) {
      if (ok) {
        if (window.MusasLoader) window.MusasLoader.mostrar();
        window.location.href = a.href;
      }
    });
  }, true);

  window.MusaConfirm = pedir;
})();
