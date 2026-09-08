import { SERVER } from "./config.js";
import { transaccionCompra } from "./fetchApis.js";
import { guardarPedido, obtenerCarrito, vaciarCarrito } from "./carritoStorage.js";
const btnComprar = document.querySelector("#comprar-producto");
btnComprar?.addEventListener("click", comprarProductos);

async function comprarProductos(e) {
  e.preventDefault();
  const formulario = document.querySelector("#form-compra");
  if (!formulario?.checkValidity()) {
    formulario?.reportValidity();
    return;
  }
  const dni = document.querySelector("#dni").value;
  const nombres = document.querySelector("#nombres").value;
  const telefono = document.querySelector("#telefono").value;
  const horaRecojo = document.querySelector("#hora-recojo").value;
  const boleta = document.querySelector("#boleta").checked;
  const billeteraDigital = document.querySelector("#billetera-digital").checked;
  let id = document.querySelector("#idUsuario");
  if (id) {
    id = id.value;
  }
  const datosPedido = {
    idUsuario: id ? id : "",
    dniNoRegistrado: dni,
    nombres,
    telefono,
    horaRecojo,
    estadoBoleta: boleta,
    billeteraDigital,
  };
  const productos = arregloProductos();
  if (!productos.length) {
    alert("Tu carrito está vacío");
    window.location.href = `${SERVER}/carrito`;
    return;
  }
  const objetoTransaccion = {
    datosPedido,
    productos,
  };
  const rpta = await transaccionCompra(objetoTransaccion);
  if (rpta?.status === "1") {
    guardarPedido(rpta.pedido, productos);
    vaciarCarrito();
    alert("Compra realizada con éxito");
    window.location.href = `${SERVER}/`;
  } else {
    alert(rpta?.mensaje ?? "No se pudo realizar la compra");
  }
}
function arregloProductos() {
  return obtenerCarrito().map(({ idProducto, cantidad, cremas }) => ({
    idProducto,
    cantidad,
    cremas,
  }));
}
