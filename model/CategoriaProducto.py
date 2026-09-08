from bd import obtener_conexion

class CategoriaProducto:
    idCategoria = 0
    nombreCategoria = ""
    descripcion = ""
    midic = dict()

    def __init__(self,p_idCategoria,p_nombreCategoria,p_descripcion):
        self.idCategoria = p_idCategoria
        self.nombreCategoria = p_nombreCategoria
        self.descripcion = p_descripcion
        self.midic["idCategoria"] = p_idCategoria
        self.midic["nombreCategoria"] = p_nombreCategoria
        self.midic["descripcion"] = p_descripcion


    @staticmethod
    def insertar_categoria(nombreCategoria, descripcion, imagen=None):
        """Devuelve None si se creó, o un texto de error."""
        nombre = (nombreCategoria or "").strip()
        if len(nombre) < 2:
            return "El nombre de la categoría es obligatorio (mínimo 2 caracteres)."
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categoriaProducto(nombreCategoria, descripcion, imagen) VALUES (%s, %s, %s)",
                (nombre[:50], (descripcion or "").strip()[:255] or None, imagen or None),
            )
        conexion.commit()
        conexion.close()
        return None

    def obtener_categorias(solo_activas=False):
        conexion = obtener_conexion()
        categoria = []
        with conexion.cursor() as cursor:
            if solo_activas:
                cursor.execute("SELECT * FROM categoriaProducto WHERE activo = 1 ORDER BY idCategoria")
            else:
                cursor.execute("SELECT * FROM categoriaProducto ORDER BY idCategoria")
            categoria = cursor.fetchall()
        conexion.close()
        return categoria

    @staticmethod
    def cambiar_estado(idCategoria, activo):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE categoriaProducto SET activo = %s WHERE idCategoria = %s",
                           (1 if activo else 0, idCategoria))
        conexion.commit()
        conexion.close()

    def eliminar_categoria(idCategoria):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("DELETE FROM categoriaProducto WHERE idCategoria = %s", (idCategoria,))
            conexion.commit()
        finally:
            conexion.close()


    def obtener_categoria_por_id(idCategoria):
        conexion = obtener_conexion()
        juego = None
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT idCategoria, nombreCategoria, descripcion, imagen FROM categoriaProducto WHERE idCategoria = %s",
                (idCategoria,))
            juego = cursor.fetchone()
        conexion.close()
        return juego

    def actualizar_categoria(nombreCategoria, descripcion, id, imagen=None):
        """Devuelve None si se actualizó, o un texto de error."""
        nombre = (nombreCategoria or "").strip()
        if len(nombre) < 2:
            return "El nombre de la categoría es obligatorio (mínimo 2 caracteres)."
        nombre = nombre[:50]
        descripcion = (descripcion or "").strip()[:255] or None
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            if imagen:
                cursor.execute(
                    "UPDATE categoriaProducto SET nombreCategoria=%s, descripcion=%s, imagen=%s WHERE idCategoria=%s",
                    (nombre, descripcion, imagen, id))
            else:
                cursor.execute(
                    "UPDATE categoriaProducto SET nombreCategoria=%s, descripcion=%s WHERE idCategoria=%s",
                    (nombre, descripcion, id))
        conexion.commit()
        conexion.close()
        return None


    # def obtener_idcategoria_por_nombre(nombreCategoria):
    #     conexion = obtener_conexion()   
    #     Cat = None
    #     with conexion.cursor() as cursor:
    #         cursor.execute("Select idCategoria FROM categoriaProducto WHERE nombreCategoria=%s",(nombreCategoria))
    #         Cat = cursor.fetchone()
    #     conexion.close()
    #     return Cat