import { SERVER } from "./config.js";
import { guardarCarrito, obtenerCarrito } from "./carritoStorage.js";
const agregarCarrito = document.querySelector("#agregar-carrito");
const cremas = document.querySelectorAll("input[type=checkbox]");

let id;
let url;
let cremasElegidas = [];
if (agregarCarrito) {
  agregarCarrito.addEventListener("click", (e) => {
    e.preventDefault();
    id = window.location.href.split("/").pop();
    url = `${SERVER}/get_producto/${id}`;

    //obtengo las cremas elegidas
    cremas.forEach((crema) => {
      if (crema.checked) {
        cremasElegidas.push(parseInt(crema.value));
      }
    });
    obtener_data_producto();
  });
}

async function obtener_data_producto() {
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("No se pudo obtener el producto");
    const data = await response.json();
    guardar_data_carrito(data);
  } catch (error) {
    console.log(error);
  }
}

function guardar_data_carrito(data) {
  const { idProducto, idCategoria, nombre, descripcion, precio, existencias, imagen } =
    data.producto;

  const obj = {
    idProducto: idProducto,
    idCategoria: idCategoria,
    nombre: nombre,
    descripcion: descripcion,
    precio: precio,
    existencias: existencias,
    imagen: imagen || "",
    cantidad: 1,
    precioTotal: precio,
    cremas: cremasElegidas,
  };

  const carrito = obtenerCarrito();
  carrito.push(obj);
  guardarCarrito(carrito);
  window.dispatchEvent(new Event("cart:updated"));
  cremasElegidas = [];
  window.location.href = `${SERVER}/carrito`;
}
