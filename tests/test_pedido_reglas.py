"""Reglas del pedido: límite de activos, stock, cancelación por estado."""

import pytest

import bd
from model.Pedido import Pedido, LimitePedidos, StockInsuficiente

from tests.conftest import CLIENTE_ID

UNA_LINEA = [{"idProducto": 2, "nombre": "Smash", "precioUnidad": 18,
              "cantidad": 1, "precioTotal": 18, "cremas": []}]


def _crear(hora="19:00:00", items=None):
    return Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "C", "999", hora, False, False, None, items or UNA_LINEA)


def test_limite_de_pedidos_activos_por_persona(bd_limpia):
    _crear()
    _crear()
    with pytest.raises(LimitePedidos):
        _crear()


def test_sin_stock_suficiente_lanza_y_no_crea(bd_limpia):
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("UPDATE producto SET existencias = 1 WHERE idProducto = 2")
        con.commit()
    con.close()
    with pytest.raises(StockInsuficiente):
        _crear(items=[{"idProducto": 2, "nombre": "Smash", "precioUnidad": 18,
                       "cantidad": 5, "precioTotal": 90, "cremas": []}])
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("SELECT existencias FROM producto WHERE idProducto = 2")
        assert cur.fetchone()[0] == 1  # no se tocó el stock
        cur.execute("SELECT COUNT(*) FROM registroPedido")
        assert cur.fetchone()[0] == 0
    con.close()


def test_cliente_cancela_solo_mientras_recibido(bd_limpia):
    idp, _ = _crear()
    # en preparación -> el cliente ya no puede
    Pedido.avanzar_preparacion(idp)
    assert Pedido.cancelar_pedido(idp, id_usuario=CLIENTE_ID) == "en_preparacion"


def test_cliente_no_cancela_pedido_ajeno(bd_limpia):
    idp, _ = _crear()
    assert Pedido.cancelar_pedido(idp, id_usuario=999) == "no_permitido"


def test_cancelar_devuelve_stock_y_libera(bd_limpia):
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("SELECT existencias FROM producto WHERE idProducto = 2")
        s0 = cur.fetchone()[0]
    con.close()
    idp, _ = _crear()
    assert Pedido.cancelar_pedido(idp, id_usuario=CLIENTE_ID) == "ok"
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("SELECT existencias FROM producto WHERE idProducto = 2")
        assert cur.fetchone()[0] == s0
    con.close()
    # el admin puede forzar, pero ya está cancelado
    assert Pedido.cancelar_pedido(idp, saltar_dueno=True) == "no_cancelable"


def test_historial_marca_cancelable_solo_recibido(bd_limpia):
    idp, _ = _crear()
    h = {p["idPedido"]: p for p in Pedido.historial_cliente(CLIENTE_ID)}
    assert h[idp]["cancelable"] is True
    Pedido.avanzar_preparacion(idp)
    h = {p["idPedido"]: p for p in Pedido.historial_cliente(CLIENTE_ID)}
    assert h[idp]["cancelable"] is False
    assert h[idp]["estado"] == "preparando"
