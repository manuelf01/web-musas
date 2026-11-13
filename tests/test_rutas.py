"""Humo de rutas: páginas públicas responden y el panel exige sesión."""

import json
from pathlib import Path

import pytest

import bd
from model.Pedido import Pedido
from tests.conftest import CLIENTE_ID


@pytest.mark.parametrize("url", [
    "/", "/carta", "/nosotros", "/login", "/registro", "/mis-pedidos",
    "/producto/2",
])
def test_paginas_publicas_ok(client, url):
    assert client.get(url).status_code == 200


@pytest.mark.parametrize("url", [
    "/admin/", "/admin/pedidos/", "/admin/productos/", "/admin/ventas/",
    "/admin/caja/", "/admin/inventario/", "/admin/medios-pago/",
])
def test_panel_sin_sesion_redirige(client, url):
    r = client.get(url, follow_redirects=False)
    assert r.status_code in (301, 302)


@pytest.mark.parametrize("url", [
    "/admin/", "/admin/pedidos/", "/admin/productos/", "/admin/categorias/",
    "/admin/ventas/", "/admin/perfil/", "/admin/usuarios/", "/admin/caja/",
    "/admin/inventario/", "/admin/medios-pago/",
])
def test_panel_con_sesion_ok(admin_client, url):
    assert admin_client.get(url).status_code == 200


def test_carrito_exige_login(client):
    r = client.get("/carrito", follow_redirects=False)
    assert r.status_code in (301, 302)


def test_navegacion_movil_publica_muestra_total_e_ingreso(client):
    publica = client.get("/carta").get_data(as_text=True)
    assert 'class="musa-tabbar"' in publica
    assert "data-carrito-total-label" in publica
    assert ">Ingresar</span>" in publica
    assert "carrito.js?v=20261026-2" in publica


def test_navegacion_movil_autenticada_muestra_mi_cuenta(cliente_client):
    autenticada = cliente_client.get("/mi-cuenta").get_data(as_text=True)
    assert ">Mi cuenta</span>" in autenticada
    assert 'class="active" aria-label="Mi cuenta"' in autenticada


def test_aviso_del_carrito_es_visible_y_permite_deshacer():
    raiz = Path(__file__).resolve().parents[1]
    js = (raiz / "static/js/carrito.js").read_text(encoding="utf-8")
    css = (raiz / "static/css/musas-theme.css").read_text(encoding="utf-8")
    assert 'opciones.deshacer' in js
    assert 'musas:carrito-deshacer' in js
    assert 'duracion: opciones.duracion || (cantidadAgregada ? 8000 : 4200)' in js
    assert ".musa-toasts" in css and "top: 96px" in css and "right: 20px" in css


def test_layout_aprovecha_monitores_grandes_sin_estirar_formularios():
    css = (Path(__file__).resolve().parents[1] / "static/css/musas-theme.css").read_text(encoding="utf-8")
    assert "--musa-ancho: 1440px" in css
    assert "--musa-ancho-panel: 1600px" in css
    assert "--musa-ancho-detalle: 1200px" in css
    assert "--musa-ancho-lectura: 900px" in css
    assert ".musa-navbar .musa-nav-actions { display: flex !important;" in css
    assert ".musa-navbar .musa-nav-actions > :not(.musa-theme-switch) { display: none !important; }" in css


def test_cabecera_y_categorias_sticky_se_compactan_solo_en_escritorio(client):
    raiz = Path(__file__).resolve().parents[1]
    css = (raiz / "static/css/musas-theme.css").read_text(encoding="utf-8")
    js = (raiz / "static/js/nav-tienda.js").read_text(encoding="utf-8")
    html = client.get("/carta").get_data(as_text=True)
    assert ".musa-navbar" in css and "position: sticky" in css
    assert ".musa-catbar" in css and "top: var(--musa-nav-h)" in css
    assert "@media (min-width: 769px)" in css and "musa-nav-compacta" in css
    assert "body:not(.adm) { padding-top: var(--musa-nav-h)" in css
    assert "position: fixed;\n    top: 0;\n    right: 0;\n    left: 0;" in css
    assert "html.musa-nav-compacta .musa-catbar__inner" in css
    assert "html.musa-nav-compacta .musa-catbar__lugar { display: none; }" in css
    assert "padding-bottom: 14px" in css
    assert 'matchMedia("(min-width: 769px)")' in js
    assert "nav-tienda.js?v=20261026-1" in html
    assert 'class="carta-head carta-head--filtros"' in html
    assert ".carta-head--filtros > .carta-filtros" in css
    assert "grid-template-columns: minmax(0, 1fr) minmax(500px, 620px)" in css


def test_pulso_de_cocina(admin_client, bd_limpia):
    d = admin_client.get("/admin/pedidos/pulso").get_json()
    assert d["pendientes"] == []
    f0 = d["firma"]
    Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "C", "999", "19:00:00", "efectivo", None,
        [{"idProducto": 2, "nombre": "Simple de Carne", "precioUnidad": 8.5,
          "cantidad": 1, "precioTotal": 8.5, "cremas": []}])
    d2 = admin_client.get("/admin/pedidos/pulso").get_json()
    assert d2["firma"] != f0
    assert len(d2["pendientes"]) == 1


def test_eventos_sse_de_cocina(admin_client, bd_limpia):
    firma_anterior = admin_client.get("/admin/pedidos/pulso").get_json()["firma"]
    id_pedido, _ = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "C", "999", "19:00:00", "efectivo", None,
        [{"idProducto": 2, "nombre": "Simple de Carne", "precioUnidad": 8.5,
          "cantidad": 1, "precioTotal": 8.5, "cremas": []}])

    respuesta = admin_client.get(
        "/admin/pedidos/eventos",
        query_string={"firma": firma_anterior},
        buffered=False,
    )
    try:
        partes = iter(respuesta.response)
        assert respuesta.mimetype == "text/event-stream"
        assert next(partes).decode("utf-8").startswith("retry: 3000")
        evento = next(partes).decode("utf-8")
        assert "event: pedidos" in evento
        datos = json.loads(evento.split("data: ", 1)[1].strip())
        assert id_pedido in datos["pendientes"]
        assert datos["firma"] != firma_anterior
    finally:
        respuesta.close()


def test_seguimiento_estado_del_cliente(cliente_client, bd_limpia):
    idp, _ = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "C", "999", "19:00:00", "efectivo", None,
        [{"idProducto": 2, "nombre": "Simple de Carne", "precioUnidad": 8.5,
          "cantidad": 1, "precioTotal": 8.5, "cremas": []}])
    d = cliente_client.get("/mis-pedidos/estado").get_json()
    assert d["estados"][str(idp)] == "recibido"
    Pedido.avanzar_preparacion(idp)

    respuesta = cliente_client.get(
        "/mis-pedidos/eventos",
        query_string={"firma": d["firma"]},
        buffered=False,
    )
    try:
        partes = iter(respuesta.response)
        assert respuesta.mimetype == "text/event-stream"
        assert next(partes).decode("utf-8").startswith("retry: 3000")
        evento = next(partes).decode("utf-8")
        datos_evento = json.loads(evento.split("data: ", 1)[1].strip())
        assert datos_evento["estados"][str(idp)] == "preparando"
    finally:
        respuesta.close()

    d2 = cliente_client.get("/mis-pedidos/estado").get_json()
    assert d2["estados"][str(idp)] == "preparando"
    assert d2["firma"] != d["firma"]


def test_sugeridos_endpoint(client, bd_limpia):
    d = client.get("/carrito/sugeridos?ids=2").get_json()
    assert "sugeridos" in d and len(d["sugeridos"]) <= 4


def test_checkout_muestra_datos_de_cuenta_solo_lectura(cliente_client, bd_limpia):
    html = cliente_client.get("/compra").get_data(as_text=True)
    assert 'id="correo"' in html and "cliente@correo.com" in html
    assert 'id="correo"' in html and "readonly" in html
    assert 'name="dni"' not in html
    assert html.count("data-ck-paso=") == 3
    assert 'data-ck-siguiente="2"' in html
    assert 'data-ck-siguiente="3"' in html
    assert 'data-ck-anterior="1"' in html and 'data-ck-anterior="2"' in html
    assert "checkout.js?v=20261026-1" in html
