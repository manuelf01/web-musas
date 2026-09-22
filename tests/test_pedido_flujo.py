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
    # Simple de Carne (id 2, S/8.50) x2 + Queso (id 57, S/2) + Tocino (id 58, S/2) -> pu = 12.50, total = 25
    {"idProducto": 2, "nombre": "Simple de Carne", "precioUnidad": 12.5,
     "cantidad": 2, "precioTotal": 25, "cremas": [57, 58]},
    # Simple de Filete de Pollo (id 4, S/8.50) x3 -> total 25.50
    {"idProducto": 4, "nombre": "Simple de Filete de Pollo", "precioUnidad": 8.5,
     "cantidad": 3, "precioTotal": 25.5, "cremas": []},
]


def test_crear_pedido_descuenta_stock_y_asigna_ids(bd_limpia):
    s2, s4 = _stock(2), _stock(4)
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "19:30:00", "yape", "sin cebolla", ITEMS,
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
    a, _ = Pedido.crear_pedido_completo(1, "a@correo.com", "A", "999", "19:00:00", "efectivo", None, ITEMS[:1])
    b, _ = Pedido.crear_pedido_completo(2, "b@correo.com", "B", "999", "19:00:00", "efectivo", None, ITEMS[:1])
    assert a != b


def test_avanzar_preparacion_y_entregar_emite_comprobante(bd_limpia):
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "yape", None, ITEMS,
    )
    total_pedido = sum(it["precioTotal"] for it in ITEMS)  # 50.5

    assert Pedido.avanzar_preparacion(idp) == "preparando"
    assert Pedido.avanzar_preparacion(idp) == "listo"
    assert Pedido.avanzar_preparacion(idp) is None  # ya está listo

    assert Pedido.marcar_recogido(idp, "0000") == "clave_mal"
    assert Pedido.marcar_recogido(idp, key, "yape", 1, "boleta", "12345679") == "ok"
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


def test_comprobante_factura_se_define_al_entregar(bd_limpia):
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "C", "999", "20:00:00", "efectivo", None, ITEMS[:1])
    Pedido.avanzar_preparacion(idp)
    Pedido.avanzar_preparacion(idp)
    Pedido.marcar_recogido(idp, key, "efectivo", 1, "factura", "20123456789", "Cliente SAC")
    d = Comprobante.listado_paginado(10, 0)
    assert d and d[0]["numero"].startswith("F001-")


def test_ventas_kpis_reflejan_la_entrega(bd_limpia):
    idp, key = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "C", "999", "20:00:00", "yape", None, ITEMS)
    assert Pedido.resumen_dashboard()["ventas_hoy"] == 0
    Pedido.avanzar_preparacion(idp)
    Pedido.avanzar_preparacion(idp)
    Pedido.marcar_recogido(idp, key, "yape", 1, "boleta", "12345679")
    k = Comprobante.kpis()
    assert k["cantidad"] == 1
    assert round(k["total"], 2) == 50.5
    assert round(k["maxima"], 2) == 50.5
    resumen = Pedido.resumen_dashboard()
    assert resumen["ventas_hoy"] == 50.5
    assert resumen["venta_maxima"] == 50.5
