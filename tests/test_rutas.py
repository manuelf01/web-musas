"""Humo de rutas: páginas públicas responden y el panel exige sesión."""

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
])
def test_panel_sin_sesion_redirige(client, url):
    r = client.get(url, follow_redirects=False)
    assert r.status_code in (301, 302)


@pytest.mark.parametrize("url", [
    "/admin/", "/admin/pedidos/", "/admin/productos/", "/admin/categorias/",
    "/admin/ventas/", "/admin/perfil/", "/admin/usuarios/",
])
def test_panel_con_sesion_ok(admin_client, url):
    assert admin_client.get(url).status_code == 200


def test_carrito_exige_login(client):
    r = client.get("/carrito", follow_redirects=False)
    assert r.status_code in (301, 302)


def test_pulso_de_cocina(admin_client, bd_limpia):
    d = admin_client.get("/admin/pedidos/pulso").get_json()
    assert d["pendientes"] == []
    f0 = d["firma"]
    Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "C", "999", "19:00:00", False, False, None,
        [{"idProducto": 2, "nombre": "Smash", "precioUnidad": 18,
          "cantidad": 1, "precioTotal": 18, "cremas": []}])
    d2 = admin_client.get("/admin/pedidos/pulso").get_json()
    assert d2["firma"] != f0
    assert len(d2["pendientes"]) == 1


def test_seguimiento_estado_del_cliente(cliente_client, bd_limpia):
    idp, _ = Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "C", "999", "19:00:00", False, False, None,
        [{"idProducto": 2, "nombre": "Smash", "precioUnidad": 18,
          "cantidad": 1, "precioTotal": 18, "cremas": []}])
    d = cliente_client.get("/mis-pedidos/estado").get_json()
    assert d["estados"][str(idp)] == "recibido"
    Pedido.avanzar_preparacion(idp)
    d2 = cliente_client.get("/mis-pedidos/estado").get_json()
    assert d2["estados"][str(idp)] == "preparando"
    assert d2["firma"] != d["firma"]


def test_sugeridos_endpoint(client, bd_limpia):
    d = client.get("/carrito/sugeridos?ids=2").get_json()
    assert "sugeridos" in d and len(d["sugeridos"]) <= 4
