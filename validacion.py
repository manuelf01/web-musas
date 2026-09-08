import re
import unicodedata


PATRON_NOMBRE = re.compile(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ' -]{2,100}$")
PATRON_CORREO = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
PATRON_ESPECIAL = re.compile(r"[^A-Za-z0-9\s]")


def reglas_password(password):
    errores = []
    if len(password) < 8:
        errores.append("tener al menos 8 caracteres")
    if not any(caracter.isupper() for caracter in password):
        errores.append("incluir una letra mayúscula")
    if not any(caracter.islower() for caracter in password):
        errores.append("incluir una letra minúscula")
    if not PATRON_ESPECIAL.search(password):
        errores.append("incluir un carácter especial, por ejemplo: !, @, # o -")
    return errores


def _texto_comparable(valor):
    normalizado = unicodedata.normalize("NFKD", str(valor).lower())
    return "".join(caracter for caracter in normalizado if caracter.isalnum() or caracter.isspace())


def reglas_similitud_password(password, dni, nombres, nombre_usuario=None):
    errores = []
    password_comparable = _texto_comparable(password).replace(" ", "")
    identificadores = [str(dni).strip(), str(nombre_usuario or "").strip()]
    if any(
        identificador and _texto_comparable(identificador).replace(" ", "") in password_comparable
        for identificador in identificadores
    ):
        errores.append("no contener el DNI ni el nombre de usuario")

    palabras_nombre = [
        palabra for palabra in _texto_comparable(nombres).split() if len(palabra) >= 3
    ]
    if any(palabra in password_comparable for palabra in palabras_nombre):
        errores.append("no contener palabras de los nombres del usuario")
    return errores


def validar_datos_usuario(
    dni, nombres, apellidos, correo, telefono, password, nombre_usuario=None
):
    errores = []
    dni = str(dni).strip()
    telefono = str(telefono).strip()
    if len(dni) != 8 or not dni.isdigit():
        errores.append("El DNI debe contener exactamente 8 dígitos")
    if not PATRON_NOMBRE.fullmatch(str(nombres).strip()):
        errores.append("Los nombres deben tener al menos 2 letras y no contener números")
    if not PATRON_NOMBRE.fullmatch(str(apellidos).strip()):
        errores.append("Los apellidos deben tener al menos 2 letras y no contener números")
    if not PATRON_CORREO.fullmatch(str(correo).strip()):
        errores.append("El correo electrónico no es válido")
    if len(telefono) != 9 or not telefono.isdigit():
        errores.append("El teléfono debe contener exactamente 9 dígitos")
    errores.extend(f"La contraseña debe {regla}" for regla in reglas_password(password))
    errores.extend(
        f"La contraseña debe {regla}"
        for regla in reglas_similitud_password(password, dni, nombres, nombre_usuario)
    )
    return errores


def generar_nombre_administrador(nombres, dni):
    nombre_normalizado = unicodedata.normalize("NFKD", str(nombres).strip())
    letras = "".join(
        caracter for caracter in nombre_normalizado if caracter.isascii() and caracter.isalpha()
    )
    dni = str(dni).strip()
    if not letras or len(dni) < 5:
        return None
    return f"{letras[0].lower()}{dni[:5]}"
