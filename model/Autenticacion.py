from bd import obtener_conexion
from werkzeug.security import check_password_hash, generate_password_hash
from model.Usuario import Usuario


class Autenticacion:

    diccionario_tipo = {
        "cliente.auth": {
            "tipoUsuario": True
        },
        "admin.auth": {
            "tipoUsuario": False
        }
    }

    # ------------------------------------------------------------------
    # Verificación de contraseña (hash con werkzeug)
    # ------------------------------------------------------------------
    @staticmethod
    def verificar_password(guardada, ingresada):
        if not guardada:
            return False
        try:
            return check_password_hash(guardada, ingresada)
        except Exception:
            # Contraseña antigua guardada en texto plano (datos previos a la
            # migración a hash). Se acepta una sola vez para no bloquear al
            # usuario; hay que recrear esas cuentas.
            return guardada == ingresada

    # ------------------------------------------------------------------
    # Login unificado: una sola puerta, decide por tipoUsuario
    # ------------------------------------------------------------------
    @staticmethod
    def dni_es_admin(dni):
        """True si el DNI corresponde a una cuenta de panel (superusuario o admin)."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM usuario WHERE dni = %s "
                "AND (rol IN ('superusuario','administrador') OR tipoUsuario = 0)",
                (dni,),
            )
            total = cursor.fetchone()[0]
        conexion.close()
        return total > 0

    @staticmethod
    def login_unificado(dni, contraseña):
        """
        Devuelve (fila_usuario, tipo) con tipo 'admin' o 'cliente',
        o un string con el mensaje de error.
        fila_usuario = idUsuario, dni, nombres, apellidos, correo, numTelf,
                       contraseña, tipoUsuario, rol, activo
        """
        filas = Usuario.login_por_dni(dni)
        if not filas:
            return "No encontramos una cuenta con ese DNI."

        for fila in filas:
            if Autenticacion.verificar_password(fila[6], contraseña):
                if len(fila) > 9 and fila[9] == 0:
                    return "Esta cuenta está dada de baja. Contacta al administrador."
                rol = fila[8] or ("usuario" if fila[7] in (1, True) else "administrador")
                tipo = "cliente" if rol == "usuario" else "admin"
                return (fila, tipo)

        return "La contraseña no es correcta."

    # ------------------------------------------------------------------
    # Login clásico por tipo (se mantiene por compatibilidad)
    # ------------------------------------------------------------------
    @staticmethod
    def login(dni, contraseña, tipo_blueprint):
        conexion = obtener_conexion()
        error = None

        tipoUsuario = Autenticacion.diccionario_tipo[tipo_blueprint]["tipoUsuario"]

        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuario WHERE dni = %s and tipoUsuario = %s",
                (dni, tipoUsuario),
            )
            user = cursor.fetchall()
        conexion.close()

        if user is None or len(user) == 0:
            error = "Usuario incorrecto"
        elif not Autenticacion.verificar_password(user[0][6], contraseña):
            error = "Contraseña incorrecta"
        else:
            error = user

        return error

    @staticmethod
    def registro(dni, nombres, apellidos, correo, numTelf, contraseña):
        if not dni or not nombres or not apellidos or not correo or not numTelf or not contraseña:
            return "Campos obligatorios"
        if Usuario.existe_dni(dni):
            return "Ese DNI ya tiene una cuenta. Inicia sesión."
        # insertar_usuario hace el hash de la contraseña.
        return Usuario.insertar_usuario(dni, nombres, apellidos, correo, numTelf, contraseña, True)

    @staticmethod
    def sesionRegistrada(blueprint_name, dni):
        conexion = obtener_conexion()
        tipoUsuario = Autenticacion.diccionario_tipo[blueprint_name]["tipoUsuario"]
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuario WHERE dni = %s and tipoUsuario = %s",
                (dni, tipoUsuario),
            )
            user = cursor.fetchall()
        conexion.close()
        return user[0]
