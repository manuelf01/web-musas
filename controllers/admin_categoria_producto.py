from flask import Blueprint, request, render_template, redirect, url_for, g, flash
from controllers.admin import admin
from model.CategoriaProducto import CategoriaProducto
from model.Producto import Producto
from subidas import guardar_imagen, guardar_desde_url

categoria_producto = Blueprint("categoria", __name__, url_prefix='/categorias')


def _imagen_del_form():
    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        ruta = guardar_imagen(archivo, "categorias")
        return ruta, (None if ruta else "La imagen no es válida (JPG, PNG o WEBP, máx. 5 MB).")
    enlace = (request.form.get("imagen_url") or "").strip()
    if enlace:
        ruta = guardar_desde_url(enlace, "categorias")
        return ruta, (None if ruta else "No se pudo descargar la imagen de ese enlace.")
    return None, None


@categoria_producto.route("/")
def home():
    q = (request.args.get("q") or "").strip()
    estado = request.args.get("estado", "activas")
    todas = CategoriaProducto.obtener_categorias()   # (id, nombre, desc, imagen, activo)
    de_baja = sum(1 for c in todas if len(c) > 4 and not c[4])
    activas = len(todas) - de_baja

    lista = todas
    if estado == "activas":
        lista = [c for c in lista if len(c) <= 4 or c[4]]
    elif estado == "baja":
        lista = [c for c in lista if len(c) > 4 and not c[4]]
    if q:
        ql = q.lower()
        lista = [c for c in lista if ql in c[1].lower() or ql in (c[2] or "").lower()]

    return render_template(
        "admin/categoria/index.html",
        categorias=lista, q=q, estado=estado,
        totales=Producto.contar_por_categoria(),
        sugerencias=sorted({c[1] for c in todas}),
        conteos={"total": len(todas), "activas": activas, "de_baja": de_baja},
        usuario=g.user,
    )


@categoria_producto.route("/agregar")
def agregar():
    return redirect(url_for("admin.categoria.home"))


@categoria_producto.route("/editar_categoria/<int:id>")
def editar(id):
    return redirect(url_for("admin.categoria.home"))


@categoria_producto.route("/guardar_categoria", methods=["POST"])
def guardar():
    imagen, err = _imagen_del_form()
    if err:
        flash(err, "error")
        return redirect(url_for("admin.categoria.home"))
    CategoriaProducto.insertar_categoria(
        request.form["nombreCategoria"], request.form["descripcion"], imagen)
    flash("Categoría creada.", "ok")
    return redirect(url_for('admin.categoria.home'))


@categoria_producto.route("/actualizar", methods=["POST"])
def actualizar():
    imagen, err = _imagen_del_form()
    if err:
        flash(err, "error")
        return redirect(url_for("admin.categoria.home"))
    CategoriaProducto.actualizar_categoria(
        request.form["nombreCategoria"], request.form["descripcion"],
        request.form["idCategoria"], imagen)
    flash("Categoría actualizada." + (" Imagen cambiada." if imagen else ""), "ok")
    return redirect(url_for("admin.categoria.home"))


@categoria_producto.route("/estado", methods=["POST"])
def estado():
    activar = request.form.get("activar") == "1"
    CategoriaProducto.cambiar_estado(request.form["idCategoria"], activar)
    flash("Categoría reactivada." if activar
          else "Categoría dada de baja (sus productos dejan de verse en la carta).", "ok")
    return redirect(url_for("admin.categoria.home", estado=request.form.get("volver", "activas")))


@categoria_producto.route("/eliminar", methods=["POST"])
def eliminar():
    try:
        CategoriaProducto.eliminar_categoria(request.form["idCategoria"])
        flash("Categoría eliminada.", "ok")
    except Exception:
        flash("No se puede eliminar: hay productos en esa categoría. Usa «Dar de baja».", "error")
    return redirect(url_for("admin.categoria.home"))
