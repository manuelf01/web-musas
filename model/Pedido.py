import os
import random

from bd import obtener_conexion
from datetime import datetime, timedelta, date


def _hora_env(nombre, defecto):
    """Lee una hora (0-24) de variable de entorno; si no es válida usa el defecto.
    Sirve para abrir el horario en local/demo sin tocar el código."""
    try:
        valor = int(os.environ.get(nombre, defecto))
        return valor if 0 <= valor <= 24 else defecto
    except (TypeError, ValueError):
        return defecto


class StockInsuficiente(Exception):
    """Se lanza cuando un producto del carrito ya no tiene existencias suficientes."""

    def __init__(self, nombre, disponible):
        self.nombre = nombre
        self.disponible = disponible
        super().__init__(f"Sin stock suficiente de {nombre}")


class LimitePedidos(Exception):
    """Se lanza cuando quien pide ya tiene demasiados pedidos sin recoger."""


# Pedido "activo" = hecho, aún no recogido, ni cancelado, ni marcado como no-show.
_ACTIVO = "estadoRecojo = 0 AND cancelado = 0 AND noShow = 0"
# Pedido que ocupa cupo de una franja = todo lo que no se canceló ni fue no-show
# (los ya recogidos sí ocuparon cocina, cuentan).
_OCUPA_CUPO = "cancelado = 0 AND noShow = 0"


class Pedido:

    cont = 0

    # --- Franjas de recojo ---------------------------------------------
    # Producción: 18–22 (6–10 p.m). En local se puede abrir con
    #   MUSAS_HORA_APERTURA / MUSAS_HORA_CIERRE  (p. ej. 0 y 24 para probar de noche).
    HORA_APERTURA = _hora_env("MUSAS_HORA_APERTURA", 18)   # 6:00 p.m
    HORA_CIERRE = _hora_env("MUSAS_HORA_CIERRE", 22)       # 10:00 p.m
    # MUSAS_DEMO=1 -> ignora el corte por hora ya pasada (solo para probar el
    # checkout fuera del horario). NUNCA activar en producción.
    DEMO = os.environ.get("MUSAS_DEMO", "0") == "1"
    FRANJA_MINUTOS = 30     # duración de cada franja
    CUPO_POR_FRANJA = 8     # pedidos máximos por franja
    ANTICIPACION_MIN = 20   # la cocina necesita este tiempo mínimo
    GRACIA_NOSHOW_MIN = 45  # min. tras la franja para marcar "no recogió"
    MAX_PEDIDOS_ACTIVOS = 2  # pedidos sin recoger simultáneos por DNI

    @staticmethod
    def _auto_no_show():
        """Marca como 'no recogió' los pedidos de hoy muy vencidos, devuelve stock
        y suma al contador del cliente. Se llama antes de leer franjas / panel."""
        # En modo demo el reloj no cuenta: no se auto-marca nada como no-show
        # (si no, los pedidos de prueba desaparecen apenas pasa su hora).
        if Pedido.DEMO:
            return
        ahora = datetime.now()
        corte = (ahora - timedelta(minutes=Pedido.GRACIA_NOSHOW_MIN)).strftime("%H:%M:%S")
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    f"SELECT idPedido, idUsuario FROM registroPedido "
                    f"WHERE fechaPedido = %s AND {_ACTIVO} AND horaRecojo < %s",
                    (ahora.date(), corte),
                )
                vencidos = cursor.fetchall()
                for id_pedido, id_usuario in vencidos:
                    cursor.execute(
                        "UPDATE registroPedido SET noShow = 1 WHERE idPedido = %s AND " + _ACTIVO,
                        (id_pedido,),
                    )
                    if cursor.rowcount != 1:
                        continue
                    Pedido._devolver_stock(cursor, id_pedido)
                    if id_usuario:
                        cursor.execute(
                            "UPDATE usuario SET noShows = noShows + 1 WHERE idUsuario = %s",
                            (id_usuario,),
                        )
            conexion.commit()
        finally:
            conexion.close()

    @staticmethod
    def _devolver_stock(cursor, id_pedido):
        """Suma de vuelta a `producto.existencias` lo que consumió un pedido."""
        cursor.execute(
            "SELECT idProducto, SUM(cantidad) FROM detalleOrden "
            "WHERE idPedido = %s GROUP BY idProducto",
            (id_pedido,),
        )
        for id_prod, cant in cursor.fetchall():
            cursor.execute(
                "UPDATE producto SET existencias = existencias + %s WHERE idProducto = %s",
                (cant, id_prod),
            )

    @staticmethod
    def _label_hora(hh, mm):
        h12 = hh - 12 if hh > 12 else (12 if hh == 0 else hh)
        sufijo = "p.m" if hh >= 12 else "a.m"
        return f"{h12}:{mm:02d} {sufijo}"

    @staticmethod
    def franjas_recojo():
        """
        Lista de franjas del día con su disponibilidad:
        [ { hora:'18:30', label:'6:30 p.m', disponible:bool,
            restantes:int, motivo:'pasada'|'llena'|None } ]
        """
        Pedido._auto_no_show()

        ahora = datetime.now()
        limite = ahora + timedelta(minutes=Pedido.ANTICIPACION_MIN)
        # Se usa la fecha del servidor de aplicacion (no CURDATE() de MySQL) para
        # que el conteo de cupos y el corte por hora esten siempre alineados.
        hoy = ahora.date()

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT horaRecojo, COUNT(*) FROM registroPedido "
                f"WHERE fechaPedido = %s AND {_OCUPA_CUPO} GROUP BY horaRecojo",
                (hoy,),
            )
            filas = cursor.fetchall()
        conexion.close()

        conteo = {}
        for h, n in filas:
            segundos = h.seconds if hasattr(h, "seconds") else 0
            clave = f"{segundos // 3600:02d}:{(segundos % 3600) // 60:02d}"
            conteo[clave] = conteo.get(clave, 0) + n

        franjas = []
        total_min = (Pedido.HORA_CIERRE - Pedido.HORA_APERTURA) * 60
        for m in range(0, total_min, Pedido.FRANJA_MINUTOS):
            hh = Pedido.HORA_APERTURA + m // 60
            mm = m % 60
            clave = f"{hh:02d}:{mm:02d}"
            inicio = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
            usados = conteo.get(clave, 0)
            pasada = (inicio < limite) and not Pedido.DEMO
            llena = usados >= Pedido.CUPO_POR_FRANJA
            franjas.append({
                "hora": clave,
                "label": Pedido._label_hora(hh, mm),
                "disponible": (not pasada) and (not llena),
                "restantes": max(0, Pedido.CUPO_POR_FRANJA - usados),
                "motivo": "pasada" if pasada else ("llena" if llena else None),
            })
        return franjas

    @staticmethod
    def franja_disponible(hora):
        """True si la franja 'HH:MM' existe y tiene cupo ahora mismo."""
        return any(f["hora"] == hora and f["disponible"] for f in Pedido.franjas_recojo())

    # ------------------------------------------------------------------
    # Crear un pedido completo (registroPedido + detalleOrden + detalleCremas)
    # en una sola transacción. Devuelve (idPedido, keyPedido).
    #   items = [ { idProducto, nombre, precioUnidad, cantidad, precioTotal,
    #               cremas: [ idCrema, ... ] } ]
    # ------------------------------------------------------------------
    @staticmethod
    def crear_pedido_completo(idUsuario, dni, nombres, telefono, hora_recojo,
                              estado_boleta, billetera_digital, notas, items):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                # --- 0. Límite de pedidos activos por persona -------------------
                if idUsuario:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM registroPedido WHERE idUsuario = %s AND {_ACTIVO}",
                        (idUsuario,),
                    )
                else:
                    cursor.execute(
                        f"SELECT COUNT(*) FROM registroPedido "
                        f"WHERE dniNoRegistrado = %s AND fechaPedido = %s AND {_ACTIVO}",
                        (dni, datetime.now().date()),
                    )
                if cursor.fetchone()[0] >= Pedido.MAX_PEDIDOS_ACTIVOS:
                    raise LimitePedidos()

                # --- 1. Control de stock (bloquea las filas de producto) --------
                unidades = {}
                for it in items:
                    unidades[it["idProducto"]] = unidades.get(it["idProducto"], 0) + it["cantidad"]
                if unidades:
                    marc = ",".join(["%s"] * len(unidades))
                    cursor.execute(
                        f"SELECT idProducto, nombre, existencias FROM producto "
                        f"WHERE idProducto IN ({marc}) FOR UPDATE",
                        list(unidades.keys()),
                    )
                    stock = {r[0]: (r[1], r[2] or 0) for r in cursor.fetchall()}
                    for id_prod, pedidas in unidades.items():
                        nombre_p, disp = stock.get(id_prod, ("Producto", 0))
                        if pedidas > disp:
                            raise StockInsuficiente(nombre_p, disp)

                cursor.execute("SELECT COALESCE(MAX(idPedido), 0) + 1 FROM registroPedido")
                id_pedido = cursor.fetchone()[0]

                # keyPedido: 4 dígitos, único entre los pedidos aún no recogidos
                key = random.randint(1000, 9999)
                for _ in range(40):
                    cursor.execute(
                        "SELECT 1 FROM registroPedido WHERE keyPedido = %s AND estadoRecojo = 0",
                        (key,),
                    )
                    if cursor.fetchone() is None:
                        break
                    key = random.randint(1000, 9999)

                cursor.execute(
                    """INSERT INTO registroPedido
                       (idPedido, idUsuario, dniNoRegistrado, nombres, numeroTelefono,
                        estadoRecojo, horaRecojo, estadoBoleta, billeteraDigital,
                        keyPedido, notas)
                       VALUES (%s, %s, %s, %s, %s, 0, %s, %s, %s, %s, %s)""",
                    (id_pedido, idUsuario, dni, nombres, telefono, hora_recojo,
                     1 if estado_boleta else 0, 1 if billetera_digital else 0,
                     key, notas or None),
                )

                cursor.execute("SELECT COALESCE(MAX(idDetalleOrden), 0) FROM detalleOrden")
                siguiente_detalle = cursor.fetchone()[0]

                for it in items:
                    siguiente_detalle += 1
                    cursor.execute(
                        """INSERT INTO detalleOrden
                           (idDetalleOrden, idPedido, idProducto, nombreProducto,
                            precioUnidad, cantidad, precioTotal)
                           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                        (siguiente_detalle, id_pedido, it["idProducto"], it["nombre"],
                         it["precioUnidad"], it["cantidad"], it["precioTotal"]),
                    )
                    for id_crema in it.get("cremas", []):
                        cursor.execute(
                            """INSERT INTO detalleCremas (idPedido, idCrema, idDetalleOrden)
                               VALUES (%s, %s, %s)""",
                            (id_pedido, id_crema, siguiente_detalle),
                        )

                # --- 2. Descuento de existencias (se reserva el stock) --------
                for id_prod, pedidas in unidades.items():
                    cursor.execute(
                        "UPDATE producto SET existencias = existencias - %s WHERE idProducto = %s",
                        (pedidas, id_prod),
                    )
                # El comprobante NO se emite aquí: el pago es al recoger, así que
                # se genera en marcar_recogido() (venta realmente cobrada).

            conexion.commit()
            return id_pedido, key
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    # ------------------------------------------------------------------
    # Comprobante: se emite al ENTREGAR el pedido (cuando se cobra). Alimenta
    # el módulo de Ventas del panel (tablas comprobante / detalleComprobante).
    # ------------------------------------------------------------------
    @staticmethod
    def _emitir_comprobante(cursor, id_pedido):
        cursor.execute(
            "SELECT idUsuario, dniNoRegistrado, estadoBoleta FROM registroPedido WHERE idPedido = %s",
            (id_pedido,),
        )
        id_usuario, dni, boleta = cursor.fetchone()

        cursor.execute(
            "SELECT idProducto, nombreProducto, SUM(cantidad), SUM(precioTotal) "
            "FROM detalleOrden WHERE idPedido = %s GROUP BY idProducto, nombreProducto",
            (id_pedido,),
        )
        lineas = cursor.fetchall()
        total = round(sum(float(l[3] or 0) for l in lineas), 2)
        sub_total = round(total / 1.18, 2)
        igv = round(total - sub_total, 2)
        ahora = datetime.now()
        serie = "B001" if boleta else "NV01"

        cursor.execute(
            """INSERT INTO comprobante
               (idPedido, idUsuario, dniNoRegistrado, fechaComprobante, horaComprobante,
                subTotal, montoTotal, igv, numeroComprobante)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (id_pedido, id_usuario, dni, ahora.date(), ahora.strftime("%H:%M:%S"),
             sub_total, total, igv, "PENDIENTE"),
        )
        id_comp = cursor.lastrowid
        cursor.execute(
            "UPDATE comprobante SET numeroComprobante = %s WHERE idComprobante = %s",
            (f"{serie}-{id_comp:08d}", id_comp),
        )
        for id_prod, nombre, cant, sub in lineas:
            cant = int(cant or 0)
            sub = round(float(sub or 0), 2)
            cursor.execute(
                """INSERT INTO detalleComprobante
                   (idComprobante, idProducto, nombreProducto, precioUnidad, cantidad, precioTotal)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (id_comp, id_prod, nombre, round(sub / cant, 2) if cant else 0, cant, sub),
            )
        return id_comp

    @staticmethod
    def cancelar_pedido(id_pedido, id_usuario=None, dni=None, saltar_dueno=False):
        """Cancela un pedido pendiente: libera el cupo y devuelve el stock.
        `saltar_dueno=True` cuando el llamador ya verificó la propiedad (admin o
        pedido de invitado presente en la sesión).
        Devuelve 'ok' | 'no_permitido' | 'no_cancelable'."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idUsuario, dniNoRegistrado, estadoRecojo, cancelado, noShow "
                    "FROM registroPedido WHERE idPedido = %s",
                    (id_pedido,),
                )
                fila = cursor.fetchone()
                if fila is None:
                    return "no_cancelable"
                if not saltar_dueno:
                    mismo = (id_usuario and fila[0] == id_usuario) or (dni and fila[1] == dni)
                    if not mismo:
                        return "no_permitido"
                if fila[2] == 1 or fila[3] == 1 or fila[4] == 1:
                    return "no_cancelable"

                cursor.execute(
                    "UPDATE registroPedido SET cancelado = 1 WHERE idPedido = %s AND " + _ACTIVO,
                    (id_pedido,),
                )
                if cursor.rowcount != 1:
                    return "no_cancelable"
                Pedido._devolver_stock(cursor, id_pedido)
            conexion.commit()
            return "ok"
        finally:
            conexion.close()

    @staticmethod
    def marcar_no_show(id_pedido):
        """El admin marca que el cliente no vino. Libera cupo, devuelve stock y
        suma al contador del cliente. Devuelve bool."""
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT idUsuario FROM registroPedido WHERE idPedido = %s AND " + _ACTIVO,
                    (id_pedido,),
                )
                fila = cursor.fetchone()
                if fila is None:
                    return False
                cursor.execute(
                    "UPDATE registroPedido SET noShow = 1 WHERE idPedido = %s AND " + _ACTIVO,
                    (id_pedido,),
                )
                if cursor.rowcount != 1:
                    return False
                Pedido._devolver_stock(cursor, id_pedido)
                if fila[0]:
                    cursor.execute(
                        "UPDATE usuario SET noShows = noShows + 1 WHERE idUsuario = %s",
                        (fila[0],),
                    )
            conexion.commit()
            return True
        finally:
            conexion.close()

    @staticmethod
    def pedidos_de_hoy(estado=None):
        """Pedidos de hoy con líneas + cremas, para el panel de Pedidos.
        estado: None | 'pendiente' | 'recogido'. No incluye cancelados ni no-shows."""
        Pedido._auto_no_show()

        cond = " AND rp.cancelado = 0 AND rp.noShow = 0"
        if estado == "pendiente":
            cond += " AND rp.estadoRecojo = 0"
        elif estado == "recogido":
            cond += " AND rp.estadoRecojo = 1"

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT rp.idPedido, rp.dniNoRegistrado, rp.nombres, rp.numeroTelefono, "
                "rp.estadoRecojo, rp.horaRecojo, rp.estadoBoleta, rp.billeteraDigital, "
                "rp.keyPedido, rp.notas, COALESCE(u.noShows, 0) "
                "FROM registroPedido rp LEFT JOIN usuario u ON u.idUsuario = rp.idUsuario "
                f"WHERE rp.fechaPedido = %s{cond} "
                "ORDER BY rp.estadoRecojo, rp.horaRecojo, rp.idPedido",
                (date.today(),),
            )
            cab = cursor.fetchall()
            if not cab:
                conexion.close()
                return []

            ids = [c[0] for c in cab]
            marc = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"SELECT dor.idPedido, dor.idDetalleOrden, dor.nombreProducto, dor.precioUnidad, "
                f"dor.cantidad, dor.precioTotal, p.imagen "
                f"FROM detalleOrden dor LEFT JOIN producto p ON p.idProducto = dor.idProducto "
                f"WHERE dor.idPedido IN ({marc}) ORDER BY dor.idPedido, dor.idDetalleOrden",
                ids,
            )
            lin = cursor.fetchall()
            cursor.execute(
                f"SELECT dc.idPedido, dc.idDetalleOrden, p.nombre "
                f"FROM detalleCremas dc LEFT JOIN producto p ON p.idProducto = dc.idCrema "
                f"WHERE dc.idPedido IN ({marc})",
                ids,
            )
            cre = cursor.fetchall()
        conexion.close()

        cremas_idx = {}
        for ped, det, nom in cre:
            cremas_idx.setdefault((ped, det), []).append(nom or "Crema")

        lin_idx = {}
        for ped, det, nom, pu, cant, pt, img in lin:
            lin_idx.setdefault(ped, []).append({
                "nombre": nom,
                "precioUnidad": float(pu or 0),
                "cantidad": cant,
                "precioTotal": float(pt or 0),
                "imagen": img,
                "cremas": cremas_idx.get((ped, det), []),
            })

        salida = []
        for c in cab:
            hora = str(timedelta(seconds=c[5].seconds))[:5] if hasattr(c[5], "seconds") else str(c[5])[:5]
            its = lin_idx.get(c[0], [])
            nombre = c[2] or "Invitado"
            salida.append({
                "idPedido": c[0],
                "cliente": nombre,
                "iniciales": "".join(x[0] for x in nombre.split()[:2]).upper() or "?",
                "dni": (c[1][:4] + "****") if c[1] else "",
                "telefono": c[3],
                "recogido": bool(c[4]),
                "hora": hora,
                "boleta": bool(c[6]),
                "digital": bool(c[7]),
                "keyPedido": c[8],
                "notas": c[9],
                "noShows": int(c[10] or 0),
                "lineas": its,
                "total": round(sum(i["precioTotal"] for i in its), 2),
            })
        return salida

    @staticmethod
    def marcar_recogido(id_pedido, key):
        """'ok' | 'clave_mal' | 'no_existe' (ya recogido, cancelado o inexistente).
        Al entregar se emite el comprobante (la venta se cobra en este momento)
        y queda visible en el módulo de Ventas del panel."""
        key = str(key).strip()
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT keyPedido, estadoRecojo, cancelado, noShow "
                    "FROM registroPedido WHERE idPedido = %s",
                    (id_pedido,),
                )
                fila = cursor.fetchone()
                if fila is None or fila[1] == 1 or fila[2] == 1 or fila[3] == 1:
                    return "no_existe"
                if str(fila[0]).strip() != key:
                    return "clave_mal"
                # Update guardado: solo pasa si sigue activo y la clave coincide.
                cursor.execute(
                    "UPDATE registroPedido SET estadoRecojo = 1 "
                    "WHERE idPedido = %s AND " + _ACTIVO + " AND keyPedido = %s",
                    (id_pedido, key),
                )
                if cursor.rowcount != 1:
                    return "no_existe"
                Pedido._emitir_comprobante(cursor, id_pedido)
            conexion.commit()
            return "ok"
        finally:
            conexion.close()

    @staticmethod
    def contadores_hoy():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(estadoRecojo = 0), 0), COALESCE(SUM(estadoRecojo = 1), 0) "
                "FROM registroPedido WHERE fechaPedido = %s AND cancelado = 0 AND noShow = 0",
                (date.today(),),
            )
            t, p, r = cursor.fetchone()
        conexion.close()
        return {"todos": int(t or 0), "pendiente": int(p or 0), "recogido": int(r or 0)}

    @staticmethod
    def resumen_dashboard():
        """KPIs + pedidos recientes + top productos + ventas 7 días para el panel."""
        Pedido._auto_no_show()
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*), COALESCE(SUM(estadoRecojo = 0), 0), COALESCE(SUM(noShow = 1), 0) "
                "FROM registroPedido WHERE fechaPedido = %s AND cancelado = 0",
                (date.today(),),
            )
            n_hoy, pendientes, no_shows_hoy = cursor.fetchone()
            n_hoy = int(n_hoy or 0)
            pendientes = int(pendientes or 0)
            no_shows_hoy = int(no_shows_hoy or 0)

            cursor.execute(
                "SELECT COALESCE(SUM(dor.precioTotal), 0) FROM detalleOrden dor "
                "INNER JOIN registroPedido r ON r.idPedido = dor.idPedido "
                "WHERE r.fechaPedido = %s AND r.cancelado = 0 AND r.noShow = 0",
                (date.today(),),
            )
            ventas_hoy = float(cursor.fetchone()[0] or 0)
            ticket = ventas_hoy / n_hoy if n_hoy else 0.0

            cursor.execute(
                "SELECT idPedido, dniNoRegistrado, nombres, horaRecojo, estadoRecojo "
                "FROM registroPedido WHERE cancelado = 0 AND noShow = 0 "
                "ORDER BY idPedido DESC LIMIT 6"
            )
            cabeceras = cursor.fetchall()
            recientes = []
            for r in cabeceras:
                cursor.execute(
                    "SELECT nombreProducto, cantidad, precioTotal FROM detalleOrden WHERE idPedido = %s",
                    (r[0],),
                )
                det = cursor.fetchall()
                total = sum(float(d[2] or 0) for d in det)
                resumen = ", ".join(f"{d[1]}× {d[0]}" for d in det[:2])
                if len(det) > 2:
                    resumen += f"  +{len(det) - 2}"
                nombre = r[2] or "Invitado"
                hora = str(timedelta(seconds=r[3].seconds))[:5] if hasattr(r[3], "seconds") else str(r[3])[:5]
                recientes.append({
                    "idPedido": r[0],
                    "cliente": nombre,
                    "iniciales": "".join(p[0] for p in nombre.split()[:2]).upper() or "?",
                    "dni": (r[1][:4] + "****") if r[1] else "",
                    "detalle": resumen or "—",
                    "hora": hora,
                    "total": round(total, 2),
                    "recogido": bool(r[4]),
                })

            cursor.execute(
                "SELECT p.nombre, p.precio, p.imagen, SUM(dor.cantidad) AS uds "
                "FROM detalleOrden dor "
                "INNER JOIN registroPedido r ON r.idPedido = dor.idPedido "
                "LEFT JOIN producto p ON p.idProducto = dor.idProducto "
                "WHERE r.fechaPedido >= CURDATE() - INTERVAL 7 DAY AND r.cancelado = 0 AND r.noShow = 0 "
                "GROUP BY dor.idProducto, p.nombre, p.precio, p.imagen "
                "ORDER BY uds DESC LIMIT 5"
            )
            top_raw = cursor.fetchall()
            max_uds = max((int(t[3]) for t in top_raw), default=1) or 1
            top = [{
                "nombre": t[0] or "—",
                "precio": float(t[1] or 0),
                "imagen": t[2],
                "uds": int(t[3]),
                "pct": round(int(t[3]) / max_uds * 100),
            } for t in top_raw]

            cursor.execute(
                "SELECT r.fechaPedido, COALESCE(SUM(dor.precioTotal), 0) "
                "FROM registroPedido r "
                "LEFT JOIN detalleOrden dor ON dor.idPedido = r.idPedido "
                "WHERE r.fechaPedido >= CURDATE() - INTERVAL 6 DAY AND r.cancelado = 0 AND r.noShow = 0 "
                "GROUP BY r.fechaPedido"
            )
            por_dia = {str(row[0]): float(row[1] or 0) for row in cursor.fetchall()}
        conexion.close()

        hoy = date.today()
        semanas_dias = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
        dias = []
        for i in range(6, -1, -1):
            d = hoy - timedelta(days=i)
            dias.append({
                "label": f"{semanas_dias[d.weekday()]} {d.day}",
                "monto": por_dia.get(str(d), 0.0),
                "hoy": i == 0,
            })
        max_dia = max((x["monto"] for x in dias), default=1) or 1
        for x in dias:
            x["pct"] = round(x["monto"] / max_dia * 100) if max_dia else 0

        return {
            "pedidos_hoy": n_hoy,
            "pendientes": pendientes,
            "no_shows_hoy": no_shows_hoy,
            "ventas_hoy": round(ventas_hoy, 2),
            "ticket": round(ticket, 2),
            "recientes": recientes,
            "top": top,
            "ventas_semana": dias,
            "total_semana": round(sum(x["monto"] for x in dias), 2),
        }

    @staticmethod
    def historial_cliente(id_usuario):
        """Pedidos del cliente (más reciente primero). El total mostrado es el que
        el cliente pagó (snapshot en detalleOrden); el precio/disponibilidad ACTUAL
        del producto solo se usa para 'repetir pedido'."""
        Pedido._auto_no_show()
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT idPedido, estadoRecojo, horaRecojo, fechaPedido, estadoBoleta, "
                "billeteraDigital, keyPedido, cancelado, noShow FROM registroPedido "
                "WHERE idUsuario = %s ORDER BY idPedido DESC",
                (id_usuario,),
            )
            cabeceras = cursor.fetchall()
            if not cabeceras:
                conexion.close()
                return []

            ids = [c[0] for c in cabeceras]
            marc = ",".join(["%s"] * len(ids))
            cursor.execute(
                f"SELECT dor.idPedido, dor.idDetalleOrden, dor.idProducto, dor.cantidad, "
                f"dor.nombreProducto, p.precio, p.imagen, dor.precioTotal "
                f"FROM detalleOrden dor LEFT JOIN producto p ON p.idProducto = dor.idProducto "
                f"WHERE dor.idPedido IN ({marc}) ORDER BY dor.idPedido, dor.idDetalleOrden",
                ids,
            )
            lineas = cursor.fetchall()
            cursor.execute(
                f"SELECT dc.idPedido, dc.idDetalleOrden, dc.idCrema, p.nombre, p.precio "
                f"FROM detalleCremas dc LEFT JOIN producto p ON p.idProducto = dc.idCrema "
                f"WHERE dc.idPedido IN ({marc})",
                ids,
            )
            cremas = cursor.fetchall()
        conexion.close()

        cremas_idx = {}
        for ped, det, idc, nom, pr in cremas:
            cremas_idx.setdefault((ped, det), []).append({
                "idProducto": idc,
                "nombre": nom or "Crema",
                "precio": float(pr) if pr is not None else 0.0,
            })

        lineas_idx = {}
        for ped, det, idp, cant, nom_snap, precio, imagen, pagado in lineas:
            lineas_idx.setdefault(ped, []).append({
                "idProducto": idp,
                "nombre": nom_snap,
                "precio": float(precio) if precio is not None else None,
                "pagado": float(pagado or 0),
                "imagen": imagen,
                "cantidad": cant,
                "disponible": precio is not None,
                "cremas": cremas_idx.get((ped, det), []),
            })

        salida = []
        for c in cabeceras:
            hora = str(timedelta(seconds=c[2].seconds))[:5] if hasattr(c[2], "seconds") else str(c[2])[:5]
            fecha = c[3].strftime("%d/%m/%Y") if hasattr(c[3], "strftime") else str(c[3])
            its = lineas_idx.get(c[0], [])
            total = sum(it["pagado"] for it in its)
            recogido, cancelado, no_show = bool(c[1]), bool(c[7]), bool(c[8])
            if recogido:
                estado = "recogido"
            elif cancelado:
                estado = "cancelado"
            elif no_show:
                estado = "no_show"
            else:
                estado = "pendiente"
            salida.append({
                "idPedido": c[0],
                "recogido": recogido,
                "estado": estado,
                "cancelable": estado == "pendiente",
                "hora": hora,
                "fecha": fecha,
                "boleta": bool(c[4]),
                "digital": bool(c[5]),
                "keyPedido": c[6],
                "lineas": its,
                "total": round(total, 2),
            })
        return salida

    @staticmethod
    def obtener_pedido_completo(id_pedido):
        """Pedido + sus líneas + cremas, para la página de confirmación."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT idPedido, idUsuario, dniNoRegistrado, nombres, numeroTelefono, "
                "estadoRecojo, cancelado, noShow, horaRecojo, estadoBoleta, billeteraDigital, "
                "keyPedido, notas FROM registroPedido WHERE idPedido = %s",
                (id_pedido,),
            )
            p = cursor.fetchone()
            if p is None:
                conexion.close()
                return None

            cursor.execute(
                "SELECT idDetalleOrden, idProducto, nombreProducto, precioUnidad, cantidad, precioTotal "
                "FROM detalleOrden WHERE idPedido = %s ORDER BY idDetalleOrden", (id_pedido,))
            filas = cursor.fetchall()

            cursor.execute(
                "SELECT dc.idDetalleOrden, pr.nombre, pr.precio "
                "FROM detalleCremas dc INNER JOIN producto pr ON pr.idProducto = dc.idCrema "
                "WHERE dc.idPedido = %s", (id_pedido,))
            cremas_raw = cursor.fetchall()
        conexion.close()

        cremas_por_detalle = {}
        for id_det, nombre, precio in cremas_raw:
            cremas_por_detalle.setdefault(id_det, []).append({"nombre": nombre, "precio": precio})

        hora = str(timedelta(seconds=p[8].seconds)) if hasattr(p[8], "seconds") else str(p[8])
        items = [
            {
                "nombre": f[2],
                "precioUnidad": f[3],
                "cantidad": f[4],
                "precioTotal": f[5],
                "cremas": cremas_por_detalle.get(f[0], []),
            }
            for f in filas
        ]
        return {
            "idPedido": p[0],
            "idUsuario": p[1],
            "dni": p[2],
            "nombres": p[3],
            "telefono": p[4],
            "estadoRecojo": p[5],
            "cancelado": bool(p[6]),
            "noShow": bool(p[7]),
            "horaRecojo": hora[:5] if len(hora) >= 5 else hora,
            "estadoBoleta": p[9],
            "billeteraDigital": p[10],
            "keyPedido": p[11],
            "notas": p[12],
            "lineas": items,
            "total": sum(i["precioTotal"] for i in items),
        }

    @staticmethod
    def get_pedidos():
        with obtener_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM registroPedido")
                pedidos = cursor.fetchall()

        if pedidos is None:
            return pedidos
        return Pedido.diccionario_pedidos(pedidos)

    def get_pedido_por_id_pedido(idPedido):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM registroPedido WHERE idPedido = %s", (idPedido))
            pedido = cursor.fetchone()
        conexion.close()
        return pedido

    @staticmethod
    def get_pedidos_por_dni(dni):
        with obtener_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM registroPedido WHERE dniNoRegistrado = %s", (dni))
                pedidos = cursor.fetchall()
        if pedidos is None:
            return pedidos
        return Pedido.diccionario_pedidos(pedidos)

    @staticmethod
    def get_pedidos_por_id(id):
        with obtener_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT * FROM registroPedido WHERE idUsuario = %s", (id))
                pedidos = cursor.fetchall()
        if pedidos is None:
            return pedidos
        return Pedido.diccionario_pedidos(pedidos)

    @staticmethod
    def actualizar_estado_recojo(keyPedido):
        with obtener_conexion() as conexion:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "SELECT estadoRecojo FROM registroPedido WHERE keyPedido = %s and estadoRecojo = 0", (keyPedido))
                seleccion = cursor.fetchone()
            if seleccion is not None:
                with conexion.cursor() as cursor:
                    cursor.execute(
                        "UPDATE registroPedido SET estadoRecojo = %s WHERE keyPedido = %s and estadoRecojo = 0", (True, keyPedido))
                    conexion.commit()
                    return True
            else:
                return False

    @staticmethod
    def diccionario_pedidos(pedidos):
        # Orden de columnas de registroPedido (tras migraciones 004 y 006):
        # 0 idPedido 1 idUsuario 2 dniNoRegistrado 3 nombres 4 numeroTelefono
        # 5 estadoRecojo 6 cancelado 7 noShow 8 horaRecojo 9 fechaPedido
        # 10 estadoBoleta 11 billeteraDigital 12 keyPedido 13 notas
        list = []
        for pedido in pedidos:
            diccionario = dict()
            horaRecojo = str(timedelta(seconds=pedido[8].seconds))
            fechaPedido = str(
                date(year=pedido[9].year, month=pedido[9].month, day=pedido[9].day))

            diccionario['idPedido'] = pedido[0]
            diccionario["idUsuario"] = pedido[1]
            diccionario["dniNoRegistrado"] = pedido[2]
            diccionario["nombres"] = pedido[3]
            diccionario["numeroTelefono"] = pedido[4]
            if pedido[6] == 1:
                diccionario["estadoRecojo"] = "Cancelado"
            elif pedido[7] == 1:
                diccionario["estadoRecojo"] = "No recogido"
            elif pedido[5] == 1:
                diccionario["estadoRecojo"] = "Recogido"
            else:
                diccionario["estadoRecojo"] = "En proceso"
            diccionario["horaRecojo"] = horaRecojo
            diccionario["fechaPedido"] = fechaPedido
            diccionario["estadoBoleta"] = "Si" if pedido[10] == 1 else "No"
            diccionario["billeteraDigital"] = "Si" if pedido[11] == 1 else "No"
            diccionario["keyPedido"] = pedido[12]
            list.append(diccionario)
        return list

    def validar_idPedido_existente(idPedido):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            consulta = "SELECT COUNT(*) FROM registroPedido WHERE idPedido = %s"
            cursor.execute(consulta, (idPedido,))
            resultado = cursor.fetchone()
        if resultado[0] > 0:
            return True
        else:
            return False

    def obtener_dni_pedido(idPedido):
        conexion = obtener_conexion()
        juego = None
        with conexion.cursor() as cursor:
            cursor.execute(
                "select idUsuario, dniNoRegistrado from registroPedido where idPedido = %s", (idPedido))
            juego = cursor.fetchone()
        conexion.close()
        return juego

    def obtener_id_pedido_registro():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT coalesce(max(idPedido),0)+1 as idpedido FROM registroPedido")
            idPedido = cursor.fetchone()
        conexion.close()
        return idPedido[0]

    def validate_key_pedido(idPedido, keyPedido):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT keyPedido FROM registroPedido WHERE idPedido = %s and keyPedido = %s", (idPedido, keyPedido))
            key = cursor.fetchone()
        conexion.close()
        if key is None:
            return False
        return True

    def get_pedidos_ordenados_horarios(per_page, start_index):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "select * from registroPedido where estadoRecojo = false and fechaPedido = (select current_date()) order by horaRecojo limit %s offset %s;", (per_page, start_index-1))
            pedidos = cursor.fetchall()
        conexion.close()
        return Pedido.diccionario_pedidos(pedidos)

    def total():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "select count(*) from registroPedido where estadoRecojo = false and fechaPedido = (select current_date())")
            total = cursor.fetchone()
        conexion.close()
        return total[0]
