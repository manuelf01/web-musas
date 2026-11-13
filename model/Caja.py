from bd import obtener_conexion
from dinero import dinero
from negocio import ahora_peru


TIPOS_MOVIMIENTO = (
    "aporte", "gasto", "retiro", "devolucion", "ajuste_ingreso", "ajuste_egreso",
    # Compatibilidad con movimientos creados antes de separar aportes y gastos.
    "ingreso", "egreso",
)
TIPOS_ENTRADA = ("aporte", "ingreso", "ajuste_ingreso")
TIPOS_SALIDA = ("gasto", "egreso", "retiro", "devolucion", "ajuste_egreso")
ETIQUETAS_MOVIMIENTO = {
    "aporte": "Aporte de caja", "gasto": "Gasto de caja chica",
    "retiro": "Retiro de efectivo", "devolucion": "Devolución",
    "ajuste_ingreso": "Ajuste de entrada", "ajuste_egreso": "Ajuste de salida",
    "ingreso": "Ingreso anterior", "egreso": "Gasto anterior",
}


class Caja:
    @staticmethod
    def abierta_cursor(cursor, bloquear=False):
        cursor.execute(
            "SELECT idSesionCaja,fechaApertura,idUsuarioApertura,fondoInicial "
            "FROM sesionCaja WHERE estado='abierta' ORDER BY idSesionCaja DESC LIMIT 1" +
            (" FOR UPDATE" if bloquear else ""))
        fila = cursor.fetchone()
        return ({"id": fila[0], "fechaApertura": fila[1], "idUsuario": fila[2],
                 "fondoInicial": float(fila[3])} if fila else None)

    @staticmethod
    def actual():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                return Caja.abierta_cursor(cursor)
        finally:
            conexion.close()

    @staticmethod
    def abrir(fondo_inicial, id_usuario):
        try:
            fondo = dinero(fondo_inicial)
        except Exception:
            return "monto_invalido"
        if fondo < 0:
            return "monto_invalido"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if Caja.abierta_cursor(cursor, bloquear=True):
                    return "ya_abierta"
                cursor.execute(
                    "INSERT INTO sesionCaja(fechaApertura,idUsuarioApertura,fondoInicial,estado) "
                    "VALUES(%s,%s,%s,'abierta')",
                    (ahora_peru().replace(tzinfo=None), id_usuario, fondo))
            conexion.commit()
            return "ok"
        finally:
            conexion.close()

    @staticmethod
    def registrar_movimiento(tipo, monto, concepto, id_medio, id_usuario,
                             documento=None, evidencia=None, categoria="General"):
        if tipo not in TIPOS_MOVIMIENTO:
            return "tipo_invalido"
        try:
            monto = dinero(monto)
        except Exception:
            return "monto_invalido"
        concepto = (concepto or "").strip()
        categoria = (categoria or "General").strip()[:60]
        if monto <= 0 or len(concepto) < 3 or not categoria:
            return "datos_invalidos"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                sesion = Caja.abierta_cursor(cursor, bloquear=True)
                if not sesion:
                    return "caja_cerrada"
                cursor.execute("SELECT afectaEfectivo FROM medioPago WHERE idMedioPago=%s AND activo=1", (id_medio,))
                fila_medio = cursor.fetchone()
                if not fila_medio:
                    return "medio_invalido"
                afecta_efectivo = bool(fila_medio[0])
                if tipo in ("aporte", "retiro") and not afecta_efectivo:
                    return "medio_invalido"
                if afecta_efectivo and tipo in TIPOS_SALIDA:
                    cursor.execute(
                        "SELECT COALESCE(SUM(pv.montoCobrado),0) FROM pagoVenta pv "
                        "JOIN medioPago mp ON mp.idMedioPago=pv.idMedioPago "
                        "WHERE pv.idSesionCaja=%s AND pv.anulado=0 AND mp.afectaEfectivo=1",
                        (sesion["id"],))
                    ventas = dinero(cursor.fetchone()[0])
                    cursor.execute(
                        "SELECT COALESCE(SUM(CASE "
                        "WHEN mc.tipo IN ('aporte','ingreso','ajuste_ingreso') THEN mc.monto "
                        "WHEN mc.tipo IN ('gasto','egreso','retiro','devolucion','ajuste_egreso') THEN -mc.monto "
                        "ELSE 0 END),0) FROM movimientoCaja mc "
                        "JOIN medioPago mp ON mp.idMedioPago=mc.idMedioPago "
                        "WHERE mc.idSesionCaja=%s AND mc.anulado=0 AND mp.afectaEfectivo=1",
                        (sesion["id"],))
                    movimientos = dinero(cursor.fetchone()[0])
                    disponible = dinero(dinero(sesion["fondoInicial"]) + ventas + movimientos)
                    if monto > disponible:
                        return "saldo_insuficiente"
                cursor.execute(
                    "INSERT INTO movimientoCaja(idSesionCaja,tipo,idMedioPago,monto,categoria,concepto,"
                    "documento,evidencia,idUsuario,fechaHora) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (sesion["id"], tipo, id_medio, monto, categoria, concepto[:255],
                     (documento or "")[:100] or None, evidencia, id_usuario,
                     ahora_peru().replace(tzinfo=None)))
            conexion.commit()
            return "ok"
        finally:
            conexion.close()

    @staticmethod
    def resumen(id_sesion=None):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if id_sesion:
                    cursor.execute(
                        "SELECT sc.idSesionCaja,sc.fechaApertura,sc.fondoInicial,sc.fechaCierre,"
                        "sc.efectivoEsperado,sc.efectivoContado,sc.diferencia,sc.observaciones,sc.estado,"
                        "TRIM(CONCAT_WS(' ',ua.nombres,ua.apellidos)),"
                        "TRIM(CONCAT_WS(' ',uc.nombres,uc.apellidos)) FROM sesionCaja sc "
                        "JOIN usuario ua ON ua.idUsuario=sc.idUsuarioApertura "
                        "LEFT JOIN usuario uc ON uc.idUsuario=sc.idUsuarioCierre WHERE sc.idSesionCaja=%s",
                        (id_sesion,))
                else:
                    cursor.execute(
                        "SELECT sc.idSesionCaja,sc.fechaApertura,sc.fondoInicial,sc.fechaCierre,"
                        "sc.efectivoEsperado,sc.efectivoContado,sc.diferencia,sc.observaciones,sc.estado,"
                        "TRIM(CONCAT_WS(' ',ua.nombres,ua.apellidos)),"
                        "TRIM(CONCAT_WS(' ',uc.nombres,uc.apellidos)) FROM sesionCaja sc "
                        "JOIN usuario ua ON ua.idUsuario=sc.idUsuarioApertura "
                        "LEFT JOIN usuario uc ON uc.idUsuario=sc.idUsuarioCierre "
                        "WHERE sc.estado='abierta' ORDER BY sc.idSesionCaja DESC LIMIT 1")
                s = cursor.fetchone()
                if not s:
                    return None
                sid = s[0]
                cursor.execute(
                    "SELECT mp.idMedioPago,mp.nombre,mp.afectaEfectivo,"
                    "COALESCE(SUM(CASE WHEN pv.anulado=0 THEN pv.montoCobrado ELSE 0 END),0),"
                    "COALESCE(SUM(CASE WHEN pv.anulado=0 THEN pv.comision ELSE 0 END),0),"
                    "COALESCE(SUM(CASE WHEN pv.anulado=0 THEN pv.montoNeto ELSE 0 END),0),"
                    "COUNT(CASE WHEN pv.anulado=0 THEN 1 END) FROM medioPago mp "
                    "LEFT JOIN pagoVenta pv ON pv.idMedioPago=mp.idMedioPago AND pv.idSesionCaja=%s "
                    "GROUP BY mp.idMedioPago,mp.nombre,mp.afectaEfectivo ORDER BY mp.idMedioPago", (sid,))
                medios = [{"id": r[0], "nombre": r[1], "efectivo": bool(r[2]),
                           "cobrado": float(r[3]), "comision": float(r[4]),
                           "neto": float(r[5]), "cantidad": int(r[6])} for r in cursor.fetchall()]
                cursor.execute(
                    "SELECT mc.idMovimientoCaja,mc.tipo,mp.nombre,mc.monto,mc.categoria,mc.concepto,mc.documento,"
                    "mc.evidencia,mc.fechaHora,TRIM(CONCAT_WS(' ',u.nombres,u.apellidos)),mc.anulado,"
                    "COALESCE(mp.afectaEfectivo,0) "
                    "FROM movimientoCaja mc LEFT JOIN medioPago mp ON mp.idMedioPago=mc.idMedioPago "
                    "JOIN usuario u ON u.idUsuario=mc.idUsuario WHERE mc.idSesionCaja=%s "
                    "ORDER BY mc.idMovimientoCaja DESC", (sid,))
                movimientos = [{"id": r[0], "tipo": r[1], "medio": r[2], "monto": float(r[3]),
                                "categoria": r[4], "concepto": r[5], "documento": r[6],
                                "evidencia": r[7], "fecha": r[8], "usuario": r[9],
                                "anulado": bool(r[10]), "efectivo": bool(r[11])}
                               for r in cursor.fetchall()]
        finally:
            conexion.close()
        fondo = dinero(s[2])
        venta_efectivo = sum(dinero(m["cobrado"]) for m in medios if m["efectivo"])
        mas = sum(dinero(m["monto"]) for m in movimientos
                  if not m["anulado"] and m["tipo"] in TIPOS_ENTRADA and m["efectivo"])
        menos = sum(dinero(m["monto"]) for m in movimientos
                    if not m["anulado"] and m["tipo"] in TIPOS_SALIDA and m["efectivo"])
        esperado = dinero(fondo + venta_efectivo + mas - menos)
        aportes = sum(dinero(m["monto"]) for m in movimientos
                      if not m["anulado"] and m["tipo"] in ("aporte", "ingreso") and m["efectivo"])
        gastos = sum(dinero(m["monto"]) for m in movimientos
                     if not m["anulado"] and m["tipo"] in ("gasto", "egreso") and m["efectivo"])
        retiros = sum(dinero(m["monto"]) for m in movimientos
                      if not m["anulado"] and m["tipo"] == "retiro" and m["efectivo"])
        return {"id": s[0], "fechaApertura": s[1], "fondoInicial": float(fondo),
                "fechaCierre": s[3], "efectivoEsperado": float(s[4] if s[4] is not None else esperado),
                "efectivoContado": float(s[5]) if s[5] is not None else None,
                "diferencia": float(s[6]) if s[6] is not None else None,
                "observaciones": s[7] or "", "estado": s[8], "abiertaPor": s[9],
                "cerradaPor": s[10] or "", "medios": medios, "movimientos": movimientos,
                "totalAportes": float(aportes), "totalGastos": float(gastos),
                "totalRetiros": float(retiros)}

    @staticmethod
    def cerrar(efectivo_contado, observaciones, id_usuario):
        try:
            contado = dinero(efectivo_contado)
        except Exception:
            return "monto_invalido"
        if contado < 0:
            return "monto_invalido"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                actual = Caja.abierta_cursor(cursor, bloquear=True)
                if not actual:
                    return "caja_cerrada"
                cursor.execute(
                    "SELECT COALESCE(SUM(pv.montoCobrado),0) FROM pagoVenta pv "
                    "JOIN medioPago mp ON mp.idMedioPago=pv.idMedioPago "
                    "WHERE pv.idSesionCaja=%s AND pv.anulado=0 AND mp.afectaEfectivo=1",
                    (actual["id"],))
                ventas = dinero(cursor.fetchone()[0])
                cursor.execute(
                    "SELECT COALESCE(SUM(CASE "
                    "WHEN mc.tipo IN ('aporte','ingreso','ajuste_ingreso') THEN mc.monto "
                    "WHEN mc.tipo IN ('gasto','egreso','retiro','devolucion','ajuste_egreso') THEN -mc.monto "
                    "ELSE 0 END),0) FROM movimientoCaja mc "
                    "JOIN medioPago mp ON mp.idMedioPago=mc.idMedioPago "
                    "WHERE mc.idSesionCaja=%s AND mc.anulado=0 AND mp.afectaEfectivo=1",
                    (actual["id"],))
                movimientos = dinero(cursor.fetchone()[0])
                esperado = dinero(dinero(actual["fondoInicial"]) + ventas + movimientos)
                cursor.execute(
                    "UPDATE sesionCaja SET fechaCierre=%s,idUsuarioCierre=%s,efectivoEsperado=%s,"
                    "efectivoContado=%s,diferencia=%s,observaciones=%s,estado='cerrada' "
                    "WHERE idSesionCaja=%s AND estado='abierta'",
                    (ahora_peru().replace(tzinfo=None), id_usuario, esperado, contado,
                     dinero(contado - esperado), (observaciones or "")[:500] or None,
                     actual["id"]))
                if cursor.rowcount != 1:
                    return "caja_cerrada"
            conexion.commit()
            return "ok"
        finally:
            conexion.close()

    @staticmethod
    def historial(limite=50):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT sc.idSesionCaja,sc.fechaApertura,sc.fechaCierre,sc.fondoInicial,"
                    "sc.efectivoEsperado,sc.efectivoContado,sc.diferencia,sc.estado,"
                    "TRIM(CONCAT_WS(' ',u.nombres,u.apellidos)) FROM sesionCaja sc "
                    "JOIN usuario u ON u.idUsuario=sc.idUsuarioApertura "
                    "ORDER BY sc.idSesionCaja DESC LIMIT %s", (int(limite),))
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{"id": r[0], "apertura": r[1], "cierre": r[2], "fondo": float(r[3]),
                 "esperado": float(r[4]) if r[4] is not None else None,
                 "contado": float(r[5]) if r[5] is not None else None,
                 "diferencia": float(r[6]) if r[6] is not None else None,
                 "estado": r[7], "usuario": r[8]} for r in filas]
