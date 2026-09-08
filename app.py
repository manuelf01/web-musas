import os
from datetime import timedelta

from flask import Flask, request, session

from controllers.admin import *
from controllers.cliente import *
from controllers.autenticacion import *
from controllers.admin_productos import *
from controllers.admin_categoria_producto import *
from controllers.admin_usuarios import *
from controllers.admin_pedidos import *
from controllers.admin_ventas import *
from controllers.admin_perfil import perfil as admin_perfil
from seguridad import (
    campo_csrf, token_csrf, csrf_valido, CAMPO_CSRF,
    REGLA_PASSWORD, PASSWORD_PATTERN,
)

try:
    from cfg import secret_key as _SECRET_KEY
except ImportError:
    _SECRET_KEY = "dev-musas-cambia-esto"

# FLASK_DEBUG=1 para desarrollo; en producción se queda apagado (el depurador
# de Werkzeug permite ejecutar código y NO debe exponerse).
DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

app = Flask(__name__)
app.config.update(
    SECRET_KEY=_SECRET_KEY,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=not DEBUG,   # solo por HTTPS en producción
)

# --- CSRF: token propio de sesión, validado en cada POST del navegador -------
app.jinja_env.globals["campo_csrf"] = campo_csrf
app.jinja_env.globals["csrf_token"] = token_csrf
app.jinja_env.globals["REGLA_PASSWORD"] = REGLA_PASSWORD
app.jinja_env.globals["PASSWORD_PATTERN"] = PASSWORD_PATTERN


@app.before_request
def _proteger_csrf():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    ctype = (request.content_type or "").split(";")[0].strip()
    formularios = ("application/x-www-form-urlencoded", "multipart/form-data", "text/plain", "")
    if ctype not in formularios:
        return
    if not csrf_valido(request.form.get(CAMPO_CSRF) or request.headers.get("X-CSRF-Token")):
        cuerpo = (
            "<!doctype html><meta charset='utf-8'>"
            "<div style=\"font-family:system-ui;max-width:32rem;margin:15vh auto;text-align:center\">"
            "<h2>La sesión expiró</h2>"
            "<p>Por seguridad no pudimos procesar el formulario. Vuelve atrás y envíalo de nuevo.</p>"
            "<a href='javascript:history.back()'>← Volver</a></div>"
        )
        return cuerpo, 400


@app.context_processor
def _inyectar_sesion():
    # Disponible en todas las plantillas: saber si hay un admin logueado
    # mientras navega la tienda (para el header y saltarse el captcha).
    return {"admin_sesion": session.get("admin.auth")}


@app.after_request
def _cabeceras_seguridad(resp):
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    resp.headers.setdefault("Referrer-Policy", "same-origin")
    return resp


admin.register_blueprint(productos)
admin.register_blueprint(categoria_producto)
admin.register_blueprint(usuarios)
admin.register_blueprint(pedidos)
admin.register_blueprint(ventas)
admin.register_blueprint(admin_perfil)
admin.register_blueprint(auth)
cliente.register_blueprint(auth)

app.register_blueprint(admin)
app.register_blueprint(cliente)

# "Recordar sesión en este equipo": duración de la sesión permanente
app.permanent_session_lifetime = timedelta(days=30)

if __name__ == "__main__":
    app.run(debug=DEBUG)
