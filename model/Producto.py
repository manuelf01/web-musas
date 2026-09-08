from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from bd import obtener_conexion


class Producto:
    COLUMNAS = """
        SELECT p.idProducto, p.idCategoria, p.nombre, p.descripcion,
               p.precio, p.existencias, p.imagen, cp.nombreCategoria
        FROM producto p
        INNER JOIN categoriaProducto cp ON p.idCategoria = cp.idCategoria
    """

    @staticmethod
    def _diccionario(fila):
        return {
            "idProducto": fila[0],
            "idCategoria": fila[1],
            "nombre": fila[2],
            "descripcion": fila[3],
            "precio": float(fila[4]),
            "existencias": fila[5],
            "imagen": fila[6],
            "nombreCategoria": fila[7],
        }

    @staticmethod
    def _precio(precio):
        try:
            valor = Decimal(str(precio).strip()).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, AttributeError, ValueError) as exc:
            raise ValueError("El precio no es válido") from exc
        if valor <= 0:
            raise ValueError("El precio debe ser mayor que cero")
        return valor

    @staticmethod
    def _stock(stock):
        try:
            valor = int(str(stock).strip())
        except (TypeError, ValueError) as exc:
            raise ValueError("El stock debe ser un número entero") from exc
        if valor < 0:
            raise ValueError("El stock no puede ser negativo")
        return valor

    @staticmethod
    def getProductosCategoria(categoria):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                if isinstance(categoria, str):
                    cursor.execute(
                        Producto.COLUMNAS + " WHERE cp.nombreCategoria = %s",
                        (categoria,),
                    )
                else:
                    cursor.execute(
                        Producto.COLUMNAS + " WHERE p.idCategoria = %s",
                        (categoria,),
                    )
                return [Producto._diccionario(fila) for fila in cursor.fetchall()]
        finally:
            conexion.close()

    @staticmethod
    def insertar_producto(nombre, descripcion, precio, stock, id_categoria, imagen=None):
        if not all((str(nombre).strip(), str(descripcion).strip(), str(id_categoria).strip())):
            return "Todos los campos son obligatorios"
        precio = Producto._precio(precio)
        stock = Producto._stock(stock)
        id_categoria = int(id_categoria)

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO producto(
                        idCategoria, nombre, descripcion, precio, existencias, imagen
                    ) VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_categoria,
                        str(nombre).strip(),
                        str(descripcion).strip(),
                        precio,
                        stock,
                        imagen,
                    ),
                )
            conexion.commit()
            return None
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def obtener_productos():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(Producto.COLUMNAS + " ORDER BY p.idProducto")
                return [Producto._diccionario(fila) for fila in cursor.fetchall()]
        finally:
            conexion.close()

    @staticmethod
    def eliminar_producto(id_producto):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("DELETE FROM producto WHERE idProducto = %s", (id_producto,))
            conexion.commit()
        finally:
            conexion.close()

    @staticmethod
    def obtener_producto_por_id(id_producto):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    Producto.COLUMNAS + " WHERE p.idProducto = %s",
                    (id_producto,),
                )
                fila = cursor.fetchone()
                return Producto._diccionario(fila) if fila else None
        finally:
            conexion.close()

    @staticmethod
    def actualizar_producto(
        nombre,
        descripcion,
        precio,
        stock_a_agregar,
        id_producto,
        id_categoria,
        imagen=None,
    ):
        producto = Producto.obtener_producto_por_id(id_producto)
        if producto is None:
            raise ValueError("El producto no existe")

        nombre = str(nombre).strip() or producto["nombre"]
        descripcion = str(descripcion).strip() or producto["descripcion"]
        precio = Producto._precio(precio if str(precio).strip() else producto["precio"])
        stock_a_agregar = Producto._stock(stock_a_agregar or 0)
        id_categoria = int(id_categoria or producto["idCategoria"])
        imagen_final = imagen or producto["imagen"]

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE producto
                    SET nombre = %s,
                        descripcion = %s,
                        precio = %s,
                        existencias = existencias + %s,
                        idCategoria = %s,
                        imagen = %s
                    WHERE idProducto = %s
                    """,
                    (
                        nombre,
                        descripcion,
                        precio,
                        stock_a_agregar,
                        id_categoria,
                        imagen_final,
                        id_producto,
                    ),
                )
            conexion.commit()
        except Exception:
            conexion.rollback()
            raise
        finally:
            conexion.close()

    @staticmethod
    def obtener_productos_limite():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    Producto.COLUMNAS
                    + """
                    WHERE (
                        SELECT COUNT(*) FROM producto p2
                        WHERE p2.idCategoria = p.idCategoria
                          AND p2.idProducto <= p.idProducto
                    ) <= 3
                    """
                )
                return [Producto._diccionario(fila) for fila in cursor.fetchall()]
        finally:
            conexion.close()

    @staticmethod
    def obtener_total_productos():
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM producto")
                return cursor.fetchone()[0]
        finally:
            conexion.close()

    @staticmethod
    def obtener_productos_paginacion(limite, start_index):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    Producto.COLUMNAS + " ORDER BY p.idProducto LIMIT %s OFFSET %s",
                    (limite, start_index - 1),
                )
                return [Producto._diccionario(fila) for fila in cursor.fetchall()]
        finally:
            conexion.close()
