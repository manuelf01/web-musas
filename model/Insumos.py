from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from bd import obtener_conexion
from negocio import ahora_peru


ALMACEN_PRINCIPAL = 1
UNIDADES = ("unidad", "g", "kg", "ml", "l")
CATEGORIAS_BASE = (
    "Carnes", "Panes y masas", "Lácteos y quesos", "Verduras",
    "Salsas y condimentos", "Papas y acompañamientos", "Bebidas", "Empaques", "Otros",
)


def _decimal(valor):
    return Decimal(str(valor or 0)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


class StockInsumoInsuficiente(Exception):
    def __init__(self, nombre, disponible, requerido):
        self.nombre = nombre
        self.disponible = disponible
        self.requerido = requerido
        super().__init__("stock_insumo_insuficiente")


class Insumos:
    """Servicio transaccional para saldos, recetas, reservas y Kardex de insumos."""

    @staticmethod
    def categorias():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT DISTINCT TRIM(categoria) FROM insumo "
                               "WHERE categoria IS NOT NULL AND TRIM(categoria)<>'' ORDER BY categoria")
                registradas = [f[0] for f in cursor.fetchall() if f[0]]
        finally:
            conexion.close()
        resultado, vistas = [], set()
        for categoria in (*CATEGORIAS_BASE, *registradas):
            clave = categoria.casefold()
            if clave not in vistas:
                resultado.append(categoria)
                vistas.add(clave)
        return resultado

    @staticmethod
    def _saldo_bloqueado(cursor, id_insumo, id_almacen=ALMACEN_PRINCIPAL):
        cursor.execute(
            "INSERT IGNORE INTO saldoInsumo(idInsumo,idAlmacen,stockFisico,stockReservado,"
            "costoPromedio,version,fechaActualizacion) VALUES(%s,%s,0,0,0,0,%s)",
            (id_insumo, id_almacen, ahora_peru().replace(tzinfo=None)))
        cursor.execute(
            "SELECT stockFisico,stockReservado,costoPromedio FROM saldoInsumo "
            "WHERE idInsumo=%s AND idAlmacen=%s FOR UPDATE", (id_insumo, id_almacen))
        fila = cursor.fetchone()
        return ({"fisico": _decimal(fila[0]), "reservado": _decimal(fila[1]),
                 "costo": Decimal(str(fila[2] or 0))} if fila else None)

    @staticmethod
    def _guardar_saldo(cursor, id_insumo, saldo, id_almacen):
        if saldo["fisico"] < 0 or saldo["reservado"] < 0 or saldo["reservado"] > saldo["fisico"]:
            raise ValueError("saldo_insumo_invalido")
        cursor.execute(
            "UPDATE saldoInsumo SET stockFisico=%s,stockReservado=%s,costoPromedio=%s,"
            "version=version+1,fechaActualizacion=%s WHERE idInsumo=%s AND idAlmacen=%s",
            (saldo["fisico"], saldo["reservado"], saldo["costo"],
             ahora_peru().replace(tzinfo=None), id_insumo, id_almacen))

    @staticmethod
    def _movimiento(cursor, id_insumo, id_almacen, tipo, cantidad, antes, despues,
                    reservado_antes, reservado_despues, costo, referencia, id_referencia,
                    motivo, id_usuario, documento=None, clave=None):
        cursor.execute(
            "INSERT INTO movimientoInsumo(idInsumo,idAlmacen,tipo,cantidad,stockAnterior,"
            "stockPosterior,reservadoAnterior,reservadoPosterior,costoUnitario,costoTotal,"
            "referenciaTipo,idReferencia,documento,claveOperacion,motivo,idUsuario,fechaHora) "
            "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (id_insumo, id_almacen, tipo, cantidad, antes, despues, reservado_antes,
             reservado_despues, costo, (Decimal(str(costo or 0)) * Decimal(str(cantidad))).quantize(
                 Decimal("0.01"), rounding=ROUND_HALF_UP), referencia, id_referencia,
             (documento or "")[:100] or None, clave, (motivo or "")[:255] or None,
             id_usuario, ahora_peru().replace(tzinfo=None)))
        return cursor.lastrowid

    @staticmethod
    def listar(id_almacen=ALMACEN_PRINCIPAL, q="", estado=""):
        condiciones, params = ["i.activo=1"], [id_almacen]
        if q:
            condiciones.append("(i.nombre LIKE %s OR i.categoria LIKE %s)")
            params.extend([f"%{q}%", f"%{q}%"])
        where = " AND ".join(condiciones)
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT i.idInsumo,i.nombre,i.categoria,i.unidad,i.stockMinimo,"
                    "COALESCE(s.stockFisico,0),COALESCE(s.stockReservado,0),"
                    "COALESCE(s.costoPromedio,0),s.fechaActualizacion "
                    "FROM insumo i LEFT JOIN saldoInsumo s ON s.idInsumo=i.idInsumo "
                    "AND s.idAlmacen=%s WHERE " + where + " ORDER BY i.nombre", params)
                filas = cursor.fetchall()
        finally:
            conexion.close()
        resultado = []
        for f in filas:
            fisico, reservado, minimo = _decimal(f[5]), _decimal(f[6]), _decimal(f[4])
            disponible = fisico - reservado
            bajo = disponible > 0 and disponible <= minimo
            agotado = disponible <= 0
            if estado == "bajo" and not bajo:
                continue
            if estado == "agotado" and not agotado:
                continue
            resultado.append({"id": f[0], "nombre": f[1], "categoria": f[2],
                              "unidad": f[3], "minimo": minimo, "fisico": fisico,
                              "reservado": reservado, "disponible": disponible,
                              "costo": float(f[7] or 0), "actualizado": f[8],
                              "bajo": bajo, "agotado": agotado})
        return resultado

    @staticmethod
    def guardar(nombre, categoria, unidad, minimo, id_insumo=None):
        nombre, categoria = (nombre or "").strip(), (categoria or "General").strip()
        try:
            minimo = _decimal(minimo)
        except (InvalidOperation, TypeError, ValueError):
            return "datos_invalidos"
        if len(nombre) < 2 or unidad not in UNIDADES or minimo < 0:
            return "datos_invalidos"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if id_insumo:
                    cursor.execute("UPDATE insumo SET nombre=%s,categoria=%s,unidad=%s,stockMinimo=%s "
                                   "WHERE idInsumo=%s", (nombre[:120], categoria[:80], unidad, minimo, id_insumo))
                    if cursor.rowcount != 1:
                        return "no_existe"
                else:
                    cursor.execute("INSERT INTO insumo(nombre,categoria,unidad,stockMinimo,activo,fechaRegistro) "
                                   "VALUES(%s,%s,%s,%s,1,%s)",
                                   (nombre[:120], categoria[:80], unidad, minimo,
                                    ahora_peru().replace(tzinfo=None)))
                    id_insumo = cursor.lastrowid
                    cursor.execute("INSERT INTO saldoInsumo(idInsumo,idAlmacen,fechaActualizacion) "
                                   "VALUES(%s,%s,%s)",
                                   (id_insumo, ALMACEN_PRINCIPAL, ahora_peru().replace(tzinfo=None)))
            conexion.commit()
            return "ok"
        except Exception as exc:
            conexion.rollback()
            if getattr(exc, "args", [None])[0] == 1062:
                return "duplicado"
            raise
        finally:
            conexion.close()

    @staticmethod
    def cambiar_estado(id_insumo, activo):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE insumo SET activo=%s WHERE idInsumo=%s",
                               (1 if activo else 0, id_insumo))
            conexion.commit()
            return cursor.rowcount == 1
        finally:
            conexion.close()

    @staticmethod
    def recetas():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT idProducto,nombre,idCategoria FROM producto WHERE activo=1 ORDER BY nombre")
                productos = cursor.fetchall()
                cursor.execute("SELECT idInsumo,nombre,unidad FROM insumo WHERE activo=1 ORDER BY nombre")
                insumos = cursor.fetchall()
                cursor.execute("SELECT r.idProducto,r.tipoUso,r.idInsumo,r.cantidad,i.nombre,i.unidad "
                               "FROM recetaInsumo r JOIN insumo i ON i.idInsumo=r.idInsumo "
                               "ORDER BY r.idProducto,r.tipoUso,i.nombre")
                filas = cursor.fetchall()
        finally:
            conexion.close()
        recetas = {}
        for f in filas:
            recetas.setdefault((f[0], f[1]), []).append(
                {"id": f[2], "cantidad": _decimal(f[3]), "nombre": f[4], "unidad": f[5]})
        return ([{"id": p[0], "nombre": p[1], "categoria": p[2]} for p in productos],
                [{"id": i[0], "nombre": i[1], "unidad": i[2]} for i in insumos], recetas)

    @staticmethod
    def guardar_receta(id_producto, tipo_uso, lineas):
        if tipo_uso not in ("producto", "opcion"):
            return "datos_invalidos"
        limpias, vistos = [], set()
        try:
            for linea in lineas:
                iid, cantidad = int(linea["idInsumo"]), _decimal(linea["cantidad"])
                if iid <= 0 or cantidad <= 0 or iid in vistos:
                    return "datos_invalidos"
                vistos.add(iid)
                limpias.append((iid, cantidad))
        except (TypeError, ValueError, KeyError, InvalidOperation):
            return "datos_invalidos"
        if not limpias:
            return "receta_vacia"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT idProducto FROM producto WHERE idProducto=%s AND activo=1 FOR UPDATE",
                               (id_producto,))
                if not cursor.fetchone():
                    return "producto_no_existe"
                marks = ",".join(["%s"] * len(limpias))
                cursor.execute(f"SELECT COUNT(*) FROM insumo WHERE activo=1 AND idInsumo IN ({marks})",
                               [i[0] for i in limpias])
                if cursor.fetchone()[0] != len(limpias):
                    return "insumo_no_existe"
                cursor.execute("DELETE FROM recetaInsumo WHERE idProducto=%s AND tipoUso=%s",
                               (id_producto, tipo_uso))
                cursor.executemany("INSERT INTO recetaInsumo(idProducto,tipoUso,idInsumo,cantidad) "
                                   "VALUES(%s,%s,%s,%s)",
                                   [(id_producto, tipo_uso, iid, qty) for iid, qty in limpias])
            conexion.commit()
            return "ok"
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def capacidades(id_almacen=ALMACEN_PRINCIPAL):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT p.idProducto,p.nombre,cp.nombreCategoria FROM producto p "
                               "JOIN categoriaProducto cp ON cp.idCategoria=p.idCategoria "
                               "WHERE p.activo=1 ORDER BY cp.nombreCategoria,p.nombre")
                productos = cursor.fetchall()
                cursor.execute("SELECT r.idProducto,i.nombre,i.unidad,r.cantidad,"
                               "COALESCE(s.stockFisico,0)-COALESCE(s.stockReservado,0) "
                               "FROM recetaInsumo r JOIN insumo i ON i.idInsumo=r.idInsumo "
                               "LEFT JOIN saldoInsumo s ON s.idInsumo=i.idInsumo AND s.idAlmacen=%s "
                               "WHERE r.tipoUso='producto' AND i.activo=1 ORDER BY r.idProducto",
                               (id_almacen,))
                filas = cursor.fetchall()
        finally:
            conexion.close()
        por_producto = {}
        for f in filas:
            qty, disponible = _decimal(f[3]), _decimal(f[4])
            maximo = int(disponible // qty) if qty > 0 else 0
            por_producto.setdefault(f[0], []).append(
                {"nombre": f[1], "unidad": f[2], "maximo": maximo})
        salida = []
        for p in productos:
            requisitos = por_producto.get(p[0], [])
            limite = min((r["maximo"] for r in requisitos), default=None)
            limitante = next((r["nombre"] for r in requisitos if r["maximo"] == limite), "")
            salida.append({"idProducto": p[0], "nombre": p[1], "categoria": p[2],
                           "limite": limite, "limitante": limitante,
                           "componentes": len(requisitos)})
        return salida

    @staticmethod
    def movimiento_manual(id_insumo, cantidad, tipo, motivo, id_usuario,
                          costo_unitario=None, documento=None, id_almacen=ALMACEN_PRINCIPAL):
        try:
            cantidad = _decimal(cantidad)
            costo = Decimal(str(costo_unitario or 0)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, TypeError, ValueError):
            return "datos_invalidos"
        if cantidad <= 0 or tipo not in ("entrada", "merma", "ajuste_entrada", "ajuste_salida") \
                or len((motivo or "").strip()) < 3 or costo < 0:
            return "datos_invalidos"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                saldo = Insumos._saldo_bloqueado(cursor, id_insumo, id_almacen)
                if not saldo:
                    return "no_existe"
                anterior, reservado = saldo["fisico"], saldo["reservado"]
                if tipo in ("entrada", "ajuste_entrada"):
                    nuevo = anterior + cantidad
                    costo_nuevo = costo if costo_unitario not in (None, "") else saldo["costo"]
                    if nuevo > 0:
                        saldo["costo"] = ((anterior * saldo["costo"] + cantidad * costo_nuevo) / nuevo).quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP)
                else:
                    if anterior - reservado < cantidad:
                        return "stock_insuficiente"
                    nuevo = anterior - cantidad
                saldo["fisico"] = nuevo
                Insumos._guardar_saldo(cursor, id_insumo, saldo, id_almacen)
                Insumos._movimiento(cursor, id_insumo, id_almacen, tipo, cantidad, anterior, nuevo,
                                    reservado, reservado, saldo["costo"], "manual", None,
                                    motivo, id_usuario, documento)
            conexion.commit()
            return "ok"
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def recibir_compra(cursor, id_insumo, cantidad, costo_unitario, id_compra,
                       id_usuario, documento, id_almacen):
        cantidad, costo_nuevo = _decimal(cantidad), Decimal(str(costo_unitario))
        saldo = Insumos._saldo_bloqueado(cursor, id_insumo, id_almacen)
        if not saldo or cantidad <= 0 or costo_nuevo < 0:
            raise ValueError("datos_insumo_invalidos")
        antes, reservado = saldo["fisico"], saldo["reservado"]
        nuevo = antes + cantidad
        saldo["costo"] = ((antes * saldo["costo"] + cantidad * costo_nuevo) / nuevo).quantize(
            Decimal("0.0001"), rounding=ROUND_HALF_UP)
        saldo["fisico"] = nuevo
        Insumos._guardar_saldo(cursor, id_insumo, saldo, id_almacen)
        Insumos._movimiento(cursor, id_insumo, id_almacen, "compra", cantidad, antes, nuevo,
                            reservado, reservado, costo_nuevo, "compra", id_compra,
                            "Ingreso por recepción de compra", id_usuario, documento,
                            f"compra:{id_compra}:insumo:{id_insumo}")

    @staticmethod
    def reservar_pedido(cursor, id_pedido, id_usuario, lineas, id_almacen=ALMACEN_PRINCIPAL):
        ids_producto = sorted({int(l["idProducto"]) for l in lineas})
        ids_opcion = sorted({int(i) for l in lineas for i in l.get("cremas", [])})
        ids = sorted(set(ids_producto + ids_opcion))
        if not ids:
            return
        marks = ",".join(["%s"] * len(ids))
        cursor.execute("SELECT r.idProducto,r.tipoUso,r.idInsumo,r.cantidad,i.nombre "
                       "FROM recetaInsumo r JOIN insumo i ON i.idInsumo=r.idInsumo "
                       f"WHERE r.idProducto IN ({marks}) AND i.activo=1 "
                       "ORDER BY r.idInsumo FOR UPDATE", ids)
        recetas = cursor.fetchall()
        por_key = {(f[0], f[1]): [] for f in recetas}
        for f in recetas:
            por_key.setdefault((f[0], f[1]), []).append(f)
        requeridos = {}
        nombres = {}
        for linea in lineas:
            mult = int(linea["cantidad"])
            for rec in por_key.get((int(linea["idProducto"]), "producto"), []):
                requeridos[rec[2]] = requeridos.get(rec[2], Decimal("0")) + _decimal(rec[3]) * mult
                nombres[rec[2]] = rec[4]
            for id_opcion in set(map(int, linea.get("cremas", []))):
                for rec in por_key.get((id_opcion, "opcion"), []):
                    requeridos[rec[2]] = requeridos.get(rec[2], Decimal("0")) + _decimal(rec[3]) * mult
                    nombres[rec[2]] = rec[4]
        for id_insumo in sorted(requeridos):
            cantidad = requeridos[id_insumo]
            saldo = Insumos._saldo_bloqueado(cursor, id_insumo, id_almacen)
            disponible = saldo["fisico"] - saldo["reservado"]
            if cantidad <= 0 or disponible < cantidad:
                raise StockInsumoInsuficiente(nombres.get(id_insumo, "Insumo"), disponible, cantidad)
            reservado_antes = saldo["reservado"]
            saldo["reservado"] += cantidad
            Insumos._guardar_saldo(cursor, id_insumo, saldo, id_almacen)
            cursor.execute("INSERT INTO pedidoInsumo(idPedido,idInsumo,idAlmacen,cantidad,costoUnitario,estado) "
                           "VALUES(%s,%s,%s,%s,%s,'reservado')",
                           (id_pedido, id_insumo, id_almacen, cantidad, saldo["costo"]))
            Insumos._movimiento(cursor, id_insumo, id_almacen, "reserva_pedido", cantidad,
                                saldo["fisico"], saldo["fisico"], reservado_antes,
                                saldo["reservado"], saldo["costo"], "pedido", id_pedido,
                                "Apartado para pedido", id_usuario,
                                clave=f"pedido:{id_pedido}:reserva_insumo:{id_insumo}")

    @staticmethod
    def liberar_pedido(cursor, id_pedido, motivo, id_usuario=None):
        cursor.execute("SELECT idInsumo,idAlmacen,cantidad,estado FROM pedidoInsumo "
                       "WHERE idPedido=%s FOR UPDATE", (id_pedido,))
        for id_insumo, id_almacen, cantidad, estado in cursor.fetchall():
            if estado != "reservado":
                continue
            saldo = Insumos._saldo_bloqueado(cursor, id_insumo, id_almacen)
            if saldo["reservado"] < _decimal(cantidad):
                raise ValueError("reserva_insumo_inconsistente")
            antes = saldo["reservado"]
            saldo["reservado"] -= _decimal(cantidad)
            Insumos._guardar_saldo(cursor, id_insumo, saldo, id_almacen)
            Insumos._movimiento(cursor, id_insumo, id_almacen, "liberacion_pedido", cantidad,
                                saldo["fisico"], saldo["fisico"], antes, saldo["reservado"],
                                saldo["costo"], "pedido", id_pedido, motivo, id_usuario,
                                clave=f"pedido:{id_pedido}:liberar_insumo:{id_insumo}")
            cursor.execute("UPDATE pedidoInsumo SET estado='liberado' WHERE idPedido=%s "
                           "AND idInsumo=%s AND idAlmacen=%s AND estado='reservado'",
                           (id_pedido, id_insumo, id_almacen))

    @staticmethod
    def consumir_pedido(cursor, id_pedido, id_usuario=None):
        cursor.execute("SELECT idInsumo,idAlmacen,cantidad,estado,costoUnitario FROM pedidoInsumo "
                       "WHERE idPedido=%s FOR UPDATE", (id_pedido,))
        reservas = cursor.fetchall()
        # Pedidos anteriores a la activación del módulo no tienen snapshot.
        # En el primer envío a cocina se calculan con la receta vigente y se
        # reservan/consumen dentro de la misma transacción.
        if not reservas:
            cursor.execute("SELECT idDetalleOrden,idProducto,cantidad FROM detalleOrden WHERE idPedido=%s",
                           (id_pedido,))
            detalles = cursor.fetchall()
            cursor.execute("SELECT idDetalleOrden,idCrema FROM detalleCremas WHERE idPedido=%s", (id_pedido,))
            opciones = {}
            for id_detalle, id_opcion in cursor.fetchall():
                opciones.setdefault(id_detalle, []).append(id_opcion)
            lineas = [{"idProducto": p, "cantidad": c,
                       "cremas": opciones.get(id_detalle, [])}
                      for id_detalle, p, c in detalles]
            Insumos.reservar_pedido(cursor, id_pedido, id_usuario, lineas)
            cursor.execute("SELECT idInsumo,idAlmacen,cantidad,estado,costoUnitario FROM pedidoInsumo "
                           "WHERE idPedido=%s FOR UPDATE", (id_pedido,))
            reservas = cursor.fetchall()
        for id_insumo, id_almacen, cantidad, estado, costo in reservas:
            if estado != "reservado":
                continue
            saldo = Insumos._saldo_bloqueado(cursor, id_insumo, id_almacen)
            qty = _decimal(cantidad)
            if saldo["reservado"] < qty or saldo["fisico"] < qty:
                raise ValueError("reserva_insumo_inconsistente")
            antes, reservado_antes = saldo["fisico"], saldo["reservado"]
            saldo["fisico"] -= qty
            saldo["reservado"] -= qty
            Insumos._guardar_saldo(cursor, id_insumo, saldo, id_almacen)
            Insumos._movimiento(cursor, id_insumo, id_almacen, "consumo_cocina", qty,
                                antes, saldo["fisico"], reservado_antes, saldo["reservado"],
                                costo, "pedido", id_pedido, "Consumo al iniciar preparación",
                                id_usuario, clave=f"pedido:{id_pedido}:consumo_insumo:{id_insumo}")
            cursor.execute("UPDATE pedidoInsumo SET estado='consumido' WHERE idPedido=%s "
                           "AND idInsumo=%s AND idAlmacen=%s AND estado='reservado'",
                           (id_pedido, id_insumo, id_almacen))

    @staticmethod
    def movimientos(limite=100, id_almacen=ALMACEN_PRINCIPAL):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT m.fechaHora,i.nombre,i.unidad,m.tipo,m.cantidad,m.stockAnterior,"
                               "m.stockPosterior,m.reservadoAnterior,m.reservadoPosterior,m.referenciaTipo,"
                               "m.idReferencia,m.motivo,TRIM(CONCAT_WS(' ',u.nombres,u.apellidos)),a.nombre "
                               "FROM movimientoInsumo m JOIN insumo i ON i.idInsumo=m.idInsumo "
                               "JOIN almacen a ON a.idAlmacen=m.idAlmacen "
                               "LEFT JOIN usuario u ON u.idUsuario=m.idUsuario "
                               "WHERE m.idAlmacen=%s ORDER BY m.idMovimientoInsumo DESC LIMIT %s",
                               (id_almacen, int(limite)))
                filas = cursor.fetchall()
        finally:
            conexion.close()
        etiquetas = {"saldo_inicial": "Stock inicial", "entrada": "Entrada", "ajuste_entrada": "Ajuste de entrada",
                     "ajuste_salida": "Ajuste de salida", "merma": "Merma", "compra": "Compra recibida",
                     "reserva_pedido": "Reservado para pedido", "liberacion_pedido": "Reserva liberada",
                     "consumo_cocina": "Consumido en cocina"}
        return [{"fecha": f[0], "nombre": f[1], "unidad": f[2], "tipo": etiquetas.get(f[3], f[3]),
                 "cantidad": _decimal(f[4]), "antes": _decimal(f[5]), "despues": _decimal(f[6]),
                 "reservadoAntes": _decimal(f[7]), "reservadoDespues": _decimal(f[8]),
                 "disponible": _decimal(f[6]) - _decimal(f[8]),
                 "origen": ("Pedido " + str(f[10])) if f[9] == "pedido" and f[10] else
                           ("Compra " + str(f[10])) if f[9] == "compra" and f[10] else
                           ("Registro manual" if f[9] == "manual" else f[9] or "—"),
                 "motivo": f[11] or "—", "usuario": f[12] or "Sistema", "almacen": f[13]}
                for f in filas]

    @staticmethod
    def consumo_del_dia(fecha, id_almacen=ALMACEN_PRINCIPAL):
        """Consumo de ingredientes atribuido a pedidos enviados a cocina."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT i.nombre,i.unidad,SUM(m.cantidad) "
                    "FROM movimientoInsumo m JOIN insumo i ON i.idInsumo=m.idInsumo "
                    "WHERE m.tipo='consumo_cocina' AND DATE(m.fechaHora)=%s AND m.idAlmacen=%s "
                    "GROUP BY i.idInsumo,i.nombre,i.unidad ORDER BY i.nombre",
                    (fecha, id_almacen))
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{"nombre": f[0], "unidad": f[1], "cantidad": _decimal(f[2])}
                for f in filas]
