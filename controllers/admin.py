import time

from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from model.Producto import Producto

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route("/")
def home():
    user = session.get("admin.auth")
    if user is None:
        return redirect(url_for("admin.auth.login"))
    else:
        productos = Producto.obtener_productos()
        return render_template("admin/main.html", productos=productos, usuario=g.user)


@admin.before_request
def verificacion_usuario_logueado():
    user = session.get("admin.auth")
    endpoints_publicos = {"admin.home", "admin.auth.login"}
    if user is not None and time.time() >= user.get("expiraEn", 0):
        session.pop("admin.auth", None)
        flash("La sesión administrativa expiró después de 30 minutos.", "warning")
        return redirect(url_for("admin.auth.login"))
    if user is None and request.endpoint not in endpoints_publicos:
        return redirect(url_for("admin.auth.login"))
    g.user = user
