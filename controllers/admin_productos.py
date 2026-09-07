from flask import Blueprint, render_template, redirect, request, url_for, g, flash
from flask_paginate import Pagination, get_page_parameter
from controllers.admin import admin
from model.Producto import Producto
from model.CategoriaProducto import CategoriaProducto
from subidas import guardar_imagen

productos = Blueprint("productos", __name__, url_prefix='/productos')


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
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    existencias = request.form["existencias"]
    idCategoria = request.form.get("categorias")
    imagen = guardar_imagen(request.files.get("imagen"), "productos")
    if request.files.get("imagen") and request.files["imagen"].filename and not imagen:
        flash("La imagen no es válida (usa JPG, PNG o WEBP, máx. 5 MB).", "error")
        return redirect(url_for("admin.productos.formulario_agregar"))
    if Producto.insertar_producto(nombre, descripcion, precio, existencias, idCategoria, imagen) is False:
        flash("Completa todos los campos del producto.", "error")
        return redirect(url_for("admin.productos.formulario_agregar"))
    flash("Producto agregado a la carta.", "ok")
    return redirect(url_for("admin.productos.home"))


@productos.route("/eliminar_producto", methods=["POST"])
def eliminar():
    try:
        Producto.eliminar_producto(request.form["id"])
        flash("Producto eliminado.", "ok")
    except Exception:
        flash("No se puede eliminar: el producto aparece en pedidos. Ponle stock 0 para ocultarlo.", "error")
    return redirect(url_for("admin.productos.home"))


@productos.route("/formulario_editar_producto/<int:id>")
def editar(id):
    producto = Producto.obtener_producto_por_id(id)
    categorias = CategoriaProducto.obtener_categorias()
    return render_template("admin/productos/editar_producto.html", producto=producto, categorias=categorias, usuario=g.user)


@productos.route("/actualizar_producto", methods=["POST"])
def actualizar():
    id = request.form["idProducto"]
    nombre = request.form["nombre"]
    descripcion = request.form["descripcion"]
    precio = request.form["precio"]
    existencias = request.form["existencias"]
    idCategoria = request.form.get("categorias")
    imagen = guardar_imagen(request.files.get("imagen"), "productos")
    if request.files.get("imagen") and request.files["imagen"].filename and not imagen:
        flash("La imagen no es válida (usa JPG, PNG o WEBP, máx. 5 MB).", "error")
        return redirect(url_for("admin.productos.editar", id=id))
    Producto.actualizar_producto(
        nombre, descripcion, precio, existencias, id, idCategoria, imagen)
    flash("Producto actualizado." + (" Imagen cambiada." if imagen else ""), "ok")
    return redirect(url_for("admin.productos.home"))
