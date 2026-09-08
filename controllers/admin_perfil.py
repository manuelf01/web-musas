import re

from flask import Blueprint, render_template, redirect, request, url_for, g, flash, session
from model.Usuario import Usuario
from seguridad import password_valida

perfil = Blueprint("perfil", __name__, url_prefix="/perfil")

RE_DNI = re.compile(r"^\d{8}$")
RE_TEL = re.compile(r"^\d{9}$")
RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@perfil.route("/")
def home():
    datos = Usuario.obtener_dict(g.user["idUsuario"])
    return render_template("admin/perfil/index.html", usuario=g.user, datos=datos)


@perfil.route("/actualizar", methods=["POST"])
def actualizar():
    id = g.user["idUsuario"]
    nombres = (request.form.get("nombres") or "").strip()
    apellidos = (request.form.get("apellidos") or "").strip()
    correo = (request.form.get("correo") or "").strip()
    dni = (request.form.get("dni") or "").strip()
    telefono = (request.form.get("telefono") or "").strip()
    contra = request.form.get("contraseña") or ""
    contra2 = request.form.get("contraseña2") or ""

    error = None
    if dni and not RE_DNI.match(dni):
        error = "El DNI debe tener 8 dígitos."
    elif correo and not RE_CORREO.match(correo):
        error = "Ingresa un correo válido."
    elif telefono and not RE_TEL.match(telefono):
        error = "El teléfono debe tener 9 dígitos."
    elif contra and contra != contra2:
        error = "Las contraseñas nuevas no coinciden."
    elif contra:
        error = password_valida(contra)

    if error is None:
        error = Usuario.actualizar_perfil(id, nombres, apellidos, correo, dni, telefono, contra)

    if error:
        flash(error, "error")
    else:
        # Refresca la sesión con los datos nuevos.
        d = Usuario.obtener_dict(id)
        session["admin.auth"].update({
            "nombres": d["nombres"], "apellidos": d["apellidos"],
            "correo": d["correo"], "dni": d["dni"], "telefono": d["telefono"],
        })
        session.modified = True
        flash("Tus datos se actualizaron.", "ok")
    return redirect(url_for("admin.perfil.home"))
