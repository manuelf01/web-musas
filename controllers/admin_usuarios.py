from flask import Blueprint, render_template, redirect, request, url_for, g, flash
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
    Usuario.actualizar_usuario(correo, numTel, contra, id, False)
    flash("Datos del administrador actualizados.", "ok")
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/eliminar", methods=["POST"])
def eliminar():
    id = request.form["id"]
    if g.user and str(g.user.get("idUsuario")) == str(id):
        flash("No puedes eliminar tu propia cuenta mientras la usas.", "error")
        return redirect(url_for("admin.usuarios.home"))
    try:
        Usuario.eliminar_usuario_id(id)
        flash("Administrador eliminado.", "ok")
    except Exception:
        flash("No se puede eliminar: el usuario tiene pedidos o comprobantes asociados.", "error")
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/guardar", methods=["POST"])
def guardar():
    dni = request.form["dni"]
    nombres = request.form["nombres"]
    apellidos = request.form["apellidos"]
    correo = request.form["correo"]
    numTel = request.form["telefono"]
    contra = request.form["contraseña"]
    if Usuario.existe_dni(dni):
        flash("Ese DNI ya está registrado.", "error")
        return redirect(url_for("admin.usuarios.form_agregar"))
    Usuario.insertar_usuario(dni, nombres, apellidos, correo, numTel, contra, False)
    flash("Administrador creado.", "ok")
    return redirect(url_for("admin.usuarios.home"))
