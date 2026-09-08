"""Crea el primer administrador sin guardar la contraseña en el historial."""

from getpass import getpass

from model.Usuario import Usuario


def solicitar(campo):
    valor = input(f"{campo}: ").strip()
    if not valor:
        raise ValueError(f"{campo} es obligatorio")
    return valor


def main():
    dni = solicitar("DNI (8 dígitos)")
    nombres = solicitar("Nombres")
    apellidos = solicitar("Apellidos")
    correo = solicitar("Correo")
    telefono = solicitar("Teléfono (9 dígitos)")
    password = getpass("Contraseña: ")
    if len(password) < 8:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")

    error = Usuario.insertar_usuario(
        dni, nombres, apellidos, correo, telefono, password, False
    )
    if error:
        raise ValueError(error)
    print("Administrador creado correctamente")


if __name__ == "__main__":
    main()
