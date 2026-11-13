from datetime import date
from decimal import Decimal, InvalidOperation

from bd import obtener_conexion
from dinero import dinero
from negocio import ahora_peru
from model.Inventario import Inventario, ALMACEN_PRINCIPAL
from model.Insumos import Insumos


class Proveedor:
    @staticmethod
    def listar(solo_activos=False):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idProveedor,ruc,razonSocial,contacto,telefono,correo,direccion,activo,"
                    "fechaRegistro FROM proveedor" + (" WHERE activo=1" if solo_activos else "") +
                    " ORDER BY razonSocial")
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{"id": f[0], "ruc": f[1] or "", "nombre": f[2], "contacto": f[3] or "",
                 "telefono": f[4] or "", "correo": f[5] or "", "direccion": f[6] or "",
                 "activo": bool(f[7]), "fecha": f[8]} for f in filas]

    @staticmethod
    def guardar(nombre, ruc=None, contacto=None, telefono=None, correo=None,
                direccion=None, id_proveedor=None):
        nombre = (nombre or "").strip()
        ruc = (ruc or "").strip() or None
        if len(nombre) < 2 or (ruc and (len(ruc) != 11 or not ruc.isdigit())):
            return "datos_invalidos"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if id_proveedor:
                    cursor.execute(
                        "UPDATE proveedor SET ruc=%s,razonSocial=%s,contacto=%s,telefono=%s,correo=%s,"
                        "direccion=%s WHERE idProveedor=%s",
                        (ruc, nombre[:180], (contacto or "")[:150] or None,
                         (telefono or "")[:20] or None, (correo or "")[:150] or None,
                         (direccion or "")[:220] or None, id_proveedor))
                    if cursor.rowcount != 1:
                        return "no_existe"
                else:
                    cursor.execute(
                        "INSERT INTO proveedor(ruc,razonSocial,contacto,telefono,correo,direccion,activo,"
                        "fechaRegistro) VALUES(%s,%s,%s,%s,%s,%s,1,%s)",
                        (ruc, nombre[:180], (contacto or "")[:150] or None,
                         (telefono or "")[:20] or None, (correo or "")[:150] or None,
                         (direccion or "")[:220] or None, ahora_peru().replace(tzinfo=None)))
            conexion.commit()
            return "ok"
        except Exception as exc:
            conexion.rollback()
            if getattr(exc, "args", [None])[0] == 1062:
                return "ruc_duplicado"
            raise
        finally:
            conexion.close()

    @staticmethod
    def cambiar_estado(id_proveedor, activo):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE proveedor SET activo=%s WHERE idProveedor=%s",
                               (1 if activo else 0, id_proveedor))
            conexion.commit()
            return "ok" if cursor.rowcount == 1 else "no_existe"
        finally:
            conexion.close()


class Compra:
    @staticmethod
    def crear(id_proveedor, documento, fecha_documento, lineas, id_usuario,
              observaciones=None, id_almacen=ALMACEN_PRINCIPAL, insumos=None):
        documento = (documento or "").strip()
        try:
            fecha_documento = date.fromisoformat(str(fecha_documento))
            limpias = []
            for linea in lineas:
                if not str(linea.get("idProducto") or "").strip():
                    continue
                cantidad = int(linea["cantidad"])
                costo = dinero(linea["costo"])
                producto = int(linea["idProducto"])
                if cantidad <= 0 or costo < 0:
                    raise ValueError
                limpias.append((producto, cantidad, costo))
            limpias_insumo = []
            for linea in (insumos or []):
                if not str(linea.get("idInsumo") or "").strip():
                    continue
                cantidad = Decimal(str(linea["cantidad"]))
                costo = Decimal(str(linea["costo"])).quantize(Decimal("0.0001"))
                id_insumo = int(linea["idInsumo"])
                if cantidad <= 0 or costo < 0:
                    raise ValueError
                limpias_insumo.append((id_insumo, cantidad, costo))
        except (TypeError, ValueError, KeyError, InvalidOperation):
            return "datos_invalidos"
        if (len({p for p, _, _ in limpias}) != len(limpias)
                or len({i for i, _, _ in limpias_insumo}) != len(limpias_insumo)):
            return "linea_duplicada"
        if not documento or (not limpias and not limpias_insumo):
            return "datos_invalidos"
        total = sum((dinero(cantidad * costo) for _, cantidad, costo in limpias), dinero(0))
        total += sum((dinero(cantidad * costo) for _, cantidad, costo in limpias_insumo), dinero(0))
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO compra(idProveedor,idAlmacen,documento,fechaDocumento,total,estado,"
                    "observaciones,idUsuarioRegistro) VALUES(%s,%s,%s,%s,%s,'borrador',%s,%s)",
                    (id_proveedor, id_almacen, documento[:100], fecha_documento, total,
                     (observaciones or "")[:500] or None, id_usuario))
                id_compra = cursor.lastrowid
                for producto, cantidad, costo in limpias:
                    cursor.execute(
                        "INSERT INTO detalleCompra(idCompra,idProducto,cantidad,costoUnitario,subtotal) "
                        "VALUES(%s,%s,%s,%s,%s)",
                        (id_compra, producto, cantidad, costo, dinero(cantidad * costo)))
                for id_insumo, cantidad, costo in limpias_insumo:
                    cursor.execute(
                        "INSERT INTO detalleCompraInsumo(idCompra,idInsumo,cantidad,costoUnitario,subtotal) "
                        "VALUES(%s,%s,%s,%s,%s)",
                        (id_compra, id_insumo, cantidad, costo, dinero(cantidad * costo)))
            conexion.commit()
            return id_compra
        except Exception as exc:
            conexion.rollback()
            if getattr(exc, "args", [None])[0] == 1062:
                return "duplicada"
            raise
        finally:
            conexion.close()

    @staticmethod
    def recibir(id_compra, id_usuario):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT estado,idAlmacen,documento FROM compra WHERE idCompra=%s FOR UPDATE",
                    (id_compra,))
                compra = cursor.fetchone()
                if not compra:
                    return "no_existe"
                if compra[0] != "borrador":
                    return "ya_procesada"
                cursor.execute(
                    "SELECT idProducto,cantidad,costoUnitario FROM detalleCompra WHERE idCompra=%s",
                    (id_compra,))
                for id_producto, cantidad, costo in cursor.fetchall():
                    Inventario.entrada(
                        cursor, id_producto, cantidad, costo, "compra", "compra", id_compra,
                        "Recepción de compra", id_usuario, compra[2], compra[1],
                        f"compra:{id_compra}:recepcion:{id_producto}")
                cursor.execute(
                    "SELECT idInsumo,cantidad,costoUnitario FROM detalleCompraInsumo WHERE idCompra=%s",
                    (id_compra,))
                for id_insumo, cantidad, costo in cursor.fetchall():
                    Insumos.recibir_compra(cursor, id_insumo, cantidad, costo, id_compra,
                                           id_usuario, compra[2], compra[1])
                cursor.execute(
                    "UPDATE compra SET estado='recibida',fechaRecepcion=%s,idUsuarioRecepcion=%s "
                    "WHERE idCompra=%s", (ahora_peru().replace(tzinfo=None), id_usuario, id_compra))
            conexion.commit()
            return "ok"
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def listar():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT c.idCompra,c.documento,c.fechaDocumento,c.fechaRecepcion,c.total,c.estado,"
                    "p.razonSocial,a.nombre,TRIM(CONCAT_WS(' ',u.nombres,u.apellidos)),"
                    "COUNT(DISTINCT dc.idDetalleCompra)+COUNT(DISTINCT di.idDetalleCompraInsumo) FROM compra c JOIN proveedor p ON p.idProveedor=c.idProveedor "
                    "JOIN almacen a ON a.idAlmacen=c.idAlmacen JOIN usuario u ON u.idUsuario=c.idUsuarioRegistro "
                    "LEFT JOIN detalleCompra dc ON dc.idCompra=c.idCompra "
                    "LEFT JOIN detalleCompraInsumo di ON di.idCompra=c.idCompra "
                    "GROUP BY c.idCompra ORDER BY c.idCompra DESC")
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{"id": f[0], "documento": f[1], "fecha": f[2], "recepcion": f[3],
                 "total": float(f[4]), "estado": f[5], "proveedor": f[6], "almacen": f[7],
                 "usuario": f[8], "lineas": f[9]} for f in filas]
