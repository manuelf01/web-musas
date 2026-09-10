"""Consultas de ventas y comprobantes emitidos al entregar un pedido."""

import json
from datetime import date, timedelta

from bd import obtener_conexion
from negocio import SEDE


class Comprobante:

    @staticmethod
    def obtener_total():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM comprobante")
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
    def kpis():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*), COALESCE(SUM(montoTotal), 0), "
                    "COALESCE(AVG(montoTotal), 0) FROM comprobante"
                )
                n, total, ticket = cursor.fetchone()
            return {
                "cantidad": int(n or 0),
                "total": round(float(total or 0), 2),
                "ticket": round(float(ticket or 0), 2),
            }
        finally:
            conexion.close()

    @staticmethod
    def ventas_por_dia(dias=7):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT fechaComprobante, COALESCE(SUM(montoTotal), 0) FROM comprobante "
                    "WHERE fechaComprobante >= CURDATE() - INTERVAL %s DAY GROUP BY fechaComprobante",
                    (dias - 1,),
                )
                por_dia = {str(f): float(m or 0) for f, m in cursor.fetchall()}
        finally:
            conexion.close()

        etiquetas = ["Dom", "Lun", "Mar", "Mié", "Jue", "Vie", "Sáb"]
        hoy = date.today()
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
    def listado_paginado(per_page, offset):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT c.idComprobante, c.numeroComprobante, c.fechaComprobante, "
                    "c.horaComprobante, c.dniNoRegistrado, c.subTotal, c.igv, c.montoTotal, "
                    "COALESCE(NULLIF(TRIM(rp.nombres), ''), "
                    "NULLIF(TRIM(CONCAT_WS(' ', u.nombres, u.apellidos)), ''), 'Cliente'), "
                    "c.medioPago FROM comprobante c "
                    "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
                    "LEFT JOIN registroPedido rp ON rp.idPedido = c.idPedido "
                    "ORDER BY c.idComprobante DESC LIMIT %s OFFSET %s",
                    (per_page, max(0, offset)),
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
                    "c.idUsuario, c.idCajero FROM comprobante c "
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
            "nombre": "Las Musas - Chiclayo",
            "direccion": SEDE["direccion"],
            "referencia": SEDE["referencia"],
        }
        nombre = snapshot.get("cliente") or cabecera[9] or "Cliente"
        boleta = bool(snapshot.get("boleta", cabecera[12]))
        return {
            "idComprobante": cabecera[0],
            "numero": snapshot.get("numero") or cabecera[1],
            "fecha": snapshot.get("fecha") or (
                cabecera[2].strftime("%d/%m/%Y") if hasattr(cabecera[2], "strftime") else str(cabecera[2])
            ),
            "hora": snapshot.get("hora") or Comprobante._hhmm(cabecera[3]),
            "dni": snapshot.get("dni") or cabecera[4] or "",
            "subTotal": float(snapshot.get("subTotal", cabecera[5]) or 0),
            "igv": float(snapshot.get("igv", cabecera[6]) or 0),
            "montoTotal": float(snapshot.get("montoTotal", cabecera[7]) or 0),
            "idPedido": int(snapshot.get("idPedido") or cabecera[8]),
            "cliente": nombre,
            "iniciales": Comprobante._iniciales(nombre),
            "telefono": snapshot.get("telefono") or cabecera[10] or "",
            "formaPago": snapshot.get("medioPago") or cabecera[11] or "No registrado",
            "boleta": boleta,
            "tipoDoc": snapshot.get("tipoDoc") or ("BOLETA DE VENTA INTERNA" if boleta else "NOTA DE VENTA"),
            "notas": snapshot.get("notas") or cabecera[13] or "",
            "horaRecojo": snapshot.get("horaRecojo") or Comprobante._hhmm(cabecera[14]),
            "estado": estado_pedido(bool(cabecera[15]), bool(cabecera[16]), bool(cabecera[17]), int(cabecera[18] or 0)),
            "idUsuario": cabecera[20],
            "idCajero": snapshot.get("idCajero", cabecera[21]),
            "negocio": negocio,
            "lineas": lineas,
        }
