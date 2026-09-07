"""
Utilidades de seguridad del login de Las Musas.

- Generación del captcha de imagen distorsionada (para el acceso de administradores).
- El hash de contraseñas se hace con werkzeug.security desde model/Usuario.py y
  model/Autenticacion.py (generate_password_hash / check_password_hash).
"""

import io
import random

from PIL import Image, ImageDraw, ImageFont, ImageFilter

CAPTCHA_LARGO = 6
# Sin caracteres ambiguos (I, O, 0, 1)
_ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

_RUTAS_FUENTE = [
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/Arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
]


def _cargar_fuente(tam):
    for ruta in _RUTAS_FUENTE:
        try:
            return ImageFont.truetype(ruta, tam)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size=tam)  # Pillow >= 10
    except TypeError:
        return ImageFont.load_default()


def generar_texto_captcha(largo=CAPTCHA_LARGO):
    return "".join(random.choice(_ALFABETO) for _ in range(largo))


def generar_imagen_captcha(texto):
    """Devuelve un BytesIO con el PNG del captcha para `texto`."""
    ancho, alto = 220, 80
    fondo = (251, 247, 240)   # crema
    tinta = (26, 21, 18)      # carbón
    brasa = (219, 66, 0)

    img = Image.new("RGB", (ancho, alto), fondo)
    draw = ImageDraw.Draw(img)
    fuente = _cargar_fuente(42)

    x = 16
    for i, ch in enumerate(texto):
        cimg = Image.new("RGBA", (48, 62), (0, 0, 0, 0))
        ImageDraw.Draw(cimg).text(
            (4, 2), ch, font=fuente, fill=(brasa if i % 2 == 0 else tinta)
        )
        cimg = cimg.rotate(random.randint(-28, 28), expand=1, resample=Image.BICUBIC)
        img.paste(cimg, (x, random.randint(2, 16)), cimg)
        x += 32

    for _ in range(6):
        draw.line(
            [(random.randint(0, ancho), random.randint(0, alto)),
             (random.randint(0, ancho), random.randint(0, alto))],
            fill=(107, 97, 87), width=1,
        )
    for _ in range(400):
        draw.point(
            (random.randint(0, ancho), random.randint(0, alto)),
            fill=(190, 178, 165),
        )

    img = img.filter(ImageFilter.SMOOTH_MORE)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
