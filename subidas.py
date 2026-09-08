"""
Subida de imágenes del panel de administración (productos y categorías).

Guarda el archivo en static/img/<subcarpeta>/ con un nombre aleatorio y
devuelve la ruta relativa que se guarda en la BD (p. ej. "productos/ab12cd.jpg").
"""

import os
import secrets

from PIL import Image

EXTENSIONES = {"jpg", "jpeg", "png", "webp", "gif"}
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img")


def _extension(nombre):
    return nombre.rsplit(".", 1)[-1].lower() if "." in (nombre or "") else ""


def guardar_imagen(archivo, subcarpeta):
    """`archivo` = FileStorage de request.files. Devuelve "subcarpeta/nombre.ext"
    o None si no hay archivo o no es una imagen válida."""
    if not archivo or not archivo.filename:
        return None

    ext = _extension(archivo.filename)
    if ext not in EXTENSIONES:
        return None

    # Verifica que el contenido sea realmente una imagen (no un script renombrado).
    try:
        Image.open(archivo.stream).verify()
    except Exception:
        return None
    archivo.stream.seek(0)

    carpeta = os.path.join(_BASE, subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"{secrets.token_hex(8)}.{'jpg' if ext == 'jpeg' else ext}"
    archivo.save(os.path.join(carpeta, nombre))
    return f"{subcarpeta}/{nombre}"


def borrar_imagen(ruta_relativa):
    """Borra static/img/<ruta_relativa> si existe (solo dentro de static/img)."""
    if not ruta_relativa:
        return
    destino = os.path.normpath(os.path.join(_BASE, ruta_relativa))
    if destino.startswith(_BASE) and os.path.isfile(destino):
        try:
            os.remove(destino)
        except OSError:
            pass
