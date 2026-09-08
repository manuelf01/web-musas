from bd import obtener_conexion
from werkzeug.security import check_password_hash, generate_password_hash

# Roles de cuenta. 'usuario' = cliente de la tienda; los otros dos entran al panel.
ROLES = ("superusuario", "administrador", "usuario")
ROLES_PANEL = ("superusuario", "administrador")
ETIQUETA_ROL = {
    "superusuario": "Superusuario",
    "administrador": "Administrador",
    "usuario": "Usuario",
}


def _tipo_de_rol(rol):
    """tipoUsuario 0 = panel (super/admin), 1 = cliente. Se mantiene sincronizado."""
    return 1 if rol == "usuario" else 0


class Usuario:
    DNI = ""
    nombres = ""
    apellidos = ""
    correo = ""
    numTel = ""
    contraseña = ""
    tipoUsuario = ""
    midic = dict()

    def __init__(self, p_DNI, p_nombres, p_apellidos, p_correo, p_numTel, p_contraseña, p_tipoUsuario):
        self.DNI = p_DNI
        self.nombres = p_nombres
        self.apellidos = p_apellidos
        self.correo = p_correo
        self.numTel = p_numTel
        self.midic["DNI"] = p_DNI
        self.midic["nombres"] = p_nombres
        self.midic["apellidos"] = p_apellidos
        self.midic["correo"] = p_correo
        self.midic["numTel"] = p_numTel
        self.midic["contraseña"] = p_contraseña
        if p_tipoUsuario:
            self.tipoUsuario = "Cliente"
        else:
            self.tipoUsuario = "Admin"

        self.midic["tipoUsuario"] = self.tipoUsuario

    def insertar_usuario(DNI, nombres, apellidos, correo, numTel, contra, tipoUsuario, rol=None):
        # Compatibilidad: si llega tipoUsuario (True/1 = cliente) y no rol, se deriva.
        if rol is None:
            rol = "usuario" if tipoUsuario in (True, 1) else "administrador"
        if rol not in ROLES:
            return "Rol no válido."
        if Usuario.existe_dni(DNI):
            return "Este DNI ya está registrado."
        contra_hash = generate_password_hash(contra)
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "INSERT INTO usuario(DNI, nombres, apellidos, correo, numTelf, contraseña, "
                "tipoUsuario, rol, activo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)",
                (DNI, nombres, apellidos, correo, numTel, contra_hash, _tipo_de_rol(rol), rol),
            )
        conexion.commit()
        conexion.close()
        return None

    def obtener_usuarios():
        conexion = obtener_conexion()
        usuarios = []
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuario where tipoUsuario = %s", (False))
            usuarios = cursor.fetchall()
        conexion.close()
        return usuarios

    @staticmethod
    def _fila_a_dict(f):
        nombre = f"{f[2]} {f[3]}".strip()
        rol = f[6] or ("usuario" if f[7] in (1, True) else "administrador")
        return {
            "idUsuario": f[0],
            "dni": f[1],
            "nombres": f[2],
            "apellidos": f[3],
            "nombreCompleto": nombre,
            "iniciales": "".join(p[0] for p in nombre.split()[:2]).upper() or "?",
            "correo": f[4],
            "telefono": f[5],
            "rol": rol,
            "rolTexto": ETIQUETA_ROL.get(rol, rol),
            "esPanel": rol in ROLES_PANEL,
            "esSuper": rol == "superusuario",
            "activo": bool(f[8]) if len(f) > 8 and f[8] is not None else True,
            "noShows": int(f[9] or 0) if len(f) > 9 else 0,
        }

    _SEL = ("SELECT idUsuario, dni, nombres, apellidos, correo, numTelf, rol, "
            "tipoUsuario, activo, COALESCE(noShows, 0) FROM usuario")

    @staticmethod
    def obtener_todos():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(Usuario._SEL + " ORDER BY FIELD(rol,'superusuario','administrador','usuario'), nombres")
            filas = cursor.fetchall()
        conexion.close()
        return [Usuario._fila_a_dict(f) for f in filas]

    @staticmethod
    def obtener_dict(id):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(Usuario._SEL + " WHERE idUsuario = %s", (id,))
            f = cursor.fetchone()
        conexion.close()
        return Usuario._fila_a_dict(f) if f else None

    @staticmethod
    def contar_por_rol():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT COALESCE(SUM(rol='superusuario'),0), COALESCE(SUM(rol='administrador'),0), "
                "COALESCE(SUM(rol='usuario'),0), COALESCE(SUM(activo=0),0) FROM usuario"
            )
            sup, adm, usr, baja = cursor.fetchone()
        conexion.close()
        return {"superusuario": int(sup or 0), "administrador": int(adm or 0),
                "usuario": int(usr or 0), "de_baja": int(baja or 0),
                "total": int((sup or 0) + (adm or 0) + (usr or 0))}

    @staticmethod
    def cambiar_estado(id, activo):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE usuario SET activo = %s WHERE idUsuario = %s",
                           (1 if activo else 0, id))
        conexion.commit()
        conexion.close()

    @staticmethod
    def actualizar_por_admin(id, correo, telefono, rol, contra):
        """El superusuario edita otra cuenta (contacto + rol). No toca superusuarios."""
        actual = Usuario.obtener_dict(id)
        if actual is None:
            return "La cuenta no existe."
        if actual["esSuper"]:
            return "No puedes editar a otro superusuario."
        if rol not in ROLES:
            rol = actual["rol"]
        if rol == "superusuario":
            return "Para dar rol de superusuario, crea la cuenta desde «Agregar usuario»."
        correo = correo or actual["correo"]
        telefono = telefono or actual["telefono"]
        sets = ["correo=%s", "numTelf=%s", "rol=%s", "tipoUsuario=%s"]
        vals = [correo, telefono, rol, _tipo_de_rol(rol)]
        if contra:
            sets.append("contraseña=%s")
            vals.append(generate_password_hash(contra))
        vals.append(id)
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE usuario SET " + ", ".join(sets) + " WHERE idUsuario=%s", vals)
        conexion.commit()
        conexion.close()
        return None

    @staticmethod
    def actualizar_perfil(id, nombres, apellidos, correo, dni, telefono, contra):
        """El propio usuario corrige sus datos."""
        actual = Usuario.obtener_dict(id)
        if actual is None:
            return "La cuenta no existe."
        if dni and dni != actual["dni"] and Usuario.existe_dni(dni, excepto_id=id):
            return "Ese DNI ya está en uso por otra cuenta."
        sets = ["nombres=%s", "apellidos=%s", "correo=%s", "dni=%s", "numTelf=%s"]
        vals = [nombres or actual["nombres"], apellidos or actual["apellidos"],
                correo or actual["correo"], dni or actual["dni"], telefono or actual["telefono"]]
        if contra:
            sets.append("contraseña=%s")
            vals.append(generate_password_hash(contra))
        vals.append(id)
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE usuario SET " + ", ".join(sets) + " WHERE idUsuario=%s", vals)
        conexion.commit()
        conexion.close()
        return None

    def obtener_usuario_id(id):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM usuario WHERE idUsuario = %s", (id))
            usuario = cursor.fetchone()
        return usuario

    def obtener_usuario_id_tipo(id, tipoUsuario):
        conexion = obtener_conexion()
        modo = None
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT DNI,nombres,apellidos,correo, numTelf, contraseña, tipoUsuario FROM usuario WHERE idUsuario= %s and tipoUsuario = %s", (id, tipoUsuario))
            modo = cursor.fetchone()
        conexion.close()
        return modo

    def actualizar_usuario(correo, numTel, contra, id, tipo):
        # NOTA (Ramirez): esta función es del módulo de Usuarios de Betancurt.
        # Solo se conserva el hash de la contraseña nueva para que sea compatible
        # con el login. Si Betancurt reescribe este método, esta versión cede.
        actual = Usuario.obtener_usuario_id_tipo(id, tipo)
        if correo == "" or correo is None:
            correo = actual[3]
        if numTel == "" or numTel is None:
            numTel = actual[4]
        if contra == "" or contra is None:
            contra = actual[5]
        else:
            contra = generate_password_hash(contra)
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("UPDATE usuario SET correo = %s, numTelf= %s, contraseña= %s WHERE idUsuario=%s and tipoUsuario = %s",
                           (correo, numTel, contra, id, tipo))
        conexion.commit()
        conexion.close()

    def eliminar_usuario(dni, tipoUsuario):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "DELETE FROM usuario WHERE DNI = %s and tipoUsuario = %s", (dni, tipoUsuario))
        conexion.commit()
        conexion.close()

    def eliminar_usuario_id(id):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("DELETE FROM usuario WHERE idUsuario = %s", (id))
        conexion.commit()
        conexion.close()

    def existe_dni(dni, excepto_id=None):
        """True si el DNI ya está registrado (opcionalmente excluyendo una cuenta)."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            if excepto_id is None:
                cursor.execute("SELECT COUNT(*) FROM usuario WHERE DNI = %s", (dni,))
            else:
                cursor.execute("SELECT COUNT(*) FROM usuario WHERE DNI = %s AND idUsuario <> %s",
                               (dni, excepto_id))
            total = cursor.fetchone()[0]
        conexion.close()
        return total > 0

    @staticmethod
    def login_por_dni(dni):
        """Filas con DNI dado, incluyendo rol y activo, para el login."""
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT idUsuario, dni, nombres, apellidos, correo, numTelf, contraseña, "
                "tipoUsuario, rol, activo FROM usuario WHERE dni = %s "
                "ORDER BY FIELD(rol,'superusuario','administrador','usuario')",
                (dni,),
            )
            filas = cursor.fetchall()
        conexion.close()
        return filas

    def obtener_usuario_dni_tipo(dni, tipo):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM usuario WHERE DNI = %s and tipoUsuario = %s", (dni, tipo))
            usuario = cursor.fetchone()
        return usuario

    def validar_usuario_id(id):
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM usuario WHERE idUsuario = %s", (id,))
            resultado = cursor.fetchone()
        conexion.close()
        if resultado[0] > 0:
            return True
        
    def obtener_usuarios_jwt():
        conexion = obtener_conexion()
        with conexion.cursor() as cursor:
            cursor.execute("SELECT idUsuario, dni, contraseña FROM usuario")
            usuarios = cursor.fetchall()
        conexion.close()
        return usuarios
