from datetime import date

from flask import Blueprint, flash, g, redirect, render_template, request, url_for

from model.Caja import Caja, ETIQUETAS_MOVIMIENTO
from model.MedioPago import MedioPago
from subidas import borrar_imagen, guardar_imagen


caja = Blueprint("caja", __name__, url_prefix="/caja")
TIPOS_FORMULARIO = (
    ("aporte", "Aporte de caja"), ("gasto", "Gasto de caja chica"),
    ("retiro", "Retiro de efectivo"), ("devolucion", "Devolución"),
    ("ajuste_ingreso", "Ajuste de entrada"), ("ajuste_egreso", "Ajuste de salida"),
)


@caja.route("/")
def home():
    id_sesion = request.args.get("sesion", type=int)
    caja_actual = Caja.actual()
    caja_operativa = Caja.resumen(caja_actual["id"]) if caja_actual else None
    resumen = Caja.resumen(id_sesion) if id_sesion else caja_operativa
    return render_template(
        "admin/caja/index.html", usuario=g.user, caja=resumen,
        caja_actual=caja_actual, caja_operativa=caja_operativa,
        historial=Caja.historial(),
        medios=MedioPago.listar(solo_activos=True), tipos=TIPOS_FORMULARIO)


@caja.route("/movimientos/")
def movimientos():
    caja_actual = Caja.actual()
    id_sesion = request.args.get("sesion", type=int)
    if not id_sesion and caja_actual:
        id_sesion = caja_actual["id"]
    resumen = Caja.resumen(id_sesion) if id_sesion else None
    filas = list(resumen["movimientos"]) if resumen else []

    tipo = (request.args.get("tipo") or "").strip()
    texto = (request.args.get("q") or "").strip().casefold()
    desde_texto = (request.args.get("desde") or "").strip()
    hasta_texto = (request.args.get("hasta") or "").strip()
    try:
        desde = date.fromisoformat(desde_texto) if desde_texto else None
    except ValueError:
        desde = None
    try:
        hasta = date.fromisoformat(hasta_texto) if hasta_texto else None
    except ValueError:
        hasta = None

    if tipo:
        filas = [m for m in filas if m["tipo"] == tipo]
    if desde:
        filas = [m for m in filas if m["fecha"].date() >= desde]
    if hasta:
        filas = [m for m in filas if m["fecha"].date() <= hasta]
    if texto:
        filas = [m for m in filas if texto in " ".join(
            str(m.get(c) or "") for c in
            ("categoria", "concepto", "documento", "usuario", "medio")
        ).casefold()]

    return render_template(
        "admin/caja/movimientos.html", usuario=g.user, caja=resumen,
        caja_actual=caja_actual, historial=Caja.historial(), movimientos=filas,
        medios=MedioPago.listar(solo_activos=True), tipos=TIPOS_FORMULARIO,
        etiquetas=ETIQUETAS_MOVIMIENTO, tipo=tipo, q=request.args.get("q", ""),
        desde=desde_texto, hasta=hasta_texto)


@caja.route("/abrir", methods=["POST"])
def abrir():
    resultado = Caja.abrir(request.form.get("fondo_inicial"), g.user["idUsuario"])
    if resultado == "ok":
        flash("Caja abierta. Ya puedes cobrar pedidos.", "ok")
    elif resultado == "ya_abierta":
        flash("Ya existe una caja abierta.", "error")
    else:
        flash("Ingresa un fondo inicial válido.", "error")
    return redirect(url_for("admin.caja.home"))


@caja.route("/movimiento", methods=["POST"])
def movimiento():
    evidencia = None
    archivo = request.files.get("evidencia")
    if archivo and archivo.filename:
        evidencia = guardar_imagen(archivo, "caja")
        if not evidencia:
            flash("La evidencia debe ser una imagen válida de hasta 5 MB.", "error")
            return redirect(url_for("admin.caja.home"))
    resultado = Caja.registrar_movimiento(
        request.form.get("tipo"), request.form.get("monto"),
        request.form.get("concepto"), request.form.get("medio", type=int),
        g.user["idUsuario"], request.form.get("documento"), evidencia,
        request.form.get("categoria"))
    if resultado != "ok" and evidencia:
        borrar_imagen(evidencia)
    mensajes = {
        "ok": ("Movimiento registrado.", "ok"),
        "caja_cerrada": ("Abre una caja antes de registrar movimientos.", "error"),
        "medio_invalido": ("Para aportes y retiros selecciona el medio Efectivo.", "error"),
        "saldo_insuficiente": ("No hay suficiente efectivo en caja. Registra primero un aporte adicional.", "error"),
    }
    texto, tono = mensajes.get(resultado, ("Revisa el tipo, monto y concepto.", "error"))
    flash(texto, tono)
    destino = "admin.caja.movimientos" if request.form.get("volver") == "movimientos" else "admin.caja.home"
    return redirect(url_for(destino))


@caja.route("/cerrar", methods=["POST"])
def cerrar():
    resultado = Caja.cerrar(request.form.get("efectivo_contado"),
                            request.form.get("observaciones"), g.user["idUsuario"])
    if resultado == "ok":
        flash("Caja cerrada. El cuadre quedó guardado y ya no puede editarse.", "ok")
    elif resultado == "caja_cerrada":
        flash("No hay una caja abierta.", "error")
    else:
        flash("Ingresa un efectivo contado válido.", "error")
    return redirect(url_for("admin.caja.home"))
