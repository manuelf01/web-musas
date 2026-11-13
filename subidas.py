"""Procesamiento seguro de imágenes subidas o descargadas.

Los productos y categorías se recodifican a WebP, sin metadatos, y generan una
versión de detalle más una miniatura. La BD guarda solo la ruta de detalle.
"""

import io
import ipaddress
import os
import secrets
import socket
import urllib.error
import urllib.request
from urllib.parse import urljoin, urlparse

from PIL import Image, ImageOps


EXTENSIONES = {"jpg", "jpeg", "png", "webp", "gif"}
_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img")
_MAX_BYTES = 5 * 1024 * 1024
_MAX_PIXELES = 25_000_000
_DETALLE_MAX = (1600, 1600)
_MINIATURA_MAX = (480, 480)
_MAX_REDIRECCIONES = 4
_MIME_FORMATO = {
    "image/jpeg": "jpeg", "image/png": "png", "image/webp": "webp",
    "image/gif": "gif",
}


def _extension(nombre):
    return nombre.rsplit(".", 1)[-1].lower() if "." in (nombre or "") else ""


def _formato_magico(datos):
    """Detecta el formato por firma binaria antes de abrirlo con Pillow."""
    if datos.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return "webp"
    if datos.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    return None


def _leer_limitado(flujo):
    datos = flujo.read(_MAX_BYTES + 1)
    return datos if datos and len(datos) <= _MAX_BYTES else None


def _abrir_verificada(datos, formato_esperado=None):
    """Número mágico, decodificación completa y límite contra bombas de imagen."""
    formato = _formato_magico(datos)
    if not formato or (formato_esperado and formato != formato_esperado):
        return None
    try:
        prueba = Image.open(io.BytesIO(datos))
        prueba.verify()
        imagen = Image.open(io.BytesIO(datos))
        imagen.load()
        if imagen.width * imagen.height > _MAX_PIXELES:
            return None
        return ImageOps.exif_transpose(imagen)
    except Exception:
        return None


def _guardar_webp(imagen, subcarpeta, prefijo=None):
    carpeta = os.path.join(_BASE, subcarpeta)
    os.makedirs(carpeta, exist_ok=True)
    base = prefijo or secrets.token_hex(8)
    detalle_nombre = f"{base}.webp"
    mini_nombre = f"{base}-thumb.webp"
    modo = "RGBA" if "A" in imagen.getbands() else "RGB"
    original = imagen.convert(modo)
    detalle = original.copy()
    detalle.thumbnail(_DETALLE_MAX, Image.Resampling.LANCZOS)
    mini = original.copy()
    mini.thumbnail(_MINIATURA_MAX, Image.Resampling.LANCZOS)
    # La recodificación crea archivos nuevos sin EXIF, comentarios ni perfiles.
    detalle.save(os.path.join(carpeta, detalle_nombre), "WEBP", quality=82, method=6)
    mini.save(os.path.join(carpeta, mini_nombre), "WEBP", quality=76, method=6)
    return f"{subcarpeta}/{detalle_nombre}"


def guardar_imagen(archivo, subcarpeta):
    """Valida extensión, firma y decodificación; devuelve una ruta WebP."""
    if not archivo or not archivo.filename:
        return None
    ext = _extension(archivo.filename)
    if ext not in EXTENSIONES:
        return None
    datos = _leer_limitado(archivo.stream)
    if not datos:
        return None
    esperado = "jpeg" if ext in ("jpg", "jpeg") else ext
    imagen = _abrir_verificada(datos, esperado)
    return _guardar_webp(imagen, subcarpeta) if imagen else None


def _host_es_publico(host):
    """Bloquea localhost e IPs internas antes de cada salto HTTP."""
    try:
        for info in socket.getaddrinfo(host, None):
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                return False
        return True
    except (socket.gaierror, ValueError):
        return False


def _url_publica(url):
    partes = urlparse(url)
    return (partes.scheme in ("http", "https") and bool(partes.hostname)
            and _host_es_publico(partes.hostname))


class _SinRedireccion(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _descargar_url(url):
    """Sigue pocos saltos y vuelve a validar destino, MIME, tamaño y firma."""
    opener = urllib.request.build_opener(_SinRedireccion())
    actual = url
    for _ in range(_MAX_REDIRECCIONES + 1):
        if not _url_publica(actual):
            return None, None
        req = urllib.request.Request(actual, headers={"User-Agent": "Mozilla/5.0 (LasDeSiempre)"})
        try:
            with opener.open(req, timeout=8) as resp:
                ctype = (resp.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
                return _leer_limitado(resp), _MIME_FORMATO.get(ctype)
        except urllib.error.HTTPError as exc:
            if exc.code not in (301, 302, 303, 307, 308):
                return None, None
            destino = exc.headers.get("Location")
            if not destino:
                return None, None
            actual = urljoin(actual, destino)
        except Exception:
            return None, None
    return None, None


def guardar_desde_url(url, subcarpeta):
    url = (url or "").strip()
    if not url:
        return None
    datos, formato = _descargar_url(url)
    if not datos or not formato:
        return None
    imagen = _abrir_verificada(datos, formato)
    return _guardar_webp(imagen, subcarpeta) if imagen else None


def miniatura_imagen(ruta_relativa):
    """Devuelve la miniatura si existe; soporta imágenes históricas."""
    if not ruta_relativa:
        return ruta_relativa
    base, ext = os.path.splitext(ruta_relativa)
    candidata = f"{base}-thumb{ext}"
    destino = os.path.join(_BASE, *candidata.split("/"))
    return candidata if os.path.isfile(destino) else ruta_relativa


def _ruta_dentro_base(ruta_relativa):
    try:
        piezas = str(ruta_relativa).replace("\\", "/").split("/")
        destino = os.path.abspath(os.path.join(_BASE, *piezas))
        return destino if os.path.commonpath((_BASE, destino)) == _BASE else None
    except (TypeError, ValueError):
        return None


def borrar_imagen(ruta_relativa):
    """Borra detalle y miniatura únicamente dentro de static/img."""
    destino = _ruta_dentro_base(ruta_relativa)
    if not destino:
        return
    base, ext = os.path.splitext(destino)
    for ruta in (destino, f"{base}-thumb{ext}"):
        if os.path.isfile(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass


AVATAR_LADO = 320


def guardar_avatar(archivo, id_usuario):
    if not archivo or not archivo.filename:
        return None, "Elige una imagen para tu foto de perfil."
    ext = _extension(archivo.filename)
    if ext not in EXTENSIONES:
        return None, "La foto debe ser JPG, PNG, WEBP o GIF."
    datos = _leer_limitado(archivo.stream)
    if not datos:
        return None, "La foto está vacía o pesa más de 5 MB."
    esperado = "jpeg" if ext in ("jpg", "jpeg") else ext
    imagen = _abrir_verificada(datos, esperado)
    if imagen is None:
        return None, "El archivo no es una imagen válida, no coincide con su extensión o es demasiado grande."
    imagen = ImageOps.fit(imagen.convert("RGB"), (AVATAR_LADO, AVATAR_LADO), Image.Resampling.LANCZOS)
    carpeta = os.path.join(_BASE, "perfiles")
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"u{int(id_usuario)}-{secrets.token_hex(6)}.webp"
    imagen.save(os.path.join(carpeta, nombre), "WEBP", quality=82, method=6)
    return f"perfiles/{nombre}", None


def ruta_avatar_valida(ruta, id_usuario):
    import re as _re
    patron = r"perfiles/u%d-[0-9a-f]{12}\.(?:jpg|webp)" % int(id_usuario)
    if not _re.fullmatch(patron, ruta or ""):
        return False
    destino = _ruta_dentro_base(ruta)
    return bool(destino and os.path.isfile(destino))


def podar_avatares(id_usuario, conservar):
    carpeta = os.path.join(_BASE, "perfiles")
    if not os.path.isdir(carpeta):
        return
    dejar = {os.path.basename(r) for r in conservar if r}
    prefijo = f"u{int(id_usuario)}-"
    for nombre in os.listdir(carpeta):
        if nombre.startswith(prefijo) and nombre not in dejar and nombre.endswith((".jpg", ".webp")):
            try:
                os.remove(os.path.join(carpeta, nombre))
            except OSError:
                pass
