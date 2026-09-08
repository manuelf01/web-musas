from flask import Blueprint, render_template, request, redirect, url_for, g
from flask_paginate import Pagination, get_page_parameter
from model.Comprobante import Comprobante
from model.Pedido import estado_pedido
from formato import soles_en_letras

ventas = Blueprint("ventas", __name__, url_prefix="/ventas")


@ventas.route("/")
def home():
    q = (request.args.get("q") or "").strip()
    per_page = 8
    page = request.args.get(get_page_parameter(), type=int, default=1)
    if page < 1:
        page = 1

    total = Comprobante.obtener_total()
    comprobantes = Comprobante.listado_paginado(per_page, (page - 1) * per_page)
    if q:
        ql = q.lower()
        comprobantes = [c for c in comprobantes
                        if ql in c["cliente"].lower()
                        or ql in str(c["numero"]).lower()
                        or ql in str(c["dni"] or "")]

    pagination = Pagination(page=page, total=total, per_page=per_page,
                            search=bool(q), record_name="comprobantes",
                            css_framework="bootstrap5")

    return render_template(
        "admin/ventas/index.html",
        usuario=g.user,
        comprobantes=comprobantes,
        pagination=pagination,
        kpis=Comprobante.kpis(),
        grafico=Comprobante.ventas_por_dia(7),
        total=total,
        rango=((page - 1) * per_page + 1 if total else 0,
               min(page * per_page, total)),
    )


@ventas.route("/detalle_comprobante/<int:idComprobante>")
def show_detalle(idComprobante):
    comprobante = Comprobante.detalle(idComprobante)
    if comprobante is None:
        return redirect(url_for("admin.ventas.home"))

    etiquetas = {
        "recibido": "Recibido", "preparando": "En preparación", "listo": "Listo para recojo",
        "recogido": "Recogido", "cancelado": "Cancelado", "no_show": "No recogió",
    }
    return render_template(
        "admin/ventas/detalle_comprobante.html",
        usuario=g.user,
        c=comprobante,
        estado_texto=etiquetas.get(comprobante["estado"], comprobante["estado"]),
        importe_letras=soles_en_letras(comprobante["montoTotal"]),
    )
