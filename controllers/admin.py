from flask import Blueprint, render_template, session, g, redirect, url_for
from model.Producto import Producto
from model.Pedido import Pedido

admin = Blueprint('admin', __name__, url_prefix='/admin')


@admin.route("/")
def home():
    resumen = Pedido.resumen_dashboard()
    return render_template("admin/dashboard.html", usuario=g.user, resumen=resumen)


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
