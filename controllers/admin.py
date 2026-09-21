from datetime import datetime, timedelta

from flask import Blueprint, render_template, session, g, redirect, url_for, request
from model.Comprobante import Comprobante
from negocio import ahora_peru
from model.Producto import Producto
from model.Pedido import Pedido

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route("/")
def home():
    resumen = Pedido.resumen_dashboard()
    hoy = ahora_peru().date()
    try:
        dia = datetime.strptime(request.args.get("dia", ""), "%Y-%m-%d").date()
    except ValueError:
        dia = hoy
    if dia > hoy:
        dia = hoy
    return render_template(
        "admin/dashboard.html", usuario=g.user, resumen=resumen,
        serie_horas=Comprobante.serie_por_hora(dia), dia=dia.isoformat(),
        hoy=hoy.isoformat(), ayer=(hoy - timedelta(days=1)).isoformat())


@admin.before_request
def verificacion_usuario_logueado():
    from flask import request, flash
    # Rutas de sesión que no requieren estar logueado.
    if request.endpoint in ("admin.auth.login", "admin.auth.logout"):
        return
    user = session.get("admin.auth")
    if user is None:
        return redirect(url_for("cliente.auth.login"))
    g.user = user

    # Gestión de usuarios: solo el superusuario.
    ep = request.endpoint or ""
    if ep.startswith("admin.usuarios.") and user.get("rol") != "superusuario":
        flash("Solo un superusuario puede entrar a la gestión de usuarios.", "error")
        return redirect(url_for("admin.home"))
