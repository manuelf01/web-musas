"""Configuración de las pruebas.

Levanta una base **de pruebas** aparte (`db_musuas_test`) a partir de `sql.sql`
—quitándole las líneas `CREATE DATABASE` / `USE` para no tocar la base real—
y apunta `bd.db` a ella antes de importar la app.
"""

import os
import re
import pathlib

# Antes de importar nada del proyecto: modo demo (sin corte por hora / no-show)
# y horario 24 h para que las pruebas no dependan del reloj.
os.environ.setdefault("MUSAS_DEMO", "1")
os.environ.setdefault("MUSAS_HORA_APERTURA", "0")
os.environ.setdefault("MUSAS_HORA_CIERRE", "24")

import pytest
import pymysql
from pymysql.constants import CLIENT

RAIZ = pathlib.Path(__file__).resolve().parent.parent
TEST_DB = os.environ.get("MUSAS_TEST_DB", "db_musuas_test")
DB_HOST = os.environ.get("MUSAS_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("MUSAS_DB_PORT", "3306"))
DB_USER = os.environ.get("MUSAS_DB_USER", "root")
DB_PASS = os.environ.get("MUSAS_DB_PASS", "")

# ids de las cuentas sembradas por sql.sql (contraseña de todas: Musas2026)
SUPER_ID, ADMIN_ID, CLIENTE_ID = 1, 2, 3
PASS_OK = "Musas2026"


def _conectar(db=None):
    return pymysql.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
        database=db, autocommit=True, charset="utf8mb4",
        client_flag=CLIENT.MULTI_STATEMENTS,
    )


def _esquema_sin_create_database():
    txt = (RAIZ / "sql.sql").read_text(encoding="utf-8")
    txt = re.sub(r"(?ims)^\s*CREATE\s+DATABASE\b.*?;\s*$", "", txt)
    txt = re.sub(r"(?im)^\s*USE\s+`?[\w-]+`?\s*;\s*$", "", txt)
    return txt


def _reconstruir_bd():
    con = _conectar()
    try:
        with con.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{TEST_DB}`")
            cur.execute(
                f"CREATE DATABASE `{TEST_DB}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )
    finally:
        con.close()
    con = _conectar(TEST_DB)
    try:
        with con.cursor() as cur:
            cur.execute(_esquema_sin_create_database())
            while cur.nextset():
                pass
    finally:
        con.close()


@pytest.fixture(scope="session", autouse=True)
def _bd_sesion():
    import bd
    bd.db = TEST_DB
    _reconstruir_bd()
    yield
    con = _conectar()
    try:
        with con.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS `{TEST_DB}`")
    finally:
        con.close()


@pytest.fixture()
def bd_limpia(_bd_sesion):
    """Deja la base como recién sembrada antes de cada prueba que la pida."""
    _reconstruir_bd()
    import bd
    bd.db = TEST_DB
    return None


@pytest.fixture()
def app(_bd_sesion):
    from app import app as flask_app
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def csrf(client):
    """Fija un token CSRF conocido en la sesión y lo devuelve para los POST."""
    with client.session_transaction() as s:
        s["_csrf_token"] = "token-de-prueba"
    return "token-de-prueba"


@pytest.fixture()
def admin_client(client, csrf):
    with client.session_transaction() as s:
        s["admin.auth"] = {
            "idUsuario": SUPER_ID, "rol": "superusuario",
            "nombres": "Piero", "apellidos": "Ramirez", "dni": "12345678",
        }
    return client


@pytest.fixture()
def cliente_client(client, csrf):
    with client.session_transaction() as s:
        s["cliente.auth"] = {
            "idUsuario": CLIENTE_ID, "rol": "usuario",
            "nombres": "Cliente", "apellidos": "Prueba", "dni": "12345679",
        }
    return client
