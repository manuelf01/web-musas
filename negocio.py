"""Datos de la sede y horario público, independiente del modo demo de pedidos."""

import os
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

# Perú usa UTC-5; no depende de la zona configurada en Windows ni de tzdata.
HORA_PERU = timezone(timedelta(hours=-5), name="America/Lima")


def ahora_peru():
    """Fecha/hora actual en Perú. Úsala SIEMPRE en el modelo en vez de
    `datetime.now()` (hora local del servidor) o `date.today()`: así el conteo
    de cupos, el corte por hora y el auto-no-show quedan alineados aunque la app
    corra en un servidor en otra zona horaria."""
    return datetime.now(HORA_PERU)
# Nombre comercial del negocio. Único lugar donde vive el texto: cámbialo acá
# y se actualiza en toda la app (Jinja, PDF del comprobante, notificaciones JS
# vía window.NOMBRE_NEGOCIO en base.html). El logo es un ícono de hamburguesa
# sin texto (static/img/marca/v1/simbolo.svg) para que un cambio de nombre no
# obligue a rehacer el logo.
NOMBRE_NEGOCIO = "Las de Siempre"

SEDE = {
    "nombre": "Sede Chiclayo",
    "direccion": "Av. José Balta Sur 006, Chiclayo 14008, Perú",
    "referencia": "La Paperia, cerca del Hotel Colibrí",
    "horario": "Lunes a viernes · 6:00 p.m. – 11:30 p.m. | Sábado · 6:00 p.m. – 11:00 p.m. | Domingo · 9:00 a.m. – 11:00 p.m.",
}
_direccion_mapa = quote("La Paperia, " + SEDE["direccion"])
SEDE["mapa_url"] = "https://www.google.com/maps?q=" + _direccion_mapa
SEDE["mapa_embed"] = SEDE["mapa_url"] + "&z=17&output=embed"

_pago_qr = os.environ.get("MUSAS_PAGO_QR", "").strip().replace("\\", "/")
_pago_qr_externo = _pago_qr.lower().startswith("https://")
if _pago_qr.startswith("static/"):
    _pago_qr = _pago_qr[len("static/"):]

PAGO_DIGITAL = {
    "numero": os.environ.get("MUSAS_PAGO_NUMERO", "").strip(),
    "titular": os.environ.get("MUSAS_PAGO_TITULAR", NOMBRE_NEGOCIO).strip(),
    "qr": _pago_qr,
    "qr_externo": _pago_qr_externo,
}


def horario_dia(fecha):
    """Minutos desde medianoche según el horario de OlaClick (/info)."""
    if fecha.weekday() == 6:
        return 9 * 60, 23 * 60
    if fecha.weekday() == 5:
        return 18 * 60, 23 * 60
    return 18 * 60, 23 * 60 + 30


def _limites_dia(ahora):
    apertura, cierre = horario_dia(ahora.date())
    medianoche = ahora.replace(hour=0, minute=0, second=0, microsecond=0)
    return medianoche + timedelta(minutes=apertura), medianoche + timedelta(minutes=cierre)


def _texto_hora(hora):
    return f"{hora.hour % 12 or 12}:{hora.minute:02d} {'p.m.' if hora.hour >= 12 else 'a.m.'}"


def estado_local(ahora=None):
    """Horario semanal en Perú: apertura inclusiva y cierre exclusivo."""
    ahora = ahora if ahora is not None else datetime.now(HORA_PERU)
    if ahora.tzinfo is None:
        raise ValueError("La fecha debe incluir su zona horaria")
    ahora = ahora.astimezone(HORA_PERU)
    apertura, cierre = _limites_dia(ahora)
    abierto = apertura <= ahora < cierre
    siguiente = cierre if abierto else apertura
    if ahora >= cierre:
        siguiente, _ = _limites_dia(ahora + timedelta(days=1))
    return {
        "abierto": abierto,
        "texto": "Abierto" if abierto else "Cerrado",
        "cambia_en": (siguiente - ahora).total_seconds(),
        "horario_hoy": f"{_texto_hora(apertura)} – {_texto_hora(cierre)}",
    }
