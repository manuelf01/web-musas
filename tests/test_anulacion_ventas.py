"""RS 14: anular ventas realizadas."""

from io import BytesIO

from pypdf import PdfReader

from model.Comprobante import Comprobante
from model.Pedido import Pedido
from model.Producto import Producto
from tests.test_comprobante_pdf import _pedido_listo

T = "token-de-prueba"


def _venta():
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, None, 1, "boleta", "") == "ok"
    return id_pedido, Comprobante.id_por_pedido(id_pedido)


def test_anular_exige_motivo_y_excluye_la_venta_de_los_totales(bd_limpia):
    _, cid = _venta()
    antes = Comprobante.kpis()
    assert Comprobante.anular(cid, "  ", 1) == "motivo_invalido"
    assert Comprobante.anular(cid, "corto", 1) == "ok"
    assert Comprobante.anular(cid, "otra vez, motivo largo", 1) == "ya_anulado"
    despues = Comprobante.kpis()
    assert despues["cantidad"] == antes["cantidad"] - 1
    assert despues["total"] == round(antes["total"] - 42.0, 2)
    assert Comprobante.serie_ventas("anio")["total"] == round(antes["total"] - 42.0, 2)
    d = Comprobante.detalle(cid)
    assert d["anulado"] and d["motivoAnulacion"] == "corto"
    assert Comprobante.anular(99999, "motivo valido", 1) == "no_existe"


def test_anular_devolviendo_stock_y_restaurar(bd_limpia):
    _, cid = _venta()
    stock0 = Producto.obtener_producto_por_id(2)["existencias"]
    assert Comprobante.anular(cid, "cliente devolvió el pedido", 1, devolver_stock=True) == "ok"
    assert Producto.obtener_producto_por_id(2)["existencias"] == stock0 + 2
    assert Comprobante.restaurar(cid) == "ok"
    assert Producto.obtener_producto_por_id(2)["existencias"] == stock0
    assert not Comprobante.detalle(cid)["anulado"]
    assert Comprobante.restaurar(cid) == "no_anulado"


def test_anulacion_por_http_listado_detalle_y_pdf(bd_limpia, admin_client, cliente_client, csrf):
    id_pedido, cid = _venta()
    r = admin_client.post(f"/admin/ventas/anular/{cid}", data={"_csrf": T, "motivo": "x"}, follow_redirects=True)
    assert "motivo de la anulación" in r.get_data(as_text=True)
    r = admin_client.post(f"/admin/ventas/anular/{cid}", data={"_csrf": T, "motivo": "Cobro duplicado"},
                          follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Venta anulada" in html and "Deshacer anulación" in html and "Cobro duplicado" in html
    lista = admin_client.get("/admin/ventas/?estado=anulado", headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
    assert "Anulada" in lista
    vigentes = admin_client.get("/admin/ventas/?estado=vigente", headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
    assert "Ningún comprobante coincide" in vigentes
    pdf = admin_client.get(f"/admin/ventas/detalle_comprobante/{cid}/pdf")
    texto = "".join(p.extract_text() or "" for p in PdfReader(BytesIO(pdf.data)).pages)
    assert "ANULADO" in texto
    assert "anulado" in cliente_client.get(f"/mis-pedidos/{id_pedido}/comprobante").get_data(as_text=True).lower()
    r = admin_client.post(f"/admin/ventas/restaurar/{cid}", data={"_csrf": T}, follow_redirects=True)
    assert "Anulación deshecha" in r.get_data(as_text=True)
    assert not Comprobante.detalle(cid)["anulado"]
