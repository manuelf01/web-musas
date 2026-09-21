"""Consultas de ventas y comprobantes emitidos al entregar un pedido."""

import json
from datetime import date, timedelta

from bd import obtener_conexion
from negocio import SEDE, NOMBRE_NEGOCIO, ahora_peru


class Comprobante:

    @staticmethod
    def obtener_total(q="", tipo="", medio=""):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                condiciones, params = Comprobante._filtros(q, tipo, medio)
                cursor.execute(
                    "SELECT COUNT(*) FROM comprobante c "
                    "LEFT JOIN registroPedido rp ON rp.idPedido=c.idPedido " + condiciones,
                    params,
                )
                return int(cursor.fetchone()[0] or 0)
        finally:
            conexion.close()

    @staticmethod
    def _iniciales(nombre):
        return "".join(p[0] for p in (nombre or "").split()[:2]).upper() or "?"

    @staticmethod
    def _hhmm(valor):
        """Devuelve HH:MM desde TIME de MySQL, datetime.time o texto."""
        if valor is None:
            return ""
        if hasattr(valor, "seconds"):
            segundos = valor.seconds
            return f"{segundos // 3600:02d}:{(segundos % 3600) // 60:02d}"
        if hasattr(valor, "strftime"):
            return valor.strftime("%H:%M")
        return str(valor)[:5]

    @staticmethod
    def _filtros(q="", tipo="", medio=""):
        condiciones, params = [], []
        if q:
            like = f"%{q.strip()}%"
            condiciones.append("(c.numeroComprobante LIKE %s OR rp.nombres LIKE %s OR c.dniNoRegistrado LIKE %s)")
            params.extend([like, like, like])
        if tipo in ("boleta", "factura"):
            condiciones.append("c.tipoComprobante = %s")
            params.append(tipo)
        if medio in ("Efectivo", "Tarjeta", "Yape", "Plin"):
            condiciones.append("c.medioPago = %s")
            params.append(medio)
        return ("WHERE " + " AND ".join(condiciones)) if condiciones else "", params

    @staticmethod
    def kpis():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*), COALESCE(SUM(montoTotal), 0), "
                    "COALESCE(MAX(montoTotal), 0) FROM comprobante"
                )
                n, total, maxima = cursor.fetchone()
            return {
                "cantidad": int(n or 0),
                "total": round(float(total or 0), 2),
                "maxima": round(float(maxima or 0), 2),
            }
        finally:
            conexion.close()

    @staticmethod
    def ventas_por_dia(dias=7):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if dias >= 365:
                    cursor.execute(
                        "SELECT DATE_FORMAT(fechaComprobante, '%%Y-%%m'), COALESCE(SUM(montoTotal),0) "
                        "FROM comprobante WHERE fechaComprobante >= CURDATE() - INTERVAL 11 MONTH "
                        "GROUP BY DATE_FORMAT(fechaComprobante, '%%Y-%%m')"
                    )
                    por_mes = {clave: float(m or 0) for clave, m in cursor.fetchall()}
                    hoy = ahora_peru().date()
                    meses = []
                    nombres = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
                    for atraso in range(11, -1, -1):
                        total_meses = hoy.year * 12 + hoy.month - 1 - atraso
                        anio, mes0 = divmod(total_meses, 12)
                        clave = f"{anio:04d}-{mes0 + 1:02d}"
                        meses.append({"label": f"{nombres[mes0]} {str(anio)[2:]}", "monto": round(por_mes.get(clave, 0), 2), "hoy": atraso == 0})
                    tope = max((x["monto"] for x in meses), default=0) or 1
                    for item in meses:
                        item["pct"] = round(item["monto"] / tope * 100)
                    return meses
                cursor.execute(
                    "SELECT fechaComprobante, COALESCE(SUM(montoTotal), 0) FROM comprobante "
                    "WHERE fechaComprobante >= CURDATE() - INTERVAL %s DAY GROUP BY fechaComprobante",
                    (dias - 1,),
                )
                por_dia = {str(f): float(m or 0) for f, m in cursor.fetchall()}
        finally:
            conexion.close()

        etiquetas = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
        hoy = ahora_peru().date()
        salida = []
        for i in range(dias - 1, -1, -1):
            d = hoy - timedelta(days=i)
            salida.append({
                "label": f"{etiquetas[(d.weekday() + 1) % 7]} {d.day:02d}",
                "monto": round(por_dia.get(str(d), 0.0), 2),
                "hoy": i == 0,
            })
        tope = max((x["monto"] for x in salida), default=0) or 1
        for item in salida:
            item["pct"] = round(item["monto"] / tope * 100)
        return salida

    @staticmethod
    def ventas_por_hora():
        """Ventas cobradas hoy agrupadas por hora real de entrega."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT HOUR(horaComprobante), COALESCE(SUM(montoTotal),0) FROM comprobante "
                    "WHERE fechaComprobante=%s GROUP BY HOUR(horaComprobante) ORDER BY 1",
                    (ahora_peru().date(),),
                )
                montos = {int(h): float(m or 0) for h, m in cursor.fetchall()}
        finally:
            conexion.close()
        horas = list(range(9, 24))
        salida = [{"label": f"{h:02d}:00", "monto": round(montos.get(h, 0), 2)} for h in horas]
        tope = max((x["monto"] for x in salida), default=0) or 1
        for item in salida:
            item["pct"] = round(item["monto"] / tope * 100)
        return salida

    @staticmethod
    def listado_paginado(per_page, offset, q="", tipo="", medio=""):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                condiciones, params = Comprobante._filtros(q, tipo, medio)
                cursor.execute(
                    "SELECT c.idComprobante, c.numeroComprobante, c.fechaComprobante, "
                    "c.horaComprobante, c.dniNoRegistrado, c.subTotal, c.igv, c.montoTotal, "
                    "COALESCE(NULLIF(TRIM(rp.nombres), ''), "
                    "NULLIF(TRIM(CONCAT_WS(' ', u.nombres, u.apellidos)), ''), 'Cliente'), "
                    "c.medioPago, c.tipoComprobante, c.razonSocial FROM comprobante c "
                    "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
                    "LEFT JOIN registroPedido rp ON rp.idPedido = c.idPedido "
                    + condiciones + " ORDER BY c.idComprobante DESC LIMIT %s OFFSET %s",
                    params + [per_page, max(0, offset)],
                )
                filas = cursor.fetchall()
        finally:
            conexion.close()

        return [{
            "idComprobante": f[0],
            "numero": f[1],
            "fecha": f[2].strftime("%d %b %Y") if hasattr(f[2], "strftime") else str(f[2]),
            "hora": Comprobante._hhmm(f[3]),
            "dni": f[4],
            "subTotal": float(f[5] or 0),
            "igv": float(f[6] or 0),
            "montoTotal": float(f[7] or 0),
            "cliente": f[8] or "Cliente",
            "iniciales": Comprobante._iniciales(f[8]),
            "formaPago": f[9] or "No registrado",
            "tipoComprobante": f[10] or "boleta",
            "razonSocial": f[11] or "",
        } for f in filas]

    @staticmethod
    def id_por_pedido(id_pedido):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idComprobante FROM comprobante WHERE idPedido = %s",
                    (id_pedido,),
                )
                fila = cursor.fetchone()
                return fila[0] if fila else None
        finally:
            conexion.close()

    @staticmethod
    def detalle_por_pedido(id_pedido, id_usuario):
        """Devuelve el comprobante únicamente si el pedido pertenece al cliente."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idComprobante FROM comprobante "
                    "WHERE idPedido = %s AND idUsuario = %s",
                    (id_pedido, id_usuario),
                )
                fila = cursor.fetchone()
        finally:
            conexion.close()
        return Comprobante.detalle(fila[0]) if fila else None

    @staticmethod
    def detalle(id_comprobante):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT c.idComprobante, c.numeroComprobante, c.fechaComprobante, "
                    "c.horaComprobante, c.dniNoRegistrado, c.subTotal, c.igv, c.montoTotal, "
                    "c.idPedido, COALESCE(NULLIF(TRIM(rp.nombres), ''), "
                    "NULLIF(TRIM(CONCAT_WS(' ', u.nombres, u.apellidos)), ''), 'Cliente'), "
                    "rp.numeroTelefono, c.medioPago, rp.estadoBoleta, rp.notas, rp.horaRecojo, "
                    "rp.estadoRecojo, rp.cancelado, rp.noShow, rp.estadoPrep, c.datosEmision, "
                    "c.idUsuario, c.idCajero, c.tipoComprobante, c.razonSocial FROM comprobante c "
                    "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
                    "LEFT JOIN registroPedido rp ON rp.idPedido = c.idPedido "
                    "WHERE c.idComprobante = %s",
                    (id_comprobante,),
                )
                cabecera = cursor.fetchone()
                if cabecera is None:
                    return None
                cursor.execute(
                    "SELECT dc.nombreProducto, dc.precioUnidad, dc.cantidad, dc.precioTotal, "
                    "p.imagen, dc.adicionales FROM detalleComprobante dc "
                    "LEFT JOIN producto p ON p.idProducto = dc.idProducto "
                    "WHERE dc.idComprobante = %s ORDER BY dc.idLinea",
                    (id_comprobante,),
                )
                filas_linea = cursor.fetchall()
        finally:
            conexion.close()

        from model.Pedido import estado_pedido

        snapshot = {}
        if cabecera[19]:
            try:
                snapshot = json.loads(cabecera[19])
            except (TypeError, ValueError):
                snapshot = {}

        lineas_snapshot = snapshot.get("lineas") if isinstance(snapshot, dict) else None
        if lineas_snapshot:
            lineas = [{
                "nombre": linea.get("nombre") or "Producto",
                "precioUnidad": float(linea.get("precioUnidad") or 0),
                "cantidad": int(linea.get("cantidad") or 0),
                "precioTotal": float(linea.get("precioTotal") or 0),
                "adicionales": list(linea.get("adicionales") or []),
                "imagen": filas_linea[i][4] if i < len(filas_linea) else None,
            } for i, linea in enumerate(lineas_snapshot)]
        else:
            lineas = []
            for linea in filas_linea:
                try:
                    adicionales = json.loads(linea[5]) if linea[5] else []
                except (TypeError, ValueError):
                    adicionales = []
                lineas.append({
                    "nombre": linea[0],
                    "precioUnidad": float(linea[1] or 0),
                    "cantidad": int(linea[2] or 0),
                    "precioTotal": float(linea[3] or 0),
                    "imagen": linea[4],
                    "adicionales": adicionales,
                })

        negocio = snapshot.get("negocio") or {
            "nombre": f"{NOMBRE_NEGOCIO} - Chiclayo",
            "direccion": SEDE["direccion"],
            "referencia": SEDE["referencia"],
        }
        nombre = snapshot.get("cliente") or cabecera[9] or "Cliente"
        tipo_comprobante = snapshot.get("tipoComprobante") or cabecera[22] or ("boleta" if cabecera[12] else "boleta")
        boleta = tipo_comprobante == "boleta"
        return {
            "idComprobante": cabecera[0],
            "numero": snapshot.get("numero") or cabecera[1],
            "fecha": snapshot.get("fecha") or (
                cabecera[2].strftime("%d/%m/%Y") if hasattr(cabecera[2], "strftime") else str(cabecera[2])
            ),
            "hora": snapshot.get("hora") or Comprobante._hhmm(cabecera[3]),
            "dni": snapshot.get("dni") or cabecera[4] or "",
            "documento": snapshot.get("documento") or snapshot.get("dni") or cabecera[4] or "",
            "razonSocial": snapshot.get("razonSocial") or cabecera[23] or "",
            "tipoComprobante": tipo_comprobante,
            "subTotal": float(snapshot.get("subTotal", cabecera[5]) or 0),
            "igv": float(snapshot.get("igv", cabecera[6]) or 0),
            "montoTotal": float(snapshot.get("montoTotal", cabecera[7]) or 0),
            "idPedido": int(snapshot.get("idPedido") or cabecera[8]),
            "cliente": nombre,
            "iniciales": Comprobante._iniciales(nombre),
            "telefono": snapshot.get("telefono") or cabecera[10] or "",
            "formaPago": snapshot.get("medioPago") or cabecera[11] or "No registrado",
            "boleta": boleta,
            "tipoDoc": snapshot.get("tipoDoc") or ("FACTURA DE VENTA INTERNA" if tipo_comprobante == "factura" else "BOLETA DE VENTA INTERNA"),
            "notas": snapshot.get("notas") or cabecera[13] or "",
            "horaProgramada": snapshot.get("horaProgramada") or Comprobante._hhmm(cabecera[14]),
            "horaEntrega": snapshot.get("horaEntrega") or snapshot.get("hora") or Comprobante._hhmm(cabecera[3]),
            "horaRecojo": snapshot.get("horaEntrega") or snapshot.get("hora") or Comprobante._hhmm(cabecera[3]),
            "estado": estado_pedido(bool(cabecera[15]), bool(cabecera[16]), bool(cabecera[17]), int(cabecera[18] or 0)),
            "idUsuario": cabecera[20],
            "idCajero": snapshot.get("idCajero", cabecera[21]),
            "negocio": negocio,
            "lineas": lineas,
        }
