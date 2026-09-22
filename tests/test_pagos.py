"""RS 9.1 / 9.2: pagos cobrados en caja, resumidos por medio."""

from model.Comprobante import Comprobante
from model.Pago import Pago
from model.Pedido import Pedido
from negocio import ahora_peru
from tests.conftest import CLIENTE_ID
from tests.test_comprobante_pdf import ITEMS


def _cobrar(medio):
    id_pedido, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", medio, None, ITEMS)
    Pedido.avanzar_preparacion(id_pedido)
    Pedido.avanzar_preparacion(id_pedido)
    assert Pedido.marcar_recogido(id_pedido, key, None, 1, "boleta", "") == "ok"
    return Comprobante.id_por_pedido(id_pedido)


def test_resumen_por_medio_y_anulados_no_suman(bd_limpia):
    hoy = ahora_peru().date()
    _cobrar("efectivo")
    cid_yape = _cobrar("yape")
    _cobrar("yape")
    r = Pago.resumen(hoy, hoy)
    por = {m["medio"]: m for m in r["medios"]}
    assert por["Efectivo"]["cantidad"] == 1 and por["Yape"]["cantidad"] == 2
    assert r["total"] == 75.0 and r["cantidad"] == 3
    assert por["Yape"]["pct"] + por["Efectivo"]["pct"] == 100
    Comprobante.anular(cid_yape, "cobro duplicado", 1)
    r = Pago.resumen(hoy, hoy)
    assert r["total"] == 50.0 and r["anulado"]["cantidad"] == 1 and r["anulado"]["total"] == 25.0
    assert Pago.total(hoy, hoy, medio="Yape") == 2          # el listado sí muestra el anulado
    assert Pago.total(hoy, hoy, estado="vigente", medio="Yape") == 1


def test_pagina_de_pagos_filtros_y_parcial(bd_limpia, admin_client):
    _cobrar("plin")
    html = admin_client.get("/admin/pagos/").get_data(as_text=True)
    assert "<html" in html and "Total cobrado" in html and "Plin" in html
    parcial = admin_client.get("/admin/pagos/?desde=&hasta=&medio=Plin",
                               headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
    assert "<html" not in parcial and "Mostrando" in parcial
    vacio = admin_client.get("/admin/pagos/?medio=Tarjeta", headers={"X-Requested-With": "fetch"}).get_data(as_text=True)
    assert "No hay pagos con estos filtros" in vacio
    assert admin_client.get("/admin/pagos/?desde=xx&hasta=2001-01-01&estado=zzz&medio=bitcoin").status_code == 200
