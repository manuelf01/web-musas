const CLAVE_CARRITO = "carrito";
const CLAVE_PEDIDOS = "mis_pedidos";

function obtenerCarrito() {
  try {
    const guardado = localStorage.getItem(CLAVE_CARRITO);
    if (guardado !== null) {
      const carrito = JSON.parse(guardado);
      return Array.isArray(carrito) ? carrito : [];
    }

    // Migra una sola vez el formato anterior, que guardaba cada producto bajo
    // una clave numérica, sin confundirlo con "mis_pedidos".
    const clavesAnteriores = Object.keys(localStorage).filter((clave) => /^\d+$/.test(clave));
    const carritoAnterior = clavesAnteriores
      .map((clave) => JSON.parse(localStorage.getItem(clave)))
      .filter((producto) => producto && producto.idProducto);
    if (carritoAnterior.length > 0) {
      guardarCarrito(carritoAnterior);
      clavesAnteriores.forEach((clave) => localStorage.removeItem(clave));
    }
    return carritoAnterior;
  } catch {
    return [];
  }
}

function guardarCarrito(carrito) {
  localStorage.setItem(CLAVE_CARRITO, JSON.stringify(carrito));
}

function vaciarCarrito() {
  localStorage.removeItem(CLAVE_CARRITO);
}

function guardarPedido(pedido, productos) {
  let pedidos = [];
  try {
    pedidos = JSON.parse(localStorage.getItem(CLAVE_PEDIDOS) ?? "[]");
    if (!Array.isArray(pedidos)) pedidos = [];
  } catch {
    pedidos = [];
  }
  pedidos.push({ ...pedido, productos, fecha: new Date().toISOString() });
  localStorage.setItem(CLAVE_PEDIDOS, JSON.stringify(pedidos));
}

export { guardarCarrito, guardarPedido, obtenerCarrito, vaciarCarrito };
