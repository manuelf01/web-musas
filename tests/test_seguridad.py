"""Política de contraseña y CSRF."""

import pytest
import bd

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


def test_cliente_se_registra_y_entra_con_correo_sin_dni(client, csrf, bd_limpia):
    respuesta = client.post("/registro", data={
        "_csrf": csrf, "nombres": "Ana", "apellidos": "Prueba",
        "correo": "ana@example.com", "telefono": "987654321",
        "contraseña": "Clave2026",
    })
    assert respuesta.status_code in (301, 302)
    con = bd.obtener_conexion()
    with con.cursor() as cur:
        cur.execute("SELECT dni FROM usuario WHERE correo=%s", ("ana@example.com",))
        assert cur.fetchone()[0] is None
    con.close()

    respuesta = client.post("/login", data={
        "_csrf": csrf, "usuario": "ana@example.com", "contraseña": "Clave2026",
    })
    assert respuesta.status_code in (301, 302)
    with client.session_transaction() as sesion:
        assert sesion["cliente.auth"]["correo"] == "ana@example.com"
