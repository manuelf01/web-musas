# Probar la rama `Ramirez` en una base local aislada

Este flujo crea una base manual llamada `db_musuas_prueba_companero` y carga
el esquema completo y los datos de demostración de `sql.sql`. El script elimina
las instrucciones `CREATE DATABASE` y `USE` del archivo antes de ejecutarlo y
nunca escribe en `db_musuas`.

## 1. Obtener el código

```powershell
git fetch origin
git switch Ramirez
git pull --ff-only origin Ramirez
```

## 2. Preparar el entorno

Inicia MySQL en XAMPP. Desde la carpeta del proyecto, configura Python y las
credenciales locales siguiendo `AGENTS.md`:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item cfg.example.py cfg.py
```

Edita `cfg.py` para indicar el usuario y contraseña locales de MySQL. Ese
archivo está ignorado por Git y no se debe compartir.

## 3. Crear la base desechable

```powershell
python scripts\preparar_bd_companero.py
```

El script crea `db_musuas_prueba_companero` solo si aún no existe. Si ya existe,
se detiene sin borrarla. La base contiene cuentas de demostración descritas en
`AGENTS.md`; usa únicamente datos de prueba.

## 4. Ejecutar la aplicación contra esa base

En la misma ventana de PowerShell:

```powershell
$env:MUSAS_DB = "db_musuas_prueba_companero"
python app.py
```

Abre <http://127.0.0.1:5000>. Al terminar, puedes quitar la variable de esa
sesión con:

```powershell
Remove-Item Env:MUSAS_DB
```

`MUSAS_DB` solo cambia la base que usa la aplicación en esa sesión. Sin esa
variable, se mantiene el valor `db` habitual de `cfg.py`.

## Pruebas automáticas

```powershell
pytest -q
```

Las pruebas usan otra base separada, `db_musuas_test`, que se recrea al iniciar
la suite. No ejecutes pruebas mientras apuntes manualmente la aplicación a una
base con información que quieras conservar.
