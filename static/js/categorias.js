document.addEventListener("DOMContentLoaded", () => {
  categoriasFija();
});

function categoriasFija() {
  const breakPoint = document.querySelector(".categorias-content");

  const categorias_lista = document.querySelector(".categorias");

  if (!breakPoint || !categorias_lista) return;

  window.addEventListener("scroll", () => {
    // console.log(breakPoint.getBoundingClientRect());
    const aviso = breakPoint.getBoundingClientRect().y;

    if (aviso < 30) {
      categorias_lista.classList.add("fijo");
    } else {
      categorias_lista.classList.remove("fijo");
    }
  });
}
