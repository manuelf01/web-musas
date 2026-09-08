import re
import time

from flask import (
    request,
    render_template,
    redirect,
    Blueprint,
    session,
    url_for,
    flash,
    send_file,
)
from model.Autenticacion import Autenticacion
from seguridad import generar_texto_captcha, generar_imagen_captcha

auth = Blueprint("auth", __name__)

RE_DNI = re.compile(r"^\d{8}$")
RE_TEL = re.compile(r"^\d{9}$")
RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# --- Freno anti fuerza-bruta en el login (en memoria del proceso) ------------
_MAX_INTENTOS = 6
_BLOQUEO_SEG = 300          # 5 minutos
_intentos_login = {}        # ip -> [timestamps de fallos recientes]


def _ip():
    return (request.headers.get("X-Forwarded-For", request.remote_addr) or "?").split(",")[0].strip()


def _login_bloqueado():
    fallos = [t for t in _intentos_login.get(_ip(), []) if time.time() - t < _BLOQUEO_SEG]
    _intentos_login[_ip()] = fallos
    return len(fallos) >= _MAX_INTENTOS


def _registrar_fallo_login():
    _intentos_login.setdefault(_ip(), []).append(time.time())


def _limpiar_fallos_login():
    _intentos_login.pop(_ip(), None)


def _datos_sesion(fila):
    # fila = idUsuario, dni, nombres, apellidos, correo, numTelf, contraseña, tipoUsuario, rol, activo
    rol = fila[8] if len(fila) > 8 and fila[8] else ("usuario" if fila[7] in (1, True) else "administrador")
    return {
        "idUsuario": fila[0],
        "id": fila[0],
        "dni": fila[1],
        "nombres": fila[2],
        "apellidos": fila[3],
        "correo": fila[4],
        "telefono": fila[5],
        "rol": rol,
    }


# ----------------------------------------------------------------------
# LOGIN UNIFICADO
#   Una sola puerta. Se valida DNI + contraseña.
#   - Si el DNI es de un administrador  -> además exige el captcha, va a /admin
#   - Si es un cliente                  -> entra directo a la tienda
# ----------------------------------------------------------------------
def _destino_post_login(defecto):
    """Ruta interna a la que volver tras el login (?next=...), si es segura."""
    destino = request.values.get("next") or ""
    if destino.startswith("/") and not destino.startswith("//"):
        return destino
    return defecto


@auth.route("/login", methods=["GET", "POST"])
def login():
    # El acceso admin antiguo (/admin/login) ahora apunta al login unificado.
    if request.blueprint == "admin.auth":
        return redirect(url_for("cliente.auth.login"))

    if request.method == "POST":
        dni = (request.form.get("usuario") or "").strip()
        contraseña = request.form.get("contraseña") or ""

        def _rerender():
            # Muestra el captcha solo si el DNI es de un administrador.
            es_admin = bool(RE_DNI.match(dni)) and Autenticacion.dni_es_admin(dni)
            return render_template(
                "client/login.html",
                form=request.form.to_dict(),
                mostrar_captcha=es_admin,
                next=request.values.get("next", ""),
            )

        if _login_bloqueado():
            flash("Demasiados intentos fallidos. Espera unos minutos antes de volver a intentar.", "error")
            return _rerender()

        if not RE_DNI.match(dni):
            flash("El DNI debe tener 8 dígitos.", "error")
            return _rerender()
        if not contraseña:
            flash("Ingresa tu contraseña.", "error")
            return _rerender()

        resultado = Autenticacion.login_unificado(dni, contraseña)
        if isinstance(resultado, str):
            _registrar_fallo_login()
            flash(resultado, "error")
            return _rerender()

        fila, tipo = resultado

        # "Recordar sesión en este equipo": sesión permanente (30 días) vs.
        # cookie de sesión que se borra al cerrar el navegador.
        session.permanent = bool(request.form.get("recordar"))

        if tipo == "admin":
            esperado = session.pop("captcha_login", None)
            ingresado = (request.form.get("captcha") or "").strip().upper()
            if not esperado or ingresado != esperado:
                _registrar_fallo_login()
                flash("El código de verificación no coincide. Intenta de nuevo.", "error")
                return _rerender()

            _limpiar_fallos_login()
            session.pop("cliente.auth", None)
            session["admin.auth"] = _datos_sesion(fila)
            return redirect(url_for("admin.home"))

        _limpiar_fallos_login()
        session.pop("admin.auth", None)
        session["cliente.auth"] = _datos_sesion(fila)
        return redirect(_destino_post_login(url_for("cliente.home")))

    return render_template("client/login.html", next=request.args.get("next", ""))


@auth.route("/login/captcha")
def login_captcha():
    """Imagen PNG del captcha. Guarda la respuesta esperada en la sesión."""
    texto = generar_texto_captcha()
    session["captcha_login"] = texto
    respuesta = send_file(generar_imagen_captcha(texto), mimetype="image/png")
    respuesta.headers["Cache-Control"] = "no-store, max-age=0"
    return respuesta


@auth.route("/login/tipo-dni")
def login_tipo_dni():
    """Dice si un DNI corresponde a un administrador (para mostrar el captcha)."""
    dni = (request.args.get("dni") or "").strip()
    es_admin = bool(RE_DNI.match(dni)) and Autenticacion.dni_es_admin(dni)
    return {"admin": es_admin}


# ----------------------------------------------------------------------
# REGISTRO (solo clientes)
# ----------------------------------------------------------------------
@auth.route("/registro", methods=["GET", "POST"])
def registro():
    if request.blueprint == "admin.auth":
        return redirect(url_for("cliente.auth.login"))

    if request.method == "POST":
        dni = (request.form.get("dni") or "").strip()
        nombres = (request.form.get("nombres") or "").strip()
        apellidos = (request.form.get("apellidos") or "").strip()
        correo = (request.form.get("correo") or "").strip()
        telefono = (request.form.get("telefono") or "").strip()
        contraseña = request.form.get("contraseña") or ""

        error = None
        if not RE_DNI.match(dni):
            error = "El DNI debe tener 8 dígitos."
        elif not nombres or not apellidos:
            error = "Completa tus nombres y apellidos."
        elif not RE_CORREO.match(correo):
            error = "Ingresa un correo electrónico válido."
        elif not RE_TEL.match(telefono):
            error = "El teléfono debe tener 9 dígitos."
        elif len(contraseña) < 8:
            error = "La contraseña debe tener al menos 8 caracteres."

        if error is None:
            error = Autenticacion.registro(dni, nombres, apellidos, correo, telefono, contraseña)

        if error is None:
            flash("¡Cuenta creada! Ya puedes iniciar sesión.", "ok")
            return redirect(url_for("cliente.auth.login"))

        flash(error, "error")
        return render_template("client/registro.html", form=request.form.to_dict())

    if session.get("cliente.auth"):
        return redirect(url_for("cliente.home"))
    return render_template("client/registro.html")


# ----------------------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------------------
@auth.route("/logout")
def logout():
    # El carrito vive en localStorage del navegador (no en la sesión): al cerrar
    # sesión se pide limpiarlo para que no quede a la vista del siguiente que use
    # el equipo. La plantilla base consume esta marca una sola vez.
    session["limpiar_carrito"] = True
    if request.blueprint == "admin.auth":
        session.pop("admin.auth", None)
        return redirect(url_for("cliente.auth.login"))
    session.pop("cliente.auth", None)
    return redirect(url_for("cliente.home"))
