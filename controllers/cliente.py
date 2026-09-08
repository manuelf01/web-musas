import json
import re

from flask import (
    Blueprint, render_template, session, redirect, url_for, request, flash,
)
from model.Producto import Producto
from model.CategoriaProducto import CategoriaProducto
from model.Pedido import Pedido, StockInsuficiente, LimitePedidos
from model.Usuario import Usuario
cliente = Blueprint('cliente', __name__)

# Categorías cuyo producto admite cremas adicionales.
CATEGORIAS_CON_CREMAS = ("Hamburguesas", "Salchipapas")

RE_DNI = re.compile(r"^\d{8}$")
RE_TEL = re.compile(r"^\d{9}$")
RE_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
RE_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _cliente_nombre():
    user = session.get("cliente.auth", None)
    return user["nombres"] if user else None


def _ruta_local(destino):
    """True si `destino` es una ruta interna segura para redirigir después del login."""
    return bool(destino) and destino.startswith("/") and not destino.startswith("//")

@cliente.route("/")
def home():
    user = session.get("cliente.auth", None)
    categorias = [c for c in CategoriaProducto.obtener_categorias(solo_activas=True) if c[1] != "Cremas"]
    return render_template(
        "client/index.html",
        cliente=user["nombres"] if user else None,
        categorias=categorias,
        favoritos=Producto.destacados(4),
        totales=Producto.contar_por_categoria(solo_activos=True),
    )

@cliente.route("/productos/<string:categoria>")
def productos_categoria(categoria):
    user = session.get("cliente.auth", None)
    categorias = CategoriaProducto.obtener_categorias(solo_activas=True)
    productos = Producto.getProductosCategoria(categoria)

    orden = request.args.get("orden", "recomendados")
    if orden == "precio-asc":
        productos.sort(key=lambda p: p["precio"])
    elif orden == "precio-desc":
        productos.sort(key=lambda p: p["precio"], reverse=True)
    elif orden == "nombre":
        productos.sort(key=lambda p: p["nombre"].lower())

    return render_template(
        "client/productos.html",
        cliente=user["nombres"] if user else None,
        productos=productos,
        categoria=categoria,
        categorias=categorias,
        orden=orden,
    )

@cliente.route("/carta")
def carta():
    categorias = CategoriaProducto.obtener_categorias(solo_activas=True)
    productos = Producto.obtener_productos(solo_activos=True)
    # Sugerencias para el autocompletado del buscador (nombres + categorías).
    sugerencias = sorted({p["nombre"] for p in productos}
                         | {c[1] for c in categorias if c[1] != "Cremas"})

    q = (request.args.get("q") or "").strip()
    if q:
        ql = q.lower()
        productos = [
            p for p in productos
            if ql in p["nombre"].lower() or ql in (p["descripcion"] or "").lower()
            or ql in (p["nombreCategoria"] or "").lower()
        ]

    orden = request.args.get("orden", "recomendados")
    if orden == "precio-asc":
        productos.sort(key=lambda p: p["precio"] or 0)
    elif orden == "precio-desc":
        productos.sort(key=lambda p: p["precio"] or 0, reverse=True)
    elif orden == "nombre":
        productos.sort(key=lambda p: p["nombre"].lower())

    return render_template(
        "client/carta.html",
        cliente=_cliente_nombre(),
        q=q,
        orden=orden,
        sugerencias=sugerencias,
        categorias=categorias,
        productos=productos,
    )


@cliente.route("/mis-pedidos")
def mis_pedidos():
    user = session.get("cliente.auth", None)
    pedidos = Pedido.historial_cliente(user["idUsuario"]) if user else []
    return render_template(
        "client/mis-pedidos.html",
        cliente=_cliente_nombre(),
        logueado=bool(user),
        pedidos=pedidos,
    )


@cliente.route("/mis-pedidos/<int:id_pedido>/cancelar", methods=["POST"])
def cancelar_pedido(id_pedido):
    user = session.get("cliente.auth", None)
    if not user:
        flash("Inicia sesión para gestionar tus pedidos.", "error")
        return redirect(url_for("cliente.auth.login"))

    resultado = Pedido.cancelar_pedido(id_pedido, id_usuario=user["idUsuario"])
    if resultado == "ok":
        flash(f"Pedido N° {id_pedido} cancelado. Se liberó tu cupo.", "ok")
    elif resultado == "no_permitido":
        flash("Ese pedido no está a tu nombre.", "error")
    elif resultado == "en_preparacion":
        flash("Ese pedido ya entró a cocina y no se puede cancelar. "
              "Si no puedes recogerlo, avísanos por WhatsApp.", "error")
    else:
        flash("Ese pedido ya no se puede cancelar (recogido, cancelado o vencido).", "error")
    return redirect(url_for("cliente.mis_pedidos"))


@cliente.route("/mi-cuenta", methods=["GET", "POST"])
def mi_cuenta():
    user = session.get("cliente.auth", None)
    if not user:
        return redirect(url_for("cliente.auth.login", next=url_for("cliente.mi_cuenta")))

    if request.method == "POST":
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
        elif contra and len(contra) < 8:
            error = "La nueva contraseña debe tener al menos 8 caracteres."
        elif contra and contra != contra2:
            error = "Las contraseñas nuevas no coinciden."
        if error is None:
            error = Usuario.actualizar_perfil(user["idUsuario"], nombres, apellidos, correo, dni, telefono, contra)

        if error:
            flash(error, "error")
        else:
            d = Usuario.obtener_dict(user["idUsuario"])
            session["cliente.auth"].update({
                "nombres": d["nombres"], "apellidos": d["apellidos"],
                "correo": d["correo"], "dni": d["dni"], "telefono": d["telefono"],
            })
            session.modified = True
            flash("Tus datos se actualizaron.", "ok")
        return redirect(url_for("cliente.mi_cuenta"))

    return render_template(
        "client/mi-cuenta.html",
        cliente=_cliente_nombre(),
        datos=Usuario.obtener_dict(user["idUsuario"]),
    )


@cliente.route("/nosotros")
def nosotros():
    return render_template("client/nosotros.html", cliente=_cliente_nombre())


@cliente.route("/libro-de-reclamaciones", methods=["GET", "POST"])
def libro_reclamaciones():
    if request.method == "POST":
        # No se persiste (no hay tabla). Se registra el envío y se confirma.
        if not (request.form.get("nombres") and request.form.get("dni") and request.form.get("detalle")):
            flash("Completa tu nombre, DNI y el detalle del reclamo.", "error")
        else:
            flash("Tu reclamo fue registrado. Te contactaremos en un plazo máximo de 15 días hábiles.", "ok")
            return redirect(url_for("cliente.libro_reclamaciones"))
    return render_template("client/reclamaciones.html", cliente=_cliente_nombre())


@cliente.route("/formulario_registro_cliente")
def formulario_registro_cliente():
     return render_template("client/registro.html")

@cliente.route("/producto/<int:id>")
def comprar_producto(id):
    producto = Producto.obtener_producto_por_id(id)
    if producto is None or not producto.get("activo", True):
        return redirect(url_for("cliente.carta"))
    cremas = (
        Producto.getProductosCategoria("Cremas")
        if producto["nombreCategoria"] in CATEGORIAS_CON_CREMAS
        else []
    )
    return render_template(
        "client/seleccion-producto.html",
        cliente=_cliente_nombre(),
        producto=producto,
        cremas=cremas,
    )

@cliente.route("/carrito")
def pag_carrito():
    return render_template("client/carrito.html", cliente=_cliente_nombre())


@cliente.route("/compra", methods=["GET", "POST"])
def pag_compra():
    user = session.get("cliente.auth", None)

    # Los pedidos son solo de clientes registrados (control de no-shows).
    if user is None:
        flash("Inicia sesión o crea tu cuenta para finalizar el pedido.", "error")
        return redirect(url_for("cliente.auth.login", next=url_for("cliente.pag_compra")))

    if request.method == "POST":
        return _procesar_compra(user)

    return render_template(
        "client/compra.html",
        cliente=_cliente_nombre(),
        sesion=user,
        franjas=Pedido.franjas_recojo(),
    )


def _recotizar(user, mensaje):
    """Vuelve a mostrar el checkout conservando lo que el usuario ya escribió."""
    flash(mensaje, "error")
    return render_template(
        "client/compra.html",
        cliente=_cliente_nombre(),
        sesion=user,
        form=request.form.to_dict(),
        franjas=Pedido.franjas_recojo(),
    )


def _procesar_compra(user):
    if user is None:
        flash("Inicia sesión para finalizar el pedido.", "error")
        return redirect(url_for("cliente.auth.login", next=url_for("cliente.pag_compra")))

    # --- items del carrito (vienen del localStorage, se re-cotizan contra la BD) ---
    try:
        carrito = json.loads(request.form.get("carrito_json") or "[]")
    except ValueError:
        carrito = []
    if not carrito:
        return _recotizar(user, "Tu carrito está vacío. Agrega algo de la carta.")

    ids_prod = [it.get("idProducto") for it in carrito]
    ids_crema = [c for it in carrito for c in (it.get("cremas") or [])]
    precios = Producto.precios_por_ids(ids_prod + ids_crema)

    items = []
    for it in carrito:
        p = precios.get(int(it.get("idProducto", 0)))
        if not p:
            continue
        cantidad = max(1, int(it.get("cantidad", 1)))
        cremas_ids, cremas_extra = [], 0.0
        for cid in (it.get("cremas") or []):
            c = precios.get(int(cid))
            if c:
                cremas_ids.append(int(cid))
                cremas_extra += c["precio"]
        precio_unidad = round(p["precio"] + cremas_extra, 2)
        items.append({
            "idProducto": int(it["idProducto"]),
            "nombre": p["nombre"],
            "precioUnidad": precio_unidad,
            "cantidad": cantidad,
            "precioTotal": round(precio_unidad * cantidad, 2),
            "cremas": cremas_ids,
        })

    if not items:
        return _recotizar(user, "No pudimos procesar los productos del carrito.")

    # --- datos del formulario (editables aunque haya sesión: puede recoger otra persona) ---
    dni = (request.form.get("dni") or "").strip()
    nombres = ((request.form.get("nombres") or "") + " " + (request.form.get("apellidos") or "")).strip()
    telefono = (request.form.get("telefono") or "").strip()
    id_usuario = user["idUsuario"]

    hora = (request.form.get("hora_recojo") or "").strip()
    boleta = bool(request.form.get("boleta"))
    pago_digital = request.form.get("pago") == "digital"
    notas = (request.form.get("notas") or "").strip()[:255]

    error = None
    if not RE_DNI.match(dni):
        error = "El DNI debe tener 8 dígitos."
    elif not nombres:
        error = "Ingresa el nombre de quien recoge."
    elif not RE_TEL.match(telefono):
        error = "El teléfono debe tener 9 dígitos."
    elif not RE_HORA.match(hora):
        error = "Elige una hora de recojo."
    elif not Pedido.franja_disponible(hora):
        error = "Esa franja se llenó o ya pasó. Elige otra."

    if error:
        return _recotizar(user, error)

    try:
        id_pedido, key = Pedido.crear_pedido_completo(
            id_usuario, dni, nombres, telefono, hora, boleta, pago_digital, notas, items
        )
    except StockInsuficiente as e:
        if e.disponible <= 0:
            return _recotizar(user, f"«{e.nombre}» se agotó. Quítalo del carrito para continuar.")
        return _recotizar(user, f"Solo quedan {e.disponible} de «{e.nombre}». Ajusta la cantidad.")
    except LimitePedidos:
        return _recotizar(
            user,
            f"Ya tienes {Pedido.MAX_PEDIDOS_ACTIVOS} pedidos sin recoger. "
            "Recoge o cancela alguno antes de hacer otro.",
        )

    return redirect(url_for("cliente.pedido_confirmado", id_pedido=id_pedido))


@cliente.route("/pedido-confirmado/<int:id_pedido>")
def pedido_confirmado(id_pedido):
    pedido = Pedido.obtener_pedido_completo(id_pedido)
    if pedido is None:
        return redirect(url_for("cliente.home"))

    # La palabra clave de recojo es sensible: solo la ve el cliente dueño del pedido.
    user = session.get("cliente.auth", None)
    if user is None or pedido.get("idUsuario") != user["idUsuario"]:
        return redirect(url_for("cliente.mis_pedidos"))

    return render_template(
        "client/pedido-confirmado.html",
        cliente=_cliente_nombre(),
        pedido=pedido,
    )
# @cliente.route("/<tipo>")
# def verMas(tipo):
#     productos = []
#     if tipo == "simples":
#         productos = Producto.getProductosTipo(1)
#     elif tipo == "mixtas":
#         productos = Producto.getProductosTipo(2)
#     elif tipo == "alopobre":
#         productos = Producto.getProductosTipo(3)
#     elif tipo == "especiales":
#         productos = Producto.getProductosTipo(4)
    
#     return render_template("client/verMas.html", productos = productos)