import { obtenerCremas } from "./fetchApis.js";
import { guardarCarrito, obtenerCarrito, vaciarCarrito } from "./carritoStorage.js";

const mapCremas = new Map();
const contenedor = document.querySelector(".productos-carrito");
const vaciar = document.querySelector("#vaciar-carrito");

function moneda(valor) { return `S/ ${Number(valor).toFixed(2)}`; }
function nodo(etiqueta, clase, texto) {
  const elemento = document.createElement(etiqueta);
  if (clase) elemento.className = clase;
  if (texto !== undefined) elemento.textContent = texto;
  return elemento;
}

function guardarYRepintar(carrito) {
  guardarCarrito(carrito);
  window.dispatchEvent(new Event("cart:updated"));
  mostrarProductos();
}

function crearProducto(producto, indice, carrito) {
  const tarjeta = nodo("article", "row align-items-center");
  const imagenCol = nodo("div", "col-md-3 text-center");
  const imagen = nodo("img");
  imagen.src = producto.imagen ? `/static/${producto.imagen}` : "/static/img/hamburguesas/h-2.jpg";
  imagen.alt = producto.nombre;
  imagenCol.appendChild(imagen);

  const datos = nodo("div", "col-md-6");
  datos.appendChild(nodo("h3", "nombre", producto.nombre));
  datos.appendChild(nodo("p", "page-subtitle", `Precio unitario: ${moneda(producto.precio)}`));
  if (Array.isArray(producto.cremas) && producto.cremas.length) {
    const nombres = producto.cremas.map((id) => mapCremas.get(id)).filter(Boolean).join(", ");
    datos.appendChild(nodo("p", "field-help", `Salsas: ${nombres}`));
  }
  const controles = nodo("div", "d-flex align-items-center gap-2 mt-3");
  const resta = nodo("button", "btn btn-success", "−");
  const cantidad = nodo("strong", "cantidad", String(producto.cantidad));
  const suma = nodo("button", "btn btn-success", "+");
  resta.type = suma.type = "button";
  resta.onclick = () => { producto.cantidad = Math.max(1, Number(producto.cantidad) - 1); producto.precioTotal = Number(producto.precio) * producto.cantidad; guardarYRepintar(carrito); };
  suma.onclick = () => { producto.cantidad = Math.min(Number(producto.existencias || Infinity), Number(producto.cantidad) + 1); producto.precioTotal = Number(producto.precio) * producto.cantidad; guardarYRepintar(carrito); };
  controles.append(resta, cantidad, suma); datos.appendChild(controles);

  const acciones = nodo("div", "col-md-3 text-md-end mt-3 mt-md-0");
  acciones.appendChild(nodo("small", "section-kicker", "Subtotal"));
  acciones.appendChild(nodo("div", "price", moneda(Number(producto.precio) * Number(producto.cantidad))));
  const eliminar = nodo("button", "btn btn-danger btn-sm mt-3", "Quitar");
  eliminar.type = "button";
  eliminar.onclick = () => { carrito.splice(indice, 1); guardarYRepintar(carrito); };
  acciones.appendChild(eliminar);
  tarjeta.append(imagenCol, datos, acciones);
  return tarjeta;
}

function actualizarResumen(carrito) {
  const cantidad = carrito.reduce((total, item) => total + Number(item.cantidad || 0), 0);
  const total = carrito.reduce((suma, item) => suma + Number(item.precio || 0) * Number(item.cantidad || 0), 0);
  const cantidadNodo = document.querySelector("#resumen-cantidad");
  const igvNodo = document.querySelector("#resumen-igv");
  const totalNodo = document.querySelector("#precio-total");
  const continuar = document.querySelector("#continuar-compra");
  if (cantidadNodo) cantidadNodo.textContent = `${cantidad} unidad${cantidad === 1 ? "" : "es"}`;
  if (igvNodo) igvNodo.textContent = moneda(total - total / 1.18);
  if (totalNodo) totalNodo.textContent = moneda(total);
  continuar?.classList.toggle("disabled", carrito.length === 0);
  continuar?.setAttribute("aria-disabled", carrito.length === 0 ? "true" : "false");
}

function mostrarProductos() {
  if (!contenedor) return;
  const carrito = obtenerCarrito();
  contenedor.replaceChildren();
  if (!carrito.length) {
    const vacio = nodo("div", "empty-state");
    vacio.append(nodo("div", "empty-state__icon", "🛍️"), nodo("h2", "", "Tu carrito está vacío"), nodo("p", "page-subtitle", "Explora la carta y agrega algo preparado a las brasas."));
    const volver = nodo("a", "musas-btn musas-btn--primary", "Ver la carta");
    volver.href = "/#carta"; vacio.appendChild(volver); contenedor.appendChild(vacio);
  } else {
    carrito.forEach((producto, indice) => contenedor.appendChild(crearProducto(producto, indice, carrito)));
  }
  actualizarResumen(carrito);
}

window.addEventListener("DOMContentLoaded", async () => { await obtenerCremas(mapCremas); mostrarProductos(); });
vaciar?.addEventListener("click", () => { vaciarCarrito(); window.dispatchEvent(new Event("cart:updated")); mostrarProductos(); });
