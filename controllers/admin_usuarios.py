import re

from flask import Blueprint, render_template, redirect, request, url_for, g, flash
from model.Usuario import Usuario, ROLES, ETIQUETA_ROL

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
                 or q in u["dni"] or q in (u["correo"] or "").lower()]

    return render_template(
        "admin/usuarios/index.html",
        usuarios=lista, filtro=rol, estado=estado, q=request.args.get("q", ""),
        conteos=Usuario.contar_por_rol(),
        roles=[(r, ETIQUETA_ROL[r]) for r in ROLES],
        sugerencias=sorted({u["nombreCompleto"] for u in todos}
                           | {u["dni"] for u in todos}),
        usuario=g.user,
    )


@usuarios.route("/agregar")
def form_agregar():
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/editar/<id>")
def form_editar(id):
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/guardar", methods=["POST"])
def guardar():
    dni = (request.form.get("dni") or "").strip()
    nombres = (request.form.get("nombres") or "").strip()
    apellidos = (request.form.get("apellidos") or "").strip()
    correo = (request.form.get("correo") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()
    contra = request.form.get("contraseña") or ""
    rol = request.form.get("rol") or "usuario"

    error = None
    if rol not in ROLES:
        error = "Elige un rol válido."
    elif not RE_DNI.match(dni):
        error = "El DNI debe tener 8 dígitos."
    elif not nombres or not apellidos:
        error = "Completa nombres y apellidos."
    elif not RE_CORREO.match(correo):
        error = "Ingresa un correo válido."
    elif not RE_TEL.match(telefono):
        error = "El teléfono debe tener 9 dígitos."
    elif len(contra) < 8:
        error = "La contraseña debe tener al menos 8 caracteres."

    if error is None:
        error = Usuario.insertar_usuario(dni, nombres, apellidos, correo, telefono, contra, None, rol=rol)

    flash(error or f"Cuenta creada ({ETIQUETA_ROL[rol]}).", "error" if error else "ok")
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/actualizar", methods=["POST"])
def actualizar():
    id = request.form["id"]
    objetivo = Usuario.obtener_dict(id)
    if objetivo is None:
        flash("La cuenta no existe.", "error")
        return redirect(url_for("admin.usuarios.home"))
    if objetivo["esSuper"]:
        flash("No puedes editar a otro superusuario. Solo puedes crear uno nuevo.", "error")
        return redirect(url_for("admin.usuarios.home"))

    correo = (request.form.get("correo") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()
    rol = request.form.get("rol") or objetivo["rol"]
    contra = request.form.get("contraseña") or ""

    if correo and not RE_CORREO.match(correo):
        flash("Ingresa un correo válido.", "error")
        return redirect(url_for("admin.usuarios.home"))
    if telefono and not RE_TEL.match(telefono):
        flash("El teléfono debe tener 9 dígitos.", "error")
        return redirect(url_for("admin.usuarios.home"))
    if contra and len(contra) < 8:
        flash("La contraseña debe tener al menos 8 caracteres.", "error")
        return redirect(url_for("admin.usuarios.home"))

    err = Usuario.actualizar_por_admin(id, correo, telefono, rol, contra)
    flash(err or "Cuenta actualizada.", "error" if err else "ok")
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
        flash("Cuenta reactivada." if activar else "Cuenta dada de baja (ya no puede iniciar sesión).", "ok")
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/eliminar", methods=["POST"])
def eliminar():
    id = request.form["id"]
    objetivo = Usuario.obtener_dict(id)
    if objetivo and objetivo["esSuper"]:
        flash("No puedes eliminar a un superusuario.", "error")
        return redirect(url_for("admin.usuarios.home"))
    if g.user and str(g.user.get("idUsuario")) == str(id):
        flash("No puedes eliminar tu propia cuenta.", "error")
        return redirect(url_for("admin.usuarios.home"))
    try:
        Usuario.eliminar_usuario_id(id)
        flash("Cuenta eliminada.", "ok")
    except Exception:
        flash("No se puede eliminar: la cuenta tiene pedidos o comprobantes. Usa «Dar de baja».", "error")
    return redirect(url_for("admin.usuarios.home"))
