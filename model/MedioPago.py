import re
import unicodedata
from decimal import Decimal

from bd import obtener_conexion
from dinero import dinero


TIPOS_MEDIO = ("efectivo", "tarjeta", "billetera", "transferencia", "otro")


def _codigo(nombre):
    texto = unicodedata.normalize("NFKD", nombre or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texto.lower()).strip("-")[:20]


class MedioPago:
    @staticmethod
    def listar(solo_activos=False):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idMedioPago,codigo,nombre,tipo,descuentoPorcentaje,"
                    "comisionPorcentaje,comisionFija,imagen,afectaEfectivo,activo "
                    "FROM medioPago " + ("WHERE activo=1 " if solo_activos else "") +
                    "ORDER BY activo DESC, idMedioPago"
                )
                filas = cursor.fetchall()
        finally:
            conexion.close()
        return [MedioPago._dict(f) for f in filas]

    @staticmethod
    def _dict(f):
        return {
            "id": f[0], "codigo": f[1], "nombre": f[2], "tipo": f[3],
            "descuentoPct": float(f[4] or 0), "comisionPct": float(f[5] or 0),
            "comisionFija": float(f[6] or 0), "imagen": f[7],
            "afectaEfectivo": bool(f[8]), "activo": bool(f[9]),
        }

    @staticmethod
    def por_codigo(codigo, cursor=None):
        propio = cursor is None
        conexion = obtener_conexion() if propio else None
        cur = conexion.cursor() if propio else cursor
        try:
            cur.execute(
                "SELECT idMedioPago,codigo,nombre,tipo,descuentoPorcentaje,"
                "comisionPorcentaje,comisionFija,imagen,afectaEfectivo,activo "
                "FROM medioPago WHERE codigo=%s", ((codigo or "").lower(),))
            fila = cur.fetchone()
            return MedioPago._dict(fila) if fila else None
        finally:
            if propio:
                cur.close()
                conexion.close()

    @staticmethod
    def calcular(medio, bruto):
        bruto = dinero(bruto)
        descuento = dinero(bruto * Decimal(str(medio["descuentoPct"])) / Decimal("100"))
        cobrado = max(Decimal("0.00"), bruto - descuento)
        comision = dinero(
            cobrado * Decimal(str(medio["comisionPct"])) / Decimal("100")
            + Decimal(str(medio["comisionFija"]))
        )
        comision = min(cobrado, comision)
        return {
            "bruto": bruto, "descuento": descuento, "cobrado": cobrado,
            "comision": comision, "neto": dinero(cobrado - comision),
        }

    @staticmethod
    def guardar(nombre, tipo, descuento, comision, comision_fija,
                afecta_efectivo=False, imagen=None, id_medio=None, activo=True):
        nombre = (nombre or "").strip()[:60]
        tipo = (tipo or "").strip().lower()
        if len(nombre) < 2:
            return "Ingresa el nombre del medio de pago."
        if tipo not in TIPOS_MEDIO:
            return "Selecciona un tipo de medio válido."
        try:
            descuento, comision = dinero(descuento), dinero(comision)
            comision_fija = dinero(comision_fija)
        except Exception:
            return "Los descuentos y comisiones deben ser números válidos."
        if not (0 <= descuento <= 100 and 0 <= comision <= 100) or comision_fija < 0:
            return "Los porcentajes deben estar entre 0 y 100 y la comisión fija no puede ser negativa."
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if id_medio:
                    cursor.execute("SELECT codigo,imagen FROM medioPago WHERE idMedioPago=%s", (id_medio,))
                    previa = cursor.fetchone()
                    if not previa:
                        return "El medio de pago no existe."
                    cursor.execute(
                        "UPDATE medioPago SET nombre=%s,tipo=%s,descuentoPorcentaje=%s,"
                        "comisionPorcentaje=%s,comisionFija=%s,afectaEfectivo=%s,activo=%s,"
                        "imagen=COALESCE(%s,imagen) WHERE idMedioPago=%s",
                        (nombre, tipo, descuento, comision, comision_fija,
                         1 if afecta_efectivo else 0, 1 if activo else 0,
                         imagen, id_medio))
                else:
                    codigo = _codigo(nombre)
                    if not codigo:
                        return "No se pudo generar un código para el medio."
                    cursor.execute(
                        "INSERT INTO medioPago(codigo,nombre,tipo,descuentoPorcentaje,"
                        "comisionPorcentaje,comisionFija,imagen,afectaEfectivo,activo) "
                        "VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                        (codigo, nombre, tipo, descuento, comision, comision_fija,
                         imagen, 1 if afecta_efectivo else 0, 1 if activo else 0))
            conexion.commit()
            return None
        except Exception as exc:
            conexion.rollback()
            if "Duplicate" in str(exc):
                return "Ya existe un medio de pago con ese nombre."
            return "No se pudo guardar el medio de pago."
        finally:
            conexion.close()

    @staticmethod
    def cambiar_estado(id_medio, activo):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("UPDATE medioPago SET activo=%s WHERE idMedioPago=%s",
                               (1 if activo else 0, id_medio))
            conexion.commit()
            return cursor.rowcount == 1
        finally:
            conexion.close()
