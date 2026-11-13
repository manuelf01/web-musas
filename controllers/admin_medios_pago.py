from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from model.MedioPago import MedioPago, TIPOS_MEDIO
from subidas import borrar_imagen, guardar_desde_url, guardar_imagen


medios_pago = Blueprint("medios_pago", __name__, url_prefix="/medios-pago")


@medios_pago.before_request
def _solo_superusuario():
    if g.user.get("rol") != "superusuario":
        flash("Solo el superusuario puede configurar medios de pago.", "error")
        return redirect(url_for("admin.pagos.home"))


@medios_pago.route("/")
def home():
    return render_template("admin/medios_pago/index.html", usuario=g.user,
                           medios=MedioPago.listar(), tipos=TIPOS_MEDIO)


def _imagen():
    archivo = request.files.get("imagen")
    if archivo and archivo.filename:
        return guardar_imagen(archivo, "medios-pago")
    url = (request.form.get("imagen_url") or "").strip()
    return guardar_desde_url(url, "medios-pago") if url else None


@medios_pago.route("/guardar", methods=["POST"])
def guardar():
    id_medio = request.form.get("id", type=int)
    anterior = next((m for m in MedioPago.listar() if m["id"] == id_medio), None)
    nueva_imagen = _imagen()
    if (request.files.get("imagen") and request.files["imagen"].filename or request.form.get("imagen_url")) and not nueva_imagen:
        flash("La imagen del medio no es válida.", "error")
        return redirect(url_for("admin.medios_pago.home"))
    estado_activo = (request.form.get("activo") == "1" if "activo" in request.form
                     else bool(anterior.get("activo", True) if anterior else True))
    error = MedioPago.guardar(
        request.form.get("nombre"), request.form.get("tipo"),
        request.form.get("descuento", "0"), request.form.get("comision", "0"),
        request.form.get("comision_fija", "0"),
        request.form.get("afecta_efectivo") == "1", nueva_imagen, id_medio,
        estado_activo)
    if error:
        if nueva_imagen:
            borrar_imagen(nueva_imagen)
        flash(error, "error")
    else:
        if nueva_imagen and anterior and anterior["imagen"]:
            borrar_imagen(anterior["imagen"])
        flash("Medio de pago actualizado." if id_medio else "Medio de pago creado.", "ok")
    return redirect(url_for("admin.medios_pago.home"))


@medios_pago.route("/estado", methods=["POST"])
def estado():
    id_medio = request.form.get("id", type=int)
    activo = request.form.get("activo") == "1"
    actualizado = bool(id_medio and MedioPago.cambiar_estado(id_medio, activo))
    flash("Estado actualizado." if actualizado
          else "No se encontró el medio de pago.", "ok" if actualizado else "error")
    return redirect(url_for("admin.medios_pago.home"))
