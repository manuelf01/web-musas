import bd

from model.Pedido import Pedido
from tests.conftest import CLIENTE_ID, SUPER_ID


ITEMS_COMANDA = [{
    "idProducto": 2,
    "nombre": "Simple de Carne",
    "precioUnidad": 12.50,
    "cantidad": 2,
    "precioTotal": 25.00,
    "cremas": [41, 48, 57],  # Mayonesa, Papas al hilo, Queso
}]


def _crear():
    return Pedido.crear_pedido_completo(
        CLIENTE_ID, "cliente@correo.com", "Cliente Prueba", "999888777",
        "20:00:00", "efectivo", "Sin cebolla", ITEMS_COMANDA,
    )[0]


def _estado_comanda(id_pedido):
    con = bd.obtener_conexion()
    try:
        with con.cursor() as cur:
            cur.execute(
                "SELECT estadoPrep,fechaEnvioCocina,idUsuarioComanda,"
                "impresionesComanda,fechaUltimaImpresion FROM registroPedido WHERE idPedido=%s",
                (id_pedido,),
            )
            return cur.fetchone()
    finally:
        con.close()


def test_enviar_a_cocina_cambia_estado_y_audita_una_sola_vez(bd_limpia):
    pedido = _crear()
    assert Pedido.enviar_a_cocina(pedido, SUPER_ID) == "en_cocina"
    estado, enviada, usuario, impresiones, ultima = _estado_comanda(pedido)
    assert estado == 1
    assert enviada is not None and ultima is not None
    assert usuario == SUPER_ID and impresiones == 1

    assert Pedido.enviar_a_cocina(pedido, SUPER_ID) == "ya_enviada"
    assert _estado_comanda(pedido)[3] == 1


def test_comanda_termica_muestra_operacion_y_oculta_datos_sensibles(
        bd_limpia, admin_client):
    pedido = _crear()
    Pedido.enviar_a_cocina(pedido, SUPER_ID)
    respuesta = admin_client.get(f"/admin/pedidos/comanda/{pedido}?imprimir=1")
    html = respuesta.get_data(as_text=True)

    assert respuesta.status_code == 200
    for texto in ("COMANDA DE COCINA", f"#{pedido}", "20:00", "Cliente",
                  "2×", "Simple de Carne", "Mayonesa", "Papas al hilo",
                  "Queso", "Sin cebolla", "window.print()"):
        assert texto in html
    for dato_sensible in ("999888777", "cliente@correo.com", "Efectivo", "S/"):
        assert dato_sensible not in html
    assert respuesta.headers["Cache-Control"] == "no-store"


def test_reimprimir_incrementa_contador_sin_cambiar_estado(
        bd_limpia, admin_client, csrf):
    pedido = _crear()
    Pedido.enviar_a_cocina(pedido, SUPER_ID)
    respuesta = admin_client.post(
        f"/admin/pedidos/comanda/{pedido}/reimprimir",
        data={"_csrf": csrf}, follow_redirects=True,
    )
    assert respuesta.status_code == 200
    assert "REIMPRESIÓN N.º 2" in respuesta.get_data(as_text=True)
    estado = _estado_comanda(pedido)
    assert estado[0] == 1 and estado[3] == 2


def test_ruta_de_preparar_exige_envio_a_cocina(
        bd_limpia, admin_client, csrf):
    pedido = _crear()
    admin_client.post("/admin/pedidos/preparar", data={"_csrf": csrf, "idPedido": pedido})
    assert _estado_comanda(pedido)[0] == 0

    envio = admin_client.post(
        "/admin/pedidos/enviar-cocina",
        data={"_csrf": csrf, "idPedido": pedido}, follow_redirects=False,
    )
    assert envio.status_code in (301, 302)
    assert f"/admin/pedidos/comanda/{pedido}" in envio.headers["Location"]
    assert _estado_comanda(pedido)[0] == 1

    # Una comanda ya emitida no puede deshacerse hasta «Recibido».
    admin_client.post("/admin/pedidos/retroceder", data={"_csrf": csrf, "idPedido": pedido})
    assert _estado_comanda(pedido)[0] == 1

    admin_client.post("/admin/pedidos/preparar", data={"_csrf": csrf, "idPedido": pedido})
    assert _estado_comanda(pedido)[0] == 2
