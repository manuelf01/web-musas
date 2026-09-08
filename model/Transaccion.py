import secrets
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from bd import obtener_conexion
from model.Comprobante import Comprobante
from model.DetalleOrden import DetalleOrden
from model.Pedido import Pedido


class DatosCompraInvalidos(ValueError):
    pass


class Transaccion:
    @staticmethod
    def _entero_positivo(valor, campo):
        try:
            numero = int(valor)
        except (TypeError, ValueError) as exc:
            raise DatosCompraInvalidos(f"{campo} no es válido") from exc
        if numero <= 0:
            raise DatosCompraInvalidos(f"{campo} debe ser mayor que cero")
        return numero

    @classmethod
    def insertarCompra(cls, datos_pedido, productos, usuario_sesion=None):
        if not isinstance(datos_pedido, dict) or not isinstance(productos, list) or not productos:
            raise DatosCompraInvalidos("El pedido debe contener al menos un producto")

        if usuario_sesion:
            id_usuario = usuario_sesion.get("idUsuario")
            dni = str(usuario_sesion.get("dni", "")).strip()
            nombres = str(usuario_sesion.get("nombres", "")).strip()
            telefono = str(usuario_sesion.get("telefono", "")).strip()
        else:
            id_usuario = None
            dni = str(datos_pedido.get("dniNoRegistrado", "")).strip()
            nombres = str(datos_pedido.get("nombres", "")).strip()
            telefono = str(datos_pedido.get("telefono", "")).strip()

        if len(dni) != 8 or not dni.isdigit():
            raise DatosCompraInvalidos("El DNI debe contener 8 dígitos")
        if len(telefono) != 9 or not telefono.isdigit():
            raise DatosCompraInvalidos("El teléfono debe contener 9 dígitos")
        if not nombres:
            raise DatosCompraInvalidos("El nombre es obligatorio")

        try:
            hora_recojo = datetime.strptime(
                str(datos_pedido.get("horaRecojo", "")), "%H:%M"
            ).time()
        except ValueError as exc:
            raise DatosCompraInvalidos("La hora de recojo no es válida") from exc

        estado_boleta = bool(datos_pedido.get("estadoBoleta", False))
        billetera_digital = bool(datos_pedido.get("billeteraDigital", False))
        key_pedido = secrets.token_urlsafe(16)
        conexion = obtener_conexion()

        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO registroPedido(
                        idUsuario, dniNoRegistrado, nombres, numeroTelefono,
                        horaRecojo, estadoBoleta, billeteraDigital, keyPedido
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_usuario,
                        dni,
                        nombres,
                        telefono,
                        hora_recojo,
                        estado_boleta,
                        billetera_digital,
                        key_pedido,
                    ),
                )
                id_pedido = cursor.lastrowid
                total_pedido = Decimal("0.00")

                for item in productos:
                    if not isinstance(item, dict):
                        raise DatosCompraInvalidos("Producto inválido")
                    id_producto = cls._entero_positivo(item.get("idProducto"), "Producto")
                    cantidad = cls._entero_positivo(item.get("cantidad"), "Cantidad")

                    cursor.execute(
                        """
                        SELECT idProducto, nombre, precio, existencias
                        FROM producto
                        WHERE idProducto = %s
                        FOR UPDATE
                        """,
                        (id_producto,),
                    )
                    producto = cursor.fetchone()
                    if producto is None:
                        raise DatosCompraInvalidos(f"El producto {id_producto} no existe")
                    if producto[3] is None or producto[3] < cantidad:
                        raise DatosCompraInvalidos(
                            f"Stock insuficiente para {producto[1]}"
                        )

                    try:
                        precio_unidad = Decimal(str(producto[2])).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    except (InvalidOperation, TypeError) as exc:
                        raise DatosCompraInvalidos(
                            f"El precio de {producto[1]} no es válido"
                        ) from exc
                    precio_total = (precio_unidad * cantidad).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )

                    cursor.execute(
                        """
                        INSERT INTO detalleOrden(
                            idPedido, idProducto, nombreProducto, precioUnidad,
                            cantidad, precioTotal
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            id_pedido,
                            id_producto,
                            producto[1],
                            precio_unidad,
                            cantidad,
                            precio_total,
                        ),
                    )
                    id_detalle = cursor.lastrowid

                    cremas = item.get("cremas", [])
                    if not isinstance(cremas, list):
                        raise DatosCompraInvalidos("La selección de cremas no es válida")
                    for id_crema_sin_validar in set(cremas):
                        id_crema = cls._entero_positivo(id_crema_sin_validar, "Crema")
                        cursor.execute(
                            """
                            SELECT p.idProducto
                            FROM producto p
                            INNER JOIN categoriaProducto c
                                ON c.idCategoria = p.idCategoria
                            WHERE p.idProducto = %s
                              AND LOWER(c.nombreCategoria) = 'cremas'
                            """,
                            (id_crema,),
                        )
                        if cursor.fetchone() is None:
                            raise DatosCompraInvalidos(f"La crema {id_crema} no existe")
                        cursor.execute(
                            """
                            INSERT INTO detalleCremas(idPedido, idCrema, idDetalleOrden)
                            VALUES (%s, %s, %s)
                            """,
                            (id_pedido, id_crema, id_detalle),
                        )

                    cursor.execute(
                        "UPDATE producto SET existencias = existencias - %s WHERE idProducto = %s",
                        (cantidad, id_producto),
                    )
                    total_pedido += precio_total

            conexion.commit()
            return {
                "idPedido": id_pedido,
                "keyPedido": key_pedido,
                "total": float(total_pedido),
            }
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def insertarComprobante(idPedido, keyPedido):
        datos_pedido = Pedido.obtener_dni_pedido(idPedido)
        if datos_pedido is None or not Pedido.validate_key_pedido(idPedido, keyPedido):
            return False

        id_usuario, dni_no_registrado = datos_pedido
        fecha_comprobante = date.today()
        hora_comprobante = datetime.now().time()
        subtotal = Decimal(str(DetalleOrden.obtener_subTotal(idPedido))).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        base = (subtotal / Decimal("1.18")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        igv = subtotal - base
        numero_comprobante = str(Comprobante.obtener_numero_comprobante())
        ordenes = DetalleOrden.obtener_detalle_orden_id_pedido(idPedido)
        conexion = obtener_conexion()

        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO comprobante(
                        idPedido, idUsuario, dniNoRegistrado, fechaComprobante,
                        horaComprobante, subTotal, montoTotal, igv, numeroComprobante
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        idPedido,
                        id_usuario,
                        dni_no_registrado,
                        fecha_comprobante,
                        hora_comprobante,
                        subtotal,
                        subtotal,
                        igv,
                        numero_comprobante,
                    ),
                )
                id_comprobante = cursor.lastrowid

                for orden in ordenes:
                    cursor.execute(
                        """
                        INSERT INTO detalleComprobante(
                            idComprobante, idProducto, nombreProducto,
                            precioUnidad, cantidad, precioTotal
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            cantidad = cantidad + VALUES(cantidad),
                            precioTotal = precioTotal + VALUES(precioTotal)
                        """,
                        (
                            id_comprobante,
                            orden[2],
                            orden[3],
                            orden[4],
                            orden[5],
                            orden[6],
                        ),
                    )
                cursor.execute(
                    "UPDATE registroPedido SET estadoRecojo = %s WHERE idPedido = %s",
                    (True, idPedido),
                )
            conexion.commit()
            return True
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()
