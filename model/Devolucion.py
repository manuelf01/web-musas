from bd import obtener_conexion
from dinero import dinero
from negocio import ahora_peru
from model.Inventario import Inventario, ALMACEN_PRINCIPAL


TIPOS_DEVOLUCION = ("cliente", "proveedor", "anulacion_venta")
CONDICIONES = ("reincorporable", "merma")
RESOLUCIONES = ("reembolso", "cambio", "sin_reembolso")


class Devolucion:
    @staticmethod
    def registrar(tipo, id_producto, cantidad, condicion, resolucion, motivo,
                  id_usuario, id_pedido=None, id_compra=None, id_proveedor=None,
                  documento=None, id_almacen=ALMACEN_PRINCIPAL):
        try:
            id_producto, cantidad = int(id_producto), int(cantidad)
        except (TypeError, ValueError):
            return "datos_invalidos"
        motivo = (motivo or "").strip()
        if (tipo not in TIPOS_DEVOLUCION or condicion not in CONDICIONES or
                resolucion not in RESOLUCIONES or cantidad <= 0 or len(motivo) < 5):
            return "datos_invalidos"
        if tipo in ("cliente", "anulacion_venta") and not id_pedido:
            return "pedido_requerido"
        if tipo == "proveedor" and (not id_proveedor or not id_compra):
            return "proveedor_requerido"

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if id_pedido:
                    cursor.execute("SELECT estadoRecojo FROM registroPedido WHERE idPedido=%s",
                                   (id_pedido,))
                    pedido = cursor.fetchone()
                    if not pedido or not pedido[0]:
                        return "pedido_no_entregado"
                    cursor.execute(
                        "SELECT COALESCE(SUM(dor.cantidad),0)-COALESCE((SELECT SUM(dd.cantidad) "
                        "FROM detalleDevolucionInventario dd JOIN devolucionInventario d "
                        "ON d.idDevolucion=dd.idDevolucion WHERE d.idPedido=%s AND "
                        "dd.idProducto=%s AND d.estado='confirmada'),0) FROM detalleOrden dor "
                        "WHERE dor.idPedido=%s AND dor.idProducto=%s",
                        (id_pedido, id_producto, id_pedido, id_producto))
                    if int(cursor.fetchone()[0]) < cantidad:
                        return "cantidad_invalida"
                if tipo == "proveedor":
                    cursor.execute(
                        "SELECT dc.cantidad-COALESCE((SELECT SUM(dd.cantidad) "
                        "FROM detalleDevolucionInventario dd JOIN devolucionInventario d "
                        "ON d.idDevolucion=dd.idDevolucion WHERE d.idCompra=c.idCompra "
                        "AND dd.idProducto=dc.idProducto AND d.tipo='proveedor' "
                        "AND d.estado='confirmada'),0) FROM compra c JOIN detalleCompra dc "
                        "ON dc.idCompra=c.idCompra WHERE c.idCompra=%s AND c.idProveedor=%s "
                        "AND dc.idProducto=%s AND c.estado='recibida'",
                        (id_compra, id_proveedor, id_producto))
                    disponible_devolver = cursor.fetchone()
                    if not disponible_devolver or int(disponible_devolver[0]) < cantidad:
                        return "cantidad_invalida"
                cursor.execute(
                    "INSERT INTO devolucionInventario(tipo,idPedido,idCompra,idProveedor,resolucion,"
                    "documento,motivo,estado,idUsuario,fechaHora) VALUES(%s,%s,%s,%s,%s,%s,%s,"
                    "'confirmada',%s,%s)",
                    (tipo, id_pedido, id_compra, id_proveedor, resolucion,
                     (documento or "")[:100] or None, motivo[:500], id_usuario,
                     ahora_peru().replace(tzinfo=None)))
                id_devolucion = cursor.lastrowid
                saldo = Inventario._saldo_bloqueado(cursor, id_producto, id_almacen)
                costo = saldo["costo"] if saldo else dinero(0)
                movimiento = None
                if tipo == "proveedor":
                    movimiento = Inventario.salida(
                        cursor, id_producto, cantidad, "devolucion_proveedor", "devolucion",
                        id_devolucion, motivo, id_usuario, documento, id_almacen,
                        f"devolucion:{id_devolucion}:salida:{id_producto}")
                else:
                    movimiento = Inventario.entrada(
                        cursor, id_producto, cantidad, costo, "devolucion_cliente", "devolucion",
                        id_devolucion, motivo, id_usuario, documento, id_almacen,
                        f"devolucion:{id_devolucion}:entrada:{id_producto}")
                    if condicion == "merma":
                        movimiento = Inventario.salida(
                            cursor, id_producto, cantidad, "merma_devolucion", "devolucion",
                            id_devolucion, "Producto devuelto no apto para venta", id_usuario,
                            documento, id_almacen,
                            f"devolucion:{id_devolucion}:merma:{id_producto}")
                cursor.execute(
                    "INSERT INTO detalleDevolucionInventario(idDevolucion,idProducto,cantidad,"
                    "condicionProducto,costoUnitario,idMovimientoInventario) VALUES(%s,%s,%s,%s,%s,%s)",
                    (id_devolucion, id_producto, cantidad, condicion, costo, movimiento))
            conexion.commit()
            return "ok"
        except ValueError as exc:
            conexion.rollback()
            return str(exc)
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def revertir(id_devolucion, motivo, id_usuario):
        motivo = (motivo or "").strip()
        if len(motivo) < 5:
            return "motivo_invalido"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT tipo,estado,documento FROM devolucionInventario WHERE idDevolucion=%s FOR UPDATE",
                    (id_devolucion,))
                cabecera = cursor.fetchone()
                if not cabecera:
                    return "no_existe"
                if cabecera[1] != "confirmada":
                    return "ya_revertida"
                cursor.execute(
                    "SELECT idProducto,cantidad,condicionProducto,costoUnitario,idMovimientoInventario "
                    "FROM detalleDevolucionInventario WHERE idDevolucion=%s", (id_devolucion,))
                for producto, cantidad, condicion, costo, movimiento in cursor.fetchall():
                    if cabecera[0] == "proveedor":
                        Inventario.entrada(
                            cursor, producto, cantidad, costo, "reversion_devolucion", "devolucion",
                            id_devolucion, motivo, id_usuario, cabecera[2], clave_operacion=
                            f"devolucion:{id_devolucion}:reversion:{producto}",
                            id_movimiento_reversion=movimiento)
                    elif condicion == "reincorporable":
                        Inventario.salida(
                            cursor, producto, cantidad, "reversion_devolucion", "devolucion",
                            id_devolucion, motivo, id_usuario, cabecera[2], clave_operacion=
                            f"devolucion:{id_devolucion}:reversion:{producto}",
                            id_movimiento_reversion=movimiento)
                    # Una devolución con merma tuvo efecto neto cero. Se conserva
                    # su doble movimiento y solo se revierte documentalmente.
                cursor.execute(
                    "UPDATE devolucionInventario SET estado='revertida',motivo=CONCAT(motivo,%s) "
                    "WHERE idDevolucion=%s", (" | Reversión: " + motivo[:250], id_devolucion))
            conexion.commit()
            return "ok"
        except ValueError as exc:
            conexion.rollback()
            return str(exc)
        finally:
            conexion.close()

    @staticmethod
    def listar():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT d.idDevolucion,d.tipo,d.idPedido,d.idCompra,d.resolucion,d.documento,"
                    "d.motivo,d.estado,d.fechaHora,TRIM(CONCAT_WS(' ',u.nombres,u.apellidos)),"
                    "p.nombre,dd.cantidad,dd.condicionProducto,pr.razonSocial "
                    "FROM devolucionInventario d JOIN usuario u ON u.idUsuario=d.idUsuario "
                    "JOIN detalleDevolucionInventario dd ON dd.idDevolucion=d.idDevolucion "
                    "JOIN producto p ON p.idProducto=dd.idProducto "
                    "LEFT JOIN proveedor pr ON pr.idProveedor=d.idProveedor "
                    "ORDER BY d.idDevolucion DESC")
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{"id": f[0], "tipo": f[1], "pedido": f[2], "compra": f[3],
                 "resolucion": f[4], "documento": f[5] or "", "motivo": f[6],
                 "estado": f[7], "fecha": f[8], "usuario": f[9], "producto": f[10],
                 "cantidad": f[11], "condicion": f[12], "proveedor": f[13] or ""}
                for f in filas]
