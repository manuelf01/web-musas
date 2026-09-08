from flask import Blueprint, render_template, redirect, request, url_for, g, flash
from model.Usuario import Usuario
usuarios = Blueprint('usuarios', __name__, url_prefix='/usuarios')


@usuarios.route("/")
def home():
    filtro = request.args.get("rol", "todos")
    todos = Usuario.obtener_todos()
    if filtro == "admin":
        lista = [u for u in todos if u["esAdmin"]]
    elif filtro == "cliente":
        lista = [u for u in todos if not u["esAdmin"]]
    else:
        lista = todos
    return render_template(
        "admin/usuarios/index.html",
        usuarios=lista, filtro=filtro,
        conteos=Usuario.contar_por_rol(),
        usuario=g.user,
    )


@usuarios.route("/agregar")
def form_agregar():
    return redirect(url_for("admin.usuarios.home"))


@usuarios.route("/editar/<id>")
def form_editar(id):
    return redirect(url_for("admin.usuarios.home"))


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
