import json

from flask import (
    Blueprint, Response, render_template, g, request, redirect, url_for, flash,
    jsonify, stream_with_context,
)
from model.Comprobante import Comprobante
from model.MedioPago import MedioPago
from model.Pedido import Pedido
from model.Insumos import StockInsumoInsuficiente
from avisos import ok_deshacer
from paginacion import paginar
from services.pedidos_eventos import esperar_cambio_pedidos, version_actual

pedidos = Blueprint("pedidos", __name__, url_prefix="/pedidos")


def _firma(lista):
    """Huella del estado de los pedidos de hoy: cambia si entra un pedido nuevo
    o si alguno cambia de estado / se recoge. SSE la envía a la cocina para
    refrescar sola la pantalla."""
    return "|".join(
        f'{p["idPedido"]}:{p["estado"]}:{1 if p["recogido"] else 0}'
        for p in sorted(lista, key=lambda p: p["idPedido"])
    )


def _datos_pulso():
    hoy = Pedido.pedidos_de_hoy(None)
    return {
        "firma": _firma(hoy),
        "pendientes": [p["idPedido"] for p in hoy if not p["recogido"]],
    }


@pedidos.route("/")
def home():
    estado = request.args.get("estado", "pendiente")
    if estado not in ("todos", "pendiente", "recibido", "preparando", "listo", "recogido"):
        estado = "pendiente"
    q = (request.args.get("q") or "").strip().lower()

    todos = Pedido.pedidos_de_hoy(None)
    medios = {m["codigo"]: m for m in MedioPago.listar()}
    for pedido in todos:
        medio = medios.get(pedido["medioPago"])
        if medio:
            importes = MedioPago.calcular(medio, pedido["total"])
            pedido["medioNombre"] = medio["nombre"]
            pedido["medioTipo"] = medio["tipo"]
            pedido["totalCobrar"] = float(importes["cobrado"])
            pedido["descuentoPago"] = float(importes["descuento"])
        else:
            pedido["medioNombre"] = pedido["medioPago"].capitalize()
            pedido["medioTipo"] = "otro"
            pedido["totalCobrar"] = pedido["total"]
            pedido["descuentoPago"] = 0.0
    if q:
        todos = [p for p in todos if q in p["cliente"].lower()
                 or q in str(p["idPedido"]) or q in (p["dni"] or "").lower()
                 or q in (p["correo"] or "").lower()]

    pendientes = [p for p in todos if not p["recogido"]]
    recogidos = [p for p in todos if p["recogido"]]
    if estado in ("recibido", "preparando", "listo"):
        pendientes = [p for p in pendientes if p["estado"] == estado]

    contadores = {
        "todos": len(todos),
        "pendiente": len([p for p in todos if not p["recogido"]]),
        "recibido": len([p for p in todos if p["estado"] == "recibido"]),
        "preparando": len([p for p in todos if p["estado"] == "preparando"]),
        "listo": len([p for p in todos if p["estado"] == "listo"]),
        "recogido": len(recogidos),
    }
    total_recogidos = len(recogidos)
    # 6 por página: así la pantalla de cocina no se satura y, a medida que se
    # entregan los primeros, los siguientes "suben" solos en el próximo sondeo.
    pendientes, pag_pendientes, rango_pendientes = paginar(pendientes, 6, "pedidos")
    recogidos, pag_recogidos, rango_recogidos = paginar(recogidos, 6, "pedidos", page_param="rpage")
    return render_template(
        "admin/pedidos/index.html",
        usuario=g.user, estado=estado, q=request.args.get("q", ""),
        pendientes=pendientes, pag_pendientes=pag_pendientes, rango_pendientes=rango_pendientes,
        recogidos=recogidos, pag_recogidos=pag_recogidos, rango_recogidos=rango_recogidos,
        total_recogidos=total_recogidos, contadores=contadores,
        sugerencias=sorted({p["cliente"] for p in todos}),
        firma=_firma(todos),
        ids_iniciales=",".join(str(p["idPedido"]) for p in todos if not p["recogido"]),
    )


@pedidos.route("/pulso")
def pulso():
    """JSON ligero usado como respaldo cuando EventSource no está disponible."""
    respuesta = jsonify(_datos_pulso())
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@pedidos.route("/eventos")
def eventos():
    """Flujo SSE que avisa a cocina cuando cambia un pedido de hoy."""
    firma_inicial = request.args.get("firma", "")

    @stream_with_context
    def generar():
        ultima_firma = firma_inicial
        version = version_actual()
        # EventSource usa este valor para reconectar pronto si se corta la red.
        yield "retry: 3000\n\n"
        while True:
            datos = _datos_pulso()
            if datos["firma"] != ultima_firma:
                ultima_firma = datos["firma"]
                cuerpo = json.dumps(datos, ensure_ascii=False, separators=(",", ":"))
                yield f"event: pedidos\ndata: {cuerpo}\n\n"
            else:
                # Evita que proxies y navegadores cierren una conexión inactiva.
                yield ": latido\n\n"
            version = esperar_cambio_pedidos(version, timeout=15)

    return Response(
        generar(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
        },
    )


@pedidos.route("/preparar", methods=["POST"])
def preparar():
    id_pedido = request.form.get("idPedido")
    estado = request.form.get("estado", "pendiente")
    deshacer = (url_for("admin.pedidos.retroceder"), {"idPedido": id_pedido, "estado": estado})
    if Pedido.marcar_listo(id_pedido):
        ok_deshacer(f"Pedido N° {id_pedido} marcado como listo para recojo.", *deshacer)
    else:
        flash(f"El pedido N° {id_pedido} debe estar en cocina antes de marcarlo como listo.", "error")
    return redirect(url_for("admin.pedidos.home", estado=estado))


@pedidos.route("/enviar-cocina", methods=["POST"])
def enviar_cocina():
    id_pedido = request.form.get("idPedido")
    estado = request.form.get("estado", "pendiente")
    try:
        resultado = Pedido.enviar_a_cocina(id_pedido, g.user["idUsuario"])
    except StockInsumoInsuficiente as exc:
        flash(f"No se puede enviar a cocina: quedan {exc.disponible} y se necesitan "
              f"{exc.requerido} de {exc.nombre}. Revisa el inventario o la receta.", "error")
        return redirect(url_for("admin.pedidos.home", estado=estado))
    if resultado in ("en_cocina", "comanda_generada"):
        return redirect(url_for("admin.pedidos.comanda", id_pedido=id_pedido, imprimir=1))
    if resultado == "ya_enviada":
        flash(f"El pedido N° {id_pedido} ya tiene una comanda. Usa «Reimprimir comanda».", "error")
    else:
        flash(f"No se pudo enviar el pedido N° {id_pedido} a cocina.", "error")
    return redirect(url_for("admin.pedidos.home", estado=estado))


@pedidos.route("/comanda/<int:id_pedido>")
def comanda(id_pedido):
    pedido = Pedido.obtener_comanda(id_pedido)
    if pedido is None:
        flash(f"El pedido N° {id_pedido} todavía no tiene una comanda.", "error")
        return redirect(url_for("admin.pedidos.home"))
    respuesta = render_template(
        "admin/pedidos/comanda.html", pedido=pedido,
        autoimprimir=request.args.get("imprimir") == "1",
    )
    return Response(respuesta, headers={"Cache-Control": "no-store"})


@pedidos.route("/comanda/<int:id_pedido>/reimprimir", methods=["POST"])
def reimprimir_comanda(id_pedido):
    if not Pedido.registrar_reimpresion_comanda(id_pedido):
        flash(f"El pedido N° {id_pedido} todavía no tiene una comanda.", "error")
        return redirect(url_for("admin.pedidos.home"))
    return redirect(url_for("admin.pedidos.comanda", id_pedido=id_pedido, imprimir=1))


@pedidos.route("/retroceder", methods=["POST"])
def retroceder():
    id_pedido = request.form.get("idPedido")
    estado = request.form.get("estado", "pendiente")
    if Pedido.volver_a_cocina(id_pedido):
        flash(f"Pedido N° {id_pedido} volvió a «En cocina».", "ok")
    else:
        flash(f"No se pudo deshacer el avance del pedido N° {id_pedido}.", "error")
    return redirect(url_for("admin.pedidos.home", estado=estado))


@pedidos.route("/confirmar", methods=["POST"])
def confirmar():
    id_pedido = request.form.get("idPedido")
    key = (request.form.get("key") or "").strip()
    opcion = (request.form.get("tipo_comprobante") or "").strip().lower()
    documento = (request.form.get("documento") or "").strip()
    razon_social = (request.form.get("razon_social") or "").strip()
    estado = request.form.get("estado", "todos")
    # boleta_simple = sin documento; boleta_dni = pide DNI; factura = pide RUC.
    tipo_comprobante = {"boleta_simple": "boleta", "boleta_dni": "boleta",
                        "boleta": "boleta", "factura": "factura"}.get(opcion, "")
    if opcion == "boleta_simple":
        documento = razon_social = ""
    elif opcion == "boleta_dni" and not documento:
        flash("Para la boleta con DNI ingresa los 8 dígitos, o elige «Boleta simple».", "error")
        return redirect(url_for("admin.pedidos.home", estado=estado))
    elif opcion == "factura" and not documento:
        flash("Para la factura ingresa el RUC de 11 dígitos y la razón social.", "error")
        return redirect(url_for("admin.pedidos.home", estado=estado))

    resultado = Pedido.marcar_recogido(
        id_pedido, key, None, g.user["idUsuario"],
        tipo_comprobante, documento, razon_social,
    )
    if resultado == "ok":
        flash(f"Pedido N° {id_pedido} entregado. Comprobante emitido.", "ok")
        id_comprobante = Comprobante.id_por_pedido(id_pedido)
        return redirect(url_for("admin.ventas.show_detalle", idComprobante=id_comprobante))
    elif resultado == "clave_mal":
        flash(f"Palabra clave incorrecta para el pedido N° {id_pedido}. Verifica los 4 dígitos con el cliente e inténtalo de nuevo.", "error")
        return redirect(url_for("admin.pedidos.home", estado=estado, clave_error=id_pedido))
    elif resultado == "no_listo":
        flash(f"El pedido N° {id_pedido} debe marcarse como listo antes de entregarlo.", "error")
    elif resultado == "pago_invalido":
        flash("El pedido no tiene un medio de pago válido.", "error")
    elif resultado == "caja_cerrada":
        flash("Abre una caja antes de cobrar y entregar pedidos.", "error")
    elif resultado == "dni_invalido":
        flash("Para la boleta ingresa un DNI válido de 8 dígitos.", "error")
    elif resultado == "ruc_invalido":
        flash("Para la factura ingresa un RUC válido de 11 dígitos.", "error")
    elif resultado == "razon_social_requerida":
        flash("Ingresa la razón social para emitir la factura.", "error")
    elif resultado == "comprobante_invalido":
        flash("Selecciona boleta o factura.", "error")
    else:
        flash(f"El pedido N° {id_pedido} ya fue recogido, cancelado o no existe.", "error")

    return redirect(url_for("admin.pedidos.home", estado=estado))


@pedidos.route("/no-show", methods=["POST"])
def no_show():
    id_pedido = request.form.get("idPedido")
    estado = request.form.get("estado", "pendiente")
    if Pedido.marcar_no_show(id_pedido):
        flash(f"Pedido N° {id_pedido} marcado como «no recogió». Se liberó el cupo y el stock.", "ok")
    else:
        flash(f"Solo puedes marcar «No recogió» cuando el pedido esté listo para entregar.", "error")
    return redirect(url_for("admin.pedidos.home", estado=estado))


@pedidos.route("/cancelar", methods=["POST"])
def cancelar():
    id_pedido = request.form.get("idPedido")
    estado = request.form.get("estado", "pendiente")
    resultado = Pedido.cancelar_pedido(id_pedido, saltar_dueno=True)
    if resultado == "ok":
        flash(f"Pedido N° {id_pedido} cancelado. Se devolvió el stock y se liberó el cupo.", "ok")
    else:
        flash(f"El pedido N° {id_pedido} ya no se puede cancelar.", "error")
    return redirect(url_for("admin.pedidos.home", estado=estado))
