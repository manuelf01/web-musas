"""Sanitización del carrito (viene del localStorage) y sugeridos (upsell)."""

import json

from model.Producto import Producto


def _leer(app, carrito_json):
    from controllers.cliente import _leer_carrito
    with app.test_request_context("/compra", method="POST",
                                  data={"carrito_json": carrito_json}):
        return _leer_carrito()


def test_carrito_json_malo_devuelve_lista_vacia(app):
    assert _leer(app, "no-es-json") == []
    assert _leer(app, '{"no": "lista"}') == []
    assert _leer(app, "") == []


def test_carrito_ignora_lineas_sin_id_y_normaliza_cantidad(app):
    crudo = json.dumps([
        {"idProducto": 2, "cantidad": 3, "cremas": [16, 16, 19]},
        {"idProducto": 0, "cantidad": 1},          # id inválido -> fuera
        {"idProducto": "abc", "cantidad": 1},      # id no numérico -> fuera
        {"idProducto": 4, "cantidad": 9999},       # se recorta a 99
        {"idProducto": 5, "cantidad": -2},         # sube a 1
        "no es un dict",
    ])
    limpio = _leer(app, crudo)
    porid = {it["idProducto"]: it for it in limpio}
    assert set(porid) == {2, 4, 5}
    assert porid[2]["cremas"] == [16, 19]   # sin duplicados
    assert porid[4]["cantidad"] == 99
    assert porid[5]["cantidad"] == 1


def test_sugeridos_ofrece_bebida_si_hay_comida_sin_bebida(bd_limpia):
    sug = Producto.sugeridos(["2"])  # solo una hamburguesa
    cats = {s["categoria"] for s in sug}
    assert "Bebidas" in cats
    assert all(s["idProducto"] != 2 for s in sug)
    assert len(sug) <= 4


def test_sugeridos_no_repite_lo_que_ya_esta(bd_limpia):
    sug = Producto.sugeridos(["2", "9"])  # hamburguesa + Chicha Morada (bebida)
    ids = {s["idProducto"] for s in sug}
    assert 2 not in ids and 9 not in ids
    assert "Bebidas" not in {s["categoria"] for s in sug}  # ya tiene bebida


def test_sugeridos_excluye_cremas_e_inactivos(bd_limpia):
    Producto.cambiar_estado(14, False)  # Cookie (postre) de baja
    sug = Producto.sugeridos([])
    assert all(s["categoria"] != "Cremas" for s in sug)
    assert 14 not in {s["idProducto"] for s in sug}
