from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from model.Inventario import Inventario
from model.Producto import Producto
from model.ProveedorCompra import Compra, Proveedor
from model.Insumos import Insumos


proveedores = Blueprint("proveedores", __name__, url_prefix="/proveedores")
compras = Blueprint("compras", __name__, url_prefix="/compras")


def _solo_superusuario(destino):
    if g.user.get("rol") != "superusuario":
        flash("Solo el Administrador puede modificar compras y proveedores.", "error")
        return redirect(url_for(destino))


@proveedores.route("/")
def home():
    return render_template("admin/proveedores/index.html", usuario=g.user,
                           proveedores=Proveedor.listar(), puede_modificar=g.user.get("rol") == "superusuario")


@proveedores.route("/guardar", methods=["POST"])
def guardar():
    bloqueo = _solo_superusuario("admin.proveedores.home")
    if bloqueo:
        return bloqueo
    resultado = Proveedor.guardar(
        request.form.get("nombre"), request.form.get("ruc"), request.form.get("contacto"),
        request.form.get("telefono"), request.form.get("correo"), request.form.get("direccion"),
        request.form.get("id", type=int))
    mensajes = {"ok": ("Proveedor guardado.", "ok"),
                "ruc_duplicado": ("Ya existe un proveedor con ese RUC.", "error")}
    flash(*mensajes.get(resultado, ("Revisa los datos del proveedor.", "error")))
    return redirect(url_for("admin.proveedores.home"))


@proveedores.route("/estado/<int:id_proveedor>", methods=["POST"])
def estado(id_proveedor):
    bloqueo = _solo_superusuario("admin.proveedores.home")
    if bloqueo:
        return bloqueo
    Proveedor.cambiar_estado(id_proveedor, request.form.get("activo") == "1")
    flash("Estado del proveedor actualizado.", "ok")
    return redirect(url_for("admin.proveedores.home"))


@compras.route("/")
def home():
    return render_template(
        "admin/compras/index.html", usuario=g.user, compras=Compra.listar(),
        proveedores=Proveedor.listar(True), productos=Producto.obtener_productos(solo_activos=True),
        insumos=Insumos.listar(), almacenes=Inventario.almacenes(),
        puede_modificar=g.user.get("rol") == "superusuario")


@compras.route("/crear", methods=["POST"])
def crear():
    bloqueo = _solo_superusuario("admin.compras.home")
    if bloqueo:
        return bloqueo
    productos = request.form.getlist("producto[]")
    cantidades = request.form.getlist("cantidad[]")
    costos = request.form.getlist("costo[]")
    lineas = [{"idProducto": p, "cantidad": c, "costo": co}
              for p, c, co in zip(productos, cantidades, costos)]
    ingredientes = request.form.getlist("insumo[]")
    cantidades_insumo = request.form.getlist("cantidad_insumo[]")
    costos_insumo = request.form.getlist("costo_insumo[]")
    lineas_insumo = [{"idInsumo": i, "cantidad": c, "costo": co}
                     for i, c, co in zip(ingredientes, cantidades_insumo, costos_insumo)]
    resultado = Compra.crear(
        request.form.get("proveedor", type=int), request.form.get("documento"),
        request.form.get("fecha"), lineas, g.user["idUsuario"],
        request.form.get("observaciones"), request.form.get("almacen", type=int) or 1,
        lineas_insumo)
    if isinstance(resultado, int):
        flash("Compra registrada como borrador. Confirma la recepción cuando llegue la mercadería.", "ok")
    elif resultado == "duplicada":
        flash("Ese documento ya fue registrado para el proveedor.", "error")
    elif resultado == "linea_duplicada":
        flash("Cada producto o insumo debe aparecer una sola vez por compra. Revisa las líneas.", "error")
    else:
        flash("Revisa el documento y los productos de la compra.", "error")
    return redirect(url_for("admin.compras.home"))


@compras.route("/recibir/<int:id_compra>", methods=["POST"])
def recibir(id_compra):
    bloqueo = _solo_superusuario("admin.compras.home")
    if bloqueo:
        return bloqueo
    resultado = Compra.recibir(id_compra, g.user["idUsuario"])
    if resultado == "ok":
        flash("Compra recibida: stock, costo promedio y Kardex actualizados.", "ok")
    else:
        flash("La compra ya fue procesada o no existe.", "error")
    return redirect(url_for("admin.compras.home"))
