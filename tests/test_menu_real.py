"""Menú real: categorías reales, y personalización (salsa obligatoria, papas
obligatorias, agregados de pago opcionales) en vez del viejo esquema de cremas."""

import re

from model.Producto import Producto, CATEGORIAS_PERSONALIZACION


def test_categorias_reales_y_ocultas(bd_limpia):
    nombres = {c[1] for c in __import__("model.CategoriaProducto", fromlist=["CategoriaProducto"])
               .CategoriaProducto.obtener_categorias()}
    esperadas = {
        "Hamburguesas Simples", "Hamburguesas Royal", "Hamburguesas Mixtas",
        "Hamburguesas Hawaianas", "Hamburguesas a lo Pobre", "Hamburguesas Especiales",
        "Maxi Burgers", "Platos Especiales", "Combos", "Bebidas",
        "Salsas", "Papas", "Agregados",
    }
    assert esperadas <= nombres
    assert set(CATEGORIAS_PERSONALIZACION) == {"Salsas", "Papas", "Agregados"}


def test_carta_no_muestra_las_categorias_ocultas(bd_limpia, client):
    html = client.get("/carta").get_data(as_text=True)
    # Nombres de personalización que no deberían colarse como "productos" de la carta.
    for nombre in ("Tártara", "Salsa Golf", "Papas al hilo", "Sin papas", "Presa de Pollo"):
        assert nombre not in html
    assert 'href="/producto/41"' not in html   # una salsa no tiene su propia ficha pública


def test_hamburguesa_ofrece_salsas_papas_y_agregados(bd_limpia, cliente_client):
    html = cliente_client.get("/producto/2").get_data(as_text=True)  # Simple de Carne
    assert 'data-admite-cremas="1"' in html
    assert "Elige tus salsas" in html and "Elige el tipo de papas" in html and "Agregados" in html
    # 7 salsas + 3 papas + 10 agregados = 20 casillas de personalización
    assert html.count('class="crema-check"') == 20
    assert 'type="radio"' in html and html.count('data-grupo="papas"') == 3
    assert html.count('data-grupo="salsa"') == 7 and html.count('data-grupo="agregado"') == 10
    assert "+ S/ 2.00" in html and "+ S/ 6.00" in html   # agregados con precio


def test_plato_especial_no_se_personaliza(bd_limpia, cliente_client):
    html = cliente_client.get("/producto/31").get_data(as_text=True)  # Salchipapa
    assert 'data-admite-cremas="0"' in html
    assert "no se personaliza" in html
    assert 'class="crema-check"' not in html


def test_precios_por_ids_solo_cremas_acepta_personalizacion_y_rechaza_hamburguesa(bd_limpia):
    precios = Producto.precios_por_ids([41, 48, 51, 2], solo_cremas=True)  # salsa, papa, agregado, hamburguesa
    assert set(precios) == {41, 48, 51}
    assert precios[51]["precio"] == 2.0


def test_sugeridos_nunca_devuelve_personalizacion(bd_limpia):
    sug = Producto.sugeridos([])
    assert all(s["categoria"] not in CATEGORIAS_PERSONALIZACION for s in sug)


def test_pedido_completo_con_salsa_papa_y_agregado(bd_limpia, cliente_client, csrf):
    """Flujo real: una hamburguesa con 1 salsa, 1 papa y 1 agregado pagado."""
    item = {
        "idProducto": 5, "nombre": "Pollo con Huevo", "precioUnidad": 11.0,  # 9.00 + Hot Dog (2.00)
        "cantidad": 1, "precioTotal": 11.0, "cremas": [41, 48, 51],
    }
    from model.Pedido import Pedido
    idp, key = Pedido.crear_pedido_completo(
        1, "cliente@correo.com", "C", "999", "19:00:00", "efectivo", None, [item])
    assert Pedido.avanzar_preparacion(idp) == "preparando"
    assert Pedido.avanzar_preparacion(idp) == "listo"
    assert Pedido.marcar_recogido(idp, key, None, 1, "boleta", "") == "ok"
    from model.Comprobante import Comprobante
    c = Comprobante.detalle(Comprobante.id_por_pedido(idp))
    assert c["montoTotal"] == 11.0
    assert set(c["lineas"][0]["adicionales"]) == {"Mayonesa", "Papas al hilo", "Hot Dog"}
