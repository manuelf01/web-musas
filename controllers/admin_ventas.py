from io import BytesIO

from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, g, send_file, jsonify, flash
from flask_paginate import Pagination, get_page_parameter
from model.Comprobante import Comprobante, MESES
from negocio import ahora_peru
from model.Pedido import estado_pedido
from formato import soles_en_letras
from avisos import ok_deshacer
from services.comprobante_pdf import generar_comprobante_pdf

ventas = Blueprint("ventas", __name__, url_prefix="/ventas")


def _fecha(texto):
    try:
        return datetime.strptime((texto or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


@ventas.route("/")
def home():
    hoy = ahora_peru().date()
    q = (request.args.get("q") or "").strip()
    tipo = (request.args.get("tipo") or "").strip().lower()
    if tipo not in ("boleta", "factura"):
        tipo = ""
    medio = (request.args.get("medio") or "").strip().capitalize()
    if medio not in ("Efectivo", "Tarjeta", "Yape", "Plin"):
        medio = ""
    estado = (request.args.get("estado") or "").strip().lower()
    if estado not in ("vigente", "anulado"):
        estado = ""
    desde = _fecha(request.args.get("desde"))
    hasta = _fecha(request.args.get("hasta"))
    if desde and hasta and desde > hasta:
        desde, hasta = hasta, desde

    vista = (request.args.get("vista") or "semana").strip().lower()
    if vista not in ("semana", "mes", "anio"):
        vista = "semana"
    anios = Comprobante.anios_disponibles()
    anio = request.args.get("anio", type=int)
    if anio not in anios:
        anio = hoy.year
    mes = request.args.get("mes", type=int)
    if not mes or not 1 <= mes <= 12:
        mes = hoy.month
    dia = _fecha(request.args.get("dia")) or hoy

    per_page = 5
    page = max(1, request.args.get(get_page_parameter(), type=int, default=1))
    total = Comprobante.obtener_total(q, tipo, medio, desde, hasta, estado)
    comprobantes = Comprobante.listado_paginado(
        per_page, (page - 1) * per_page, q, tipo, medio, desde, hasta, estado)
    pagination = Pagination(page=page, total=total, per_page=per_page,
                            search=bool(q), record_name="comprobantes",
                            css_framework="bootstrap5")

    contexto = dict(
        usuario=g.user,
        comprobantes=comprobantes,
        pagination=pagination,
        filtros={"q": q, "tipo": tipo, "medio": medio, "estado": estado,
                 "desde": desde.isoformat() if desde else "",
                 "hasta": hasta.isoformat() if hasta else ""},
        total=total,
        rango=((page - 1) * per_page + 1 if total else 0, min(page * per_page, total)),
    )
    # Filtrado en vivo: el navegador pide solo la tabla, sin recargar la página.
    if request.headers.get("X-Requested-With") == "fetch":
        return render_template("admin/ventas/_comprobantes.html", **contexto)

    return render_template(
        "admin/ventas/index.html",
        kpis=Comprobante.kpis(),
        serie=Comprobante.serie_ventas(vista, anio, mes),
        serie_horas=Comprobante.serie_por_hora(dia),
        vista=vista, anio=anio, mes=mes, anios=anios, meses=MESES,
        dia=dia.isoformat(), hoy=hoy.isoformat(), ayer=(hoy - timedelta(days=1)).isoformat(),
        **contexto,
    )


@ventas.route("/sugerencias")
def sugerencias():
    return jsonify(Comprobante.sugerencias(request.args.get("q", "")))


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


@ventas.route("/anular/<int:idComprobante>", methods=["POST"])
def anular(idComprobante):
    resultado = Comprobante.anular(
        idComprobante, request.form.get("motivo"), g.user["idUsuario"],
        request.form.get("devolver_stock") == "1")
    destino = redirect(url_for("admin.ventas.show_detalle", idComprobante=idComprobante))
    if resultado == "ok":
        devuelto = request.form.get("devolver_stock") == "1"
        mensaje = "Venta anulada. Ya no cuenta en los totales de ventas."
        if devuelto:
            mensaje += " Se devolvieron los productos al inventario."
        ok_deshacer(mensaje, url_for("admin.ventas.restaurar", idComprobante=idComprobante), {},
                    "Deshacer anulación")
    elif resultado == "motivo_invalido":
        flash("Escribe el motivo de la anulación (mínimo 5 caracteres).", "error")
    elif resultado == "ya_anulado":
        flash("Este comprobante ya estaba anulado.", "error")
    else:
        return redirect(url_for("admin.ventas.home"))
    return destino


@ventas.route("/restaurar/<int:idComprobante>", methods=["POST"])
def restaurar(idComprobante):
    resultado = Comprobante.restaurar(idComprobante)
    if resultado == "ok":
        flash("Anulación deshecha: la venta vuelve a contar en los totales.", "ok")
    elif resultado == "sin_stock":
        flash("No se puede deshacer: ya no hay existencias suficientes para volver a descontarlas.", "error")
    elif resultado == "no_anulado":
        flash("Este comprobante no está anulado.", "error")
    else:
        return redirect(url_for("admin.ventas.home"))
    return redirect(url_for("admin.ventas.show_detalle", idComprobante=idComprobante))


@ventas.route("/detalle_comprobante/<int:idComprobante>/pdf")
def descargar_pdf(idComprobante):
    comprobante = Comprobante.detalle(idComprobante)
    if comprobante is None:
        return redirect(url_for("admin.ventas.home"))
    pdf = generar_comprobante_pdf(comprobante)
    return send_file(
        BytesIO(pdf), mimetype="application/pdf", as_attachment=True,
        download_name=f"comprobante-{comprobante['numero']}.pdf",
    )
