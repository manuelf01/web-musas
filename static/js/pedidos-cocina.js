/* Pantalla de cocina: sondea el estado de los pedidos de hoy y refresca sola
   la lista. Cuando entra un pedido NUEVO: pitido + aviso visual + título
   parpadeante. Sin dependencias, sin archivos de audio. */
(function () {
  var cfg = document.getElementById("ped-cocina");
  if (!cfg) return;

  var URL_PULSO = cfg.dataset.pulsoUrl;
  var INTERVALO = 15000; // ms entre sondeos
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
  var sonidoActivo = false;
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
    if (audio.state === "suspended") audio.resume();
    sonidoActivo = true;
    if (conPrueba) pitido();
    pintarBotonSonido();
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
      if (!sonidoActivo) activarSonido(false);
    },
    { once: true }
  );

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
        // Re-aplica el filtro en vivo si había texto tecleado.
        var inp = document.getElementById("ped-buscar");
        if (inp && inp.value) inp.dispatchEvent(new Event("input"));
        if (nuevos && nuevos.length && !SIN_MOV) resaltarNuevos(nuevos);
      })
      .catch(function () {
        /* silencioso: se reintenta en el próximo sondeo */
      });
  }

  // ---------------------------------------------------------------
  //  Sondeo
  // ---------------------------------------------------------------
  function tick() {
    fetch(URL_PULSO, {
      headers: { "X-Requested-With": "fetch" },
      credentials: "same-origin",
    })
      .then(function (r) {
        return r.ok ? r.json() : Promise.reject();
      })
      .then(function (d) {
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
      })
      .catch(function () {});
  }

  setInterval(tick, INTERVALO);
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden) tick();
  });

  pintarBotonSonido();
})();
