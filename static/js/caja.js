(function () {
  "use strict";

  function enfocarPrimerCampo(modal) {
    var campo = modal.querySelector(
      "input:not([type='hidden']):not([disabled]), select:not([disabled]), textarea:not([disabled])"
    );
    if (campo) window.setTimeout(function () { campo.focus(); }, 120);
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-caja-tipo]").forEach(function (boton) {
      boton.addEventListener("click", function () {
        var selector = document.getElementById("caja-mov-tipo");
        if (selector) selector.value = boton.dataset.cajaTipo || "aporte";
      });
    });

    document.querySelectorAll(".caja-modal").forEach(function (modal) {
      modal.addEventListener("shown.bs.modal", function () {
        enfocarPrimerCampo(modal);
      });
    });

    var resumenHistorico = document.querySelector(
      "#cajaResumenModal[data-caja-auto-resumen]"
    );
    if (resumenHistorico && window.bootstrap && window.bootstrap.Modal) {
      window.bootstrap.Modal.getOrCreateInstance(resumenHistorico).show();
    }
  });
})();
