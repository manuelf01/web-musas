/* Avisos del panel: se cierran solos cuando termina la barra de tiempo
   (pausan al pasar el mouse) o con la X. */
(function () {
  function cerrar(el) {
    if (el.classList.contains("is-saliendo")) return;
    el.classList.add("is-saliendo");
    setTimeout(function () { el.remove(); }, 320);
  }
  document.querySelectorAll("[data-aviso]").forEach(function (el) {
    var barra = el.querySelector(".aviso__tiempo");
    if (barra) barra.addEventListener("animationend", function () { cerrar(el); });
    var x = el.querySelector(".aviso__cerrar");
    if (x) x.addEventListener("click", function () { cerrar(el); });
  });
  // «Ver dónde me equivoqué»: reabre el formulario con lo que se escribió,
  // marca el campo con error y explica el motivo.
  var ubicacion = document.querySelector("[data-ver-donde]");
  var datos = document.getElementById("musa-error-form");
  if (ubicacion && datos) {
    var info = JSON.parse(datos.textContent);
    ubicacion.addEventListener("click", function () {
      var caja = ubicacion.closest("[data-aviso]");
      if (caja) cerrar(caja);
      var selector = info.modo === "editar"
        ? '[data-modo="editar"][data-id="' + info.id + '"]'
        : '[data-modo="crear"]';
      var abrir = document.querySelector(selector) || document.querySelector('[data-modo="crear"]');
      if (abrir) abrir.click();
      setTimeout(function () {
        var form = document.querySelector(".adm-panel.abierto form, .adm-modal__backdrop.abierto form, .adm-modal__backdrop.is-abierto form, form[enctype]");
        if (!form) return;
        Object.keys(info.valores || {}).forEach(function (n) {
          var el = form.elements[n];
          if (el && el.type !== "file" && el.type !== "hidden") el.value = info.valores[n];
        });
        var campo = form.elements[info.campo];
        if (!campo) return;
        campo.classList.add("is-invalid");
        var aviso = document.createElement("div");
        aviso.className = "musa-campo-error";
        aviso.innerHTML = '<i class="bi bi-exclamation-circle-fill"></i>';
        aviso.appendChild(document.createTextNode(info.mensaje));
        (campo.closest(".musa-field") || campo.parentNode).appendChild(aviso);
        campo.scrollIntoView({ block: "center", behavior: "smooth" });
        campo.focus();
        var limpiar = function () {
          campo.classList.remove("is-invalid");
          aviso.remove();
          campo.removeEventListener("input", limpiar);
          campo.removeEventListener("change", limpiar);
        };
        campo.addEventListener("input", limpiar);
        campo.addEventListener("change", limpiar);
      }, 260);
    });
  }

  var campo = document.querySelector("input[data-enfocar]");
  if (campo) { campo.focus(); campo.select(); }
})();
