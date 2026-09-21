"""
Subida de imágenes del panel de administración (productos y categorías).

Guarda el archivo en static/img/<subcarpeta>/ con un nombre aleatorio y
devuelve la ruta relativa que se guarda en la BD (p. ej. "productos/ab12cd.jpg").
"""

import io
import ipaddress
import os
import secrets
import socket
import urllib.request
from urllib.parse import urlparse

from PIL import Image

EXTENSIONES = {"jpg", "jpeg", "png", "webp", "gif"}
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img")
_MAX_BYTES = 5 * 1024 * 1024
_MIME_EXT = {
    "image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif",
}


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


def _host_es_publico(host):
    """Bloquea localhost / IPs privadas (evita SSRF a la red interna)."""
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return False
        return True
    except (socket.gaierror, ValueError):
        return False


def guardar_desde_url(url, subcarpeta):
    """Descarga una imagen desde un enlace de internet y la guarda como un archivo
    local. Devuelve "subcarpeta/nombre.ext" o None si el enlace no sirve."""
    url = (url or "").strip()
    if not url:
        return None
    partes = urlparse(url)
    if partes.scheme not in ("http", "https") or not partes.hostname:
        return None
    if not _host_es_publico(partes.hostname):
        return None

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (LasMusas)"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            if ctype not in _MIME_EXT:
                return None
            datos = resp.read(_MAX_BYTES + 1)
    except Exception:
        return None
    if not datos or len(datos) > _MAX_BYTES:
        return None

    try:
        Image.open(io.BytesIO(datos)).verify()
    except Exception:
        return None

    ext = _MIME_EXT[ctype]
    carpeta = os.path.join(_BASE, subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"{secrets.token_hex(8)}.{ext}"
    with open(os.path.join(carpeta, nombre), "wb") as fh:
        fh.write(datos)
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


# ----------------------------------------------------------------------
#  Foto de perfil: cuadrada, 320x320, JPEG (misma proporción en todos lados)
# ----------------------------------------------------------------------
AVATAR_LADO = 320


def guardar_avatar(archivo, id_usuario):
    """Recorta al centro en cuadrado, redimensiona y guarda en static/img/perfiles/.
    Devuelve (ruta_relativa | None, mensaje_de_error | None)."""
    from PIL import ImageOps

    if not archivo or not archivo.filename:
        return None, "Elige una imagen para tu foto de perfil."
    if _extension(archivo.filename) not in EXTENSIONES:
        return None, "La foto debe ser JPG, PNG, WEBP o GIF."
    datos = archivo.stream.read(_MAX_BYTES + 1)
    if len(datos) > _MAX_BYTES:
        return None, "La foto pesa más de 5 MB."
    try:
        imagen = Image.open(io.BytesIO(datos))
        imagen.verify()
        imagen = Image.open(io.BytesIO(datos))
        imagen = ImageOps.exif_transpose(imagen)
        if imagen.width * imagen.height > 40_000_000:
            return None, "La foto es demasiado grande."
        imagen = ImageOps.fit(imagen.convert("RGB"), (AVATAR_LADO, AVATAR_LADO), Image.LANCZOS)
    except Exception:
        return None, "El archivo no es una imagen válida."

    carpeta = os.path.join(_BASE, "perfiles")
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"u{int(id_usuario)}-{secrets.token_hex(6)}.jpg"
    imagen.save(os.path.join(carpeta, nombre), "JPEG", quality=88, optimize=True)
    return f"perfiles/{nombre}", None


def ruta_avatar_valida(ruta, id_usuario):
    """True si `ruta` es una foto de ESTE usuario que existe (evita apuntar a archivos ajenos)."""
    import re as _re
    if not _re.fullmatch(r"perfiles/u%d-[0-9a-f]{12}\.jpg" % int(id_usuario), ruta or ""):
        return False
    return os.path.isfile(os.path.join(_BASE, *ruta.split("/")))


def podar_avatares(id_usuario, conservar):
    """Borra las fotos viejas de un usuario, dejando solo las de `conservar`
    (la actual y la anterior, para poder deshacer el cambio)."""
    carpeta = os.path.join(_BASE, "perfiles")
    if not os.path.isdir(carpeta):
        return
    dejar = {os.path.basename(r) for r in conservar if r}
    prefijo = "u%d-" % int(id_usuario)
    for nombre in os.listdir(carpeta):
        if nombre.startswith(prefijo) and nombre.endswith(".jpg") and nombre not in dejar:
            try:
                os.remove(os.path.join(carpeta, nombre))
            except OSError:
                pass
