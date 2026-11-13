from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from model.Devolucion import Devolucion
from model.Producto import Producto
from model.ProveedorCompra import Proveedor


devoluciones = Blueprint("devoluciones", __name__, url_prefix="/devoluciones")


@devoluciones.route("/")
def home():
    return render_template(
        "admin/devoluciones/index.html", usuario=g.user,
        devoluciones=Devolucion.listar(), productos=Producto.obtener_productos(),
        proveedores=Proveedor.listar(True), puede_modificar=g.user.get("rol") == "superusuario")


@devoluciones.route("/registrar", methods=["POST"])
def registrar():
    if g.user.get("rol") != "superusuario":
        flash("Solo el Administrador puede autorizar devoluciones.", "error")
        return redirect(url_for("admin.devoluciones.home"))
    resultado = Devolucion.registrar(
        request.form.get("tipo"), request.form.get("producto"), request.form.get("cantidad"),
        request.form.get("condicion"), request.form.get("resolucion"), request.form.get("motivo"),
        g.user["idUsuario"], request.form.get("pedido", type=int),
        request.form.get("compra", type=int), request.form.get("proveedor", type=int),
        request.form.get("documento"))
    mensajes = {"ok": ("Devolución registrada y Kardex actualizado.", "ok"),
                "pedido_no_entregado": ("El pedido debe estar entregado antes de devolverlo.", "error"),
                "cantidad_invalida": ("La cantidad supera lo vendido en ese pedido.", "error"),
                "proveedor_requerido": ("Selecciona el proveedor y la compra recibida de origen.", "error"),
                "stock_insuficiente": ("No hay stock disponible para devolver al proveedor.", "error")}
    flash(*mensajes.get(resultado, ("Revisa el origen, producto, cantidad y motivo.", "error")))
    return redirect(url_for("admin.devoluciones.home"))


@devoluciones.route("/revertir/<int:id_devolucion>", methods=["POST"])
def revertir(id_devolucion):
    if g.user.get("rol") != "superusuario":
        flash("Solo el Administrador puede revertir devoluciones.", "error")
        return redirect(url_for("admin.devoluciones.home"))
    resultado = Devolucion.revertir(id_devolucion, request.form.get("motivo"), g.user["idUsuario"])
    flash("Reversión documentada." if resultado == "ok" else "No se pudo revertir el movimiento.",
          "ok" if resultado == "ok" else "error")
    return redirect(url_for("admin.devoluciones.home"))
