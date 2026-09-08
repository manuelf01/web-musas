from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, g, redirect, render_template, request, url_for
from flask_paginate import Pagination, get_page_parameter
from werkzeug.utils import secure_filename
from controllers.admin import admin
from model.Producto import Producto
from model.CategoriaProducto import CategoriaProducto

productos = Blueprint("productos", __name__, url_prefix='/productos')
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}


def guardar_imagen(imagen):
    if imagen is None or not imagen.filename:
        return None
    nombre_seguro = secure_filename(imagen.filename)
    extension = Path(nombre_seguro).suffix.lower()
    if extension not in EXTENSIONES_IMAGEN:
        raise ValueError("La imagen debe ser JPG, PNG o WEBP")
    nombre_final = f"{uuid4().hex}{extension}"
    carpeta = Path(current_app.static_folder) / "img" / "productos"
    carpeta.mkdir(parents=True, exist_ok=True)
    imagen.save(carpeta / nombre_final)
    return f"img/productos/{nombre_final}"


@productos.route("/")
def home():
    search = False
    q = request.args.get('q')
    if q:
        search = True

    productosTotal = Producto.obtener_total_productos()
    per_page = 9
    page = request.args.get(get_page_parameter(), type=int, default=1)
    start_index = (page - 1) * per_page + 1

    pagination = Pagination(page=page, total=productosTotal, per_page=per_page,
                            search=search, record_name='productos')

    productos = Producto.obtener_productos_paginacion(per_page, start_index)
    return render_template("admin/productos/index.html", productos=productos, usuario=g.user, pagination=pagination)


@productos.route("/agregar_producto")
def formulario_agregar():
    nombreCategorias = CategoriaProducto.obtener_categorias()
    return render_template("admin/productos/agregar_producto.html", categorias=nombreCategorias, usuario=g.user)


@productos.route("/guardar_producto", methods=["POST"])
def guardar():
    try:
        imagen = guardar_imagen(request.files.get("imagen"))
        error = Producto.insertar_producto(
            request.form.get("nombre", ""),
            request.form.get("descripcion", ""),
            request.form.get("precio", ""),
            request.form.get("existencias", ""),
            request.form.get("categorias", ""),
            imagen,
        )
        if error:
            raise ValueError(error)
        flash("Producto agregado correctamente.", "success")
    except ValueError as error:
        flash(str(error), "danger")
        return redirect(url_for("admin.productos.formulario_agregar"))
    return redirect(url_for("admin.productos.home"))


@productos.route("/eliminar_producto", methods=["POST"])
def eliminar():
    Producto.eliminar_producto(request.form["id"])
    return redirect(url_for("admin.productos.home"))


@productos.route("/formulario_editar_producto/<int:id>")
def editar(id):
    producto = Producto.obtener_producto_por_id(id)
    categorias = CategoriaProducto.obtener_categorias()
    return render_template(
        "admin/productos/editar_producto.html",
        producto=producto,
        categorias=categorias,
        usuario=g.user,
    )


@productos.route("/actualizar_producto", methods=["POST"])
def actualizar():
    id_producto = request.form["idProducto"]
    try:
        imagen = guardar_imagen(request.files.get("imagen"))
        Producto.actualizar_producto(
            request.form.get("nombre", ""),
            request.form.get("descripcion", ""),
            request.form.get("precio", ""),
            request.form.get("stockAgregar", "0"),
            id_producto,
            request.form.get("categorias", ""),
            imagen,
        )
        flash("Producto y stock actualizados correctamente.", "success")
    except ValueError as error:
        flash(str(error), "danger")
        return redirect(url_for("admin.productos.editar", id=id_producto))
    return redirect(url_for("admin.productos.home"))
