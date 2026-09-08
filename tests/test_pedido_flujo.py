"""Flujo completo del pedido: crear → preparar → entregar → comprobante."""

import bd
from model.Pedido import Pedido
from model.Comprobante import Comprobante

from tests.conftest import CLIENTE_ID


def _stock(id_prod):
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("SELECT existencias FROM producto WHERE idProducto = %s", (id_prod,))
        n = cur.fetchone()[0]
    con.close()
    return n


ITEMS = [
    # Smash (id 2, S/18) x2  + 2 cremas (id 16 S/1, id 19 S/2) -> pu = 21, total = 42
    {"idProducto": 2, "nombre": "Smash Las Musas", "precioUnidad": 21,
     "cantidad": 2, "precioTotal": 42, "cremas": [16, 19]},
    # Clásica (id 4, S/20) x3 -> total 60
    {"idProducto": 4, "nombre": "Clásica Parrillera", "precioUnidad": 20,
     "cantidad": 3, "precioTotal": 60, "cremas": []},
]


def test_crear_pedido_descuenta_stock_y_asigna_ids(bd_limpia):
    s2, s4 = _stock(2), _stock(4)
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "Cliente Prueba", "999888777",
        "19:30:00", True, True, "sin cebolla", ITEMS,
    )
    assert isinstance(idp, int) and idp > 0
    assert 1000 <= int(key) <= 9999
    assert _stock(2) == s2 - 2
    assert _stock(4) == s4 - 3

    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute(
            "SELECT idDetalleOrden, precioUnidad, cantidad, precioTotal "
            "FROM detalleOrden WHERE idPedido = %s ORDER BY idDetalleOrden", (idp,))
        lineas = cur.fetchall()
        cur.execute("SELECT COUNT(*) FROM detalleCremas WHERE idPedido = %s", (idp,))
        n_cremas = cur.fetchone()[0]
        # sin FK huérfana
        cur.execute(
            "SELECT COUNT(*) FROM detalleCremas dc "
            "LEFT JOIN detalleOrden d "
            "  ON d.idDetalleOrden = dc.idDetalleOrden AND d.idPedido = dc.idPedido "
            "WHERE dc.idPedido = %s AND d.idDetalleOrden IS NULL", (idp,))
        huerfanas = cur.fetchone()[0]
    con.close()

    assert [l[0] for l in lineas] == sorted(l[0] for l in lineas)  # ids crecientes
    assert lineas[0][1] * lineas[0][2] == lineas[0][3]             # pu * cant = total
    assert n_cremas == 2
    assert huerfanas == 0


def test_ids_de_pedido_son_autoincrement_y_distintos(bd_limpia):
    # dos clientes distintos (para no chocar con el límite de 2 activos por persona)
    a, _ = Pedido.crear_pedido_completo(1, "12345678", "A", "999", "19:00:00", False, False, None, ITEMS[:1])
    b, _ = Pedido.crear_pedido_completo(2, "87654321", "B", "999", "19:00:00", False, False, None, ITEMS[:1])
    assert a != b


def test_avanzar_preparacion_y_entregar_emite_comprobante(bd_limpia):
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "Cliente Prueba", "999888777",
        "20:00:00", True, True, None, ITEMS,
    )
    total_pedido = sum(it["precioTotal"] for it in ITEMS)  # 102

    assert Pedido.avanzar_preparacion(idp) == "preparando"
    assert Pedido.avanzar_preparacion(idp) == "listo"
    assert Pedido.avanzar_preparacion(idp) is None  # ya está listo

    assert Pedido.marcar_recogido(idp, "0000") == "clave_mal"
    assert Pedido.marcar_recogido(idp, key) == "ok"
    assert Pedido.marcar_recogido(idp, key) == "no_existe"  # no se emite dos veces

    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute(
            "SELECT subTotal, igv, montoTotal, numeroComprobante "
            "FROM comprobante WHERE idPedido = %s", (idp,))
        c = cur.fetchone()
    con.close()
    sub, igv, monto, numero = float(c[0]), float(c[1]), float(c[2]), c[3]
    assert round(monto, 2) == round(total_pedido, 2)
    assert round(sub + igv, 2) == round(monto, 2)
    assert round(sub * 1.18, 2) == round(monto, 2)
    assert numero.startswith("B001-")  # pidió boleta


def test_comprobante_nota_de_venta_si_no_pide_boleta(bd_limpia):
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "C", "999", "20:00:00", False, False, None, ITEMS[:1])
    Pedido.avanzar_preparacion(idp)
    Pedido.avanzar_preparacion(idp)
    Pedido.marcar_recogido(idp, key)
    d = Comprobante.listado_paginado(10, 0)
    assert d and d[0]["numero"].startswith("NV01-")


def test_ventas_kpis_reflejan_la_entrega(bd_limpia):
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "12345679", "C", "999", "20:00:00", True, True, None, ITEMS)
    Pedido.avanzar_preparacion(idp)
    Pedido.avanzar_preparacion(idp)
    Pedido.marcar_recogido(idp, key)
    k = Comprobante.kpis()
    assert k["cantidad"] == 1
    assert round(k["total"], 2) == 102.0
    assert round(k["ticket"], 2) == 102.0
