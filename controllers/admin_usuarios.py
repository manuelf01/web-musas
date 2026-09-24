import re

from flask import Blueprint, render_template, redirect, request, url_for, g, flash
from model.Usuario import Usuario, ROLES, ETIQUETA_ROL
from seguridad import password_valida
from paginacion import paginar
from avisos import ok_deshacer, error_en_formulario

usuarios = Blueprint('usuarios', __name__, url_prefix='/usuarios')

RE_DNI = re.compile(r"^\d{8}$")
RE_TEL = re.compile(r"^\d{9}$")
RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@usuarios.route("/")
def home():
    rol = request.args.get("rol", "todos")
    estado = request.args.get("estado", "todos")
    q = (request.args.get("q") or "").strip().lower()

    todos = Usuario.obtener_todos()
    lista = todos
    if rol in ROLES:
        lista = [u for u in lista if u["rol"] == rol]
    if estado == "activos":
        lista = [u for u in lista if u["activo"]]
    elif estado == "baja":
        lista = [u for u in lista if not u["activo"]]
    if q:
        lista = [u for u in lista if q in u["nombreCompleto"].lower()
                 or q in (u["dni"] or "") or q in (u["correo"] or "").lower()]

    lista, pagination, rango = paginar(lista, 10, "cuentas")
    return render_template(
        "admin/usuarios/index.html",
        usuarios=lista, pagination=pagination, rango=rango, filtro=rol, estado=estado, q=request.args.get("q", ""),
        conteos=Usuario.contar_por_rol(),
        roles=[(r, ETIQUETA_ROL[r]) for r in ROLES],
        sugerencias=sorted({u["nombreCompleto"] for u in todos}
                           | {u["dni"] for u in todos if u["dni"]}),
        usuario=g.user,
    )


@usuarios.route("/agregar")
def form_agregar():
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/editar/<id>")
def form_editar(id):
    return redirect(url_for("admin.usuarios.home"))


def _validar_datos(rol, dni, nombres, apellidos, correo, telefono):
    """Reglas de los datos de una cuenta (crear o editar). None si todo está bien."""
    if rol not in ROLES:
        return "Elige un rol válido."
    if rol in ("superusuario", "administrador") and not RE_DNI.match(dni):
        return "Las cuentas del panel requieren un DNI de 8 dígitos."
    if dni and not RE_DNI.match(dni):
        return "Si ingresas un DNI, debe tener 8 dígitos."
    if not nombres or not apellidos:
        return "Completa nombres y apellidos."
    if not RE_CORREO.match(correo):
        return "Ingresa un correo válido."
    if not RE_TEL.match(telefono):
        return "El teléfono debe tener 9 dígitos."
    return None


@usuarios.route("/guardar", methods=["POST"])
def guardar():
    dni = (request.form.get("dni") or "").strip()
    nombres = (request.form.get("nombres") or "").strip()
    apellidos = (request.form.get("apellidos") or "").strip()
    correo = (request.form.get("correo") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()
    contra = request.form.get("contraseña") or ""
    rol = request.form.get("rol") or "usuario"

    error = _validar_datos(rol, dni, nombres, apellidos, correo, telefono)
    if error is None:
        error = password_valida(contra)

    if error is None:
        error = Usuario.insertar_usuario(dni or None, nombres, apellidos, correo, telefono, contra, None, rol=rol)

    if error:
        error_en_formulario(error, "crear", request.form,
                            obligatorios=("nombres", "apellidos", "correo", "telefono"))
    else:
        nuevo = Usuario.id_por_correo(correo)
        mensaje = f"Cuenta creada ({ETIQUETA_ROL[rol]})."
        if nuevo:
            ok_deshacer(mensaje, url_for("admin.usuarios.estado"), {"id": nuevo, "activar": 0})
        else:
            flash(mensaje, "ok")
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/actualizar", methods=["POST"])
def actualizar():
    """El administrador corrige los datos de la cuenta (DNI, nombres, apellidos,
    correo, teléfono), cambia su rol y la da de alta/baja. La contraseña NO se
    toca: solo la cambia cada persona en su perfil."""
    id = request.form["id"]
    objetivo = Usuario.obtener_dict(id)
    if objetivo is None:
        flash("La cuenta no existe.", "error")
        return redirect(url_for("admin.usuarios.home"))
    if objetivo["esSuper"]:
        flash("No puedes editar a otro superusuario. Solo puedes crear uno nuevo.", "error")
        return redirect(url_for("admin.usuarios.home"))

    rol = request.form.get("rol") or objetivo["rol"]
    dni = (request.form.get("dni") or "").strip()
    nombres = (request.form.get("nombres") or "").strip()
    apellidos = (request.form.get("apellidos") or "").strip()
    correo = (request.form.get("correo") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()

    err = _validar_datos(rol, dni, nombres, apellidos, correo, telefono)
    if err is None and rol == "superusuario":
        err = "Para dar rol de superusuario, crea la cuenta desde «Agregar usuario»."
    if err is None:
        err = Usuario.actualizar_datos(id, dni, nombres, apellidos, correo, telefono)
    if err is None:
        err = Usuario.cambiar_rol(id, rol)
    if err is None and str(g.user.get("idUsuario")) != str(id):
        Usuario.cambiar_estado(id, request.form.get("activo", "1") == "1")
    if err:
        error_en_formulario(err, "editar", request.form, id)
    else:
        ok_deshacer("Cuenta actualizada.", url_for("admin.usuarios.actualizar"), {
            "id": id, "rol": objetivo["rol"], "activo": 1 if objetivo["activo"] else 0,
            "dni": objetivo["dni"] or "", "nombres": objetivo["nombres"],
            "apellidos": objetivo["apellidos"] or "", "correo": objetivo["correo"],
            "telefono": objetivo["telefono"] or ""})
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/estado", methods=["POST"])
def estado():
    id = request.form["id"]
    activar = request.form.get("activar") == "1"
    objetivo = Usuario.obtener_dict(id)
    if objetivo is None:
        flash("La cuenta no existe.", "error")
    elif objetivo["esSuper"]:
        flash("No puedes dar de baja a un superusuario.", "error")
    elif str(g.user.get("idUsuario")) == str(id):
        flash("No puedes dar de baja tu propia cuenta.", "error")
    else:
        Usuario.cambiar_estado(id, activar)
        ok_deshacer("Cuenta reactivada." if activar else "Cuenta dada de baja (ya no puede iniciar sesión).",
                    url_for("admin.usuarios.estado"), {"id": id, "activar": 0 if activar else 1})
    return redirect(url_for("admin.usuarios.home"))
