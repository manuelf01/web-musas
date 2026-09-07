/* Carrito de Las Musas — almacenamiento en localStorage (sin dependencias).
   Clave:  musas_carrito
   Valor:  [ { idProducto, nombre, precio, imagen, cantidad,
               cremas: [ { idProducto, nombre, precio } ] } ]
   El subtotal de una línea = (precio + suma cremas) * cantidad
*/
(function () {
  var CLAVE = "musas_carrito";

  function leer() {
    try {
      var v = JSON.parse(localStorage.getItem(CLAVE));
      return Array.isArray(v) ? v : [];
    } catch (e) {
      return [];
    }
  }

  function guardar(items) {
    try {
      localStorage.setItem(CLAVE, JSON.stringify(items));
    } catch (e) {}
    actualizarNav();
  }

  function subtotalLinea(it) {
    var cremas = (it.cremas || []).reduce(function (s, c) {
      return s + Number(c.precio || 0);
    }, 0);
    return (Number(it.precio || 0) + cremas) * Number(it.cantidad || 1);
  }

  function total() {
    return leer().reduce(function (s, it) {
      return s + subtotalLinea(it);
    }, 0);
  }

  function cantidadTotal() {
    return leer().reduce(function (s, it) {
      return s + Number(it.cantidad || 1);
    }, 0);
  }

  function agregar(item) {
    var items = leer();
    items.push(item);
    guardar(items);
  }

  function vaciar() {
    guardar([]);
  }

  function actualizarNav() {
    var n = cantidadTotal();
    var t = total();
    document.querySelectorAll("[data-carrito-count]").forEach(function (el) {
      el.textContent = n;
    });
    document.querySelectorAll("[data-carrito-total]").forEach(function (el) {
      el.textContent = "S/ " + t.toFixed(2);
    });
  }

  document.addEventListener("DOMContentLoaded", actualizarNav);

  window.MusasCarrito = {
    leer: leer,
    guardar: guardar,
    subtotalLinea: subtotalLinea,
    total: total,
    cantidadTotal: cantidadTotal,
    agregar: agregar,
    vaciar: vaciar,
    actualizarNav: actualizarNav,
  };
})();
