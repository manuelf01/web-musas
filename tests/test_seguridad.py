"""Política de contraseña y CSRF."""

import pytest

from seguridad import password_valida, PASSWORD_MIN


@pytest.mark.parametrize("pw", [
    "Musas2026",       # 8+, mayúscula, número
    "Abcdefg1",
    "PASSWORD9x",
])
def test_password_valida_acepta(pw):
    assert password_valida(pw) is None


@pytest.mark.parametrize("pw", [
    "",                # vacía
    "Corta1",          # < 8
    "minuscula123",    # sin mayúscula
    "SinNumeros",      # sin dígito
    "12345678",        # sin mayúscula
    None,
])
def test_password_valida_rechaza(pw):
    assert password_valida(pw) is not None


def test_password_min_es_ocho():
    assert PASSWORD_MIN == 8
    assert password_valida("Abcdef1") is not None      # 7
    assert password_valida("Abcdefg1") is None          # 8


def test_post_sin_csrf_es_rechazado(client):
    r = client.post("/login", data={"dni": "12345678", "contrasena": "x"})
    assert r.status_code == 400


def test_post_con_csrf_pasa_la_barrera(client, csrf):
    # Con token válido ya no da 400 de CSRF (puede fallar el login, pero no por CSRF).
    r = client.post("/login", data={"_csrf": csrf, "dni": "0", "contrasena": "x", "captcha": ""})
    assert r.status_code != 400
