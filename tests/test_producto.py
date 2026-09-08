"""CRUD de productos y su efecto en la carta."""

import bd
from model.Producto import Producto, _a_precio, _a_stock
from model.CategoriaProducto import CategoriaProducto


def test_a_precio_rechaza_texto_y_negativos():
    assert _a_precio("dieciocho")[1] is not None
    assert _a_precio("-5")[1] is not None
    assert _a_precio("999999999")[1] is not None
    assert _a_precio("18.5") == (18.5, None)


def test_a_stock_rechaza_texto_y_negativos():
    assert _a_stock("muchos")[1] is not None
    assert _a_stock("-1")[1] is not None
    assert _a_stock("25") == (25, None)


def test_insertar_producto_valida(bd_limpia):
    assert Producto.insertar_producto("X", "d", "-1", "5", 1) is not None       # precio malo
    assert Producto.insertar_producto("X", "d", "10", "-3", 1) is not None      # stock malo
    assert Producto.insertar_producto("X", "d", "10", "5", 999) is not None     # categoría inexistente
    assert Producto.insertar_producto("Nuevo Test", "rica", "12.5", "8", 1) is None
    nombres = [p["nombre"] for p in Producto.obtener_productos()]
    assert "Nuevo Test" in nombres


def test_actualizar_producto_precio_texto_no_rompe(bd_limpia):
    err = Producto.actualizar_producto("Smash Las Musas", "d", "carísimo", "10", 2, 1)
    assert err is not None
    p = Producto.obtener_producto_por_id(2)
    assert p["precio"] == 18.0  # no cambió


def test_dar_de_baja_categoria_saca_sus_productos_de_la_carta(bd_limpia):
    antes = {p["idProducto"] for p in Producto.obtener_productos(solo_activos=True)}
    assert 2 in antes  # Smash está en Hamburguesas (cat 1)
    CategoriaProducto.cambiar_estado(1, False)
    despues = {p["idProducto"] for p in Producto.obtener_productos(solo_activos=True)}
    assert 2 not in despues
    CategoriaProducto.cambiar_estado(1, True)
    assert 2 in {p["idProducto"] for p in Producto.obtener_productos(solo_activos=True)}


def test_dar_de_baja_producto(bd_limpia):
    Producto.cambiar_estado(2, False)
    activos = {p["idProducto"] for p in Producto.obtener_productos(solo_activos=True)}
    assert 2 not in activos


def test_precios_por_ids_ignora_inactivos_y_basura(bd_limpia):
    Producto.cambiar_estado(2, False)
    precios = Producto.precios_por_ids(["2", "4", "abc", "-1", "9999"])
    assert 2 not in precios
    assert 4 in precios


def test_categoria_nombre_muy_corto(bd_limpia):
    assert CategoriaProducto.insertar_categoria("A", "x") is not None
    assert CategoriaProducto.insertar_categoria("Veggies", "hamburguesas sin carne") is None
