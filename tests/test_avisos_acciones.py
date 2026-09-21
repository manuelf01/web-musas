"""Avisos del panel: «Deshacer» en los verdes y «Ver dónde» en los rojos."""

import json
import re

from model.Pedido import Pedido
from model.Producto import Producto
from model.Usuario import Usuario
from tests.test_comprobante_pdf import ITEMS
from tests.conftest import CLIENTE_ID

T = "token-de-prueba"


def _pagina(cli, url):
    return cli.get(url, follow_redirects=True).get_data(as_text=True)


def test_agregar_producto_ofrece_deshacer_y_lo_da_de_baja(bd_limpia, admin_client, csrf):
    r = admin_client.post("/admin/productos/guardar_producto", data={
        "_csrf": T, "nombre": "Prueba Deshacer", "descripcion": "x", "precio": "10",
        "existencias": "5", "categorias": "1"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Producto agregado" in html and "Deshacer" in html
    nuevo = Producto.ultimo_id()
    m = re.search(r'action="(/admin/productos/estado)"[^>]*class="aviso__form"', html)
    assert m, "el aviso debe traer el formulario de deshacer"
    assert f'name="id" value="{nuevo}"' in html and 'name="activar" value="0"' in html
    r = admin_client.post("/admin/productos/estado", data={
        "_csrf": T, "id": nuevo, "activar": "0", "volver": "activos"}, follow_redirects=True)
    assert "eliminado de la carta" in r.get_data(as_text=True)
    assert Producto.obtener_producto_por_id(nuevo)["activo"] is False


def test_editar_producto_puede_revertirse(bd_limpia, admin_client, csrf):
    antes = Producto.obtener_producto_por_id(2)
    r = admin_client.post("/admin/productos/actualizar_producto", data={
        "_csrf": T, "idProducto": 2, "nombre": "Nombre nuevo", "descripcion": antes["descripcion"],
        "precio": "99", "existencias": antes["existencias"], "categorias": antes["idCategoria"],
        "activo": "1"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Deshacer" in html and f'name="nombre" value="{antes["nombre"]}"' in html
    admin_client.post("/admin/productos/actualizar_producto", data={
        "_csrf": T, "idProducto": 2, "nombre": antes["nombre"], "descripcion": antes["descripcion"],
        "precio": antes["precio"], "existencias": antes["existencias"],
        "categorias": antes["idCategoria"], "activo": "1", "imagen_ruta": ""})
    despues = Producto.obtener_producto_por_id(2)
    assert despues["nombre"] == antes["nombre"] and float(despues["precio"]) == float(antes["precio"])


def test_error_de_precio_senala_el_campo(bd_limpia, admin_client, csrf):
    r = admin_client.post("/admin/productos/guardar_producto", data={
        "_csrf": T, "nombre": "X", "descripcion": "y", "precio": "abc",
        "existencias": "5", "categorias": "1"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "data-ver-donde" in html
    info = json.loads(re.search(r'id="musa-error-form">(.*?)</script>', html, re.S).group(1))
    assert info["campo"] == "precio" and info["modo"] == "crear" and info["valores"]["nombre"] == "X"


def test_error_de_usuario_no_guarda_la_contrasena_y_senala_telefono(bd_limpia, admin_client, csrf):
    r = admin_client.post("/admin/usuarios/guardar", data={
        "_csrf": T, "nombres": "A", "apellidos": "B", "correo": "a@b.co", "telefono": "12",
        "contraseña": "Secreta123", "rol": "usuario"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    info = json.loads(re.search(r'id="musa-error-form">(.*?)</script>', html, re.S).group(1))
    assert info["campo"] == "telefono"
    assert "Secreta123" not in html and not any("contra" in k.lower() for k in info["valores"])


def test_usuario_creado_se_puede_deshacer(bd_limpia, admin_client, csrf):
    r = admin_client.post("/admin/usuarios/guardar", data={
        "_csrf": T, "nombres": "Nuevo", "apellidos": "Cliente", "correo": "nuevo@undo.co",
        "telefono": "987654321", "contraseña": "Secreta123", "rol": "usuario"}, follow_redirects=True)
    html = r.get_data(as_text=True)
    nid = Usuario.id_por_correo("nuevo@undo.co")
    assert "Deshacer" in html and f'name="id" value="{nid}"' in html


def test_avance_de_cocina_se_puede_deshacer(bd_limpia, admin_client, csrf):
    id_pedido, _ = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "efectivo", None, ITEMS)
    r = admin_client.post("/admin/pedidos/preparar", data={"_csrf": T, "idPedido": id_pedido},
                          follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Deshacer" in html and "/admin/pedidos/retroceder" in html
    admin_client.post("/admin/pedidos/retroceder", data={"_csrf": T, "idPedido": id_pedido})
    assert Pedido.avanzar_preparacion(id_pedido) == "preparando"
