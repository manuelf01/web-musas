from model.Usuario import Usuario
from model.Autenticacion import Autenticacion


class User(object):

    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

    def __str__(self):
        return "User(id='%s')" % self.id

    @staticmethod
    def obtener_usuarios():
        return [User(u[0], u[1], u[2]) for u in Usuario.obtener_usuarios_jwt()]


def _buscar_por_dni(username):
    for u in Usuario.obtener_usuarios_jwt():
        if str(u[1]) == str(username):
            return User(u[0], u[1], u[2])
    return None


def _buscar_por_id(user_id):
    for u in Usuario.obtener_usuarios_jwt():
        if u[0] == user_id:
            return User(u[0], u[1], u[2])
    return None


def authenticate(username, password):
    # Se consulta la BD en cada intento (no en el import) para no romper el
    # arranque si MySQL aún no está listo y para ver usuarios nuevos sin reiniciar.
    try:
        user = _buscar_por_dni(username)
    except Exception:
        return None
    if user and Autenticacion.verificar_password(user.password, password):
        return user


def identity(payload):
    try:
        return _buscar_por_id(payload["identity"])
    except Exception:
        return None
