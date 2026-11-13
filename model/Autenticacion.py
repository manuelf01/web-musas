from werkzeug.security import check_password_hash

from model.Usuario import Usuario


class Autenticacion:
    """Autenticación unificada sin consultas auxiliares que enumeren cuentas."""

    ERROR_CREDENCIALES = "Credenciales inválidas."
    # Se verifica este hash cuando la cuenta no existe para reducir diferencias
    # de tiempo frente al caso de contraseña incorrecta.
    _HASH_FICTICIO = (
        "pbkdf2:sha256:260000$vxtBrOTidMwkCp4V$"
        "dab206ee6109184d8e1c8c4eb65e8678aa8d13a7ebe150b2cef577f55cef51b3"
    )

    @staticmethod
    def verificar_password(guardada, ingresada):
        if not guardada:
            return False
        try:
            return check_password_hash(guardada, ingresada)
        except Exception:
            # Compatibilidad temporal con cuentas antiguas en texto plano.
            return guardada == ingresada

    @staticmethod
    def login_unificado(identificador, contraseña):
        """Devuelve ``(usuario, tipo)`` o siempre el mismo error público."""
        filas = Usuario.login_por_identificador(identificador)
        if not filas:
            Autenticacion.verificar_password(Autenticacion._HASH_FICTICIO, contraseña)
            return Autenticacion.ERROR_CREDENCIALES

        for fila in filas:
            if Autenticacion.verificar_password(fila[6], contraseña):
                if len(fila) > 9 and fila[9] == 0:
                    return Autenticacion.ERROR_CREDENCIALES
                rol = fila[8] or ("usuario" if fila[7] in (1, True) else "administrador")
                return fila, ("cliente" if rol == "usuario" else "admin")

        return Autenticacion.ERROR_CREDENCIALES

    @staticmethod
    def registro(nombres, apellidos, correo, numTelf, contraseña):
        if not nombres or not apellidos or not correo or not numTelf or not contraseña:
            return "Campos obligatorios"
        return Usuario.insertar_usuario(
            None, nombres, apellidos, correo, numTelf, contraseña, True
        )
