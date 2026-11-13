"""Crea una base local desechable para probar la rama Ramirez.

No modifica ni elimina db_musuas. La base de pruebas se crea una sola vez;
si ya existe, el script se detiene para evitar borrar datos del compañero.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pymysql
from pymysql.constants import CLIENT

from cfg import host, password, port, username


NOMBRE_BD_PRUEBA = "db_musuas_prueba_companero"
RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_ESQUEMA = RAIZ / "sql.sql"


def main() -> int:
    if not ARCHIVO_ESQUEMA.is_file():
        print(f"No se encontró el esquema: {ARCHIVO_ESQUEMA}", file=sys.stderr)
        return 1

    conexion = pymysql.connect(
        host=host,
        port=port,
        user=username,
        password=password,
        charset="utf8mb4",
        autocommit=True,
        client_flag=CLIENT.MULTI_STATEMENTS,
    )
    creada_por_este_proceso = False
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM information_schema.schemata WHERE schema_name=%s",
                (NOMBRE_BD_PRUEBA,),
            )
            if cursor.fetchone():
                print(
                    f"La base {NOMBRE_BD_PRUEBA} ya existe. No se modificó. "
                    "Si quieres rehacerla, respalda primero lo que necesites y "
                    "elimínala manualmente desde phpMyAdmin.",
                    file=sys.stderr,
                )
                return 2

            cursor.execute(
                f"CREATE DATABASE `{NOMBRE_BD_PRUEBA}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )
            creada_por_este_proceso = True

        sql = ARCHIVO_ESQUEMA.read_text(encoding="utf-8")
        sql = re.sub(r"(?ims)^\s*CREATE\s+DATABASE\b.*?;\s*$", "", sql)
        sql = re.sub(r"(?im)^\s*USE\s+`?[\w-]+`?\s*;\s*$", "", sql)

        conexion.select_db(NOMBRE_BD_PRUEBA)
        with conexion.cursor() as cursor:
            cursor.execute(sql)
            while cursor.nextset():
                pass

        print(f"Base desechable creada y cargada: {NOMBRE_BD_PRUEBA}")
        print("La base db_musuas no fue modificada.")
        return 0
    except Exception as exc:
        if creada_por_este_proceso:
            try:
                with conexion.cursor() as cursor:
                    cursor.execute(f"DROP DATABASE IF EXISTS `{NOMBRE_BD_PRUEBA}`")
            except Exception:
                pass
        print(f"No se pudo preparar la base de prueba: {exc}", file=sys.stderr)
        return 1
    finally:
        conexion.close()


if __name__ == "__main__":
    raise SystemExit(main())
