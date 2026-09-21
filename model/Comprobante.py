"""Consultas de ventas y comprobantes emitidos al entregar un pedido."""

import json
import calendar
from datetime import date, datetime, timedelta

from bd import obtener_conexion
from negocio import SEDE, NOMBRE_NEGOCIO, ahora_peru


MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
         "Septiembre", "Octubre", "Noviembre", "Diciembre"]
DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def _tope_bonito(maximo):
    """Redondea hacia arriba a un número 'redondo' para el eje del gráfico."""
    if maximo <= 0:
        return 100
    magnitud = 10 ** (len(str(int(maximo))) - 1)
    for paso in (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if paso * magnitud >= maximo:
            return paso * magnitud
    return 10 * magnitud


def _armar_serie(items, titulo, subtitulo):
    """items: [{label, tip, monto, hoy, etiquetar}] -> datos listos para pintar."""
    maximo = max((i["monto"] for i in items), default=0)
    tope = _tope_bonito(maximo)
    for i in items:
        i["pct"] = round(i["monto"] / tope * 100, 1) if tope else 0
    total = round(sum(i["monto"] for i in items), 2)
    return {
        "barras": items, "titulo": titulo, "subtitulo": subtitulo, "total": total,
        "tope": tope, "mitad": tope / 2, "vacio": total == 0,
        "denso": len(items) > 12, "n": len(items),
        "ventas": sum(1 for i in items if i["monto"] > 0),
    }


class Comprobante:

    @staticmethod
    def anios_disponibles():
        """Años con ventas + el año actual (para el selector del gráfico)."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT DISTINCT YEAR(fechaComprobante) FROM comprobante")
                anios = {int(a) for (a,) in cursor.fetchall() if a}
        finally:
            conexion.close()
        anios.add(ahora_peru().year)
        return sorted(anios, reverse=True)

    @staticmethod
    def serie_ventas(vista="semana", anio=None, mes=None):
        """Ventas cobradas para el gráfico principal.
        vista: 'semana' (últimos 7 días) | 'mes' (un mes concreto) | 'anio' (un año concreto)."""
        hoy = ahora_peru().date()
        anio = anio or hoy.year
        mes = mes if mes and 1 <= mes <= 12 else hoy.month
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if vista == "anio":
                    cursor.execute(
                        "SELECT MONTH(fechaComprobante), COALESCE(SUM(montoTotal),0) FROM comprobante "
                        "WHERE anulado = 0 AND YEAR(fechaComprobante) = %s GROUP BY MONTH(fechaComprobante)", (anio,))
                    datos = {int(m): float(t or 0) for m, t in cursor.fetchall()}
                    items = [{
                        "label": MESES[m - 1][:3], "etiquetar": True,
                        "tip": f"{MESES[m - 1]} {anio}",
                        "monto": round(datos.get(m, 0), 2),
                        "hoy": (anio, m) == (hoy.year, hoy.month),
                    } for m in range(1, 13)]
                    return _armar_serie(items, f"Año {anio}", "Ventas por mes")
                if vista == "mes":
                    ultimo = calendar.monthrange(anio, mes)[1]
                    cursor.execute(
                        "SELECT DAY(fechaComprobante), COALESCE(SUM(montoTotal),0) FROM comprobante "
                        "WHERE anulado = 0 AND YEAR(fechaComprobante) = %s AND MONTH(fechaComprobante) = %s "
                        "GROUP BY DAY(fechaComprobante)", (anio, mes))
                    datos = {int(d): float(t or 0) for d, t in cursor.fetchall()}
                    items = []
                    for d in range(1, ultimo + 1):
                        fecha = date(anio, mes, d)
                        items.append({
                            "label": f"{d:02d}", "etiquetar": d == 1 or d % 5 == 0 or d == ultimo,
                            "tip": f"{DIAS_SEMANA[fecha.weekday()]} {d:02d} {MESES[mes - 1][:3].lower()} {anio}",
                            "monto": round(datos.get(d, 0), 2), "hoy": fecha == hoy,
                        })
                    return _armar_serie(items, f"{MESES[mes - 1]} {anio}", "Ventas por día")
                cursor.execute(
                    "SELECT fechaComprobante, COALESCE(SUM(montoTotal), 0) FROM comprobante "
                    "WHERE anulado = 0 AND fechaComprobante BETWEEN %s AND %s GROUP BY fechaComprobante",
                    (hoy - timedelta(days=6), hoy))
                datos = {str(f): float(t or 0) for f, t in cursor.fetchall()}
        finally:
            conexion.close()
        items = []
        for i in range(6, -1, -1):
            d = hoy - timedelta(days=i)
            items.append({
                "label": f"{DIAS_SEMANA[d.weekday()]} {d.day:02d}", "etiquetar": True,
                "tip": f"{DIAS_SEMANA[d.weekday()]} {d.day:02d} {MESES[d.month - 1][:3].lower()} {d.year}",
                "monto": round(datos.get(str(d), 0.0), 2), "hoy": i == 0,
            })
        return _armar_serie(items, "Últimos 7 días", "Ventas por día")

    @staticmethod
    def serie_por_hora(fecha=None):
        """Ventas cobradas de un día (por defecto hoy) agrupadas por hora de entrega."""
        hoy = ahora_peru().date()
        fecha = fecha or hoy
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT HOUR(horaComprobante), COALESCE(SUM(montoTotal),0) FROM comprobante "
                    "WHERE anulado = 0 AND fechaComprobante=%s GROUP BY HOUR(horaComprobante)", (fecha,))
                datos = {int(h): float(m or 0) for h, m in cursor.fetchall()}
        finally:
            conexion.close()
        ahora_h = ahora_peru().hour
        horas = sorted(set(range(9, 24)) | set(datos))
        items = [{
            "label": f"{h:02d}h", "etiquetar": True,
            "tip": f"{h:02d}:00 – {h:02d}:59",
            "monto": round(datos.get(h, 0), 2), "hoy": fecha == hoy and h == ahora_h,
        } for h in horas]
        titulo = "Hoy" if fecha == hoy else f"{fecha.day:02d} {MESES[fecha.month - 1][:3].lower()} {fecha.year}"
        return _armar_serie(items, titulo, "Ventas por hora")

    @staticmethod
    def sugerencias(q, limite=8):
        """Coincidencias (número, cliente, documento) para el autocompletado."""
        q = (q or "").strip()
        if not q:
            return []
        like = f"%{q}%"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT c.numeroComprobante, "
                    "COALESCE(NULLIF(TRIM(rp.nombres), ''), NULLIF(TRIM(CONCAT_WS(' ', u.nombres, u.apellidos)), ''), 'Cliente'), "
                    "c.dniNoRegistrado, c.razonSocial FROM comprobante c "
                    "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
                    "LEFT JOIN registroPedido rp ON rp.idPedido = c.idPedido "
                    "WHERE c.numeroComprobante LIKE %s OR rp.nombres LIKE %s OR u.nombres LIKE %s "
                    "OR u.apellidos LIKE %s OR c.dniNoRegistrado LIKE %s OR c.razonSocial LIKE %s "
                    "ORDER BY c.idComprobante DESC LIMIT 40",
                    (like, like, like, like, like, like))
                filas = cursor.fetchall()
        finally:
            conexion.close()
        vistos, salida = set(), []
        ql = q.lower()
        for fila in filas:
            for valor in fila:
                if valor and ql in str(valor).lower() and valor not in vistos:
                    vistos.add(valor)
                    salida.append(str(valor))
        return salida[:limite]

    @staticmethod
    def obtener_total(q="", tipo="", medio="", desde=None, hasta=None, estado=""):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                condiciones, params = Comprobante._filtros(q, tipo, medio, desde, hasta, estado)
                cursor.execute(
                    "SELECT COUNT(*) FROM comprobante c "
                    "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
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
    def _filtros(q="", tipo="", medio="", desde=None, hasta=None, estado=""):
        condiciones, params = [], []
        if estado == "vigente":
            condiciones.append("c.anulado = 0")
        elif estado == "anulado":
            condiciones.append("c.anulado = 1")
        if q:
            like = f"%{q.strip()}%"
            condiciones.append(
                "(c.numeroComprobante LIKE %s OR rp.nombres LIKE %s OR c.dniNoRegistrado LIKE %s "
                "OR c.razonSocial LIKE %s OR u.nombres LIKE %s OR u.apellidos LIKE %s)")
            params.extend([like] * 6)
        if desde:
            condiciones.append("c.fechaComprobante >= %s")
            params.append(desde)
        if hasta:
            condiciones.append("c.fechaComprobante <= %s")
            params.append(hasta)
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
                    "COALESCE(MAX(montoTotal), 0) FROM comprobante WHERE anulado = 0"
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
    def listado_paginado(per_page, offset, q="", tipo="", medio="", desde=None, hasta=None, estado=""):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                condiciones, params = Comprobante._filtros(q, tipo, medio, desde, hasta, estado)
                cursor.execute(
                    "SELECT c.idComprobante, c.numeroComprobante, c.fechaComprobante, "
                    "c.horaComprobante, c.dniNoRegistrado, c.subTotal, c.igv, c.montoTotal, "
                    "COALESCE(NULLIF(TRIM(rp.nombres), ''), "
                    "NULLIF(TRIM(CONCAT_WS(' ', u.nombres, u.apellidos)), ''), 'Cliente'), "
                    "c.medioPago, c.tipoComprobante, c.razonSocial, c.anulado FROM comprobante c "
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
            "anulado": bool(f[12]),
        } for f in filas]

    @staticmethod
    def anular(id_comprobante, motivo, id_usuario, devolver_stock=False):
        """Anula la venta (el comprobante se conserva, marcado). Devuelve
        'ok' | 'no_existe' | 'ya_anulado' | 'motivo_invalido'."""
        motivo = (motivo or "").strip()
        if len(motivo) < 5:
            return "motivo_invalido"
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idPedido, anulado FROM comprobante WHERE idComprobante = %s FOR UPDATE",
                    (id_comprobante,))
                fila = cursor.fetchone()
                if fila is None:
                    return "no_existe"
                if fila[1]:
                    return "ya_anulado"
                cursor.execute(
                    "UPDATE comprobante SET anulado = 1, motivoAnulacion = %s, fechaAnulacion = %s, "
                    "idAnulador = %s, stockDevuelto = %s WHERE idComprobante = %s",
                    (motivo[:255], ahora_peru().replace(tzinfo=None), id_usuario,
                     1 if devolver_stock else 0, id_comprobante))
                if devolver_stock:
                    from model.Pedido import Pedido
                    Pedido._devolver_stock(cursor, fila[0])
            conexion.commit()
            return "ok"
        finally:
            conexion.close()

    @staticmethod
    def restaurar(id_comprobante):
        """Revierte una anulación. Si se había devuelto el stock, se vuelve a descontar.
        Devuelve 'ok' | 'no_existe' | 'no_anulado' | 'sin_stock'."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idPedido, anulado, stockDevuelto FROM comprobante "
                    "WHERE idComprobante = %s FOR UPDATE", (id_comprobante,))
                fila = cursor.fetchone()
                if fila is None:
                    return "no_existe"
                if not fila[1]:
                    return "no_anulado"
                if fila[2]:
                    cursor.execute(
                        "SELECT dor.idProducto, SUM(dor.cantidad), p.existencias FROM detalleOrden dor "
                        "LEFT JOIN producto p ON p.idProducto = dor.idProducto "
                        "WHERE dor.idPedido = %s GROUP BY dor.idProducto, p.existencias", (fila[0],))
                    lineas = cursor.fetchall()
                    if any(disp is None or disp < cant for _, cant, disp in lineas):
                        return "sin_stock"
                    for id_prod, cant, _ in lineas:
                        cursor.execute(
                            "UPDATE producto SET existencias = existencias - %s WHERE idProducto = %s",
                            (cant, id_prod))
                cursor.execute(
                    "UPDATE comprobante SET anulado = 0, motivoAnulacion = NULL, fechaAnulacion = NULL, "
                    "idAnulador = NULL, stockDevuelto = 0 WHERE idComprobante = %s", (id_comprobante,))
            conexion.commit()
            return "ok"
        finally:
            conexion.close()

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
                    "c.idUsuario, c.idCajero, c.tipoComprobante, c.razonSocial, "
                    "c.anulado, c.motivoAnulacion, c.fechaAnulacion, c.stockDevuelto, "
                    "NULLIF(TRIM(CONCAT_WS(' ', ua.nombres, ua.apellidos)), '') FROM comprobante c "
                    "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
                    "LEFT JOIN usuario ua ON ua.idUsuario = c.idAnulador "
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
            "anulado": bool(cabecera[24]),
            "motivoAnulacion": cabecera[25] or "",
            "fechaAnulacion": (cabecera[26].strftime("%d/%m/%Y %H:%M")
                               if hasattr(cabecera[26], "strftime") else ""),
            "stockDevuelto": bool(cabecera[27]),
            "anuladoPor": cabecera[28] or "",
        }
