"""Emisión, acceso y descarga del comprobante interno de venta."""

from io import BytesIO

from pypdf import PdfReader

from model.Comprobante import Comprobante
from model.Pedido import Pedido
from tests.conftest import CLIENTE_ID


ITEMS = [{
    "idProducto": 2,
    "nombre": "Simple de Carne",
    "precioUnidad": 12.5,   # 8.50 base + Queso (2.00) + Tocino (2.00)
    "cantidad": 2,
    "precioTotal": 25,
    "cremas": [57, 58],
}]


def _pedido_listo():
    id_pedido, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "yape", "Sin cebolla", ITEMS,
    )
    assert Pedido.avanzar_preparacion(id_pedido) == "preparando"
    assert Pedido.avanzar_preparacion(id_pedido) == "listo"
    return id_pedido, key


def test_entrega_exige_pedido_listo_y_medio_valido(bd_limpia):
    id_pedido, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "efectivo", None, ITEMS,
    )
    assert Pedido.marcar_recogido(id_pedido, key, "efectivo", 1) == "no_listo"
    Pedido.avanzar_preparacion(id_pedido)
    Pedido.avanzar_preparacion(id_pedido)
    assert Pedido.marcar_recogido(id_pedido, key, "bitcoin", 1) == "pago_invalido"
    assert Comprobante.id_por_pedido(id_pedido) is None


def test_caja_exige_dni_para_boleta_y_ruc_para_factura(bd_limpia):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, "yape", 1, "boleta", "123") == "dni_invalido"
    assert Pedido.marcar_recogido(id_pedido, key, "yape", 1, "factura", "20123456789") == "razon_social_requerida"
    assert Pedido.marcar_recogido(
        id_pedido, key, "yape", 1, "factura", "20123456789", "Cliente SAC") == "ok"
    comprobante = Comprobante.detalle(Comprobante.id_por_pedido(id_pedido))
    assert comprobante["tipoComprobante"] == "factura"
    assert comprobante["documento"] == "20123456789"
    assert comprobante["horaEntrega"] == comprobante["hora"]


def test_dni_y_ruc_son_opcionales(bd_limpia):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, None, 1, "boleta", "") == "ok"
    comprobante = Comprobante.detalle(Comprobante.id_por_pedido(id_pedido))
    assert comprobante["documento"] == ""
    id_pedido2, key2 = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido2, key2, None, 1, "factura", "") == "ok"


def test_snapshot_conserva_pago_lineas_y_cremas(bd_limpia):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, "yape", 1, "boleta", "12345679") == "ok"
    id_comprobante = Comprobante.id_por_pedido(id_pedido)
    comprobante = Comprobante.detalle(id_comprobante)

    assert comprobante["formaPago"] == "Yape"
    assert comprobante["idCajero"] == 1
    assert comprobante["montoTotal"] == 25.0
    assert comprobante["lineas"][0]["nombre"] == "Simple de Carne"
    assert set(comprobante["lineas"][0]["adicionales"]) == {"Queso", "Tocino"}


def test_cliente_y_caja_descargan_el_mismo_pdf(bd_limpia, cliente_client, admin_client):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, "tarjeta", 1, "boleta", "12345679") == "ok"
    id_comprobante = Comprobante.id_por_pedido(id_pedido)

    vista_cliente = cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante")
    pdf_cliente = cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante/pdf")
    pdf_caja = admin_client.get(f"/admin/ventas/detalle_comprobante/{id_comprobante}/pdf")

    assert vista_cliente.status_code == 200
    assert "Simple de Carne" in vista_cliente.get_data(as_text=True)
    for respuesta in (pdf_cliente, pdf_caja):
        assert respuesta.status_code == 200
        assert respuesta.mimetype == "application/pdf"
        assert respuesta.data.startswith(b"%PDF")
        texto = "".join(p.extract_text() or "" for p in PdfReader(BytesIO(respuesta.data)).pages)
        assert "LAS DE SIEMPRE" in texto
        assert "B001-" in texto
        assert "25.00" in texto


def test_cliente_no_puede_ver_comprobante_ajeno(bd_limpia, cliente_client):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, "efectivo", 1, "boleta", "12345679") == "ok"
    with cliente_client.session_transaction() as sesion:
        otro = dict(sesion["cliente.auth"])
        otro["idUsuario"] = 1
        sesion["cliente.auth"] = otro
    assert cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante").status_code == 404


def _confirmar(admin_client, id_pedido, key, **extra):
    datos = {"_csrf": "token-de-prueba", "idPedido": id_pedido, "key": key, "estado": "listo"}
    datos.update(extra)
    return admin_client.post("/admin/pedidos/confirmar", data=datos, follow_redirects=True)


def test_tres_opciones_de_comprobante_en_caja(bd_limpia, admin_client, csrf):
    # Boleta con DNI sin escribir el DNI: se rechaza y no se entrega.
    id1, key1 = _pedido_listo()
    r = _confirmar(admin_client, id1, key1, tipo_comprobante="boleta_dni")
    assert "8 dígitos" in r.get_data(as_text=True) and Comprobante.id_por_pedido(id1) is None
    # Boleta con DNI válido.
    _confirmar(admin_client, id1, key1, tipo_comprobante="boleta_dni", documento="12345678")
    assert Comprobante.detalle(Comprobante.id_por_pedido(id1))["documento"] == "12345678"
    # Boleta simple: sin documento aunque llegue uno.
    id2, key2 = _pedido_listo()
    _confirmar(admin_client, id2, key2, tipo_comprobante="boleta_simple", documento="99999999")
    c2 = Comprobante.detalle(Comprobante.id_por_pedido(id2))
    assert c2["documento"] == "" and c2["numero"].startswith("B001-")
    # Factura: exige RUC y razón social.
    id3, key3 = _pedido_listo()
    r = _confirmar(admin_client, id3, key3, tipo_comprobante="factura")
    assert "RUC" in r.get_data(as_text=True) and Comprobante.id_por_pedido(id3) is None
    _confirmar(admin_client, id3, key3, tipo_comprobante="factura",
               documento="20123456789", razon_social="Cliente SAC")
    assert Comprobante.detalle(Comprobante.id_por_pedido(id3))["numero"].startswith("F001-")
