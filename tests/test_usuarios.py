"""Roles y política de contraseña en el CRUD de usuarios."""

from model.Usuario import Usuario

from tests.conftest import SUPER_ID, ADMIN_ID, CLIENTE_ID


def test_cambiar_rol_normal(bd_limpia):
    assert Usuario.cambiar_rol(CLIENTE_ID, "administrador") is None
    assert Usuario.obtener_dict(CLIENTE_ID)["rol"] == "administrador"


def test_no_se_cambia_el_rol_de_un_superusuario(bd_limpia):
    assert Usuario.cambiar_rol(SUPER_ID, "administrador") is not None
    assert Usuario.obtener_dict(SUPER_ID)["rol"] == "superusuario"


def test_no_se_promueve_a_superusuario_por_edicion(bd_limpia):
    assert Usuario.cambiar_rol(ADMIN_ID, "superusuario") is not None


def test_rol_invalido(bd_limpia):
    assert Usuario.cambiar_rol(CLIENTE_ID, "jefe") is not None


def test_insertar_usuario_exige_password_fuerte(bd_limpia):
    err = Usuario.insertar_usuario(
        "44556677", "Nuevo", "Test", "n@t.pe", "999888777", "corta", 1)
    assert err is not None
    ok = Usuario.insertar_usuario(
        "44556677", "Nuevo", "Test", "n@t.pe", "999888777", "Segura123", 1)
    assert ok is None


def test_insertar_usuario_dni_repetido(bd_limpia):
    err = Usuario.insertar_usuario(
        "12345678", "Otro", "Test", "o@t.pe", "999888777", "Segura123", 0, "administrador")
    assert err is not None


def test_conteo_por_rol(bd_limpia):
    c = Usuario.contar_por_rol()
    assert c["superusuario"] == 1
    assert c["administrador"] == 1
    assert c["usuario"] == 1


def test_admin_no_entra_a_gestion_de_usuarios(client, csrf):
    with client.session_transaction() as s:
        s["admin.auth"] = {"idUsuario": ADMIN_ID, "rol": "administrador",
                           "nombres": "Admin", "apellidos": "P", "dni": "87654321"}
    r = client.get("/admin/usuarios/", follow_redirects=False)
    assert r.status_code in (301, 302)  # lo saca al panel


def test_superusuario_si_entra(admin_client):
    r = admin_client.get("/admin/usuarios/")
    assert r.status_code == 200
