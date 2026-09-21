/* Foto de perfil: vista previa inmediata antes de guardar. */
(function () {
  "use strict";
  var caja = document.querySelector("[data-perfil-foto]");
  if (!caja) return;
  var archivo = caja.querySelector("[data-foto-archivo]");
  var guardar = caja.querySelector("[data-foto-guardar]");
  var visor = caja.querySelector("[data-foto-visor]");
  var hint = caja.querySelector("[data-foto-hint]");
  var hintOriginal = hint ? hint.textContent : "";
  var MAX = 5 * 1024 * 1024;

  function aviso(texto, error) {
    if (!hint) return;
    hint.textContent = texto;
    hint.classList.toggle("is-error", !!error);
  }

  archivo.addEventListener("change", function () {
    var f = archivo.files && archivo.files[0];
    if (!f) { guardar.hidden = true; aviso(hintOriginal, false); return; }
    if (!/^image\/(png|jpe?g|webp|gif)$/.test(f.type)) {
      archivo.value = ""; guardar.hidden = true; aviso("Elige una imagen JPG, PNG, WEBP o GIF.", true); return;
    }
    if (f.size > MAX) {
      archivo.value = ""; guardar.hidden = true; aviso("La foto pesa más de 5 MB.", true); return;
    }
    var url = URL.createObjectURL(f);
    var img = visor.querySelector("img");
    if (!img) {
      visor.innerHTML = '<span class="perfil-foto__img perfil-foto__img--foto"><img alt="" /></span>';
      img = visor.querySelector("img");
    }
    img.src = url;
    guardar.hidden = false;
    aviso("Así se verá tu foto. Pulsa «Guardar foto» para confirmarla.", false);
  });
})();
