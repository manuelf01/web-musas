from bd import obtener_conexion
from model.Pedido import Pedido
from model.DetalleOrden import DetalleOrden
from datetime import date, datetime, timedelta


class Comprobante:
    idComprobante = 0
    idPedido = 0
    idUsuario = ""
    dniNoRegistrado = 0
    fechaComprobante = ""
    horaComprobante = ""
    subTotal = 0
    montoTotal = 0
    igv = 0
    numeroComprobante = ""
    midic = dict()

    def __init__(self, p_idComprobate, p_idPedido, p_idUsuario, p_dniNoRegistrado, p_fechaComprobante, p_horaComprobante, p_subTotal, p_montoTotal, p_igv, p_numComprobante):
        self.idComprobante = p_idComprobate
        self.idPedido = p_idPedido
        self.idUsuario = p_idUsuario
        self.dniNoRegistrado = p_dniNoRegistrado
        self.fechaComprobante = p_fechaComprobante
        self.horaComprobante = p_horaComprobante
        self.subTotal = p_subTotal
        self.montoTotal = p_montoTotal
        self.igv = p_igv
        self.numeroComprobante = p_numComprobante
        self.midic["idComprobante"] = p_idComprobate
        self.midic["idPedido"] = p_idPedido
        self.midic["idUsuario"] = p_idUsuario
        self.midic["dniNoRegistrado"] = p_dniNoRegistrado
        self.midic["fechaComprobante"] = str(date(
            year=p_fechaComprobante.year, month=p_fechaComprobante.month, day=p_fechaComprobante.day))
        self.midic["horaComprobante"] = str(
            timedelta(seconds=p_horaComprobante.seconds))
        self.midic["subTotal"] = p_subTotal
        self.midic["montoTotal"] = p_montoTotal
        self.midic["igv"] = p_igv
        self.midic["numComprobante"] = p_numComprobante

    def obtener_comprobante():
        conexion = obtener_conexion()
        comprobantes = []
        with conexion.cursor() as cursor:
            cursor.execute("select * from comprobante")
            comprobantes = cursor.fetchall()
        conexion.close()
        return comprobantes

    def obtener_comprobante_idUsuario(idUsuario):
        conexion = obtener_conexion()
        juego = None
        with conexion.cursor() as cursor:
            cursor.execute(
                "select * from comprobante where idUsuario = %s", (idUsuario))
            juego = cursor.fetchall()
        conexion.close()
        return juego

    def validar_idComprobante_existente(idComprobante):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            consulta = "SELECT COUNT(*) FROM comprobante WHERE idComprobante = %s"
            cursor.execute(consulta, (idComprobante,))
            resultado = cursor.fetchone()
        conexion.close()
        if resultado[0] > 0:
            return True
        else:
            return False

    def obtener_id_comprobante_registro():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT coalesce(MAX(idComprobante),0)+1 as idComprobante FROM comprobante")
            idComprobante = cursor.fetchone()
        conexion.close()
        return idComprobante[0]

    def obtener_numero_comprobante():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT coalesce(MAX(numeroComprobante),0)+1 as numeroComprobante FROM comprobante")
            numeroComprobante = cursor.fetchone()
        conexion.close()
        return numeroComprobante[0]

    def obtener_comprobante_id(idComprobante):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "select * from comprobante where idComprobante = %s", idComprobante)
            comprobante = cursor.fetchone()
        conexion.close()
        return comprobante

    def obtener_comprobantes_paginacion(per_page, start_index):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "select * from comprobante  limit %s offset %s", (per_page, start_index-1))
            comprobantes = cursor.fetchall()
        conexion.close()
        return comprobantes

    def obtener_total():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("select count(*) from comprobante")
            total = cursor.fetchone()
        conexion.close()
        return total[0]

    # ------------------------------------------------------------------
    # Vistas para el panel de Ventas (diccionarios con datos ya cruzados).
    # ------------------------------------------------------------------
    @staticmethod
    def _iniciales(nombre):
        return "".join(p[0] for p in (nombre or "").split()[:2]).upper() or "?"

    @staticmethod
    def _hhmm(valor):
        """'HH:MM' desde un TIME de MySQL (timedelta) o texto."""
        seg = valor.seconds if hasattr(valor, "seconds") else 0
        return f"{seg // 3600:02d}:{(seg % 3600) // 60:02d}"

    @staticmethod
    def kpis():
        """Totales acumulados de todo lo facturado."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(montoTotal), 0), COALESCE(AVG(montoTotal), 0) FROM comprobante"
            )
            n, total, ticket = cursor.fetchone()
        conexion.close()
        return {
            "cantidad": int(n or 0),
            "total": round(float(total or 0), 2),
            "ticket": round(float(ticket or 0), 2),
        }

    @staticmethod
    def ventas_por_dia(dias=7):
        """[{label, monto, pct, hoy}] de los últimos `dias` días, para el gráfico."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT fechaComprobante, COALESCE(SUM(montoTotal), 0) FROM comprobante "
                "WHERE fechaComprobante >= CURDATE() - INTERVAL %s DAY GROUP BY fechaComprobante",
                (dias - 1,),
            )
            por_dia = {str(f): float(m or 0) for f, m in cursor.fetchall()}
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
        for x in salida:
            x["pct"] = round(x["monto"] / tope * 100)
        return salida

    @staticmethod
    def listado_paginado(per_page, offset):
        """Comprobantes (más reciente primero) con cliente y forma de pago."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT c.idComprobante, c.numeroComprobante, c.fechaComprobante, c.horaComprobante, "
                "c.dniNoRegistrado, c.subTotal, c.igv, c.montoTotal, "
                "COALESCE(u.nombres, rp.nombres, 'Cliente') AS cliente, rp.billeteraDigital "
                "FROM comprobante c "
                "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
                "LEFT JOIN registroPedido rp ON rp.idPedido = c.idPedido "
                "ORDER BY c.idComprobante DESC LIMIT %s OFFSET %s",
                (per_page, max(0, offset)),
            )
            filas = cursor.fetchall()
        conexion.close()

        salida = []
        for f in filas:
            hora = Comprobante._hhmm(f[3])
            nombre = f[8] or "Cliente"
            salida.append({
                "idComprobante": f[0],
                "numero": f[1],
                "fecha": f[2].strftime("%d %b %Y") if hasattr(f[2], "strftime") else str(f[2]),
                "hora": hora,
                "dni": f[4],
                "subTotal": float(f[5] or 0),
                "igv": float(f[6] or 0),
                "montoTotal": float(f[7] or 0),
                "cliente": nombre,
                "iniciales": Comprobante._iniciales(nombre),
                "formaPago": "Yape / Plin" if f[9] == 1 else "Efectivo",
            })
        return salida

    @staticmethod
    def detalle(id_comprobante):
        """Todo lo necesario para la boleta: cabecera + cliente + pedido + líneas."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT c.idComprobante, c.numeroComprobante, c.fechaComprobante, c.horaComprobante, "
                "c.dniNoRegistrado, c.subTotal, c.igv, c.montoTotal, c.idPedido, "
                "COALESCE(u.nombres, rp.nombres, 'Cliente'), rp.numeroTelefono, rp.billeteraDigital, "
                "rp.estadoBoleta, rp.notas, rp.horaRecojo, rp.estadoRecojo, rp.cancelado, rp.noShow, rp.estadoPrep "
                "FROM comprobante c "
                "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
                "LEFT JOIN registroPedido rp ON rp.idPedido = c.idPedido "
                "WHERE c.idComprobante = %s",
                (id_comprobante,),
            )
            c = cursor.fetchone()
            if c is None:
                conexion.close()
                return None
            cursor.execute(
                "SELECT dc.nombreProducto, dc.precioUnidad, dc.cantidad, dc.precioTotal, p.imagen "
                "FROM detalleComprobante dc LEFT JOIN producto p ON p.idProducto = dc.idProducto "
                "WHERE dc.idComprobante = %s",
                (id_comprobante,),
            )
            lineas = cursor.fetchall()
        conexion.close()

        from model.Pedido import estado_pedido
        hora_r = Comprobante._hhmm(c[14])
        nombre = c[9] or "Cliente"
        return {
            "idComprobante": c[0],
            "numero": c[1],
            "fecha": c[2].strftime("%d/%m/%Y") if hasattr(c[2], "strftime") else str(c[2]),
            "hora": Comprobante._hhmm(c[3]),
            "dni": c[4],
            "subTotal": float(c[5] or 0),
            "igv": float(c[6] or 0),
            "montoTotal": float(c[7] or 0),
            "idPedido": c[8],
            "cliente": nombre,
            "iniciales": Comprobante._iniciales(nombre),
            "telefono": c[10],
            "formaPago": "Yape / Plin" if c[11] == 1 else "Efectivo",
            "boleta": bool(c[12]),
            "tipoDoc": "BOLETA ELECTRÓNICA" if c[12] else "NOTA DE VENTA",
            "notas": c[13],
            "horaRecojo": hora_r,
            "estado": estado_pedido(bool(c[15]), bool(c[16]), bool(c[17]), int(c[18] or 0)),
            "lineas": [
                {
                    "nombre": l[0],
                    "precioUnidad": float(l[1] or 0),
                    "cantidad": int(l[2] or 0),
                    "precioTotal": float(l[3] or 0),
                    "imagen": l[4],
                }
                for l in lineas
            ],
        }
