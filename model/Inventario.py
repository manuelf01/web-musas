from decimal import Decimal, ROUND_HALF_UP

from bd import obtener_conexion
from dinero import dinero
from negocio import ahora_peru


ALMACEN_PRINCIPAL = 1


def _costo(valor):
    return Decimal(str(valor or 0)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


class Inventario:
    """Servicio único para cambiar saldos y escribir el Kardex."""

    @staticmethod
    def registrar(cursor, id_producto, tipo, cantidad, anterior, posterior,
                  referencia_tipo=None, id_referencia=None, motivo=None,
                  id_usuario=None, costo_unitario=None, id_almacen=ALMACEN_PRINCIPAL,
                  reservado_anterior=0, reservado_posterior=0, documento=None,
                  clave_operacion=None, id_movimiento_reversion=None):
        costo = _costo(costo_unitario) if costo_unitario not in (None, "") else None
        cursor.execute(
            "INSERT INTO movimientoInventario(idProducto,idAlmacen,tipo,cantidad,stockAnterior,"
            "stockPosterior,stockReservadoAnterior,stockReservadoPosterior,costoUnitario,costoTotal,"
            "referenciaTipo,idReferencia,documento,claveOperacion,idMovimientoReversion,motivo,"
            "idUsuario,fechaHora) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (id_producto, id_almacen, tipo, abs(int(cantidad)), int(anterior), int(posterior),
             int(reservado_anterior), int(reservado_posterior), costo,
             dinero(costo * abs(int(cantidad))) if costo is not None else None,
             referencia_tipo, id_referencia, (documento or "")[:100] or None,
             clave_operacion, id_movimiento_reversion, (motivo or "")[:255] or None,
             id_usuario, ahora_peru().replace(tzinfo=None)))
        return cursor.lastrowid

    @staticmethod
    def _saldo_bloqueado(cursor, id_producto, id_almacen=ALMACEN_PRINCIPAL):
        cursor.execute(
            "INSERT IGNORE INTO inventarioSaldo(idProducto,idAlmacen,stockFisico,stockReservado,"
            "costoPromedio,version,fechaActualizacion) "
            "SELECT idProducto,%s,existencias,0,0,0,%s FROM producto WHERE idProducto=%s",
            (id_almacen, ahora_peru().replace(tzinfo=None), id_producto))
        cursor.execute(
            "SELECT stockFisico,stockReservado,costoPromedio,version FROM inventarioSaldo "
            "WHERE idProducto=%s AND idAlmacen=%s FOR UPDATE", (id_producto, id_almacen))
        fila = cursor.fetchone()
        return ({"fisico": int(fila[0]), "reservado": int(fila[1]),
                 "costo": _costo(fila[2]), "version": int(fila[3])} if fila else None)

    @staticmethod
    def _guardar_saldo(cursor, id_producto, saldo, id_almacen=ALMACEN_PRINCIPAL):
        disponible = int(saldo["fisico"]) - int(saldo["reservado"])
        if saldo["fisico"] < 0 or saldo["reservado"] < 0 or disponible < 0:
            raise ValueError("saldo_invalido")
        cursor.execute(
            "UPDATE inventarioSaldo SET stockFisico=%s,stockReservado=%s,costoPromedio=%s,"
            "version=version+1,fechaActualizacion=%s WHERE idProducto=%s AND idAlmacen=%s",
            (saldo["fisico"], saldo["reservado"], saldo["costo"],
             ahora_peru().replace(tzinfo=None), id_producto, id_almacen))
        cursor.execute("UPDATE producto SET existencias=%s WHERE idProducto=%s",
                       (disponible, id_producto))

    @staticmethod
    def reservar(cursor, id_producto, cantidad, id_pedido, id_usuario=None,
                 id_almacen=ALMACEN_PRINCIPAL):
        cantidad = int(cantidad)
        saldo = Inventario._saldo_bloqueado(cursor, id_producto, id_almacen)
        if not saldo or cantidad <= 0 or saldo["fisico"] - saldo["reservado"] < cantidad:
            return False
        reservado_anterior = saldo["reservado"]
        saldo["reservado"] += cantidad
        Inventario._guardar_saldo(cursor, id_producto, saldo, id_almacen)
        Inventario.registrar(
            cursor, id_producto, "reserva_pedido", cantidad, saldo["fisico"], saldo["fisico"],
            "pedido", id_pedido, "Stock reservado al confirmar el pedido", id_usuario,
            saldo["costo"], id_almacen, reservado_anterior, saldo["reservado"],
            clave_operacion=f"pedido:{id_pedido}:reserva:{id_producto}")
        return True

    @staticmethod
    def liberar_reserva(cursor, id_producto, cantidad, id_pedido, tipo, motivo,
                        id_usuario=None, id_almacen=ALMACEN_PRINCIPAL):
        cantidad = int(cantidad)
        saldo = Inventario._saldo_bloqueado(cursor, id_producto, id_almacen)
        if not saldo or cantidad <= 0 or saldo["reservado"] < cantidad:
            raise ValueError("reserva_insuficiente")
        reservado_anterior = saldo["reservado"]
        saldo["reservado"] -= cantidad
        Inventario._guardar_saldo(cursor, id_producto, saldo, id_almacen)
        return Inventario.registrar(
            cursor, id_producto, tipo, cantidad, saldo["fisico"], saldo["fisico"],
            "pedido", id_pedido, motivo, id_usuario, saldo["costo"], id_almacen,
            reservado_anterior, saldo["reservado"],
            clave_operacion=f"pedido:{id_pedido}:{tipo}:{id_producto}")

    @staticmethod
    def confirmar_salida(cursor, id_producto, cantidad, id_pedido, id_usuario=None,
                         id_almacen=ALMACEN_PRINCIPAL):
        cantidad = int(cantidad)
        saldo = Inventario._saldo_bloqueado(cursor, id_producto, id_almacen)
        if not saldo or cantidad <= 0 or saldo["reservado"] < cantidad or saldo["fisico"] < cantidad:
            raise ValueError("reserva_insuficiente")
        fisico_anterior, reservado_anterior = saldo["fisico"], saldo["reservado"]
        saldo["fisico"] -= cantidad
        saldo["reservado"] -= cantidad
        Inventario._guardar_saldo(cursor, id_producto, saldo, id_almacen)
        return Inventario.registrar(
            cursor, id_producto, "salida_venta", cantidad, fisico_anterior, saldo["fisico"],
            "pedido", id_pedido, "Salida definitiva al cobrar y entregar", id_usuario,
            saldo["costo"], id_almacen, reservado_anterior, saldo["reservado"],
            clave_operacion=f"pedido:{id_pedido}:salida:{id_producto}")

    @staticmethod
    def entrada(cursor, id_producto, cantidad, costo_unitario, tipo, referencia_tipo,
                id_referencia, motivo, id_usuario, documento=None,
                id_almacen=ALMACEN_PRINCIPAL, clave_operacion=None,
                id_movimiento_reversion=None):
        cantidad = int(cantidad)
        saldo = Inventario._saldo_bloqueado(cursor, id_producto, id_almacen)
        costo_nuevo = saldo["costo"] if saldo and costo_unitario in (None, "") else _costo(costo_unitario)
        if not saldo or cantidad <= 0 or costo_nuevo < 0:
            raise ValueError("datos_invalidos")
        anterior = saldo["fisico"]
        valor_anterior = Decimal(anterior) * saldo["costo"]
        saldo["fisico"] += cantidad
        saldo["costo"] = _costo((valor_anterior + Decimal(cantidad) * costo_nuevo) / saldo["fisico"])
        Inventario._guardar_saldo(cursor, id_producto, saldo, id_almacen)
        return Inventario.registrar(
            cursor, id_producto, tipo, cantidad, anterior, saldo["fisico"], referencia_tipo,
            id_referencia, motivo, id_usuario, costo_nuevo, id_almacen,
            saldo["reservado"], saldo["reservado"], documento, clave_operacion,
            id_movimiento_reversion)

    @staticmethod
    def salida(cursor, id_producto, cantidad, tipo, referencia_tipo, id_referencia,
               motivo, id_usuario, documento=None, id_almacen=ALMACEN_PRINCIPAL,
               clave_operacion=None, id_movimiento_reversion=None):
        cantidad = int(cantidad)
        saldo = Inventario._saldo_bloqueado(cursor, id_producto, id_almacen)
        if not saldo or cantidad <= 0 or saldo["fisico"] - saldo["reservado"] < cantidad:
            raise ValueError("stock_insuficiente")
        anterior = saldo["fisico"]
        saldo["fisico"] -= cantidad
        Inventario._guardar_saldo(cursor, id_producto, saldo, id_almacen)
        return Inventario.registrar(
            cursor, id_producto, tipo, cantidad, anterior, saldo["fisico"], referencia_tipo,
            id_referencia, motivo, id_usuario, saldo["costo"], id_almacen,
            saldo["reservado"], saldo["reservado"], documento, clave_operacion,
            id_movimiento_reversion)

    @staticmethod
    def ajustar(id_producto, nuevo_stock, tipo, motivo, id_usuario, costo_unitario=None,
                id_almacen=ALMACEN_PRINCIPAL):
        if tipo not in ("entrada", "compra", "merma", "ajuste"):
            return "tipo_invalido"
        try:
            nuevo_stock = int(nuevo_stock)
        except (TypeError, ValueError):
            return "stock_invalido"
        if nuevo_stock < 0 or len((motivo or "").strip()) < 3:
            return "datos_invalidos"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                saldo = Inventario._saldo_bloqueado(cursor, id_producto, id_almacen)
                if not saldo:
                    return "no_existe"
                if saldo["fisico"] == nuevo_stock:
                    return "sin_cambio"
                if nuevo_stock < saldo["reservado"]:
                    return "menor_reservado"
                anterior = saldo["fisico"]
                saldo["fisico"] = nuevo_stock
                if costo_unitario not in (None, ""):
                    saldo["costo"] = _costo(costo_unitario)
                Inventario._guardar_saldo(cursor, id_producto, saldo, id_almacen)
                Inventario.registrar(cursor, id_producto, tipo, abs(nuevo_stock - anterior),
                    anterior, nuevo_stock, "ajuste_manual", None, motivo, id_usuario,
                    saldo["costo"], id_almacen, saldo["reservado"], saldo["reservado"])
            conexion.commit()
            return "ok"
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def movimiento_manual(id_producto, cantidad, tipo, motivo, id_usuario,
                          costo_unitario=None, documento=None,
                          id_almacen=ALMACEN_PRINCIPAL):
        if tipo not in ("entrada", "ajuste_entrada", "ajuste_salida", "merma"):
            return "tipo_invalido"
        try:
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            return "datos_invalidos"
        if cantidad <= 0 or len((motivo or "").strip()) < 3:
            return "datos_invalidos"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if tipo in ("entrada", "ajuste_entrada"):
                    Inventario.entrada(
                        cursor, id_producto, cantidad, costo_unitario, tipo, "manual", None,
                        motivo, id_usuario, documento, id_almacen)
                else:
                    Inventario.salida(
                        cursor, id_producto, cantidad, tipo, "manual", None, motivo,
                        id_usuario, documento, id_almacen)
            conexion.commit()
            return "ok"
        except ValueError as exc:
            conexion.rollback()
            return str(exc)
        finally:
            conexion.close()

    @staticmethod
    def saldos(id_almacen=None):
        params, where = [], ""
        if id_almacen:
            where, params = " WHERE s.idAlmacen=%s", [id_almacen]
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT p.idProducto,p.nombre,cp.nombreCategoria,a.idAlmacen,a.nombre,"
                    "s.stockFisico,s.stockReservado,(s.stockFisico-s.stockReservado),"
                    "s.costoPromedio,s.fechaActualizacion,p.activo "
                    "FROM inventarioSaldo s JOIN producto p ON p.idProducto=s.idProducto "
                    "JOIN categoriaProducto cp ON cp.idCategoria=p.idCategoria "
                    "JOIN almacen a ON a.idAlmacen=s.idAlmacen" + where + " ORDER BY p.nombre", params)
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{"idProducto": f[0], "producto": f[1], "categoria": f[2],
                 "idAlmacen": f[3], "almacen": f[4], "fisico": f[5],
                 "reservado": f[6], "disponible": f[7], "costo": float(f[8]),
                 "actualizado": f[9], "activo": bool(f[10])} for f in filas]

    @staticmethod
    def almacenes(solo_activos=True):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT idAlmacen,nombre,direccion,activo FROM almacen" +
                               (" WHERE activo=1" if solo_activos else "") + " ORDER BY nombre")
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{"id": f[0], "nombre": f[1], "direccion": f[2] or "", "activo": bool(f[3])}
                for f in filas]

    @staticmethod
    def kardex(id_producto=None, tipo="", limite=200, id_almacen=None,
               desde=None, hasta=None):
        condiciones, params = [], []
        for expresion, valor in (("mi.idProducto=%s", id_producto), ("mi.tipo=%s", tipo),
                                  ("mi.idAlmacen=%s", id_almacen),
                                  ("DATE(mi.fechaHora)>=%s", desde),
                                  ("DATE(mi.fechaHora)<=%s", hasta)):
            if valor:
                condiciones.append(expresion)
                params.append(valor)
        where = " WHERE " + " AND ".join(condiciones) if condiciones else ""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT mi.idMovimientoInventario,mi.idProducto,p.nombre,cp.nombreCategoria,"
                    "mi.tipo,mi.cantidad,mi.stockAnterior,mi.stockPosterior,mi.costoUnitario,"
                    "mi.referenciaTipo,mi.idReferencia,mi.motivo,mi.fechaHora,"
                    "TRIM(CONCAT_WS(' ',u.nombres,u.apellidos)),a.nombre,"
                    "mi.stockReservadoAnterior,mi.stockReservadoPosterior,mi.documento,"
                    "mi.idMovimientoReversion,mi.claveOperacion "
                    "FROM movimientoInventario mi JOIN producto p ON p.idProducto=mi.idProducto "
                    "JOIN categoriaProducto cp ON cp.idCategoria=p.idCategoria "
                    "JOIN almacen a ON a.idAlmacen=mi.idAlmacen "
                    "LEFT JOIN usuario u ON u.idUsuario=mi.idUsuario" + where +
                    " ORDER BY mi.idMovimientoInventario DESC LIMIT %s", params + [int(limite)])
                filas = cursor.fetchall()
        finally:
            conexion.close()
        etiquetas = {
            "saldo_inicial": "Stock inicial", "reserva_pedido": "Reservado para pedido",
            "liberacion_cancelacion": "Reserva liberada", "devolucion_cancelacion": "Reserva liberada",
            "devolucion_no_show": "Stock devuelto por no recojo", "salida_venta": "Venta entregada",
            "entrada": "Entrada de mercadería", "compra": "Compra recibida",
            "ajuste_entrada": "Ajuste: stock aumentado", "ajuste_salida": "Ajuste: stock reducido",
            "merma": "Merma", "devolucion_cliente": "Devolución de cliente",
            "devolucion_proveedor": "Devolución a proveedor", "merma_devolucion": "Merma de devolución",
            "reversion_devolucion": "Reversión de devolución", "salida_restauracion": "Venta restaurada",
        }
        origenes = {"pedido": "Pedido", "compra": "Compra", "manual": "Movimiento manual",
                    "ajuste_manual": "Ajuste", "carga_inicial": "Carga inicial", "comprobante": "Comprobante"}
        resultado = []
        for f in filas:
            cambio_fisico = int(f[7] or 0) - int(f[6] or 0)
            cambio_reservado = int(f[16] or 0) - int(f[15] or 0)
            if cambio_fisico > 0:
                cambio = f"+{cambio_fisico} unidades"
            elif cambio_fisico < 0:
                cambio = f"{cambio_fisico} unidades"
            elif cambio_reservado > 0:
                cambio = f"{cambio_reservado} reservadas"
            elif cambio_reservado < 0:
                cambio = f"{abs(cambio_reservado)} reserva liberada(s)"
            else:
                cambio = f"{int(f[5] or 0)} unidades"
            ref = origenes.get(f[9], f[9] or "—")
            if f[10]:
                ref += f" #{f[10]}"
            resultado.append({"id": f[0], "idProducto": f[1], "producto": f[2], "categoria": f[3],
                 "tipo": f[4], "tipoTexto": etiquetas.get(f[4], f[4].replace("_", " ").title()),
                 "cambio": cambio, "disponible": int(f[7] or 0) - int(f[16] or 0),
                 "cantidad": f[5], "anterior": f[6], "posterior": f[7],
                 "costo": float(f[8]) if f[8] is not None else None,
                 "referenciaTipo": f[9], "idReferencia": f[10], "motivo": f[11] or "",
                 "fecha": f[12], "usuario": f[13] or "Sistema", "almacen": f[14],
                 "reservadoAnterior": f[15], "reservadoPosterior": f[16],
                 "documento": f[17] or "", "idReversion": f[18],
                 "claveOperacion": f[19], "origenTexto": ref})
        return resultado
