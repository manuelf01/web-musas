from flask import Blueprint, render_template, g, request, redirect, url_for, flash, jsonify
from model.Comprobante import Comprobante
from model.Pedido import Pedido
from avisos import ok_deshacer

pedidos = Blueprint("pedidos", __name__, url_prefix="/pedidos")


def _firma(lista):
    """Huella del estado de los pedidos de hoy: cambia si entra un pedido nuevo
    o si alguno cambia de estado / se recoge. La cocina la sondea cada pocos
    segundos para refrescar sola la pantalla."""
    return "|".join(
        f'{p["idPedido"]}:{p["estado"]}:{1 if p["recogido"] else 0}'
        for p in sorted(lista, key=lambda p: p["idPedido"])
    )


@pedidos.route("/")
def home():
    estado = request.args.get("estado", "pendiente")
    if estado not in ("todos", "pendiente", "recibido", "preparando", "listo", "recogido"):
        estado = "pendiente"
    q = (request.args.get("q") or "").strip().lower()

    todos = Pedido.pedidos_de_hoy(None)
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
    return render_template(
        "admin/pedidos/index.html",
        usuario=g.user, estado=estado, q=request.args.get("q", ""),
        pendientes=pendientes, recogidos=recogidos, contadores=contadores,
        sugerencias=sorted({p["cliente"] for p in todos}),
        firma=_firma(todos),
        ids_iniciales=",".join(str(p["idPedido"]) for p in todos if not p["recogido"]),
    )


@pedidos.route("/pulso")
def pulso():
    """JSON ligero para el sondeo de la pantalla de cocina."""
    hoy = Pedido.pedidos_de_hoy(None)
    return jsonify({
        "firma": _firma(hoy),
        "pendientes": [p["idPedido"] for p in hoy if not p["recogido"]],
    })


@pedidos.route("/preparar", methods=["POST"])
def preparar():
    id_pedido = request.form.get("idPedido")
    estado = request.form.get("estado", "pendiente")
    nuevo = Pedido.avanzar_preparacion(id_pedido)
    deshacer = (url_for("admin.pedidos.retroceder"), {"idPedido": id_pedido, "estado": estado})
    if nuevo == "preparando":
        ok_deshacer(f"Pedido N° {id_pedido} en preparación. El cliente ya no puede cancelarlo.", *deshacer)
    elif nuevo == "listo":
        ok_deshacer(f"Pedido N° {id_pedido} marcado como listo para recojo.", *deshacer)
    else:
        flash(f"No se pudo avanzar el pedido N° {id_pedido}.", "error")
    return redirect(url_for("admin.pedidos.home", estado=estado))


@pedidos.route("/retroceder", methods=["POST"])
def retroceder():
    id_pedido = request.form.get("idPedido")
    estado = request.form.get("estado", "pendiente")
    nuevo = Pedido.retroceder_preparacion(id_pedido)
    if nuevo == "recibido":
        flash(f"Pedido N° {id_pedido} volvió a «recibido». El cliente puede cancelarlo otra vez.", "ok")
    elif nuevo == "preparando":
        flash(f"Pedido N° {id_pedido} volvió a «en preparación».", "ok")
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
