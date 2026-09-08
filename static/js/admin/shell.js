const boton = document.querySelector(".admin-menu-button");
const barra = document.querySelector(".admin-sidebar");
boton?.addEventListener("click", () => barra?.classList.toggle("is-open"));
document.addEventListener("click", (evento) => {
  if (window.innerWidth <= 820 && barra?.classList.contains("is-open") && !barra.contains(evento.target) && !boton?.contains(evento.target)) barra.classList.remove("is-open");
});
