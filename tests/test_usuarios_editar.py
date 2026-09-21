"""RS 2.2: el administrador modifica los datos de una cuenta."""

from model.Usuario import Usuario

T = "token-de-prueba"


def _crear(admin_client, correo="editar@undo.co", dni=""):
    admin_client.post("/admin/usuarios/guardar", data={
        "_csrf": T, "dni": dni, "nombres": "Ana", "apellidos": "Lopez", "correo": correo,
        "telefono": "987654321", "contraseña": "Secreta123", "rol": "usuario"})
    return Usuario.id_por_correo(correo)


def _editar(admin_client, uid, **cambios):
    datos = {"_csrf": T, "id": uid, "rol": "usuario", "activo": "1", "dni": "",
             "nombres": "Ana", "apellidos": "Lopez", "correo": "editar@undo.co", "telefono": "987654321"}
    datos.update(cambios)
    return admin_client.post("/admin/usuarios/actualizar", data=datos, follow_redirects=True)


def test_admin_modifica_datos_y_puede_deshacer(bd_limpia, admin_client, csrf):
    uid = _crear(admin_client)
    r = _editar(admin_client, uid, nombres="Ana María", telefono="911222333", correo="nuevo@undo.co")
    html = r.get_data(as_text=True)
    u = Usuario.obtener_dict(uid)
    assert u["nombres"] == "Ana María" and u["telefono"] == "911222333" and u["correo"] == "nuevo@undo.co"
    assert "Cuenta actualizada" in html and "Deshacer" in html and 'name="nombres" value="Ana"' in html
    _editar(admin_client, uid, nombres="Ana", telefono="987654321", correo="editar@undo.co")
    assert Usuario.obtener_dict(uid)["nombres"] == "Ana"


def test_edicion_valida_datos_y_unicidad(bd_limpia, admin_client, csrf):
    uid = _crear(admin_client)
    otro = _crear(admin_client, "otro@undo.co")
    r = _editar(admin_client, uid, telefono="12")
    assert "9 dígitos" in r.get_data(as_text=True) and Usuario.obtener_dict(uid)["telefono"] == "987654321"
    r = _editar(admin_client, uid, correo="otro@undo.co")
    assert "ya está en uso" in r.get_data(as_text=True)
    r = _editar(admin_client, uid, rol="administrador", dni="")
    assert "DNI de 8 dígitos" in r.get_data(as_text=True) and Usuario.obtener_dict(uid)["rol"] == "usuario"
    _editar(admin_client, uid, rol="administrador", dni="45678912")
    u = Usuario.obtener_dict(uid)
    assert u["rol"] == "administrador" and u["dni"] == "45678912"
    assert otro != uid


def _hash(uid):
    import bd
    conexion = bd.obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT contraseña FROM usuario WHERE idUsuario = %s", (uid,))
            return cursor.fetchone()[0]
    finally:
        conexion.close()


def test_la_contrasena_no_se_toca_al_editar(bd_limpia, admin_client, csrf):
    uid = _crear(admin_client)
    antes = _hash(uid)
    _editar(admin_client, uid, nombres="Cambiado", **{"contraseña": "Otra12345"})
    assert Usuario.obtener_dict(uid)["nombres"] == "Cambiado"
    assert _hash(uid) == antes
