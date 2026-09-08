from flask import Blueprint, render_template, redirect, request, url_for, g, flash
from flask_paginate import Pagination, get_page_parameter
from controllers.admin import admin
from model.Producto import Producto
from model.CategoriaProducto import CategoriaProducto
from subidas import guardar_imagen, guardar_desde_url

productos = Blueprint("productos", __name__, url_prefix='/productos')


def _imagen_del_form(prefijo_ruta):
    """Toma la imagen del formulario: archivo subido o enlace de internet.
    Devuelve (ruta_relativa | None, error | None)."""
    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        ruta = guardar_imagen(archivo, prefijo_ruta)
        if not ruta:
            return None, "La imagen no es válida (usa JPG, PNG o WEBP, máx. 5 MB)."
        return ruta, None
    enlace = (request.form.get("imagen_url") or "").strip()
    if enlace:
        ruta = guardar_desde_url(enlace, prefijo_ruta)
        if not ruta:
            return None, "No se pudo descargar la imagen de ese enlace. Revisa que sea el enlace directo a una imagen."
        return ruta, None
    return None, None


@productos.route("/")
def home():
    q = (request.args.get("q") or "").strip()
    estado = request.args.get("estado", "activos")
    per_page = 9
    page = request.args.get(get_page_parameter(), type=int, default=1)

    catalogo = Producto.obtener_productos()
    sin_stock = sum(1 for p in catalogo if p["activo"] and not p["existencias"])
    de_baja = sum(1 for p in catalogo if not p["activo"])
    activos = len(catalogo) - de_baja

    filtrados = catalogo
    if estado == "activos":
        filtrados = [p for p in filtrados if p["activo"]]
    elif estado == "baja":
        filtrados = [p for p in filtrados if not p["activo"]]
    elif estado == "sin_stock":
        filtrados = [p for p in filtrados if p["activo"] and not p["existencias"]]

    if q:
        ql = q.lower()
        filtrados = [p for p in filtrados if ql in p["nombre"].lower()
                     or ql in (p["descripcion"] or "").lower()
                     or ql in (p["nombreCategoria"] or "").lower()]

    total = len(filtrados)
    inicio = (page - 1) * per_page
    pagina = filtrados[inicio:inicio + per_page]
    pagination = Pagination(page=page, total=total, per_page=per_page,
                            search=bool(q), record_name="productos", css_framework="bootstrap5")

    categorias = CategoriaProducto.obtener_categorias(solo_activas=True)
    return render_template(
        "admin/productos/index.html",
        productos=pagina, usuario=g.user, pagination=pagination,
        categorias=categorias, q=q, estado=estado,
        sugerencias=sorted({p["nombre"] for p in catalogo}
                           | {p["nombreCategoria"] for p in catalogo if p["nombreCategoria"]}),
        rango=(inicio + 1 if total else 0, inicio + len(pagina)),
        conteos={"total": len(catalogo), "activos": activos, "de_baja": de_baja,
                 "sin_stock": sin_stock, "categorias": len(categorias)},
    )


@productos.route("/agregar_producto")
def formulario_agregar():
    return redirect(url_for("admin.productos.home"))


@productos.route("/formulario_editar_producto/<int:id>")
def editar(id):
    return redirect(url_for("admin.productos.home"))


@productos.route("/guardar_producto", methods=["POST"])
def guardar():
    imagen, err = _imagen_del_form("productos")
    if err:
        flash(err, "error")
        return redirect(url_for("admin.productos.home"))
    resultado = Producto.insertar_producto(
        request.form["nombre"], request.form["descripcion"], request.form["precio"],
        request.form["existencias"], request.form.get("categorias"), imagen,
    )
    if resultado is False:
        flash("Completa todos los campos del producto.", "error")
    else:
        flash("Producto agregado a la carta.", "ok")
    return redirect(url_for("admin.productos.home"))


@productos.route("/actualizar_producto", methods=["POST"])
def actualizar():
    id = request.form["idProducto"]
    imagen, err = _imagen_del_form("productos")
    if err:
        flash(err, "error")
        return redirect(url_for("admin.productos.home"))
    Producto.actualizar_producto(
        request.form["nombre"], request.form["descripcion"], request.form["precio"],
        request.form["existencias"], id, request.form.get("categorias"), imagen,
    )
    flash("Producto actualizado." + (" Imagen cambiada." if imagen else ""), "ok")
    return redirect(url_for("admin.productos.home"))


@productos.route("/estado", methods=["POST"])
def estado():
    id = request.form["id"]
    activar = request.form.get("activar") == "1"
    Producto.cambiar_estado(id, activar)
    flash("Producto reactivado." if activar else "Producto dado de baja (ya no aparece en la carta).", "ok")
    return redirect(url_for("admin.productos.home", estado=request.form.get("volver", "activos")))


@productos.route("/eliminar_producto", methods=["POST"])
def eliminar():
    # Se mantiene el borrado real solo para productos que nunca se usaron.
    try:
        Producto.eliminar_producto(request.form["id"])
        flash("Producto eliminado.", "ok")
    except Exception:
        flash("No se puede eliminar: el producto aparece en pedidos. Usa «Dar de baja».", "error")
    return redirect(url_for("admin.productos.home"))
