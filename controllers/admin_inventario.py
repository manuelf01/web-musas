from datetime import datetime

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from model.Inventario import Inventario
from model.Producto import Producto
from model.Insumos import Insumos, UNIDADES
from negocio import ahora_peru


inventario = Blueprint("inventario", __name__, url_prefix="/inventario")


def _puede_modificar():
    return g.user.get("rol") == "superusuario"


@inventario.route("/")
def home():
    almacen_id = request.args.get("almacen", type=int) or 1
    saldos = Inventario.saldos(almacen_id)
    q = (request.args.get("q") or "").strip().casefold()
    if q:
        saldos = [s for s in saldos if q in f"{s['producto']} {s['categoria']}".casefold()]
    return render_template(
        "admin/inventario/index.html", usuario=g.user, saldos=saldos,
        almacenes=Inventario.almacenes(False), almacen_id=almacen_id, q=request.args.get("q", ""),
        alertas=[s for s in saldos if s["activo"] and s["disponible"] <= 5],
        puede_modificar=_puede_modificar())


@inventario.route("/kardex/")
def kardex():
    producto_id = request.args.get("producto", type=int)
    almacen_id = request.args.get("almacen", type=int) or 1
    tipo = (request.args.get("tipo") or "").strip()
    desde, hasta = request.args.get("desde", ""), request.args.get("hasta", "")
    return render_template(
        "admin/inventario/kardex.html", usuario=g.user,
        productos=Producto.obtener_productos(), almacenes=Inventario.almacenes(False),
        movimientos=Inventario.kardex(producto_id, tipo, 500, almacen_id, desde, hasta),
        producto_id=producto_id, almacen_id=almacen_id, tipo=tipo, desde=desde, hasta=hasta)


@inventario.route("/movimientos/")
def movimientos():
    almacen_id = request.args.get("almacen", type=int) or 1
    return render_template(
        "admin/inventario/movimientos.html", usuario=g.user,
        productos=Producto.obtener_productos(), almacenes=Inventario.almacenes(),
        almacen_id=almacen_id,
        movimientos=Inventario.kardex(limite=100, id_almacen=almacen_id),
        movimientos_insumos=Insumos.movimientos(100, almacen_id),
        puede_modificar=_puede_modificar())


@inventario.route("/insumos/")
def insumos():
    q = (request.args.get("q") or "").strip()
    estado = request.args.get("estado", "")
    almacen_id = request.args.get("almacen", type=int) or 1
    dia = request.args.get("dia", "")
    try:
        dia = datetime.strptime(dia, "%Y-%m-%d").date().isoformat()
    except ValueError:
        dia = ahora_peru().date().isoformat()
    if estado not in ("", "bajo", "agotado"):
        estado = ""
    return render_template(
        "admin/inventario/insumos.html", usuario=g.user,
        insumos=Insumos.listar(almacen_id, q, estado), q=q, estado=estado,
        dia=dia, consumo_dia=Insumos.consumo_del_dia(dia, almacen_id),
        almacenes=Inventario.almacenes(False), almacen_id=almacen_id,
        unidades=UNIDADES, categorias_insumo=Insumos.categorias(),
        puede_modificar=_puede_modificar())


@inventario.route("/insumos/guardar", methods=["POST"])
def guardar_insumo():
    if not _puede_modificar():
        flash("Solo el Administrador puede gestionar el catálogo de insumos.", "error")
        return redirect(url_for("admin.inventario.insumos"))
    categoria = request.form.get("categoria", "")
    if categoria == "__nueva__":
        categoria = request.form.get("categoria_nueva", "")
    resultado = Insumos.guardar(
        request.form.get("nombre"), categoria,
        request.form.get("unidad"), request.form.get("stockMinimo"),
        request.form.get("idInsumo", type=int))
    mensajes = {"ok": ("Insumo guardado.", "ok"), "duplicado": ("Ya existe un insumo con ese nombre.", "error")}
    flash(*mensajes.get(resultado, ("Revisa nombre, unidad y stock mínimo.", "error")))
    return redirect(url_for("admin.inventario.insumos"))


@inventario.route("/insumos/movimiento", methods=["POST"])
def movimiento_insumo():
    if not _puede_modificar():
        flash("Solo el Administrador puede registrar movimientos de insumos.", "error")
        return redirect(url_for("admin.inventario.insumos"))
    resultado = Insumos.movimiento_manual(
        request.form.get("idInsumo", type=int), request.form.get("cantidad"),
        request.form.get("tipo"), request.form.get("motivo"), g.user["idUsuario"],
        request.form.get("costo"), request.form.get("documento"),
        request.form.get("almacen", type=int) or 1)
    mensajes = {"ok": ("Movimiento registrado. El saldo y el Kardex quedaron actualizados.", "ok"),
                "stock_insuficiente": ("La salida supera el stock disponible.", "error")}
    flash(*mensajes.get(resultado, ("Revisa el insumo, cantidad y motivo.", "error")))
    return redirect(url_for("admin.inventario.insumos"))


@inventario.route("/recetas/")
def recetas():
    productos, catalogo_insumos, mapa = Insumos.recetas()
    almacen_id = request.args.get("almacen", type=int) or 1
    capacidades = Insumos.capacidades(almacen_id)
    recetas_lista = []
    for producto in productos:
        for tipo in ("producto", "opcion"):
            lineas = mapa.get((producto["id"], tipo), [])
            if lineas:
                recetas_lista.append({"producto": producto, "tipo": tipo, "lineas": lineas})
    return render_template(
        "admin/inventario/recetas.html", usuario=g.user, productos=productos,
        insumos=catalogo_insumos, recetas=recetas_lista, capacidades=capacidades,
        almacenes=Inventario.almacenes(False), almacen_id=almacen_id,
        puede_modificar=_puede_modificar())


@inventario.route("/recetas/guardar", methods=["POST"])
def guardar_receta():
    if not _puede_modificar():
        flash("Solo el Administrador puede configurar recetas.", "error")
        return redirect(url_for("admin.inventario.recetas"))
    ids, cantidades = request.form.getlist("idInsumo[]"), request.form.getlist("cantidad[]")
    resultado = Insumos.guardar_receta(
        request.form.get("idProducto", type=int), request.form.get("tipoUso"),
        [{"idInsumo": i, "cantidad": c} for i, c in zip(ids, cantidades)])
    mensajes = {"ok": ("Receta guardada. Las nuevas reservas usarán esta preparación.", "ok"),
                "receta_vacia": ("Agrega al menos un insumo a la receta.", "error")}
    flash(*mensajes.get(resultado, ("Revisa el producto y las cantidades de la receta.", "error")))
    return redirect(url_for("admin.inventario.recetas"))


@inventario.route("/movimientos/registrar", methods=["POST"])
def registrar_movimiento():
    if not _puede_modificar():
        flash("Solo el Administrador puede registrar movimientos manuales de inventario.", "error")
        return redirect(url_for("admin.inventario.movimientos"))
    resultado = Inventario.movimiento_manual(
        request.form.get("producto", type=int), request.form.get("cantidad"),
        request.form.get("tipo"), request.form.get("motivo"), g.user["idUsuario"],
        request.form.get("costo"), request.form.get("documento"),
        request.form.get("almacen", type=int) or 1)
    mensajes = {
        "ok": ("Movimiento registrado con trazabilidad.", "ok"),
        "stock_insuficiente": ("El movimiento supera el stock disponible no reservado.", "error"),
    }
    texto, tono = mensajes.get(resultado, ("Revisa el producto, cantidad y motivo.", "error"))
    flash(texto, tono)
    return redirect(url_for("admin.inventario.movimientos"))


@inventario.route("/ajustar", methods=["POST"])
def ajustar():
    if not _puede_modificar():
        flash("Solo el Administrador puede ajustar el inventario.", "error")
        return redirect(url_for("admin.inventario.home"))
    resultado = Inventario.ajustar(
        request.form.get("idProducto", type=int), request.form.get("nuevo_stock"),
        request.form.get("tipo"), request.form.get("motivo"),
        g.user["idUsuario"], request.form.get("costo_unitario"),
        request.form.get("almacen", type=int) or 1)
    mensajes = {
        "ok": ("Stock físico actualizado y movimiento registrado en el Kardex.", "ok"),
        "sin_cambio": ("El stock indicado es igual al actual.", "error"),
        "menor_reservado": ("El stock físico no puede ser menor que el reservado.", "error"),
    }
    texto, tono = mensajes.get(resultado, ("Revisa el producto, el stock y el motivo.", "error"))
    flash(texto, tono)
    return redirect(url_for("admin.inventario.home"))
