import re

from flask import Blueprint, render_template, redirect, request, url_for, g, flash, session
from model.Usuario import Usuario
from seguridad import password_valida
from subidas import guardar_avatar, podar_avatares, ruta_avatar_valida
from avisos import ok_deshacer, error_en_formulario

perfil = Blueprint("perfil", __name__, url_prefix="/perfil")

RE_DNI = re.compile(r"^\d{8}$")
RE_TEL = re.compile(r"^\d{9}$")
RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@perfil.route("/")
def home():
    datos = Usuario.obtener_dict(g.user["idUsuario"])
    return render_template("admin/perfil/index.html", usuario=g.user, datos=datos)


@perfil.route("/foto", methods=["POST"])
def foto():
    id = g.user["idUsuario"]
    ruta, error = guardar_avatar(request.files.get("foto"), id)
    if error:
        flash(error, "error")
    else:
        anterior = Usuario.actualizar_foto(id, ruta)
        podar_avatares(id, [ruta, anterior])
        ok_deshacer("Tu foto de perfil se actualizó.", url_for("admin.perfil.restaurar_foto"),
                    {"ruta": anterior or ""})
    return redirect(url_for("admin.perfil.home"))


@perfil.route("/foto/quitar", methods=["POST"])
def quitar_foto():
    id = g.user["idUsuario"]
    anterior = Usuario.actualizar_foto(id, None)
    podar_avatares(id, [anterior])
    if anterior:
        ok_deshacer("Quitaste tu foto de perfil.", url_for("admin.perfil.restaurar_foto"), {"ruta": anterior})
    else:
        flash("Quitaste tu foto de perfil.", "ok")
    return redirect(url_for("admin.perfil.home"))


@perfil.route("/foto/restaurar", methods=["POST"])
def restaurar_foto():
    """«Deshacer» de la foto: vuelve a la anterior (o a las iniciales si no había)."""
    id = g.user["idUsuario"]
    ruta = (request.form.get("ruta") or "").strip()
    if ruta and not ruta_avatar_valida(ruta, id):
        flash("Esa foto ya no está disponible.", "error")
        return redirect(url_for("admin.perfil.home"))
    actual = Usuario.actualizar_foto(id, ruta or None)
    podar_avatares(id, [ruta, actual])
    ok_deshacer("Foto restaurada.", url_for("admin.perfil.restaurar_foto"), {"ruta": actual or ""})
    return redirect(url_for("admin.perfil.home"))


@perfil.route("/actualizar", methods=["POST"])
def actualizar():
    id = g.user["idUsuario"]
    antes = Usuario.obtener_dict(id)
    nombres = (request.form.get("nombres") or "").strip()
    apellidos = (request.form.get("apellidos") or "").strip()
    correo = (request.form.get("correo") or "").strip()
    dni = (request.form.get("dni") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()
    contra = request.form.get("contraseña") or ""
    contra2 = request.form.get("contraseña2") or ""

    error, campo = None, None
    if dni and not RE_DNI.match(dni):
        error = "El DNI debe tener 8 dígitos."
    elif correo and not RE_CORREO.match(correo):
        error = "Ingresa un correo válido."
    elif telefono and not RE_TEL.match(telefono):
        error = "El teléfono debe tener 9 dígitos."
    elif contra and contra != contra2:
        error, campo = "Las contraseñas nuevas no coinciden.", "contraseña2"
    elif contra:
        error = password_valida(contra)

    if error is None:
        error = Usuario.actualizar_perfil(id, nombres, apellidos, correo, dni, telefono, contra)

    if error:
        error_en_formulario(error, "pagina", request.form, campo=campo)
    else:
        # Refresca la sesión con los datos nuevos.
        d = Usuario.obtener_dict(id)
        session["admin.auth"].update({
            "nombres": d["nombres"], "apellidos": d["apellidos"],
            "correo": d["correo"], "dni": d["dni"], "telefono": d["telefono"],
        })
        session.modified = True
        if contra or not antes:
            flash("Tus datos se actualizaron." + (" Tu contraseña cambió." if contra else ""), "ok")
        else:
            ok_deshacer("Tus datos se actualizaron.", url_for("admin.perfil.actualizar"), {
                "nombres": antes["nombres"], "apellidos": antes["apellidos"] or "",
                "correo": antes["correo"], "dni": antes["dni"] or "", "telefono": antes["telefono"] or ""})
    return redirect(url_for("admin.perfil.home"))
