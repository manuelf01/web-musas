const dni = document.querySelector("#dni");
const nombres = document.querySelector("#nombres");
const salida = document.querySelector("#nombreUsuario");

function actualizarUsuario() {
  if (!dni || !nombres || !salida) return;
  const primeraLetra = nombres.value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim()
    .charAt(0)
    .toLowerCase();
  salida.value = primeraLetra && dni.value.length >= 5
    ? `${primeraLetra}${dni.value.slice(0, 5)}`
    : "";
}

dni?.addEventListener("input", actualizarUsuario);
nombres?.addEventListener("input", actualizarUsuario);
