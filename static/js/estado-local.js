/* Actualiza los avisos con la hora del servidor, incluso con la página abierta. */
(() => {
  "use strict";
  const avisos = document.querySelectorAll("[data-estado-local]");
  if (!avisos.length) return;
  let temporizador;
  let consultando = false;

  async function actualizar() {
    if (consultando) return;
    clearTimeout(temporizador);
    if (document.hidden) return;
    consultando = true;
    let espera = 30000;
    try {
      const respuesta = await fetch(avisos[0].dataset.estadoUrl, { cache: "no-store" });
      if (!respuesta.ok) throw new Error("No se pudo consultar el horario");
      const estado = await respuesta.json();
      avisos.forEach((aviso) => {
        const texto = aviso.querySelector("[data-estado-texto]");
        texto.textContent = estado.texto;
        aviso.classList.toggle("local-cerrado", !estado.abierto);
      });
      // Reconsulta justo al abrir/cerrar y al menos una vez por minuto.
      espera = Math.min(60000, Math.max(250, estado.cambia_en * 1000 + 50));
    } catch (_) {
      // Conserva el último estado válido y vuelve a intentar.
    } finally {
      consultando = false;
      temporizador = setTimeout(actualizar, espera);
    }
  }
  document.addEventListener("visibilitychange", actualizar);
  actualizar();
})();
