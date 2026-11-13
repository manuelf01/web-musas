import pymysql
import os
from cfg import *

# Permite ejecutar una copia local contra una base desechable sin editar cfg.py.
# Si no se define, se conserva la base configurada habitualmente.
db = os.environ.get("MUSAS_DB", db)

def obtener_conexion():
    return pymysql.connect(host=host, port=port, user=username, password=password, db=db)
