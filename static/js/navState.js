import { obtenerCarrito } from "./carritoStorage.js";

function actualizarCarritoGlobal() {
  const carrito = obtenerCarrito();
  const cantidad = carrito.reduce((total, item) => total + Number(item.cantidad || 0), 0);
  const importe = carrito.reduce((total, item) => total + Number(item.precio || 0) * Number(item.cantidad || 0), 0);
  document.querySelectorAll("[data-cart-count]").forEach((nodo) => { nodo.textContent = cantidad; });
  document.querySelectorAll("[data-cart-total]").forEach((nodo) => { nodo.textContent = `S/ ${importe.toFixed(2)}`; });
  const barra = document.querySelector(".button-carrito");
  const pagina = document.body.dataset.page || "";
  barra?.classList.toggle("is-visible", cantidad > 0 && !pagina.endsWith("pag_carrito") && !pagina.endsWith("pag_compra"));
}

document.addEventListener("DOMContentLoaded", actualizarCarritoGlobal);
window.addEventListener("storage", actualizarCarritoGlobal);
window.addEventListener("cart:updated", actualizarCarritoGlobal);
export { actualizarCarritoGlobal };
