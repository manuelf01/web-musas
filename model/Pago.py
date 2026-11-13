"""Pagos cobrados en caja (RS 9.1 registrar / 9.2 consultar).

El pago se registra al «Cobrar y entregar» un pedido: medio (efectivo, tarjeta,
Yape, Plin), monto, cajero y hora quedan guardados en el comprobante. Este
módulo solo los consulta y resume; una venta anulada se muestra pero no suma.
"""

from bd import obtener_conexion
from model.Comprobante import Comprobante
from model.MedioPago import MedioPago

_FROM = (
    "FROM comprobante c "
    "JOIN pagoVenta pv ON pv.idComprobante = c.idComprobante "
    "JOIN medioPago mp ON mp.idMedioPago = pv.idMedioPago "
    "LEFT JOIN usuario u ON u.idUsuario = c.idUsuario "
    "LEFT JOIN usuario uc ON uc.idUsuario = c.idCajero "
    "LEFT JOIN registroPedido rp ON rp.idPedido = c.idPedido "
)
_CLIENTE = ("COALESCE(NULLIF(TRIM(rp.nombres), ''), "
            "NULLIF(TRIM(CONCAT_WS(' ', u.nombres, u.apellidos)), ''), 'Cliente')")


class Pago:

    @staticmethod
    def _condiciones(desde, hasta, q, estado, medio=None):
        cond, params = [], []
        if desde:
            cond.append("c.fechaComprobante >= %s")
            params.append(desde)
        if hasta:
            cond.append("c.fechaComprobante <= %s")
            params.append(hasta)
        if q:
            like = f"%{q.strip()}%"
            cond.append("(c.numeroComprobante LIKE %s OR rp.nombres LIKE %s OR u.nombres LIKE %s "
                        "OR u.apellidos LIKE %s OR CAST(c.idPedido AS CHAR) LIKE %s)")
            params.extend([like] * 5)
        if estado == "vigente":
            cond.append("c.anulado = 0")
        elif estado == "anulado":
            cond.append("c.anulado = 1")
        if medio:
            cond.append("mp.codigo = %s")
            params.append(str(medio).strip().lower())
        return ("WHERE " + " AND ".join(cond)) if cond else "", params

    @staticmethod
    def resumen(desde, hasta, q="", estado=""):
        """Total y cantidad cobrados por medio de pago (solo ventas vigentes)
        más lo anulado en el mismo período."""
        cond, params = Pago._condiciones(desde, hasta, q, estado)
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT pv.medioNombre, c.anulado, COUNT(*), "
                    "COALESCE(SUM(pv.montoCobrado),0),COALESCE(SUM(pv.comision),0),"
                    "COALESCE(SUM(pv.montoNeto),0),COALESCE(SUM(pv.descuento),0) "
                    + _FROM + cond + " GROUP BY pv.medioNombre, c.anulado", params)
                filas = cursor.fetchall()
        finally:
            conexion.close()
        medios = {m["nombre"]: {"medio": m["nombre"], "codigo": m["codigo"],
                  "total": 0.0, "cantidad": 0, "comision": 0.0,
                  "neto": 0.0, "descuento": 0.0} for m in MedioPago.listar()}
        anulado = {"cantidad": 0, "total": 0.0}
        for medio, anul, n, total, comision, neto, descuento in filas:
            if anul:
                anulado["cantidad"] += int(n)
                anulado["total"] += float(total)
                continue
            m = medios.setdefault(medio, {"medio": medio, "codigo": "", "total": 0.0,
                                  "cantidad": 0, "comision": 0.0, "neto": 0.0,
                                  "descuento": 0.0})
            m["total"] += float(total)
            m["cantidad"] += int(n)
            m["comision"] += float(comision)
            m["neto"] += float(neto)
            m["descuento"] += float(descuento)
        lista = list(medios.values())
        gran_total = round(sum(m["total"] for m in lista), 2)
        cantidad = sum(m["cantidad"] for m in lista)
        for m in lista:
            m["total"] = round(m["total"], 2)
            m["comision"] = round(m["comision"], 2)
            m["neto"] = round(m["neto"], 2)
            m["descuento"] = round(m["descuento"], 2)
            m["pct"] = round(m["total"] / gran_total * 100) if gran_total else 0
        anulado["total"] = round(anulado["total"], 2)
        return {"medios": lista, "total": gran_total, "cantidad": cantidad, "anulado": anulado}

    @staticmethod
    def total(desde, hasta, q="", estado="", medio=""):
        cond, params = Pago._condiciones(desde, hasta, q, estado, medio)
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) " + _FROM + cond, params)
                return int(cursor.fetchone()[0] or 0)
        finally:
            conexion.close()

    @staticmethod
    def listado(per_page, offset, desde, hasta, q="", estado="", medio=""):
        cond, params = Pago._condiciones(desde, hasta, q, estado, medio)
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT c.idComprobante, c.numeroComprobante, c.fechaComprobante, c.horaComprobante, "
                    f"c.idPedido, {_CLIENTE}, pv.medioNombre, pv.montoCobrado, c.anulado, "
                    "NULLIF(TRIM(CONCAT_WS(' ', uc.nombres, uc.apellidos)), ''), c.tipoComprobante "
                    ",pv.montoBruto,pv.descuento,pv.comision,pv.montoNeto "
                    + _FROM + cond + " ORDER BY c.fechaComprobante DESC, c.horaComprobante DESC, "
                    "c.idComprobante DESC LIMIT %s OFFSET %s",
                    params + [per_page, max(0, offset)])
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [{
            "idComprobante": f[0], "numero": f[1],
            "fecha": f[2].strftime("%d/%m/%Y") if hasattr(f[2], "strftime") else str(f[2]),
            "hora": Comprobante._hhmm(f[3]), "idPedido": f[4], "cliente": f[5],
            "iniciales": Comprobante._iniciales(f[5]), "medio": f[6] or "No registrado",
            "monto": float(f[7] or 0), "anulado": bool(f[8]), "cajero": f[9] or "—",
            "tipo": "Factura" if f[10] == "factura" else "Boleta",
            "bruto": float(f[11] or 0), "descuento": float(f[12] or 0),
            "comision": float(f[13] or 0), "neto": float(f[14] or 0),
        } for f in filas]
