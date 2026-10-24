/* Pantalla de cocina: recibe por Server-Sent Events los cambios de pedidos y
   refresca sola la lista. Conserva /pulso como respaldo. Cuando entra un
   pedido NUEVO: pitido + aviso visual + título parpadeante. */
(function () {
  var cfg = document.getElementById("ped-cocina");
  if (!cfg) return;

  var URL_EVENTOS = cfg.dataset.eventosUrl;
  var URL_PULSO = cfg.dataset.pulsoUrl;
  var INTERVALO_RESPALDO = 15000;
  var firma = cfg.dataset.firma || "";
  var conocidos = {};
  (cfg.dataset.idsIniciales || "").split(",").forEach(function (id) {
    if (id) conocidos[id] = true;
  });

  var SIN_MOV =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---------------------------------------------------------------
  //  Sonido: dos tonos cortos generados con WebAudio.
  // ---------------------------------------------------------------
  var audio = null;
  var sonidoActivo = localStorage.getItem("musas_sonido_cocina") !== "0";
  var btnSonido = document.getElementById("ped-sonido");

  function crearAudio() {
    if (audio) return audio;
    try {
      var AC = window.AudioContext || window.webkitAudioContext;
      audio = new AC();
    } catch (e) {
      audio = null;
    }
    return audio;
  }

  function pintarBotonSonido() {
    if (!btnSonido) return;
    var ok = sonidoActivo && audio && audio.state === "running";
    btnSonido.setAttribute("aria-pressed", ok ? "true" : "false");
    btnSonido.classList.toggle("is-on", ok);
    var i = btnSonido.querySelector("i");
    if (i) i.className = ok ? "bi bi-bell-fill" : "bi bi-bell-slash";
  }

  function activarSonido(conPrueba) {
    crearAudio();
    if (!audio) return;
    sonidoActivo = true;
    localStorage.setItem("musas_sonido_cocina", "1");
    var listo = audio.state === "suspended" ? audio.resume() : Promise.resolve();
    Promise.resolve(listo).then(function () {
      pintarBotonSonido();
      if (conPrueba) pitido();
    }).catch(pintarBotonSonido);
  }

  function pitido() {
    if (!sonidoActivo || !audio) return;
    if (audio.state === "suspended") audio.resume();
    var t0 = audio.currentTime;
    [[880, 0], [1245, 0.16]].forEach(function (p) {
      var osc = audio.createOscillator();
      var gan = audio.createGain();
      osc.type = "sine";
      osc.frequency.value = p[0];
      osc.connect(gan);
      gan.connect(audio.destination);
      var t = t0 + p[1];
      gan.gain.setValueAtTime(0.0001, t);
      gan.gain.exponentialRampToValueAtTime(0.5, t + 0.02);
      gan.gain.exponentialRampToValueAtTime(0.0001, t + 0.32);
      osc.start(t);
      osc.stop(t + 0.34);
    });
  }

  if (btnSonido) {
    btnSonido.addEventListener("click", function () {
      if (sonidoActivo && audio && audio.state === "running") {
        sonidoActivo = false; // apagar
        localStorage.setItem("musas_sonido_cocina", "0");
        pintarBotonSonido();
      } else {
        activarSonido(true);
      }
    });
  }
  // Cualquier clic en la página cuenta como gesto: deja el audio listo.
  document.addEventListener(
    "pointerdown",
    function () {
      if (sonidoActivo) activarSonido(Object.keys(conocidos).length > 0);
    },
    { once: true }
  );

  // Intenta restaurar la preferencia. El navegador puede mantener el audio
  // suspendido hasta la primera interacción; el listener anterior lo habilita.
  if (sonidoActivo) activarSonido(false);

  // Boleta simple: sin documento. Boleta con DNI: 8 dígitos.
  // Factura: RUC de 11 dígitos y razón social.
  document.addEventListener("change", function (ev) {
    if (!ev.target.matches('select[name="tipo_comprobante"]')) return;
    var form = ev.target.closest("form");
    if (!form) return;
    var tipo = ev.target.value;
    var pideDoc = tipo !== "boleta_simple";
    var factura = tipo === "factura";
    var docWrap = form.querySelector("[data-doc-wrap]");
    var doc = form.querySelector('input[name="documento"]');
    var razonWrap = form.querySelector("[data-razon-social]");
    var razon = form.querySelector('input[name="razon_social"]');
    if (docWrap) docWrap.hidden = !pideDoc;
    if (doc) {
      doc.disabled = !pideDoc;
      doc.required = pideDoc;
      doc.maxLength = factura ? 11 : 8;
      doc.pattern = factura ? "[0-9]{11}" : "[0-9]{8}";
      doc.placeholder = factura ? "RUC (11 dígitos)" : "DNI (8 dígitos)";
      doc.value = "";
      if (pideDoc) doc.focus();
    }
    if (razonWrap) razonWrap.hidden = !factura;
    if (razon) { razon.disabled = !factura; razon.required = factura; razon.value = ""; }
  });

  // ---------------------------------------------------------------
  //  Aviso visual + título parpadeante
  // ---------------------------------------------------------------
  var aviso = document.getElementById("ped-nuevo");
  var avisoTxt = document.getElementById("ped-nuevo-txt");
  var avisoOk = document.getElementById("ped-nuevo-ok");
  var tituloBase = document.title;
  var parpadeo = null;
  var cuentaNuevos = 0;
  var ocultarAviso = null;

  function marcarTitulo() {
    if (parpadeo) return;
    var on = false;
    parpadeo = setInterval(function () {
      document.title = on
        ? tituloBase
        : "🔔 (" + cuentaNuevos + ") pedido" + (cuentaNuevos > 1 ? "s" : "") + " nuevo" + (cuentaNuevos > 1 ? "s" : "");
      on = !on;
    }, 1000);
  }

  function limpiarAvisos() {
    if (parpadeo) {
      clearInterval(parpadeo);
      parpadeo = null;
    }
    cuentaNuevos = 0;
    document.title = tituloBase;
    if (aviso) aviso.hidden = true;
  }

  if (avisoOk) avisoOk.addEventListener("click", limpiarAvisos);
  window.addEventListener("focus", limpiarAvisos);

  function avisar(nuevos) {
    cuentaNuevos += nuevos.length;
    pitido();
    marcarTitulo();
    if (aviso && avisoTxt) {
      avisoTxt.textContent =
        nuevos.length === 1
          ? "Nuevo pedido #" + nuevos[0]
          : nuevos.length + " pedidos nuevos (#" + nuevos.join(", #") + ")";
      aviso.hidden = false;
      aviso.classList.remove("is-in");
      void aviso.offsetWidth;
      aviso.classList.add("is-in");
      if (ocultarAviso) clearTimeout(ocultarAviso);
      ocultarAviso = setTimeout(function () {
        if (aviso) aviso.hidden = true;
      }, 12000);
    }
  }

  // ---------------------------------------------------------------
  //  Refresco parcial de la lista (sin recargar toda la página)
  // ---------------------------------------------------------------
  function resaltarNuevos(nuevos) {
    nuevos.forEach(function (id) {
      var card = document.querySelector('.ped-card[data-pedido-id="' + id + '"]');
      if (card) card.classList.add("ped-card--nuevo");
    });
  }

  function refrescar(nuevos) {
    fetch(location.href, {
      headers: { "X-Requested-With": "fetch" },
      credentials: "same-origin",
    })
      .then(function (r) {
        return r.ok ? r.text() : Promise.reject();
      })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        var nuevaLista = doc.getElementById("ped-lista");
        var nuevosChips = doc.getElementById("ped-chips");
        var listaActual = document.getElementById("ped-lista");
        if (!nuevaLista || !listaActual) {
          location.reload(); // sesión caída u otra cosa: recargar de verdad
          return;
        }
        listaActual.replaceWith(nuevaLista);
        if (nuevosChips && document.getElementById("ped-chips")) {
          // Conserva el botón de sonido (estado en memoria) al reemplazar.
          var btnViejo = document.getElementById("ped-sonido");
          document.getElementById("ped-chips").replaceWith(nuevosChips);
          var btnNuevo = document.getElementById("ped-sonido");
          if (btnViejo && btnNuevo) btnNuevo.replaceWith(btnViejo);
        }
        if (nuevos && nuevos.length && !SIN_MOV) resaltarNuevos(nuevos);
      })
      .catch(function () {
        /* silencioso: se reintenta en el próximo sondeo */
      });
  }

  // ---------------------------------------------------------------
  //  Actualización en vivo: SSE como canal principal, sondeo como respaldo.
  // ---------------------------------------------------------------
  function aplicarCambio(d) {
    if (!d || d.firma === firma) return;
    var pend = d.pendientes || [];
    var nuevos = pend.filter(function (id) {
      return !conocidos[id];
    });
    firma = d.firma;
    pend.forEach(function (id) {
      conocidos[id] = true;
    });
    refrescar(nuevos);
    if (nuevos.length) avisar(nuevos);
  }

  function consultarPulso() {
    return fetch(URL_PULSO, {
      headers: { "X-Requested-With": "fetch" },
      credentials: "same-origin",
    })
      .then(function (r) {
        return r.ok ? r.json() : Promise.reject();
      })
      .then(aplicarCambio)
      .catch(function () {});
  }

  var eventos = null;
  if (window.EventSource && URL_EVENTOS) {
    var separador = URL_EVENTOS.indexOf("?") === -1 ? "?" : "&";
    eventos = new EventSource(
      URL_EVENTOS + separador + "firma=" + encodeURIComponent(firma)
    );
    eventos.addEventListener("pedidos", function (ev) {
      try {
        aplicarCambio(JSON.parse(ev.data));
      } catch (e) {
        consultarPulso();
      }
    });
    // EventSource se reconecta solo. El pulso comprueba el estado mientras
    // recupera la conexión y también detecta una sesión vencida.
    eventos.onerror = consultarPulso;
    window.addEventListener("pagehide", function () {
      eventos.close();
    });
  } else {
    setInterval(consultarPulso, INTERVALO_RESPALDO);
  }

  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) consultarPulso();
  });

  pintarBotonSonido();
})();
