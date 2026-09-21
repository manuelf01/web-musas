"""Ventas: gráfico por año/mes elegible, filtros de comprobantes y sugerencias."""

from model.Comprobante import Comprobante
from tests.test_comprobante_pdf import _pedido_listo
from model.Pedido import Pedido


def _emitir(medio="efectivo", tipo="boleta", doc="12345678", razon=""):
    id_pedido, key = _pedido_listo()
    assert Pedido.marcar_recogido(id_pedido, key, None, 1, tipo, doc, razon) == "ok"
    return id_pedido


def test_serie_por_mes_y_anio_tienen_las_barras_esperadas(bd_limpia):
    _emitir()
    mes = Comprobante.serie_ventas("mes", 2030, 2)
    assert mes["n"] == 28 and mes["vacio"] and mes["denso"]
    anio = Comprobante.serie_ventas("anio", 2030)
    assert anio["n"] == 12
    hoy = Comprobante.serie_ventas("anio")
    assert not hoy["vacio"] and hoy["total"] > 0
    assert max(b["pct"] for b in hoy["barras"]) <= 100


def test_anios_disponibles_incluye_el_actual(bd_limpia):
    assert Comprobante.anios_disponibles()[0] >= 2026


def test_filtros_de_comprobantes_y_respuesta_parcial(bd_limpia, admin_client):
    _emitir()
    todo = admin_client.get("/admin/ventas/").get_data(as_text=True)
    assert "<html" in todo and "vchart" in todo
    parcial = admin_client.get("/admin/ventas/?tipo=factura",
                               headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
    assert "<html" not in parcial and "Ningún comprobante coincide" in parcial
    parcial = admin_client.get("/admin/ventas/?tipo=boleta&q=B001",
                               headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
    assert "B001-" in parcial and "Mostrando" in parcial


def test_filtro_por_fechas_y_sugerencias(bd_limpia, admin_client):
    _emitir()
    fuera = admin_client.get("/admin/ventas/?desde=2001-01-01&hasta=2001-12-31",
                             headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
    assert "Ningún comprobante coincide" in fuera
    sug = admin_client.get("/admin/ventas/sugerencias?q=B00").get_json()
    assert any(s.startswith("B001-") for s in sug)
    assert admin_client.get("/admin/ventas/sugerencias?q=").get_json() == []
    assert admin_client.get("/admin/ventas/?vista=mes&anio=1999&mes=13&dia=xx").status_code == 200
