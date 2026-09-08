/* Seguimiento en vivo del pedido del cliente (página "Mis pedidos").
   Sondea el estado cada 20 s y actualiza la línea de tiempo + la etiqueta
   sin recargar. Cuando un pedido pasa a "listo" avisa con un toast. */
(function () {
  var marca = document.getElementById("mp-seg");
  if (!marca || !window.fetch) return;

  var ACTIVOS = ["recibido", "preparando", "listo"];
  var lineas = document.querySelectorAll("[data-mp-timeline]");
  var hayActivo = Array.prototype.some.call(lineas, function (t) {
    return ACTIVOS.indexOf(t.dataset.estado) !== -1;
  });
  if (!hayActivo) return; // nada en curso: no hace falta sondear

  var URL = marca.dataset.url;
  var firma = marca.dataset.firma || "";

  var BADGE = {
    recibido: ["pendiente", "bi-clock-fill", "Recibido"],
    preparando: ["preparando", "bi-fire", "En preparación"],
    listo: ["listo", "bi-bag-check-fill", "Listo para recojo"],
    recogido: ["recogido", "bi-check-circle-fill", "Recogido"],
    cancelado: ["cancelado", "bi-x-circle-fill", "Cancelado"],
    no_show: ["cancelado", "bi-exclamation-circle-fill", "No recogido"],
  };

  function avisarListo(id) {
    if (window.MusasCarrito && window.MusasCarrito.toast) {
      window.MusasCarrito.toast(
        "Tu pedido N° " + id + " está listo · pasa a recogerlo",
        { duracion: 9000 }
      );
    }
    if (window.Notification && Notification.permission === "granted") {
      try {
        new Notification("Las Musas", {
          body: "Tu pedido N° " + id + " está listo para recoger 🛍️",
        });
      } catch (e) {}
    }
  }

  function aplicar(estados) {
    var recargar = false;
    document.querySelectorAll(".mp-card[data-pedido-id]").forEach(function (c) {
      var id = c.dataset.pedidoId;
      var nuevo = estados[id];
      if (!nuevo) return;
      var tl = c.querySelector("[data-mp-timeline]");
      var previo = tl ? tl.dataset.estado : null;
      if (nuevo === previo) return;

      // Estados finales cambian toda la tarjeta (acciones, agrupación del
      // filtro, etc.): más simple y seguro recargar.
      if (nuevo === "recogido" || nuevo === "cancelado" || nuevo === "no_show") {
        recargar = true;
        return;
      }

      if (tl) tl.dataset.estado = nuevo;

      var b = c.querySelector("[data-mp-badge]");
      var info = BADGE[nuevo];
      if (b && info) {
        b.className = "mp-estado " + info[0];
        b.innerHTML = '<i class="bi ' + info[1] + '"></i> ' + info[2];
      }

      // Si ya entró a cocina, el botón de cancelar se cambia por la nota.
      if (nuevo === "preparando" || nuevo === "listo") {
        var form = c.querySelector(".mp-acciones form[data-confirm]");
        if (form) {
          var nota = document.createElement("span");
          nota.className = "mp-nota-cancel";
          nota.innerHTML =
            '<i class="bi bi-info-circle"></i> Ya en cocina · no se puede cancelar';
          form.replaceWith(nota);
        }
      }

      if (nuevo === "listo") {
        c.classList.add("mp-card--listo");
        avisarListo(id);
      }
    });
    if (recargar) window.location.reload();
  }

  function tick() {
    fetch(URL, {
      headers: { "X-Requested-With": "fetch" },
      credentials: "same-origin",
    })
      .then(function (r) {
        return r.ok ? r.json() : Promise.reject();
      })
      .then(function (d) {
        if (!d || d.firma === firma) return;
        firma = d.firma;
        aplicar(d.estados || {});
      })
      .catch(function () {});
  }

  setInterval(tick, 20000);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) tick();
  });
})();
