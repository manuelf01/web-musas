from bd import obtener_conexion


class Producto:
    @staticmethod
    def getProductosCategoria(id):
        conexion = obtener_conexion()
        productos = []
        with conexion.cursor() as cursor:
            if type(id) == str:
                cursor.execute(
                    "select p.* from producto p inner join categoriaProducto cp on cp.idCategoria = p.idCategoria where cp.nombreCategoria = %s order by p.idProducto", (id,))
            else:
                cursor.execute(
                    "select * from producto where idCategoria = %s order by idProducto", (id,))
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

        if nombre == "" or descripcion == "" or precio == "" or existencias == "" or idCategoria == "":
            return False

        nombre = nombre.strip()
        descripcion = descripcion.strip()
        precio = float(precio.strip()) if type(precio) == str else precio
        existencias = int(existencias.strip()) if type(
            existencias) == str else existencias
        idCategoria = int(idCategoria.strip()) if type(
            idCategoria) == str else idCategoria

        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO producto(idCategoria, nombre, descripcion, precio, existencias, imagen) "
                "VALUES (%s, %s, %s, %s, %s, %s)",
                (idCategoria, nombre, descripcion, precio, existencias, imagen or None),
            )
        conexion.commit()
        conexion.close()

    _COLS = ("p.idProducto, p.idCategoria, p.nombre, p.descripcion, p.precio, "
             "p.existencias, p.imagen, p.destacado, p.nota, cp.nombreCategoria")

    @staticmethod
    def _fila_a_dict(f):
        return {
            "idProducto": f[0], "idCategoria": f[1], "nombre": f[2],
            "descripcion": f[3], "precio": f[4], "existencias": f[5],
            "imagen": f[6], "destacado": f[7], "nota": f[8], "nombreCategoria": f[9],
        }

    @staticmethod
    def obtener_productos():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {Producto._COLS} FROM producto p "
                "INNER JOIN categoriaProducto cp ON p.idCategoria = cp.idCategoria "
                "ORDER BY p.idCategoria, p.idProducto"
            )
            productos = cursor.fetchall()
        conexion.close()
        return [Producto._fila_a_dict(f) for f in productos]

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
                "cp.nombreCategoria, p.idCategoria, p.imagen, p.destacado, p.nota "
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
        }

    @staticmethod
    def actualizar_producto(nombre, descripcion, precio, existencias, id, idCategoria, imagen=None):

        id = int(id)
        nombre = nombre.strip()
        descripcion = descripcion.strip()
        precio = float(precio.strip()) if type(precio) == str else precio
        existencias = int(existencias.strip()) if type(
            existencias) == str else existencias
        idCategoria = int(idCategoria.strip()) if type(
            idCategoria) == str else idCategoria

        if nombre == "" or descripcion == "" or precio == "" or existencias == "" or idCategoria == "":
            producto = Producto.obtener_producto_por_id(id)
            if nombre == "":
                nombre = producto["nombre"]
            if descripcion == "":
                descripcion = producto["descripcion"]
            if precio == "":
                precio = producto["precio"]
            if existencias == "":
                existencias = producto["existencias"]
            if idCategoria == "":
                idCategoria = producto["idCategoria"]

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
    def precios_por_ids(ids):
        """{ idProducto: {'nombre':..., 'precio':...} } para los ids dados."""
        ids = [int(i) for i in ids if str(i).isdigit()]
        if not ids:
            return {}
        marcadores = ",".join(["%s"] * len(ids))
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT idProducto, nombre, precio FROM producto WHERE idProducto IN ({marcadores})",
                ids,
            )
            filas = cursor.fetchall()
        conexion.close()
        return {f[0]: {"nombre": f[1], "precio": float(f[2])} for f in filas}

    @staticmethod
    def destacados(limite=8):
        """Productos marcados como destacados (para la fila 'favoritos' del inicio).
        Si no hay suficientes, completa con los de más existencias."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                f"SELECT {Producto._COLS} FROM producto p "
                "INNER JOIN categoriaProducto cp ON cp.idCategoria = p.idCategoria "
                "WHERE cp.nombreCategoria <> 'Cremas' "
                "ORDER BY (p.destacado IS NULL), p.existencias DESC, p.idProducto "
                "LIMIT %s",
                (limite,),
            )
            filas = cursor.fetchall()
        conexion.close()
        return [Producto._fila_a_dict(f) for f in filas]

    @staticmethod
    def contar_por_categoria():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
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
