"""Ruta de navegación (migas): cada pantalla dice dónde estás y cómo volver."""

import re

from model.Comprobante import Comprobante
from model.Pedido import Pedido
from tests.test_comprobante_pdf import _pedido_listo


def _migas(html):
    m = re.search(r'<nav class="migas[^"]*"[^>]*>(.*?)</nav>', html, re.S)
    assert m, "la pantalla debe mostrar la ruta"
    return m.group(1)


def _actual(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", re.search(
        r'aria-current="page"[^>]*>(.*?)</span>', _migas(html), re.S).group(1))).strip()


def test_migas_de_la_tienda(client, cliente_client):
    carta = cliente_client.get("/carta").get_data(as_text=True)
    assert _actual(carta) == "Carta" and "Inicio" in _migas(carta)
    cat = cliente_client.get("/productos/Hamburguesas").get_data(as_text=True)
    assert _actual(cat) == "Hamburguesas" and 'href="/carta"' in _migas(cat)
    prod = cliente_client.get("/producto/2").get_data(as_text=True)
    ruta = _migas(prod)
    assert 'href="/carta"' in ruta and 'href="/productos/Hamburguesas"' in ruta
    assert "carta-breadcrumb" not in prod
    editar = cliente_client.get("/producto/2?editar=0").get_data(as_text=True)
    assert _actual(editar).startswith("Editar") and 'href="/carrito"' in _migas(editar)
    assert _actual(cliente_client.get("/carrito").get_data(as_text=True)) == "Carrito"
    assert _actual(cliente_client.get("/mis-pedidos").get_data(as_text=True)) == "Mis pedidos"
    assert _actual(cliente_client.get("/mi-cuenta").get_data(as_text=True)) == "Mi cuenta"
    assert _actual(cliente_client.get("/nosotros").get_data(as_text=True)) == "Conócenos"
    assert "migas" not in client.get("/").get_data(as_text=True).split("<main>")[0].split("</header>")[-1]


def test_migas_del_comprobante_del_cliente(bd_limpia, cliente_client):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, None, 1, "boleta", "") == "ok"
    html = cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante").get_data(as_text=True)
    assert _actual(html).startswith("Comprobante B001-")
    assert f"Pedido N° {id_pedido}" in _migas(html) and 'href="/mis-pedidos"' in _migas(html)


def test_migas_del_panel(bd_limpia, admin_client):
    esperado = {
        "/admin/": "Resumen", "/admin/pedidos/": "Por entregar",
        "/admin/pedidos/?estado=listo": "Listos para cobrar",
        "/admin/productos/": "Productos", "/admin/productos/?estado=baja": "Productos · De baja",
        "/admin/productos/?estado=sin_stock": "Productos · Sin stock",
        "/admin/categorias/": "Categorías", "/admin/usuarios/": "Usuarios",
        "/admin/usuarios/?rol=usuario": "Usuarios · Clientes",
        "/admin/ventas/": "Ventas", "/admin/ventas/?estado=anulado": "Ventas · Anuladas",
        "/admin/pagos/": "Pagos", "/admin/perfil/": "Mi perfil",
    }
    for url, ultimo in esperado.items():
        html = admin_client.get(url).get_data(as_text=True)
        assert 'migas--panel' in html and _actual(html) == ultimo, url
    id_pedido, key = _pedido_listo()
    Pedido.marcar_recogido(id_pedido, key, None, 1, "boleta", "")
    cid = Comprobante.id_por_pedido(id_pedido)
    html = admin_client.get(f"/admin/ventas/detalle_comprobante/{cid}").get_data(as_text=True)
    assert _actual(html).startswith("Comprobante B001-") and 'href="/admin/ventas/"' in _migas(html)
