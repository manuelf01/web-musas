from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from model.Usuario import Usuario
usuarios = Blueprint('usuarios', __name__, url_prefix='/usuarios')


@usuarios.route("/")
def home():
    usuarios = Usuario.obtener_usuarios()
    return render_template("admin/usuarios/index.html", usuarios=usuarios, usuario=g.user)


@usuarios.route("/agregar")
def form_agregar():
    return render_template("admin/usuarios/agregar.html", usuario=g.user)


@usuarios.route("/editar/<id>")
def form_editar(id):
    userUsuario = Usuario.obtener_usuario_id(id)
    if userUsuario is not None:
        return render_template("admin/usuarios/editar.html", usuario=g.user, userUsuario=userUsuario)
    return redirect(url_for('admin.usuarios.home'))


@usuarios.route("/actualizar", methods=["POST"])
def actualizar():
    id = request.form["id"]
    correo = request.form["correo"]
    numTel = request.form["telefono"]
    contra = request.form["contraseña"]
    error = Usuario.actualizar_usuario(correo, numTel, contra, id, False)
    if error:
        flash(error, "danger")
        return redirect(url_for("admin.usuarios.form_editar", id=id))
    flash("Usuario actualizado correctamente.", "success")
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/eliminar", methods=["POST"])
def eliminar():
    id = request.form["id"]
    Usuario.eliminar_usuario_id(id)
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/guardar", methods=["POST"])
def guardar():
    dni = request.form["dni"]
    nombres = request.form["nombres"]
    apellidos = request.form["apellidos"]
    correo = request.form["correo"]
    numTel = request.form["telefono"]
    contra = request.form["contraseña"]
    error = Usuario.insertar_usuario(
        dni, nombres, apellidos, correo, numTel, contra, False
    )
    if error:
        flash(error, "danger")
        return redirect(url_for("admin.usuarios.form_agregar"))
    flash("Administrador creado correctamente.", "success")
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/desbloquear", methods=["POST"])
def desbloquear():
    Usuario.desbloquear_usuario(request.form["id"])
    flash("Cuenta desbloqueada correctamente.", "success")
    return redirect(url_for("admin.usuarios.home"))
