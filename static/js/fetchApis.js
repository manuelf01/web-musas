import { SERVER } from "./config.js";

async function obtenerCremas(mapCremas) {
  const url = `${SERVER}/get_productos_categoria_nombre/${encodeURIComponent("Cremas")}`;

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error("No se pudieron obtener las cremas");
    const data = await response.json();

    data.productos.forEach((crema) => {
      mapCremas.set(crema.idProducto, crema.nombre);
    });
  } catch (error) {
    console.log(error);
  }
}

async function transaccionCompra(datosTransaccion) {
  const url = `${SERVER}/transaccion_compra`;
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(datosTransaccion),
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok && response.status >= 500) throw new Error("Error del servidor");
    return response.json();
  } catch (error) {
    console.log(error);
  }
}

async function transaccionComprobante(datosTransaccion) {
  const url = `${SERVER}/transaccion_comprobante`;
  try {
    const response = await fetch(url, {
      method: "POST",
      body: JSON.stringify(datosTransaccion),
      headers: {
        "Content-Type": "application/json",
      },
    });
    if (!response.ok && response.status >= 500) throw new Error("Error del servidor");
    return response.json();
  } catch (error) {
    console.log(error);
  }
}
export { obtenerCremas, transaccionCompra, transaccionComprobante };
