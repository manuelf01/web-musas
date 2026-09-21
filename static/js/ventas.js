/* Ventas: comprobantes filtrados en vivo (por carácter, sin recargar) y
   autocompletado del buscador. La tabla la renderiza el servidor; aquí solo
   se pide y se reemplaza. */
(function () {
  "use strict";
  var form = document.getElementById("vent-filtros");
  var destino = document.getElementById("vent-resultados");
  if (!form || !destino || !window.fetch) return;

  var q = form.elements.q;
  var lista = document.getElementById("vent-sug");
  var limpiar = form.querySelector("[data-limpiar]");
  var URL_SUG = form.dataset.urlSugerencias;
  var pedido = 0;
  var temporizador = null;
  var temporizadorSug = null;

  // La paginación se resuelve aquí: el loader global no debe taparla.
  function marcarEnlaces() {
    destino.querySelectorAll(".adm-pag a").forEach(function (a) { a.setAttribute("data-loader-skip", ""); });
  }
  marcarEnlaces();

  function parametros(extra) {
    var p = new URLSearchParams(new FormData(form));
    var fechasAbiertas = form.hasAttribute("data-fechas-abiertas");
    Array.from(p.keys()).forEach(function (k) {
      if (p.get(k) === "" && !(fechasAbiertas && (k === "desde" || k === "hasta"))) p.delete(k);
    });
    if (extra) Object.keys(extra).forEach(function (k) { p.set(k, extra[k]); });
    return p;
  }

  function hayFiltros() {
    return ["q", "tipo", "medio", "estado", "desde", "hasta"].some(function (n) {
      return form.elements[n] && form.elements[n].value !== "";
    });
  }

  function cargar(url) {
    var mio = ++pedido;
    destino.classList.add("is-cargando");
    fetch(url, { headers: { "X-Requested-With": "fetch" }, credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.text() : Promise.reject(); })
      .then(function (html) {
        if (mio !== pedido) return;
        destino.innerHTML = html;
        marcarEnlaces();
        destino.classList.remove("is-cargando");
        if (limpiar) limpiar.hidden = !hayFiltros();
        var visible = new URL(url, location.href);
        history.replaceState(null, "", visible.pathname + (visible.search || ""));
      })
      .catch(function () {
        if (mio !== pedido) return;
        destino.classList.remove("is-cargando");
        form.submit();
      });
  }

  function filtrar() {
    cargar(form.action + "?" + parametros().toString());
  }

  // Cada carácter filtra (con una pausa mínima para no saturar al servidor).
  q.addEventListener("input", function () {
    clearTimeout(temporizador);
    temporizador = setTimeout(filtrar, 200);
    clearTimeout(temporizadorSug);
    temporizadorSug = setTimeout(sugerir, 150);
  });
  q.addEventListener("search", filtrar);

  ["tipo", "medio", "estado", "desde", "hasta"].forEach(function (n) {
    if (form.elements[n]) form.elements[n].addEventListener("change", filtrar);
  });

  // Enter no recarga: solo aplica el filtro.
  form.addEventListener("submit", function (e) { e.preventDefault(); clearTimeout(temporizador); filtrar(); });

  // Paginación sin recarga.
  destino.addEventListener("click", function (e) {
    var a = e.target.closest(".adm-pag a[href]");
    if (!a) return;
    e.preventDefault();
    e.stopPropagation();
    cargar(a.href);
  }, true);

  // Limpiar filtros.
  if (limpiar) {
    limpiar.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      q.value = "";
      ["tipo", "medio", "estado", "desde", "hasta"].forEach(function (n) { if (form.elements[n]) form.elements[n].value = ""; });
      lista.innerHTML = "";
      filtrar();
    }, true);
  }

  // Autocompletado: sugerencias reales (número, cliente, DNI/RUC).
  function sugerir() {
    var texto = q.value.trim();
    if (!texto) { lista.innerHTML = ""; return; }
    fetch(URL_SUG + "?q=" + encodeURIComponent(texto), { credentials: "same-origin" })
      .then(function (r) { return r.ok ? r.json() : []; })
      .then(function (valores) {
        if (q.value.trim() !== texto) return;
        lista.innerHTML = "";
        valores.forEach(function (v) {
          var o = document.createElement("option");
          o.value = v;
          lista.appendChild(o);
        });
      })
      .catch(function () {});
  }
})();
