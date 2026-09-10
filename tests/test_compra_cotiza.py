"""Re-cotización del carrito contra la BD y cupo de franja en la transacción."""

import json

import pytest

import bd
from model.Pedido import Pedido, FranjaLlena

from tests.conftest import CLIENTE_ID


def _cotizar(app, carrito):
    from controllers.cliente import _cotizar_carrito
    with app.test_request_context("/compra/cotizar", method="POST"):
        return _cotizar_carrito(carrito)


def test_cotiza_usa_el_precio_actual_de_la_bd(app, bd_limpia):
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("UPDATE producto SET precio = 25.50 WHERE idProducto = 2")
        con.commit()
    con.close()
    items, total = _cotizar(app, [{"idProducto": 2, "cantidad": 2, "cremas": []}])
    assert str(items[0]["precioUnidad"]) == "25.50"
    assert str(total) == "51.00"


def test_cotiza_ignora_cremas_en_productos_que_no_las_admiten(app, bd_limpia):
    # Chicha Morada (id 9, Bebida) con una crema colada por POST directo.
    items, total = _cotizar(app, [{"idProducto": 9, "cantidad": 1, "cremas": [16]}])
    assert items[0]["cremas"] == []
    assert str(items[0]["precioUnidad"]) == "8.00"


def test_cotiza_suma_cremas_en_hamburguesa(app, bd_limpia):
    items, _ = _cotizar(app, [{"idProducto": 2, "cantidad": 1, "cremas": [16, 19]}])
    assert sorted(items[0]["cremas"]) == [16, 19]
    assert str(items[0]["precioUnidad"]) == "21.00"   # 18 + 1 + 2


def test_endpoint_cotizar_devuelve_total_de_servidor(cliente_client, csrf):
    carrito = json.dumps([{"idProducto": 2, "cantidad": 1, "cremas": []}])
    r = cliente_client.post("/compra/cotizar",
                            data={"carrito_json": carrito, "_csrf": csrf})
    assert r.status_code == 200
    assert r.get_json()["total"] == "18.00"


def test_franja_llena_se_rechaza_dentro_de_la_transaccion(bd_limpia, monkeypatch):
    monkeypatch.setattr(Pedido, "CUPO_POR_FRANJA", 1)
    linea = [{"idProducto": 2, "nombre": "Smash", "precioUnidad": 18,
              "cantidad": 1, "precioTotal": 18, "cremas": []}]
    Pedido.crear_pedido_completo(1, "12345678", "A", "999", "19:00:00",
                                 False, False, None, linea)
    with pytest.raises(FranjaLlena):
        Pedido.crear_pedido_completo(2, "87654321", "B", "999", "19:00:00",
                                     False, False, None, linea)
    # otra franja sigue libre
    idp, _ = Pedido.crear_pedido_completo(2, "87654321", "B", "999", "19:30:00",
                                          False, False, None, linea)
    assert idp > 0
