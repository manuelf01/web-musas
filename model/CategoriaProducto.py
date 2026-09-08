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
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO categoriaProducto(nombreCategoria, descripcion, imagen) VALUES (%s, %s, %s)",
                (nombreCategoria, descripcion, imagen or None),
            )
        conexion.commit()
        conexion.close()

    def obtener_categorias():
        conexion = obtener_conexion()
        categoria = []
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM categoriaProducto")
            categoria = cursor.fetchall()
        conexion.close()
        return categoria

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
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            if imagen:
                cursor.execute(
                    "UPDATE categoriaProducto SET nombreCategoria=%s, descripcion=%s, imagen=%s WHERE idCategoria=%s",
                    (nombreCategoria, descripcion, imagen, id))
            else:
                cursor.execute(
                    "UPDATE categoriaProducto SET nombreCategoria=%s, descripcion=%s WHERE idCategoria=%s",
                    (nombreCategoria, descripcion, id))
        conexion.commit()
        conexion.close()


    # def obtener_idcategoria_por_nombre(nombreCategoria):
    #     conexion = obtener_conexion()   
    #     Cat = None
    #     with conexion.cursor() as cursor:
    #         cursor.execute("Select idCategoria FROM categoriaProducto WHERE nombreCategoria=%s",(nombreCategoria))
    #         Cat = cursor.fetchone()
    #     conexion.close()
    #     return Cat