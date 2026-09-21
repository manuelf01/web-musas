"""Avisos del panel con acciones: «Deshacer» (verde) y «Ver dónde» (rojo).

Los controladores llaman a `ok_deshacer` / `error_en_formulario` en lugar de
`flash` a secas. La plantilla base del panel lee lo pendiente con
`pop_deshacer()` / `pop_error_form()` (ver app.py) y pinta el botón.
"""

from flask import flash, session

# Campos que nunca se guardan en la sesión (secretos o archivos).
_EXCLUIDOS = ("csrf", "contra", "pass", "imagen")

# (fragmento del mensaje en minúsculas, nombre del campo del formulario)
_REGLAS = (
    ("precio", "precio"),
    ("existencias", "existencias"),
    ("categoría seleccionada", "categorias"),
    ("nombre de la categoría", "nombreCategoria"),
    ("imagen", "imagen_url"),
    ("contraseña", "contraseña"),
    ("dni", "dni"),
    ("correo", "correo"),
    ("teléfono", "telefono"),
    ("nombres y apellidos", "nombres"),
    ("código de verificación", "captcha"),
    ("rol", "rol"),
)


def _valores_seguros(formulario):
    salida = {}
    for clave, valor in formulario.items():
        if any(x in clave.lower() for x in _EXCLUIDOS):
            continue
        salida[clave] = str(valor)[:300]
    return salida


def campo_del_error(mensaje, valores, obligatorios=()):
    """Adivina qué campo causó el error a partir del texto de validación."""
    texto = (mensaje or "").lower()
    if "nombres y apellidos" in texto:
        return "nombres" if not valores.get("nombres", "").strip() else "apellidos"
    for fragmento, campo in _REGLAS:
        if fragmento in texto:
            return campo
    if "completa todos" in texto or "obligatorio" in texto:
        for campo in obligatorios:
            if not str(valores.get(campo, "")).strip():
                return campo
    return None


def error_en_formulario(mensaje, modo, formulario, id_registro=None, obligatorios=(), campo=None):
    """Avisa el error (rojo) y guarda dónde ocurrió para poder señalarlo.
    modo: 'crear' / 'editar' (formulario en panel deslizante) o 'pagina' (formulario ya
    visible en la página: login, registro, mi cuenta). `campo` fuerza el campo señalado."""
    flash(mensaje, "error")
    valores = _valores_seguros(formulario)
    session["_error_form"] = {
        "modo": modo, "id": str(id_registro) if id_registro is not None else "",
        "campo": campo or campo_del_error(mensaje, valores, obligatorios),
        "mensaje": mensaje, "valores": valores,
    }


def ok_deshacer(mensaje, url, campos, etiqueta="Deshacer"):
    """Avisa el éxito (verde) con un botón que envía `campos` por POST a `url`."""
    flash(mensaje, "ok")
    session["_deshacer"] = {
        "url": url, "etiqueta": etiqueta,
        "campos": {k: ("" if v is None else str(v)) for k, v in campos.items()},
    }


def pop_deshacer():
    return session.pop("_deshacer", None)


def pop_error_form():
    return session.pop("_error_form", None)
