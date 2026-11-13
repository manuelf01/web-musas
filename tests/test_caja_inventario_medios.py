import bd

from model.Caja import Caja
from model.Inventario import Inventario
from model.MedioPago import MedioPago
from model.Pedido import Pedido
from tests.conftest import CLIENTE_ID, SUPER_ID
from tests.test_comprobante_pdf import ITEMS


def _efectivo_id():
    return next(m["id"] for m in MedioPago.listar() if m["codigo"] == "efectivo")


def test_caja_calcula_solo_el_efectivo_fisico_y_cierra_inmutable(bd_limpia):
    efectivo = _efectivo_id()
    yape = next(m["id"] for m in MedioPago.listar() if m["codigo"] == "yape")
    assert Caja.registrar_movimiento("ingreso", 10, "Vuelto adicional", efectivo, SUPER_ID) == "ok"
    assert Caja.registrar_movimiento("ingreso", 50, "Ingreso digital", yape, SUPER_ID) == "ok"
    assert Caja.registrar_movimiento("egreso", 3, "Compra menor", efectivo, SUPER_ID) == "ok"
    assert Caja.resumen()["efectivoEsperado"] == 7.0
    assert Caja.cerrar(5, "Faltante revisado", SUPER_ID) == "ok"
    cerrado = Caja.historial()[0]
    assert cerrado["estado"] == "cerrada" and cerrado["diferencia"] == -2.0
    assert Caja.registrar_movimiento("ingreso", 1, "No permitido", efectivo, SUPER_ID) == "caja_cerrada"


def test_aporte_repone_caja_y_no_permite_gastar_mas_del_disponible(bd_limpia):
    efectivo = _efectivo_id()
    yape = next(m["id"] for m in MedioPago.listar() if m["codigo"] == "yape")

    assert Caja.registrar_movimiento("aporte", 30, "Reposición de sencillo", efectivo, SUPER_ID) == "ok"
    assert Caja.resumen()["totalAportes"] == 30.0
    assert Caja.resumen()["efectivoEsperado"] == 30.0
    assert Caja.registrar_movimiento("aporte", 10, "Aporte digital", yape, SUPER_ID) == "medio_invalido"
    assert Caja.registrar_movimiento("gasto", 31, "Compra excesiva", efectivo, SUPER_ID) == "saldo_insuficiente"
    assert Caja.registrar_movimiento("gasto", 12, "Compra de bolsas", efectivo, SUPER_ID) == "ok"
    resumen = Caja.resumen()
    assert resumen["totalGastos"] == 12.0
    assert resumen["efectivoEsperado"] == 18.0


def test_descuento_comision_y_neto_quedan_congelados_en_el_pago(bd_limpia):
    yape = next(m for m in MedioPago.listar() if m["codigo"] == "yape")
    assert MedioPago.guardar(
        yape["nombre"], yape["tipo"], 10, 2, 0.50,
        yape["afectaEfectivo"], None, yape["id"], True,
    ) is None
    id_pedido, clave = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "yape", None, ITEMS,
    )
    Pedido.avanzar_preparacion(id_pedido)
    Pedido.avanzar_preparacion(id_pedido)
    assert Pedido.marcar_recogido(id_pedido, clave, "yape", SUPER_ID, "boleta", "") == "ok"
    con = bd.obtener_conexion()
    try:
        with con.cursor() as cur:
            cur.execute(
                "SELECT montoBruto,descuento,montoCobrado,comision,montoNeto "
                "FROM pagoVenta WHERE idComprobante=(SELECT idComprobante FROM comprobante WHERE idPedido=%s)",
                (id_pedido,),
            )
            valores = tuple(float(x) for x in cur.fetchone())
    finally:
        con.close()
    assert valores == (25.0, 2.5, 22.5, 0.95, 21.55)


def test_reserva_y_kardex_cambian_en_la_misma_operacion(bd_limpia):
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("SELECT existencias FROM producto WHERE idProducto=2")
        antes = cur.fetchone()[0]
    con.close()
    id_pedido, _ = Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "efectivo", None, ITEMS,
    )
    movimientos = Inventario.kardex(2, "reserva_pedido")
    assert movimientos[0]["idReferencia"] == id_pedido
    assert movimientos[0]["anterior"] == antes
    assert movimientos[0]["posterior"] == antes
    assert movimientos[0]["reservadoAnterior"] == 0
    assert movimientos[0]["reservadoPosterior"] == 2
    saldo = next(s for s in Inventario.saldos() if s["idProducto"] == 2)
    assert saldo["fisico"] == antes and saldo["reservado"] == 2
    assert saldo["disponible"] == antes - 2


def test_modulos_administrativos_cargan(bd_limpia, admin_client):
    for ruta in ("/admin/caja/", "/admin/caja/movimientos/", "/admin/inventario/", "/admin/medios-pago/"):
        respuesta = admin_client.get(ruta)
        assert respuesta.status_code == 200


def test_caja_presenta_operaciones_en_modales(bd_limpia, admin_client):
    respuesta = admin_client.get("/admin/caja/movimientos/")
    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    assert 'id="cajaMovimientoModal"' in html
    assert 'data-caja-tipo="aporte"' in html
    assert "Aportes de efectivo" in html
    assert "No se contabilizan como ventas" in html
    assert "js/caja.js" in html
