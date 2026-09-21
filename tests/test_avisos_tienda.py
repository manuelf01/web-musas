"""Avisos de la tienda: verde (con Deshacer si aplica) y rojo (que señala el campo), también en
login, registro y «Mi cuenta». El inicio de sesión exitoso solo avisa, sin acciones."""

import json
import re

import pytest

from controllers import autenticacion
from model.Usuario import Usuario
from tests.conftest import CLIENTE_ID

T = "token-de-prueba"


@pytest.fixture(autouse=True)
def _sin_bloqueo_de_login():
    autenticacion._intentos_login.clear()
    yield
    autenticacion._intentos_login.clear()


def _info(html):
    return json.loads(re.search(r'id="musa-error-form">(.*?)</script>', html, re.S).group(1))


def _login(client, usuario, clave, **extra):
    datos = {"_csrf": T, "usuario": usuario, "contraseña": clave, "next": ""}
    datos.update(extra)
    return client.post("/login", data=datos, follow_redirects=True)


def test_login_exitoso_solo_dice_inicio_de_sesion_exitoso(bd_limpia, client, csrf):
    html = _login(client, "cliente@correo.com", "Musas2026").get_data(as_text=True)
    assert html.count("Inicio de sesión exitoso") == 1
    assert 'class="aviso aviso--ok"' in html
    assert "aviso__form" not in html and "data-ver-donde" not in html          # sin Deshacer ni «Ver dónde»


def test_login_con_clave_incorrecta_senala_la_contrasena(bd_limpia, client, csrf):
    html = _login(client, "cliente@correo.com", "Equivocada1").get_data(as_text=True)
    assert "La contraseña no es correcta" in html and "data-ver-donde" in html
    info = _info(html)
    assert info["campo"] == "contraseña" and info["modo"] == "pagina"
    assert "Equivocada1" not in html                                            # la clave nunca se guarda


def test_login_con_cuenta_inexistente_senala_el_usuario(bd_limpia, client, csrf):
    html = _login(client, "nadie@correo.com", "Musas2026").get_data(as_text=True)
    assert _info(html)["campo"] == "usuario"
    html = _login(client, "esto no es un correo", "x").get_data(as_text=True)
    assert _info(html)["campo"] == "usuario"
    html = _login(client, "cliente@correo.com", "").get_data(as_text=True)
    assert _info(html)["campo"] == "contraseña"


def test_registro_con_error_senala_el_campo_y_el_exito_solo_avisa(bd_limpia, client, csrf):
    base = {"_csrf": T, "nombres": "Ana", "apellidos": "Lopez", "correo": "ana@nueva.co",
            "telefono": "987654321", "contraseña": "Secreta123"}
    r = client.post("/registro", data={**base, "telefono": "12"})
    assert _info(r.get_data(as_text=True))["campo"] == "telefono"
    r = client.post("/registro", data={**base, "apellidos": ""})
    assert _info(r.get_data(as_text=True))["campo"] == "apellidos"
    r = client.post("/registro", data={**base, "contraseña": "corta"})
    assert _info(r.get_data(as_text=True))["campo"] == "contraseña"
    r = client.post("/registro", data=base, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert html.count("Cuenta creada") == 1 and "aviso__form" not in html


def test_mi_cuenta_actualiza_con_deshacer_y_sin_mensajes_duplicados(bd_limpia, cliente_client):
    antes = Usuario.obtener_dict(CLIENTE_ID)
    datos = {"_csrf": T, "nombres": "Otro Nombre", "apellidos": antes["apellidos"],
             "correo": antes["correo"], "telefono": antes["telefono"]}
    html = cliente_client.post("/mi-cuenta", data=datos, follow_redirects=True).get_data(as_text=True)
    assert html.count("Tus datos se actualizaron") == 1                         # ya no sale doble
    assert Usuario.obtener_dict(CLIENTE_ID)["nombres"] == "Otro Nombre"
    assert 'class="aviso__form"' in html and f'name="nombres" value="{antes["nombres"]}"' in html
    cliente_client.post("/mi-cuenta", data={**datos, "nombres": antes["nombres"]})
    assert Usuario.obtener_dict(CLIENTE_ID)["nombres"] == antes["nombres"]


def test_mi_cuenta_errores_senalan_el_campo(bd_limpia, cliente_client):
    antes = Usuario.obtener_dict(CLIENTE_ID)
    datos = {"_csrf": T, "nombres": antes["nombres"], "apellidos": antes["apellidos"],
             "correo": antes["correo"], "telefono": "12"}
    html = cliente_client.post("/mi-cuenta", data=datos, follow_redirects=True).get_data(as_text=True)
    assert _info(html)["campo"] == "telefono"
    datos = {**datos, "telefono": antes["telefono"], "contraseña": "Nueva12345", "contraseña2": "Distinta123"}
    info = _info(cliente_client.post("/mi-cuenta", data=datos, follow_redirects=True).get_data(as_text=True))
    assert info["campo"] == "contraseña2" and "Nueva12345" not in json.dumps(info)
    datos = {**datos, "contraseña": "", "contraseña2": "", "correo": "no-es-correo"}
    html = cliente_client.post("/mi-cuenta", data=datos, follow_redirects=True).get_data(as_text=True)
    assert _info(html)["campo"] == "correo"


def test_perfil_admin_actualiza_con_deshacer(bd_limpia, admin_client):
    datos = {"_csrf": T, "nombres": "Cambiado", "apellidos": "Ramirez", "correo": "superadmin@lasmusas.pe",
             "dni": "12345678", "telefono": "987654321"}
    html = admin_client.post("/admin/perfil/actualizar", data=datos, follow_redirects=True).get_data(as_text=True)
    assert html.count("Tus datos se actualizaron") == 1 and 'class="aviso__form"' in html
    html = admin_client.post("/admin/perfil/actualizar", data={**datos, "telefono": "1"},
                             follow_redirects=True).get_data(as_text=True)
    assert _info(html)["campo"] == "telefono"
