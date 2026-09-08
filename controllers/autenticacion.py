import secrets
import time

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from model.Autenticacion import Autenticacion


auth = Blueprint("auth", __name__)


def _clave_captcha(accion):
    return f"captcha:{request.blueprint}:{accion}"


def _nuevo_captcha(accion):
    izquierda = secrets.randbelow(8) + 2
    derecha = secrets.randbelow(8) + 1
    session[_clave_captcha(accion)] = str(izquierda + derecha)
    return f"¿Cuánto es {izquierda} + {derecha}?"


def _captcha_valido(accion):
    esperado = session.pop(_clave_captcha(accion), None)
    respuesta = request.form.get("captcha", "").strip()
    return esperado is not None and secrets.compare_digest(esperado, respuesta)


def _datos_sesion(usuario):
    return {
        "nombres": usuario[2],
        "apellidos": usuario[3],
        "id": usuario[0],
        "telefono": usuario[5],
        "dni": usuario[1],
        "idUsuario": usuario[0],
        "nombreUsuario": usuario[8] if len(usuario) > 8 else None,
    }


@auth.route("/login", methods=["GET", "POST"])
def login():
    blueprint_name = request.blueprint

    if request.method == "POST":
        identificador = request.form.get("usuario", "").strip()
        password = request.form.get("contraseña", "")

        if not _captcha_valido("login"):
            flash("La respuesta del CAPTCHA no es correcta. Inténtalo nuevamente.", "danger")
        else:
            usuario = Autenticacion.login(identificador, password, blueprint_name)
            destino = blueprint_name

            # El acceso público también reconoce al personal y lo envía al
            # panel administrativo correspondiente.
            if isinstance(usuario, str) and blueprint_name == "cliente.auth":
                resultado_admin = Autenticacion.login_por_tipo(
                    identificador, password, False
                )
                if isinstance(resultado_admin, list):
                    usuario = resultado_admin
                    destino = "admin.auth"
                elif resultado_admin != Autenticacion.MENSAJE_CREDENCIALES:
                    usuario = resultado_admin

            if not isinstance(usuario, str):
                session.clear()
                datos = _datos_sesion(usuario[0])
                if destino == "admin.auth":
                    datos["expiraEn"] = time.time() + (30 * 60)
                session[destino] = datos
                flash(
                    f"Bienvenido, {datos['nombres']}. Has ingresado correctamente al sistema.",
                    "success",
                )
                return redirect(
                    url_for("cliente.home" if destino == "cliente.auth" else "admin.home")
                )
            flash(usuario, "danger")

    captcha = _nuevo_captcha("login")
    plantilla = "client/login.html" if blueprint_name == "cliente.auth" else "admin/login.html"
    return render_template(plantilla, captcha_pregunta=captcha)


@auth.route("/registro", methods=["GET", "POST"])
def registro():
    blueprint_name = request.blueprint
    if blueprint_name != "cliente.auth":
        return redirect(url_for("admin.home"))
    if session.get("cliente.auth") is not None:
        return redirect(url_for("cliente.home"))

    if request.method == "POST":
        dni = request.form.get("dni", "")
        nombres = request.form.get("nombres", "")
        apellidos = request.form.get("apellidos", "")
        correo = request.form.get("correo", "")
        telefono = request.form.get("telefono", "")
        password = request.form.get("contraseña", "")

        if not _captcha_valido("registro"):
            flash("La respuesta del CAPTCHA no es correcta. Inténtalo nuevamente.", "danger")
        else:
            error = Autenticacion.registro(
                dni, nombres, apellidos, correo, telefono, password
            )
            if error is None:
                flash(
                    f"Registro completado, {nombres.strip()}. Ya puedes iniciar sesión.",
                    "success",
                )
                return redirect(url_for("cliente.auth.login"))
            flash(error, "danger")

    return render_template(
        "client/registro.html", captcha_pregunta=_nuevo_captcha("registro")
    )


@auth.route("/logout", methods=["POST"])
def logout():
    blueprint_name = request.blueprint
    session.pop(blueprint_name, None)
    return redirect(
        url_for("cliente.home" if blueprint_name == "cliente.auth" else "admin.home")
    )
