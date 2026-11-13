import bd

from model.Devolucion import Devolucion
from model.Inventario import Inventario
from model.Pedido import Pedido
from model.ProveedorCompra import Compra, Proveedor
from tests.conftest import CLIENTE_ID, SUPER_ID
from tests.test_comprobante_pdf import ITEMS


def _crear_pedido(clave=None):
    return Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "efectivo", None, ITEMS, clave)


def _saldo(producto=2):
    return next(s for s in Inventario.saldos() if s["idProducto"] == producto)


def test_reserva_cancelacion_y_entrega_separan_fisico_disponible(bd_limpia):
    inicial = _saldo()
    pedido, clave = _crear_pedido()
    reservado = _saldo()
    assert reservado["fisico"] == inicial["fisico"]
    assert reservado["reservado"] == 2
    assert reservado["disponible"] == inicial["disponible"] - 2

    assert Pedido.cancelar_pedido(pedido, CLIENTE_ID) == "ok"
    liberado = _saldo()
    assert liberado["fisico"] == inicial["fisico"]
    assert liberado["reservado"] == 0

    pedido, clave = _crear_pedido()
    Pedido.avanzar_preparacion(pedido)
    Pedido.avanzar_preparacion(pedido)
    assert Pedido.marcar_recogido(pedido, clave, "efectivo", SUPER_ID, "boleta", "") == "ok"
    entregado = _saldo()
    assert entregado["fisico"] == inicial["fisico"] - 2
    assert entregado["reservado"] == 0
    assert Inventario.kardex(2, "salida_venta")[0]["idReferencia"] == pedido


def test_idempotencia_evitar_doble_pedido_y_doble_reserva(bd_limpia):
    primero = _crear_pedido("checkout-unico-001")
    segundo = _crear_pedido("checkout-unico-001")
    assert primero == segundo
    assert _saldo()["reservado"] == 2
    con = bd.obtener_conexion()
    with con.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM registroPedido WHERE idempotencia='checkout-unico-001'")
        assert cursor.fetchone()[0] == 1
    con.close()


def test_compra_actualiza_fisico_costo_promedio_y_kardex(bd_limpia):
    assert Proveedor.guardar("Distribuidora Norte", "20123456789") == "ok"
    proveedor = Proveedor.listar(True)[0]
    compra = Compra.crear(
        proveedor["id"], "F001-100", "2026-10-25",
        [{"idProducto": 2, "cantidad": 10, "costo": "5.00"}], SUPER_ID)
    assert isinstance(compra, int)
    antes = _saldo()
    assert Compra.recibir(compra, SUPER_ID) == "ok"
    despues = _saldo()
    assert despues["fisico"] == antes["fisico"] + 10
    assert despues["costo"] == 1.25
    mov = Inventario.kardex(2, "compra")[0]
    assert mov["documento"] == "F001-100" and mov["idReferencia"] == compra
    assert Compra.recibir(compra, SUPER_ID) == "ya_procesada"


def test_devolucion_cliente_distingue_reincorporable_y_merma(bd_limpia):
    pedido, clave = _crear_pedido()
    Pedido.avanzar_preparacion(pedido)
    Pedido.avanzar_preparacion(pedido)
    Pedido.marcar_recogido(pedido, clave, "efectivo", SUPER_ID, "boleta", "")
    base = _saldo()["fisico"]
    assert Devolucion.registrar(
        "cliente", 2, 1, "merma", "reembolso", "Producto abierto", SUPER_ID,
        id_pedido=pedido) == "ok"
    assert _saldo()["fisico"] == base
    assert Devolucion.registrar(
        "cliente", 2, 1, "reincorporable", "cambio", "Producto cerrado", SUPER_ID,
        id_pedido=pedido) == "ok"
    assert _saldo()["fisico"] == base + 1
    registrada = Devolucion.listar()[0]
    assert Devolucion.revertir(registrada["id"], "Registro duplicado", SUPER_ID) == "ok"
    assert _saldo()["fisico"] == base
    reversion = Inventario.kardex(2, "reversion_devolucion")[0]
    assert reversion["idReversion"] is not None


def test_devolucion_a_proveedor_reduce_stock_disponible(bd_limpia):
    assert Proveedor.guardar("Proveedor Bebidas", "20987654321") == "ok"
    proveedor = Proveedor.listar(True)[0]
    compra = Compra.crear(
        proveedor["id"], "F001-DEV", "2026-10-25",
        [{"idProducto": 2, "cantidad": 5, "costo": "4.00"}], SUPER_ID)
    assert Compra.recibir(compra, SUPER_ID) == "ok"
    antes = _saldo()
    assert Devolucion.registrar(
        "proveedor", 2, 3, "reincorporable", "reembolso", "Mercadería defectuosa",
        SUPER_ID, id_compra=compra, id_proveedor=proveedor["id"], documento="NC-001") == "ok"
    assert _saldo()["fisico"] == antes["fisico"] - 3
    assert Inventario.kardex(2, "devolucion_proveedor")[0]["documento"] == "NC-001"


def test_nuevas_pantallas_de_inventario_cargan(bd_limpia, admin_client):
    for ruta in ("/admin/inventario/", "/admin/inventario/kardex/",
                 "/admin/inventario/movimientos/", "/admin/proveedores/",
                 "/admin/compras/", "/admin/devoluciones/"):
        assert admin_client.get(ruta).status_code == 200


def test_administrador_solo_consulta_movimientos_manuales(bd_limpia, client, csrf):
    with client.session_transaction() as sesion:
        sesion["admin.auth"] = {"idUsuario": 2, "rol": "administrador", "nombres": "Admin"}
    antes = _saldo()["fisico"]
    respuesta = client.post("/admin/inventario/movimientos/registrar", data={
        "_csrf": csrf, "producto": 2, "almacen": 1, "tipo": "entrada",
        "cantidad": 5, "motivo": "Intento sin permiso",
    }, follow_redirects=True)
    assert "Solo el Administrador" in respuesta.get_data(as_text=True)
    assert _saldo()["fisico"] == antes
