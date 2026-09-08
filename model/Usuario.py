from bd import obtener_conexion
from pymysql.err import IntegrityError
from werkzeug.security import generate_password_hash
from validacion import (
    generar_nombre_administrador,
    reglas_password,
    reglas_similitud_password,
    validar_datos_usuario,
)


class Usuario:
    DNI = ""
    nombres = ""
    apellidos = ""
    correo = ""
    numTel = ""
    contraseña = ""
    tipoUsuario = ""
    def __init__(self, p_DNI, p_nombres, p_apellidos, p_correo, p_numTel, p_contraseña, p_tipoUsuario, p_nombreUsuario=None):
        self.DNI = p_DNI
        self.nombres = p_nombres
        self.apellidos = p_apellidos
        self.correo = p_correo
        self.numTel = p_numTel
        self.midic = {}
        self.midic["DNI"] = p_DNI
        self.midic["nombres"] = p_nombres
        self.midic["apellidos"] = p_apellidos
        self.midic["correo"] = p_correo
        self.midic["numTel"] = p_numTel
        self.midic["nombreUsuario"] = p_nombreUsuario
        if p_tipoUsuario:
            self.tipoUsuario = "Cliente"
        else:
            self.tipoUsuario = "Admin"

        self.midic["tipoUsuario"] = self.tipoUsuario

    @staticmethod
    def insertar_usuario(DNI, nombres, apellidos, correo, numTel, contra, tipoUsuario):
        user = Usuario.obtener_usuario_dni(DNI)
        if user is not None:
            return "Ya existe un usuario registrado con ese DNI"

        nombre_usuario = None
        if not tipoUsuario:
            nombre_usuario = generar_nombre_administrador(nombres, DNI)
            if nombre_usuario is None:
                return "No se pudo generar el nombre de usuario administrativo"

        errores = validar_datos_usuario(
            DNI, nombres, apellidos, correo, numTel, contra, nombre_usuario
        )
        if errores:
            return ". ".join(errores)

        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                password_hash = generate_password_hash(contra)
                cursor.execute("INSERT INTO usuario(DNI, nombres, apellidos, correo, numTelf,contraseña, tipoUsuario, nombreUsuario) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (
                    str(DNI).strip(), nombres.strip(), apellidos.strip(), correo.strip().lower(), str(numTel).strip(), password_hash, tipoUsuario, nombre_usuario))
            conexion.commit()
            return None
        except IntegrityError as error:
            conexion.rollback()
            if "uq_usuario_correo" in str(error):
                return "El correo ya está registrado"
            if "uq_usuario_nombreUsuario" in str(error):
                return "El nombre de usuario administrativo ya existe"
            return "El usuario ya está registrado"
        finally:
            conexion.close()

    @staticmethod
    def obtener_usuarios():
        conexion = obtener_conexion()
        usuarios = []
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuario where tipoUsuario = %s", (False,))
            usuarios = cursor.fetchall()
        conexion.close()
        return usuarios

    @staticmethod
    def obtener_usuario_id(id):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM usuario WHERE idUsuario = %s", (id,))
            usuario = cursor.fetchone()
        conexion.close()
        return usuario

    @staticmethod
    def obtener_usuario_id_tipo(id, tipoUsuario):
        conexion = obtener_conexion()
        modo = None
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT DNI,nombres,apellidos,correo, numTelf, contraseña, tipoUsuario FROM usuario WHERE idUsuario= %s and tipoUsuario = %s", (id, tipoUsuario))
            modo = cursor.fetchone()
        conexion.close()
        return modo

    @staticmethod
    def actualizar_usuario(correo, numTel, contra, id, tipo):
        usuario = Usuario.obtener_usuario_id(id)
        if usuario is None:
            return "El usuario no existe"
        if correo == "":
            correo = usuario[4]
        if numTel == "":
            numTel = usuario[5]
        if contra == "":
            contra = usuario[6]
        else:
            errores_password = reglas_password(contra)
            errores_password.extend(
                reglas_similitud_password(
                    contra,
                    usuario[1],
                    usuario[2],
                    usuario[8] if len(usuario) > 8 else None,
                )
            )
            if errores_password:
                return ". ".join(
                    f"La contraseña debe {regla}" for regla in errores_password
                )
            contra = generate_password_hash(contra)
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE usuario SET correo = %s, numTelf= %s, contraseña= %s WHERE idUsuario=%s and tipoUsuario = %s",
                           (correo, numTel, contra, id, tipo))
        conexion.commit()
        conexion.close()
        return None

    @staticmethod
    def actualizar_password_hash(id_usuario, password):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    "UPDATE usuario SET contraseña = %s WHERE idUsuario = %s",
                    (generate_password_hash(password), id_usuario),
                )
            conexion.commit()
        finally:
            conexion.close()

    @staticmethod
    def eliminar_usuario(dni, tipoUsuario):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "DELETE FROM usuario WHERE DNI = %s and tipoUsuario = %s", (dni, tipoUsuario))
        conexion.commit()
        conexion.close()

    @staticmethod
    def eliminar_usuario_id(id):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM usuario WHERE idUsuario = %s", (id,))
        conexion.commit()
        conexion.close()

    @staticmethod
    def obtener_usuario_dni_tipo(dni, tipo):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuario WHERE DNI = %s and tipoUsuario = %s", (dni, tipo))
            usuario = cursor.fetchone()
        conexion.close()
        return usuario

    @staticmethod
    def desbloquear_usuario(id_usuario):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE usuario
                    SET intentosFallidos = 0,
                        bloqueadoHasta = NULL,
                        bloqueoPermanente = 0
                    WHERE idUsuario = %s
                    """,
                    (id_usuario,),
                )
            conexion.commit()
        finally:
            conexion.close()
        return None

    @staticmethod
    def obtener_usuario_dni(dni):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute("SELECT * FROM usuario WHERE DNI = %s", (dni,))
                return cursor.fetchone()
        finally:
            conexion.close()

    @staticmethod
    def validar_usuario_id(id):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM usuario WHERE idUsuario = %s", (id,))
            resultado = cursor.fetchone()
        conexion.close()
        if resultado[0] > 0:
            return True
        
    @staticmethod
    def obtener_usuarios_jwt():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT idUsuario, dni, contraseña FROM usuario")
            usuarios = cursor.fetchall()
        conexion.close()
        return usuarios
