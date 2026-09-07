from flask import Blueprint, request, render_template, redirect, url_for, g, flash
from controllers.admin import admin
from model.CategoriaProducto import CategoriaProducto

categoria_producto = Blueprint("categoria", __name__, url_prefix='/categorias')


@categoria_producto.route("/")
def home():
    categoria = CategoriaProducto.obtener_categorias()
    return render_template("admin/categoria/index.html", categorias=categoria, usuario=g.user)


@categoria_producto.route("/agregar")
def agregar():
    return render_template("admin/categoria/agregar.html", usuario=g.user)


@categoria_producto.route("/guardar_categoria", methods=["POST"])
def guardar():
    nombreCategoria = request.form["nombreCategoria"]
    descripcion = request.form["descripcion"]
    CategoriaProducto.insertar_categoria(nombreCategoria, descripcion)
    flash("Categoría creada.", "ok")
    return redirect(url_for('admin.categoria.home'))


@categoria_producto.route("/eliminar", methods=["POST"])
def eliminar():
    try:
        CategoriaProducto.eliminar_categoria(request.form["idCategoria"])
        flash("Categoría eliminada.", "ok")
    except Exception:
        flash("No se puede eliminar: hay productos en esa categoría. Muévelos primero.", "error")
    return redirect(url_for("admin.categoria.home"))


@categoria_producto.route("/editar_categoria/<int:id>")
def editar(id):
    # Obtener el categoria por ID
    categoria = CategoriaProducto.obtener_categoria_por_id(id)
    return render_template("admin/categoria/editar.html", categoria=categoria, usuario=g.user)


@categoria_producto.route("/actualizar", methods=["POST"])
def actualizar():
    id = request.form["idCategoria"]
    nombreCategoria = request.form["nombreCategoria"]
    descripcion = request.form["descripcion"]
    CategoriaProducto.actualizar_categoria(nombreCategoria, descripcion, id)
    flash("Categoría actualizada.", "ok")
    return redirect(url_for("admin.categoria.home"))
