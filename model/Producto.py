from bd import obtener_conexion

PRECIO_MAX = 100000     # tope defensivo


def _a_precio(valor):
    """Devuelve (precio_float, error). Nunca lanza."""
    try:
        p = round(float(str(valor).strip()), 2)
    except (TypeError, ValueError):
        return 0.0, "El precio debe ser un número (ej. 18.50)."
    if p < 0:
        return 0.0, "El precio no puede ser negativo."
    if p > PRECIO_MAX:
        return 0.0, f"El precio no puede pasar de S/ {PRECIO_MAX:,.0f}."
    return p, None


def _a_stock(valor):
    """Devuelve (stock_int, error). Nunca lanza."""
    try:
        s = int(float(str(valor).strip()))
    except (TypeError, ValueError):
        return 0, "Las existencias deben ser un número entero."
    if s < 0:
        return 0, "Las existencias no pueden ser negativas."
    return s, None


class Producto:

    @staticmethod
    def categoria_existe(id_categoria):
        try:
            idc = int(id_categoria)
        except (TypeError, ValueError):
            return False
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT 1 FROM categoriaProducto WHERE idCategoria = %s", (idc,))
            existe = cursor.fetchone() is not None
        conexion.close()
        return existe

    @staticmethod
    def getProductosCategoria(id):
        conexion = obtener_conexion()
        productos = []
        with conexion.cursor() as cursor:
            if type(id) == str:
                cursor.execute(
                    "select p.* from producto p inner join categoriaProducto cp on cp.idCategoria = p.idCategoria "
                    "where cp.nombreCategoria = %s and p.activo = 1 and cp.activo = 1 order by p.idProducto", (id,))
            else:
                cursor.execute(
                    "select p.* from producto p inner join categoriaProducto cp on cp.idCategoria = p.idCategoria "
                    "where p.idCategoria = %s and p.activo = 1 and cp.activo = 1 order by p.idProducto", (id,))
            productos = cursor.fetchall()
        conexion.close()

        if productos is None:
            return productos

        lista_diccionarios = []
        for producto in productos:
            diccionario = dict()
            diccionario["idProducto"] = producto[0]
            diccionario["idCategoria"] = producto[1]
            diccionario["nombre"] = producto[2]
            diccionario["descripcion"] = producto[3]
            diccionario["precio"] = producto[4]
            diccionario["existencias"] = producto[5]
            diccionario["imagen"] = producto[6] if len(producto) > 6 else None
            diccionario["destacado"] = producto[7] if len(producto) > 7 else None
            diccionario["nota"] = producto[8] if len(producto) > 8 else None
            lista_diccionarios.append(diccionario)
        return lista_diccionarios

    @staticmethod
    def insertar_producto(nombre, descripcion, precio, existencias, idCategoria, imagen=None):
        """Devuelve None si se creó, o un texto de error."""
        nombre = (nombre or "").strip()
        descripcion = (descripcion or "").strip()
        if not nombre or not descripcion or str(precio).strip() == "" \
                or str(existencias).strip() == "" or str(idCategoria).strip() == "":
            return "Completa todos los campos del producto."
        precio, err = _a_precio(precio)
        if err:
            return err
        existencias, err = _a_stock(existencias)
        if err:
            return err
        if not Producto.categoria_existe(idCategoria):
            return "La categoría seleccionada no existe."

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO producto(idCategoria, nombre, descripcion, precio, existencias, imagen) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (int(idCategoria), nombre[:100], descripcion[:255], precio, existencias, imagen or None),
            )
        conexion.commit()
        conexion.close()
        return None

    _COLS = ("p.idProducto, p.idCategoria, p.nombre, p.descripcion, p.precio, "
             "p.existencias, p.imagen, p.destacado, p.nota, cp.nombreCategoria, p.activo")

    @staticmethod
    def _fila_a_dict(f):
        return {
            "idProducto": f[0], "idCategoria": f[1], "nombre": f[2],
            "descripcion": f[3], "precio": f[4], "existencias": f[5],
            "imagen": f[6], "destacado": f[7], "nota": f[8], "nombreCategoria": f[9],
            "activo": bool(f[10]) if len(f) > 10 and f[10] is not None else True,
        }

    @staticmethod
    def obtener_productos(solo_activos=False):
        cond = " WHERE p.activo = 1 AND cp.activo = 1" if solo_activos else ""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {Producto._COLS} FROM producto p "
                "INNER JOIN categoriaProducto cp ON p.idCategoria = cp.idCategoria "
                f"{cond} ORDER BY p.idCategoria, p.idProducto"
            )
            productos = cursor.fetchall()
        conexion.close()
        return [Producto._fila_a_dict(f) for f in productos]

    @staticmethod
    def cambiar_estado(id, activo):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE producto SET activo = %s WHERE idProducto = %s",
                           (1 if activo else 0, id))
        conexion.commit()
        conexion.close()

    @staticmethod
    def sugeridos(ids_en_carrito, limite=4):
        """Complementos para 'Completa tu pedido' en el carrito: productos activos
        y con stock que aún no están en el carrito. Prioriza lo que le falta al
        pedido (bebida si hay comida, un postre, una salchipapa para compartir)
        y rellena con los destacados."""
        ids = set()
        for i in ids_en_carrito:
            try:
                ids.add(int(i))
            except (TypeError, ValueError):
                pass

        todos = Producto.obtener_productos(solo_activos=True)
        cat_por_id = {p["idProducto"]: p["nombreCategoria"] for p in todos}
        cats_carrito = {cat_por_id.get(i) for i in ids}
        tiene_bebida = "Bebidas" in cats_carrito
        tiene_postre = "Postres" in cats_carrito
        tiene_principal = bool(cats_carrito & {"Hamburguesas", "Salchipapas", "Combos"})

        disp = [p for p in todos
                if p["idProducto"] not in ids
                and (p["existencias"] or 0) > 0
                and p["nombreCategoria"] != "Cremas"]

        salida, vistos = [], set()

        def sumar(items, motivo, tope=2):
            n = 0
            for p in items:
                if len(salida) >= limite or n >= tope or p["idProducto"] in vistos:
                    continue
                vistos.add(p["idProducto"])
                n += 1
                salida.append({
                    "idProducto": p["idProducto"],
                    "nombre": p["nombre"],
                    "precio": float(p["precio"] or 0),
                    "imagen": p["imagen"],
                    "categoria": p["nombreCategoria"],
                    "motivo": motivo,
                })

        por_cat = lambda c: [p for p in disp if p["nombreCategoria"] == c]

        if tiene_principal and not tiene_bebida:
            sumar(por_cat("Bebidas"), "Para acompañar")
        if not tiene_postre:
            sumar(por_cat("Postres"), "El toque dulce")
        if tiene_principal and "Salchipapas" not in cats_carrito:
            sumar(por_cat("Salchipapas"), "Para compartir", tope=1)
        sumar([p for p in disp if p["destacado"]], "Los más pedidos", tope=limite)
        sumar(disp, "También te puede gustar", tope=limite)
        return salida[:limite]

    @staticmethod
    def eliminar_producto(id):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("DELETE FROM producto WHERE idProducto = %s", (id,))
            conexion.commit()
        finally:
            conexion.close()

    @staticmethod
    def obtener_producto_por_id(id):
        conexion = obtener_conexion()
        seleccion = None
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT p.idProducto, p.nombre, p.descripcion, p.precio, p.existencias, "
                "cp.nombreCategoria, p.idCategoria, p.imagen, p.destacado, p.nota, p.activo, cp.activo "
                "FROM producto p INNER JOIN categoriaProducto cp ON p.idCategoria = cp.idCategoria "
                "WHERE p.idProducto = %s", (id,))
            seleccion = cursor.fetchone()
        conexion.close()

        if seleccion is None:
            return seleccion

        return {
            "idProducto": seleccion[0],
            "nombre": seleccion[1],
            "descripcion": seleccion[2],
            "precio": seleccion[3],
            "existencias": seleccion[4],
            "nombreCategoria": seleccion[5],
            "idCategoria": seleccion[6],
            "imagen": seleccion[7],
            "destacado": seleccion[8],
            "nota": seleccion[9],
            "activo": bool(seleccion[10]) if seleccion[10] is not None else True,
            "categoriaActiva": bool(seleccion[11]) if seleccion[11] is not None else True,
            "disponibleTienda": bool(seleccion[10]) and bool(seleccion[11]),
        }

    @staticmethod
    def actualizar_producto(nombre, descripcion, precio, existencias, id, idCategoria, imagen=None):
        """Devuelve None si se actualizó, o un texto de error. Los campos vacíos
        conservan el valor actual."""
        try:
            id = int(id)
        except (TypeError, ValueError):
            return "Producto no válido."
        actual = Producto.obtener_producto_por_id(id)
        if actual is None:
            return "El producto ya no existe."

        nombre = (nombre or "").strip() or actual["nombre"]
        descripcion = (descripcion or "").strip() or actual["descripcion"]

        if str(precio).strip() == "":
            precio = actual["precio"]
        else:
            precio, err = _a_precio(precio)
            if err:
                return err

        if str(existencias).strip() == "":
            existencias = actual["existencias"]
        else:
            existencias, err = _a_stock(existencias)
            if err:
                return err

        if str(idCategoria).strip() == "":
            idCategoria = actual["idCategoria"]
        elif not Producto.categoria_existe(idCategoria):
            return "La categoría seleccionada no existe."
        idCategoria = int(idCategoria)
        nombre, descripcion = nombre[:100], descripcion[:255]

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            if imagen:
                # Solo se cambia la imagen si se subió una nueva.
                cursor.execute(
                    "UPDATE producto SET nombre=%s, descripcion=%s, precio=%s, existencias=%s, "
                    "idCategoria=%s, imagen=%s WHERE idProducto=%s",
                    (nombre, descripcion, precio, existencias, idCategoria, imagen, id),
                )
            else:
                cursor.execute(
                    "UPDATE producto SET nombre=%s, descripcion=%s, precio=%s, existencias=%s, "
                    "idCategoria=%s WHERE idProducto=%s",
                    (nombre, descripcion, precio, existencias, idCategoria, id),
                )
        conexion.commit()
        conexion.close()
        return None

    def obtener_productos_limite(por_categoria=4):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.idProducto, p.idCategoria, p.nombre, p.descripcion, p.precio,
                       p.existencias, p.imagen, p.destacado, p.nota, cp.nombreCategoria
                FROM producto p
                INNER JOIN categoriaProducto cp ON cp.idCategoria = p.idCategoria
                WHERE (SELECT COUNT(*) FROM producto x
                       WHERE x.idCategoria = p.idCategoria
                         AND x.idProducto <= p.idProducto) <= %s
                ORDER BY p.idCategoria, p.idProducto
                """,
                (por_categoria,),
            )
            productos = cursor.fetchall()
        conexion.close()

        return [
            {
                "idProducto": p[0],
                "idCategoria": p[1],
                "nombre": p[2],
                "descripcion": p[3],
                "precio": p[4],
                "existencias": p[5],
                "imagen": p[6],
                "destacado": p[7],
                "nota": p[8],
                "nombreCategoria": p[9],
            }
            for p in productos
        ]

    @staticmethod
    def precios_por_ids(ids, solo_cremas=False):
        """{ idProducto: {'nombre':..., 'precio':..., 'categoria':...} } para los ids
        dados, solo de productos activos de categorías activas. `solo_cremas=True`
        restringe a la categoría 'Cremas' (para que una hamburguesa no cuele como
        crema)."""
        ids = [int(i) for i in ids if str(i).strip().lstrip("-").isdigit() and int(i) > 0]
        if not ids:
            return {}
        marcadores = ",".join(["%s"] * len(ids))
        extra = " AND cp.nombreCategoria = 'Cremas'" if solo_cremas else ""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT p.idProducto, p.nombre, p.precio, cp.nombreCategoria FROM producto p "
                f"INNER JOIN categoriaProducto cp ON cp.idCategoria = p.idCategoria "
                f"WHERE p.idProducto IN ({marcadores}) AND p.activo = 1 AND cp.activo = 1{extra}",
                ids,
            )
            filas = cursor.fetchall()
        conexion.close()
        return {f[0]: {"nombre": f[1], "precio": float(f[2]), "categoria": f[3]} for f in filas}

    @staticmethod
    def destacados(limite=8):
        """Productos marcados como destacados (para la fila 'favoritos' del inicio).
        Si no hay suficientes, completa con los de más existencias."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {Producto._COLS} FROM producto p "
                "INNER JOIN categoriaProducto cp ON cp.idCategoria = p.idCategoria "
                "WHERE cp.nombreCategoria <> 'Cremas' AND p.activo = 1 AND cp.activo = 1 "
                "ORDER BY (p.destacado IS NULL), p.existencias DESC, p.idProducto "
                "LIMIT %s",
                (limite,),
            )
            filas = cursor.fetchall()
        conexion.close()
        return [Producto._fila_a_dict(f) for f in filas]

    @staticmethod
    def contar_por_categoria(solo_activos=False):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            if solo_activos:
                cursor.execute(
                    "SELECT p.idCategoria, COUNT(*) FROM producto p "
                    "INNER JOIN categoriaProducto cp ON cp.idCategoria = p.idCategoria "
                    "WHERE p.activo = 1 AND cp.activo = 1 GROUP BY p.idCategoria")
            else:
                cursor.execute("SELECT idCategoria, COUNT(*) FROM producto GROUP BY idCategoria")
            filas = cursor.fetchall()
        conexion.close()
        return {idc: n for idc, n in filas}

    def obtener_total_productos():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM producto")
            total = cursor.fetchone()
        conexion.close()
        return total[0]

    def obtener_productos_paginacion(limite, start_index):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {Producto._COLS} FROM producto p "
                "INNER JOIN categoriaProducto cp ON p.idCategoria = cp.idCategoria "
                "LIMIT %s OFFSET %s",
                (limite, (start_index - 1)),
            )
            productos = cursor.fetchall()
        conexion.close()
        return [Producto._fila_a_dict(f) for f in productos]
