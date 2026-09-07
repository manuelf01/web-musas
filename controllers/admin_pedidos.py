from flask import Blueprint, render_template, g, request, redirect, url_for, flash
from model.Pedido import Pedido

pedidos = Blueprint("pedidos", __name__, url_prefix="/pedidos")


@pedidos.route("/")
def home():
    estado = request.args.get("estado", "pendiente")
    if estado not in ("todos", "pendiente", "recogido"):
        estado = "pendiente"
    todos = Pedido.pedidos_de_hoy(None)
    pendientes = [p for p in todos if not p["recogido"]]
    recogidos = [p for p in todos if p["recogido"]]
    return render_template(
        "admin/pedidos/index.html",
        usuario=g.user,
        estado=estado,
        pendientes=pendientes,
        recogidos=recogidos,
        contadores={"todos": len(todos), "pendiente": len(pendientes), "recogido": len(recogidos)},
    )


@pedidos.route("/confirmar", methods=["POST"])
def confirmar():
    id_pedido = request.form.get("idPedido")
    key = (request.form.get("key") or "").strip()
    estado = request.form.get("estado", "todos")

    resultado = Pedido.marcar_recogido(id_pedido, key)
    if resultado == "ok":
        flash(f"Pedido N° {id_pedido} entregado. Estado actualizado a recogido.", "ok")
    elif resultado == "clave_mal":
        flash(f"La palabra clave no coincide con el pedido N° {id_pedido}.", "error")
    else:
        flash(f"El pedido N° {id_pedido} ya fue recogido o no existe.", "error")

    return redirect(url_for("admin.pedidos.home", estado=estado))
