import json
import re

from flask import (
    Blueprint, render_template, session, redirect, url_for, request, flash, send_file,
)
from model.Producto import Producto
from model.CategoriaProducto import CategoriaProducto
from model.Pedido import Pedido, StockInsuficiente, LimitePedidos
from seguridad import generar_texto_captcha, generar_imagen_captcha
cliente = Blueprint('cliente', __name__)

# Categorías cuyo producto admite cremas adicionales.
CATEGORIAS_CON_CREMAS = ("Hamburguesas", "Salchipapas")

RE_DNI = re.compile(r"^\d{8}$")
RE_TEL = re.compile(r"^\d{9}$")
RE_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _cliente_nombre():
    user = session.get("cliente.auth", None)
    return user["nombres"] if user else None


def _identidad():
    """Cualquier sesión autenticada (cliente o admin). Un admin que navega la
    tienda no es un bot: se le puede saltar el captcha del checkout."""
    return session.get("cliente.auth") or session.get("admin.auth")

@cliente.route("/")
def home():
    user = session.get("cliente.auth", None)
    categorias = [c for c in CategoriaProducto.obtener_categorias() if c[1] != "Cremas"]
    return render_template(
        "client/index.html",
        cliente=user["nombres"] if user else None,
        categorias=categorias,
        favoritos=Producto.destacados(4),
        totales=Producto.contar_por_categoria(),
    )

@cliente.route("/productos/<string:categoria>")
def productos_categoria(categoria):
    user = session.get("cliente.auth", None)
    categorias = CategoriaProducto.obtener_categorias()
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
    categorias = CategoriaProducto.obtener_categorias()
    productos = Producto.obtener_productos()

    q = (request.args.get("q") or "").strip()
    if q:
        ql = q.lower()
        productos = [
            p for p in productos
            if ql in p["nombre"].lower() or ql in (p["descripcion"] or "").lower()
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
    propios = session.get("pedidos_propios", [])
    por_sesion = id_pedido in propios
    if not user and not por_sesion:
        flash("No pudimos identificar ese pedido.", "error")
        return redirect(url_for("cliente.mis_pedidos"))

    resultado = Pedido.cancelar_pedido(
        id_pedido,
        id_usuario=user["idUsuario"] if user else None,
        saltar_dueno=por_sesion,
    )
    if resultado == "ok":
        flash(f"Pedido N° {id_pedido} cancelado. Se liberó tu cupo.", "ok")
    elif resultado == "no_permitido":
        flash("Ese pedido no está a tu nombre.", "error")
    else:
        flash("Ese pedido ya no se puede cancelar (en preparación, recogido o vencido).", "error")
    return redirect(url_for("cliente.mis_pedidos"))


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
    if producto is None:
        return redirect(url_for("cliente.home"))
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

    if request.method == "POST":
        return _procesar_compra(user)

    return render_template(
        "client/compra.html",
        cliente=_cliente_nombre(),
        sesion=user,
        invitado=_identidad() is None,
        franjas=Pedido.franjas_recojo(),
    )


@cliente.route("/compra/captcha")
def compra_captcha():
    """Imagen del captcha para el checkout de invitados."""
    texto = generar_texto_captcha()
    session["captcha_compra"] = texto
    resp = send_file(generar_imagen_captcha(texto), mimetype="image/png")
    resp.headers["Cache-Control"] = "no-store, max-age=0"
    return resp


def _recotizar(user, mensaje):
    """Vuelve a mostrar el checkout conservando lo que el usuario ya escribió."""
    flash(mensaje, "error")
    return render_template(
        "client/compra.html",
        cliente=_cliente_nombre(),
        sesion=user,
        invitado=_identidad() is None,
        form=request.form.to_dict(),
        franjas=Pedido.franjas_recojo(),
    )


def _procesar_compra(user):
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
    id_usuario = user["idUsuario"] if user else None

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
    elif _identidad() is None:
        # Invitado sin cuenta: se exige el captcha para frenar pedidos automatizados.
        # Un cliente o admin logueado ya está identificado y se lo salta.
        esperado = session.pop("captcha_compra", None)
        ingresado = (request.form.get("captcha") or "").strip().upper()
        if not esperado or ingresado != esperado:
            error = "El código de verificación no coincide. Escríbelo de nuevo."

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

    # Recordar qué pedidos puede ver este visitante (registrado o invitado).
    propios = session.get("pedidos_propios", [])
    propios.append(id_pedido)
    session["pedidos_propios"] = propios[-20:]
    return redirect(url_for("cliente.pedido_confirmado", id_pedido=id_pedido))


@cliente.route("/pedido-confirmado/<int:id_pedido>")
def pedido_confirmado(id_pedido):
    pedido = Pedido.obtener_pedido_completo(id_pedido)
    if pedido is None:
        return redirect(url_for("cliente.home"))

    # La palabra clave de recojo es sensible: solo la ve quien hizo el pedido
    # (invitado con el pedido en su sesión) o el cliente dueño de la cuenta.
    user = session.get("cliente.auth", None)
    es_propio = id_pedido in session.get("pedidos_propios", [])
    es_dueno = user is not None and pedido.get("idUsuario") == user["idUsuario"]
    if not (es_propio or es_dueno):
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