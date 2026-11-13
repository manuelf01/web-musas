"""El login no enumera personal y carga solo los recursos que necesita."""


def test_endpoint_de_deteccion_de_dni_fue_eliminado(client):
    assert client.get("/login/tipo-dni?dni=12345678").status_code == 404


def test_login_no_carga_scripts_de_paginas_ajenas(client):
    html = client.get("/login").get_data(as_text=True)
    assert "ui-comun.js" in html
    assert "loader.js" in html
    assert "avisos.js" in html
    assert "animaciones.js" not in html
    assert "estado-local.js" not in html
    assert "fonts.googleapis.com" not in html
    assert "fonts.gstatic.com" not in html
    assert "ha-1-desktop.webp" in html
    assert "ha-1-mobile.webp" in html
    assert "Correo electrónico</label>" in html
    assert "DNI administrativo" not in html
    assert "Clientes: usa tu correo" not in html


def test_cliente_no_puede_ingresar_con_dni(client, csrf, bd_limpia):
    respuesta = client.post("/login", data={
        "_csrf": csrf,
        "usuario": "12345679",
        "contraseña": "Musas2026",
        "captcha": "cualquiera",
    }, follow_redirects=True)
    html = respuesta.get_data(as_text=True)
    assert "No pudimos iniciar sesión con esos datos" in html
    with client.session_transaction() as sesion:
        assert "cliente.auth" not in sesion
