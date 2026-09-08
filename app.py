
import collections
import collections.abc
collections.Mapping = collections.abc.Mapping

import os
from datetime import timedelta
from flask import Flask, request, session, jsonify
from flask_jwt import JWT
from flask_swagger_ui import get_swaggerui_blueprint
from Token.usuario import authenticate, identity
from controllers.admin import *
from controllers.cliente import *
from controllers.autenticacion import *
from controllers.admin_productos import *
from controllers.admin_categoria_producto import *
from controllers.admin_usuarios import *
from controllers.admin_pedidos import *
from controllers.admin_ventas import *
# Importando apis
from APIS.productos import *
from APIS.usuarios import api_usuarios
from APIS.registro_pedidos import api_registro_pedidos
from APIS.detalleOrden import api_detalleOrden
from APIS.categoriaProducto import api_categoriaProducto
from APIS.detalleComprobante import api_detalleComprobante
from APIS.detalleCremas import api_detalleCremas
from APIS.comprobante import api_comprobante
from APIS.transacciones import transaccion
from seguridad import campo_csrf, token_csrf, csrf_valido, CAMPO_CSRF

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
jwt = JWT(app, authenticate, identity)

# --- CSRF: token propio de sesión, validado en cada POST del navegador -------
app.jinja_env.globals["campo_csrf"] = campo_csrf
app.jinja_env.globals["csrf_token"] = token_csrf

@app.before_request
def _proteger_csrf():
    if request.method not in ("POST", "PUT", "PATCH", "DELETE"):
        return
    ep = request.endpoint or ""
    # Las APIs JSON (JWT, /api/*) no se pueden falsificar desde otra web sin CORS;
    # el CSRF solo aplica a los tipos que un <form> del navegador puede enviar.
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

# swagger
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI (without trailing '/')
# Our API url (can of course be a local resource)
API_URL = '/static/documentacion.yaml'

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Test application"
    },
    # oauth_config={  # OAuth config. See https://github.com/swagger-api/swagger-ui#oauth2-configuration .
    #    'clientId': "your-client-id",
    #    'clientSecret': "your-client-secret-if-required",
    #    'realm': "your-realms",
    #    'appName': "your-app-name",
    #    'scopeSeparator': " ",
    #    'additionalQueryStringParams': {'test': "hello"}
    # }
)

admin.register_blueprint(productos)
admin.register_blueprint(categoria_producto)
admin.register_blueprint(usuarios)
admin.register_blueprint(pedidos)
admin.register_blueprint(ventas)
admin.register_blueprint(auth)
cliente.register_blueprint(auth)

app.register_blueprint(admin)
app.register_blueprint(cliente)
# Registro de swagger
app.register_blueprint(swaggerui_blueprint)
# Registrando apis
app.register_blueprint(api_productos)
app.register_blueprint(api_usuarios)
app.register_blueprint(api_registro_pedidos)
app.register_blueprint(api_detalleOrden)
app.register_blueprint(api_categoriaProducto)
app.register_blueprint(api_detalleComprobante)
app.register_blueprint(api_detalleCremas)
app.register_blueprint(api_comprobante)
app.register_blueprint(transaccion)

# "Recordar sesión en este equipo": duración de la sesión permanente
app.permanent_session_lifetime = timedelta(days=30)
# Iniciar el servidor

if __name__ == "__main__":
    app.run(debug=DEBUG)

# print(app.url_map)
