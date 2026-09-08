import { obtenerCremas } from "./fetchApis.js";
import { obtenerCarrito } from "./carritoStorage.js";

const mapCremas = new Map();
const contenedor = document.querySelector(".productos-comprar");

function moneda(valor) { return `S/ ${Number(valor).toFixed(2)}`; }
function pintar() {
  if (!contenedor) return;
  const carrito = obtenerCarrito();
  contenedor.replaceChildren();
  carrito.forEach((producto) => {
    const fila = document.createElement("div");
    fila.className = "summary-line";
    const detalle = document.createElement("span");
    const nombre = document.createElement("strong");
    nombre.textContent = `${producto.cantidad}× ${producto.nombre}`;
    detalle.appendChild(nombre);
    const salsas = (producto.cremas || []).map((id) => mapCremas.get(id)).filter(Boolean).join(", ");
    if (salsas) { const small = document.createElement("small"); small.className = "field-help"; small.textContent = salsas; detalle.appendChild(small); }
    const precio = document.createElement("strong"); precio.textContent = moneda(Number(producto.precio) * Number(producto.cantidad));
    fila.append(detalle, precio); contenedor.appendChild(fila);
  });
  const total = carrito.reduce((suma, item) => suma + Number(item.precio) * Number(item.cantidad), 0);
  const salida = document.querySelector("#checkout-total"); if (salida) salida.textContent = moneda(total);
}

document.addEventListener("DOMContentLoaded", async () => { await obtenerCremas(mapCremas); pintar(); });
