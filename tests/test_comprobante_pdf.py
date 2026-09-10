"""Emisión, acceso y descarga del comprobante interno de venta."""

from io import BytesIO

from pypdf import PdfReader

from model.Comprobante import Comprobante
from model.Pedido import Pedido
from tests.conftest import CLIENTE_ID


ITEMS = [{
    "idProducto": 2,
    "nombre": "Smash Las Musas",
    "precioUnidad": 21,
    "cantidad": 2,
    "precioTotal": 42,
    "cremas": [16, 19],
}]


def _pedido_listo():
    id_pedido, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "Cliente Prueba", "999888777",
        "20:00:00", True, True, "Sin cebolla", ITEMS,
    )
    assert Pedido.avanzar_preparacion(id_pedido) == "preparando"
    assert Pedido.avanzar_preparacion(id_pedido) == "listo"
    return id_pedido, key


def test_entrega_exige_pedido_listo_y_medio_valido(bd_limpia):
    id_pedido, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "Cliente Prueba", "999888777",
        "20:00:00", True, False, None, ITEMS,
    )
    assert Pedido.marcar_recogido(id_pedido, key, "efectivo", 1) == "no_listo"
    Pedido.avanzar_preparacion(id_pedido)
    Pedido.avanzar_preparacion(id_pedido)
    assert Pedido.marcar_recogido(id_pedido, key, "bitcoin", 1) == "pago_invalido"
    assert Comprobante.id_por_pedido(id_pedido) is None


def test_snapshot_conserva_pago_lineas_y_cremas(bd_limpia):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, "yape", 1) == "ok"
    id_comprobante = Comprobante.id_por_pedido(id_pedido)
    comprobante = Comprobante.detalle(id_comprobante)

    assert comprobante["formaPago"] == "Yape"
    assert comprobante["idCajero"] == 1
    assert comprobante["montoTotal"] == 42.0
    assert comprobante["lineas"][0]["nombre"] == "Smash Las Musas"
    assert set(comprobante["lineas"][0]["adicionales"]) == {"Mayonesa de la Casa", "Cheddar Fundido"}


def test_cliente_y_caja_descargan_el_mismo_pdf(bd_limpia, cliente_client, admin_client):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, "tarjeta", 1) == "ok"
    id_comprobante = Comprobante.id_por_pedido(id_pedido)

    vista_cliente = cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante")
    pdf_cliente = cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante/pdf")
    pdf_caja = admin_client.get(f"/admin/ventas/detalle_comprobante/{id_comprobante}/pdf")

    assert vista_cliente.status_code == 200
    assert "Smash Las Musas" in vista_cliente.get_data(as_text=True)
    for respuesta in (pdf_cliente, pdf_caja):
        assert respuesta.status_code == 200
        assert respuesta.mimetype == "application/pdf"
        assert respuesta.data.startswith(b"%PDF")
        texto = "".join(p.extract_text() or "" for p in PdfReader(BytesIO(respuesta.data)).pages)
        assert "LAS MUSAS" in texto
        assert "B001-" in texto
        assert "42.00" in texto


def test_cliente_no_puede_ver_comprobante_ajeno(bd_limpia, cliente_client):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, "efectivo", 1) == "ok"
    with cliente_client.session_transaction() as sesion:
        otro = dict(sesion["cliente.auth"])
        otro["idUsuario"] = 1
        sesion["cliente.auth"] = otro
    assert cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante").status_code == 404
