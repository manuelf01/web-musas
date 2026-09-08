import hmac
from datetime import datetime, timedelta

from werkzeug.security import check_password_hash

from bd import obtener_conexion
from model.Usuario import Usuario


class Autenticacion:
    diccionario_tipo = {
        "cliente.auth": {"tipoUsuario": True},
        "admin.auth": {"tipoUsuario": False},
    }
    MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos"

    @staticmethod
    def _buscar_usuario(identificador, tipo_usuario):
        identificador = str(identificador).strip()
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT * FROM usuario
                    WHERE (dni = %s OR nombreUsuario = %s)
                      AND tipoUsuario = %s
                    """,
                    (identificador, identificador.lower(), tipo_usuario),
                )
                return cursor.fetchone()
        finally:
            conexion.close()

    @staticmethod
    def _password_valido(usuario, password):
        password_guardado = usuario[6]
        try:
            valido = check_password_hash(password_guardado, password)
        except (ValueError, TypeError):
            valido = False

        if not valido and hmac.compare_digest(str(password_guardado), password):
            Usuario.actualizar_password_hash(usuario[0], password)
            valido = True
        return valido

    @staticmethod
    def _actualizar_control(id_usuario, intentos=0, bloqueado_hasta=None, permanente=False):
        conexion = obtener_conexion()
        try:
            with conexion.cursor() as cursor:
                cursor.execute(
                    """
                    UPDATE usuario
                    SET intentosFallidos = %s,
                        bloqueadoHasta = %s,
                        bloqueoPermanente = %s
                    WHERE idUsuario = %s
                    """,
                    (intentos, bloqueado_hasta, permanente, id_usuario),
                )
            conexion.commit()
        finally:
            conexion.close()

    @staticmethod
    def _registrar_fallo(usuario):
        ahora = datetime.now()
        intentos = int(usuario[9] or 0)
        bloqueo_anterior = usuario[10]

        # Tras cumplir el bloqueo temporal, un nuevo error cierra el acceso de
        # esa cuenta hasta que sea desbloqueada administrativamente.
        if bloqueo_anterior is not None and bloqueo_anterior <= ahora:
            Autenticacion._actualizar_control(
                usuario[0], intentos=intentos + 1, bloqueado_hasta=None, permanente=True
            )
            return "Cuenta bloqueada por seguridad. Contacta a un administrador"

        intentos += 1
        if intentos >= 3:
            hasta = ahora + timedelta(minutes=5)
            Autenticacion._actualizar_control(
                usuario[0], intentos=intentos, bloqueado_hasta=hasta
            )
            return (
                f"{Autenticacion.MENSAJE_CREDENCIALES}. "
                "La cuenta quedó bloqueada durante 5 minutos"
            )

        Autenticacion._actualizar_control(usuario[0], intentos=intentos)
        return Autenticacion.MENSAJE_CREDENCIALES

    @staticmethod
    def login_por_tipo(identificador, password, tipo_usuario):
        usuario = Autenticacion._buscar_usuario(identificador, tipo_usuario)
        if usuario is None:
            return Autenticacion.MENSAJE_CREDENCIALES

        ahora = datetime.now()
        if bool(usuario[11]):
            return "Cuenta bloqueada por seguridad. Contacta a un administrador"
        if usuario[10] is not None and usuario[10] > ahora:
            return "Acceso temporalmente bloqueado. Inténtalo nuevamente en 5 minutos"

        if not Autenticacion._password_valido(usuario, password):
            return Autenticacion._registrar_fallo(usuario)

        Autenticacion._actualizar_control(usuario[0])
        return [usuario]

    @staticmethod
    def login(identificador, password, tipo_blueprint):
        configuracion = Autenticacion.diccionario_tipo.get(tipo_blueprint)
        if configuracion is None:
            return Autenticacion.MENSAJE_CREDENCIALES
        return Autenticacion.login_por_tipo(
            str(identificador).strip(), password, configuracion["tipoUsuario"]
        )

    @staticmethod
    def autenticar_api(identificador, password, tipo_usuario):
        resultado = Autenticacion.login_por_tipo(identificador, password, tipo_usuario)
        return resultado[0] if isinstance(resultado, list) else None

    @staticmethod
    def registro(dni, nombres, apellidos, correo, num_telf, password):
        campos = (dni, nombres, apellidos, correo, num_telf, password)
        if not all(str(campo).strip() for campo in campos):
            return "Todos los campos son obligatorios"
        return Usuario.insertar_usuario(
            str(dni).strip(),
            nombres.strip(),
            apellidos.strip(),
            correo.strip().lower(),
            str(num_telf).strip(),
            password,
            True,
        )

    @staticmethod
    def sesionRegistrada(blueprint_name, dni):
        configuracion = Autenticacion.diccionario_tipo.get(blueprint_name)
        if configuracion is None:
            return None
        return Autenticacion._buscar_usuario(dni, configuracion["tipoUsuario"])
