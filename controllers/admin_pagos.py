from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, g
from flask_paginate import Pagination, get_page_parameter

from model.Pago import Pago, MEDIOS
from negocio import ahora_peru

pagos = Blueprint("pagos", __name__, url_prefix="/pagos")


def _fecha(texto):
    try:
        return datetime.strptime((texto or "").strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


@pagos.route("/")
def home():
    hoy = ahora_peru().date()
    # Sin fechas = hoy. Si el usuario borra una de las dos, ese lado queda abierto.
    if "desde" not in request.args and "hasta" not in request.args:
        desde = hasta = hoy
    else:
        desde, hasta = _fecha(request.args.get("desde")), _fecha(request.args.get("hasta"))
    if desde and hasta and desde > hasta:
        desde, hasta = hasta, desde
    q = (request.args.get("q") or "").strip()
    medio = (request.args.get("medio") or "").strip().capitalize()
    if medio not in MEDIOS:
        medio = ""
    estado = (request.args.get("estado") or "").strip().lower()
    if estado not in ("vigente", "anulado"):
        estado = ""

    per_page = 10
    page = max(1, request.args.get(get_page_parameter(), type=int, default=1))
    total = Pago.total(desde, hasta, q, estado, medio)
    lista = Pago.listado(per_page, (page - 1) * per_page, desde, hasta, q, estado, medio)
    pagination = Pagination(page=page, total=total, per_page=per_page, search=bool(q),
                            record_name="pagos", css_framework="bootstrap5")
    contexto = dict(
        usuario=g.user, resumen=Pago.resumen(desde, hasta, q, estado), pagos=lista,
        pagination=pagination, total=total, medios=MEDIOS,
        rango=((page - 1) * per_page + 1 if total else 0, min(page * per_page, total)),
        filtros={"q": q, "medio": medio, "estado": estado,
                 "desde": desde.isoformat() if desde else "", "hasta": hasta.isoformat() if hasta else ""},
    )
    if request.headers.get("X-Requested-With") == "fetch":
        return render_template("admin/pagos/_lista.html", **contexto)

    ayer = hoy - timedelta(days=1)
    return render_template(
        "admin/pagos/index.html", hoy=hoy.isoformat(), ayer=ayer.isoformat(),
        hace7=(hoy - timedelta(days=6)).isoformat(), inicio_mes=hoy.replace(day=1).isoformat(),
        **contexto)
