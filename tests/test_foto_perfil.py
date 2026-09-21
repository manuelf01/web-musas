"""Foto de perfil: se sube, se recorta cuadrada y aparece junto al nombre en tienda y panel."""

import io
import os

import pytest
from PIL import Image

import subidas
from model.Usuario import Usuario
from tests.conftest import CLIENTE_ID, SUPER_ID

T = "token-de-prueba"


@pytest.fixture()
def carpeta_fotos(tmp_path, monkeypatch):
    monkeypatch.setattr(subidas, "_BASE", str(tmp_path))
    return tmp_path


def _png(ancho=400, alto=200, color=(200, 60, 20)):
    buf = io.BytesIO()
    Image.new("RGB", (ancho, alto), color).save(buf, "PNG")
    buf.seek(0)
    return buf


def _subir(cli, url, contenido, nombre="yo.png"):
    return cli.post(url, data={"_csrf": T, "foto": (contenido, nombre)},
                    content_type="multipart/form-data", follow_redirects=True)


def test_cliente_sube_foto_cuadrada_y_se_ve_en_la_cabecera(bd_limpia, cliente_client, carpeta_fotos):
    r = _subir(cliente_client, "/mi-cuenta/foto", _png())
    html = r.get_data(as_text=True)
    assert "foto de perfil se actualizó" in html
    ruta = Usuario.obtener_dict(CLIENTE_ID)["foto"]
    assert ruta.startswith("perfiles/u%d-" % CLIENTE_ID) and ruta.endswith(".jpg")
    with Image.open(carpeta_fotos / ruta) as img:
        assert img.size == (320, 320)                       # recortada al centro, cuadrada
    cabecera = cliente_client.get("/carta").get_data(as_text=True)
    assert f'class="musa-avatar musa-avatar--foto"><img src="/static/img/{ruta}"' in cabecera
    assert 'class="musa-perfil"' in cabecera and "Mi cuenta" in cabecera


def test_cambiar_foto_conserva_la_anterior_para_deshacer_y_poda_las_viejas(bd_limpia, cliente_client, carpeta_fotos):
    _subir(cliente_client, "/mi-cuenta/foto", _png())
    primera = Usuario.obtener_dict(CLIENTE_ID)["foto"]
    r = _subir(cliente_client, "/mi-cuenta/foto", _png(color=(10, 10, 200)))
    segunda = Usuario.obtener_dict(CLIENTE_ID)["foto"]
    html = r.get_data(as_text=True)
    assert primera != segunda
    assert (carpeta_fotos / primera).exists() and (carpeta_fotos / segunda).exists()   # la vieja sirve para deshacer
    assert 'action="/mi-cuenta/foto/restaurar"' in html and f'value="{primera}"' in html
    _subir(cliente_client, "/mi-cuenta/foto", _png(color=(10, 200, 10)))
    assert not (carpeta_fotos / primera).exists()                                        # dos cambios atrás: se borra


def test_deshacer_foto_y_quitar_con_deshacer(bd_limpia, cliente_client, carpeta_fotos):
    _subir(cliente_client, "/mi-cuenta/foto", _png())
    primera = Usuario.obtener_dict(CLIENTE_ID)["foto"]
    _subir(cliente_client, "/mi-cuenta/foto", _png(color=(10, 10, 200)))
    r = cliente_client.post("/mi-cuenta/foto/restaurar", data={"_csrf": T, "ruta": primera}, follow_redirects=True)
    assert "Foto restaurada" in r.get_data(as_text=True)
    assert Usuario.obtener_dict(CLIENTE_ID)["foto"] == primera
    r = cliente_client.post("/mi-cuenta/foto/quitar", data={"_csrf": T}, follow_redirects=True)
    html = r.get_data(as_text=True)
    assert "Quitaste tu foto" in html and 'action="/mi-cuenta/foto/restaurar"' in html
    assert Usuario.obtener_dict(CLIENTE_ID)["foto"] is None
    assert "musa-avatar--foto" not in cliente_client.get("/carta").get_data(as_text=True)
    cliente_client.post("/mi-cuenta/foto/restaurar", data={"_csrf": T, "ruta": primera})
    assert Usuario.obtener_dict(CLIENTE_ID)["foto"] == primera


def test_restaurar_rechaza_rutas_ajenas(bd_limpia, cliente_client, carpeta_fotos):
    _subir(cliente_client, "/mi-cuenta/foto", _png())
    propia = Usuario.obtener_dict(CLIENTE_ID)["foto"]
    for ruta in ("perfiles/u1-aaaaaaaaaaaa.jpg", "../../cfg.py", "productos/x.jpg", "perfiles/u%d-zzzz.jpg" % CLIENTE_ID):
        r = cliente_client.post("/mi-cuenta/foto/restaurar", data={"_csrf": T, "ruta": ruta}, follow_redirects=True)
        assert "ya no está disponible" in r.get_data(as_text=True)
    assert Usuario.obtener_dict(CLIENTE_ID)["foto"] == propia


def test_archivos_invalidos_se_rechazan(bd_limpia, cliente_client, carpeta_fotos):
    r = _subir(cliente_client, "/mi-cuenta/foto", io.BytesIO(b"esto no es una imagen"), "falsa.png")
    assert "no es una imagen válida" in r.get_data(as_text=True)
    r = _subir(cliente_client, "/mi-cuenta/foto", _png(), "virus.exe")
    assert "JPG, PNG, WEBP o GIF" in r.get_data(as_text=True)
    r = _subir(cliente_client, "/mi-cuenta/foto", io.BytesIO(b"0" * (5 * 1024 * 1024 + 10)), "grande.png")
    assert "más de 5 MB" in r.get_data(as_text=True)
    assert Usuario.obtener_dict(CLIENTE_ID)["foto"] is None
    assert not list(carpeta_fotos.rglob("*.jpg"))


def test_sin_sesion_no_se_puede_subir(client, carpeta_fotos):
    r = client.post("/mi-cuenta/foto", data={"_csrf": T}, follow_redirects=False)
    assert r.status_code in (302, 400)


def test_admin_sube_foto_y_aparece_en_la_barra_superior(bd_limpia, admin_client, carpeta_fotos):
    r = _subir(admin_client, "/admin/perfil/foto", _png(300, 500))
    assert "foto de perfil se actualizó" in r.get_data(as_text=True)
    ruta = Usuario.obtener_dict(SUPER_ID)["foto"]
    assert ruta and os.path.exists(carpeta_fotos / ruta)
    html = admin_client.get("/admin/").get_data(as_text=True)
    assert 'class="adm-perfil"' in html and f'/static/img/{ruta}' in html
    assert html.count("adm-avatar--foto") >= 2                 # barra superior y pie del menú lateral
    perfil = admin_client.get("/admin/perfil/").get_data(as_text=True)
    assert "Cambiar foto" in perfil and "Quitar foto" in perfil


def test_sin_foto_se_muestran_las_iniciales(bd_limpia, admin_client, cliente_client):
    html = admin_client.get("/admin/").get_data(as_text=True)
    assert 'class="adm-avatar">' in html and "adm-avatar--foto" not in html
    tienda = cliente_client.get("/carta").get_data(as_text=True)
    assert "musa-perfil__txt" in tienda and "musa-avatar--foto" not in tienda
