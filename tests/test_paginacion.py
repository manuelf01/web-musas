"""Listados con flechas/números: productos (10), comprobantes (5), usuarios (10) y Mis pedidos (5)."""

import re

from bd import obtener_conexion


def _filas(html):
    return len(re.findall(r'<td>\s*<div class="adm-prod-cel">', html))


def test_productos_10_por_pagina_y_pagina_2(bd_limpia, admin_client):
    p1 = admin_client.get("/admin/productos/").get_data(as_text=True)
    p2 = admin_client.get("/admin/productos/?page=2").get_data(as_text=True)
    assert _filas(p1) == 10 and _filas(p2) == 10
    assert "Mostrando 1–10 de 60 productos" in p1
    assert "Mostrando 11–20 de 60 productos" in p2
    assert 'class="page-link"' in p1


def test_productos_filtrar_por_categoria(bd_limpia, admin_client):
    html = admin_client.get("/admin/productos/?cat=13").get_data(as_text=True)  # Agregados: 10
    assert "Mostrando 1–10 de 10 productos" in html
    assert "<strong>Presa de Pollo</strong>" in html
    assert "<strong>Simple de Pollo</strong>" not in html


def test_usuarios_pagina_de_10(bd_limpia, admin_client):
    con = obtener_conexion()
    try:
        with con.cursor() as cur:
            for i in range(12):
                cur.execute(
                    "INSERT INTO usuario (nombres, apellidos, correo, numTelf, `contraseña`, tipoUsuario, rol, activo) "
                    "VALUES (%s, 'Prueba', %s, '900000000', 'x', 1, 'usuario', 1)",
                    (f"Cliente{i:02d}", f"cli{i}@correo.com"))
        con.commit()
    finally:
        con.close()
    p1 = admin_client.get("/admin/usuarios/").get_data(as_text=True)
    p2 = admin_client.get("/admin/usuarios/?page=2").get_data(as_text=True)
    assert "Mostrando 1–10 de" in p1
    assert "Mostrando 11–" in p2


def test_detalle_muestra_la_imagen_de_la_salsa(bd_limpia, cliente_client):
    con = obtener_conexion()
    try:
        with con.cursor() as cur:
            cur.execute("UPDATE producto SET imagen='productos/mayo.jpg' WHERE idProducto=41")
        con.commit()
    finally:
        con.close()
    html = cliente_client.get("/producto/2").get_data(as_text=True)
    assert 'img/productos/mayo.jpg' in html


def test_mis_pedidos_de_5_en_5_con_busqueda_y_fechas(bd_limpia, cliente_client):
    from model.Pedido import Pedido
    from tests.conftest import CLIENTE_ID
    item = {"idProducto": 2, "nombre": "Simple de Carne", "precioUnidad": 8.5,
            "cantidad": 1, "precioTotal": 8.5, "cremas": []}
    horas = ["12:00:00", "12:30:00", "13:00:00", "13:30:00", "14:00:00", "14:30:00", "15:00:00"]
    for h in horas:
        idp, _ = Pedido.crear_pedido_completo(CLIENTE_ID, "cliente@correo.com", "Cliente Prueba",
                                              "999888777", h, "efectivo", None, [item])
        con = obtener_conexion()  # se cancela para no chocar con el límite de pedidos activos
        try:
            with con.cursor() as cur:
                cur.execute("UPDATE registroPedido SET cancelado = 1 WHERE idPedido = %s", (idp,))
            con.commit()
        finally:
            con.close()
    p1 = cliente_client.get("/mis-pedidos").get_data(as_text=True)
    p2 = cliente_client.get("/mis-pedidos?page=2").get_data(as_text=True)
    assert p1.count('class="mp-card"') == 5 and p2.count('class="mp-card"') == 2
    assert "Mostrando 1–5 de 7 pedidos" in p1
    assert 'name="desde"' in p1 and 'name="q"' in p1
    assert cliente_client.get("/mis-pedidos?q=zzzz-no-existe").get_data(as_text=True).count('class="mp-card"') == 0
    assert cliente_client.get("/mis-pedidos?q=simple+de+carne").get_data(as_text=True).count('class="mp-card"') == 5
    assert cliente_client.get("/mis-pedidos?desde=2999-01-01").get_data(as_text=True).count('class="mp-card"') == 0
