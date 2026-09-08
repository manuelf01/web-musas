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
