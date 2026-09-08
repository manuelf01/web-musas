# Introducción

MVC en construcción para una hamburguesería. Se usa las siguientes herramientas:

- [Flask](https://flask.palletsprojects.com/en/2.3.x/http:// "Flask")
- SGBD MySQL

# Instalación

Una vez clonamos el repositorio:

1. Creamos el entorno virtual:
<p>Linux:</p>

```bash
python3 -m venv .venv
```

<p>Windows:</p>

```bash
py -3 -m venv .venv
```

2. Activamos el entorno virtual:
<p>Linux:</p>

```bash
. .venv/bin/activate
```

<p>Windows:</p>

```bash
.venv\Scripts\activate
```

3. Instalamos las dependencias:

```bash
powershell -ExecutionPolicy Bypass -File scripts/instalar_dependencias.ps1
```

El instalador retira `flask-jwt 0.3.2`, que es incompatible con la versión
actual de `PyJWT`, e instala `Flask-JWT-Extended`.

4. La configuración se define con variables de entorno. Copia `.env.example`
como `.env` si necesitas cambiar los valores locales. Sin `.env`, el proyecto
usa los valores habituales de XAMPP y la base `bd_musuas`.

```
host = 'host'
port = 1111
db = 'nombre_bd'
username = 'user'
password = 'password'
```

5. En una base creada con una versión anterior del proyecto, ejecutamos una sola
vez y en orden:

```text
migrations/001_actividades_3_a_9.sql
migrations/002_productos_usuarios_captcha.sql
```

La segunda migración convierte el precio a `DECIMAL(10,2)`, formaliza el stock,
agrega la ruta de imagen del producto y los campos de usuario necesarios para
el nombre administrativo y el control de intentos.

6. Si la base está vacía, creamos el primer administrador desde la raíz del
proyecto:

```bash
python -m scripts.crear_admin
```

El nombre de acceso administrativo se genera con la inicial del primer nombre y
los primeros cinco dígitos del DNI. Por ejemplo, `Manuel` y `74228679` producen
`m74228`. Las sesiones administrativas caducan a los 30 minutos.

## Sistema visual

Las vistas de cliente y administración comparten el sistema visual
`static/styles/musas-design.css`, adaptado de las plantillas Stitch y del archivo
`nocturnal_artisanal_culinary/DESIGN.md`. La integración conserva las rutas
Flask, los formularios Jinja, el carrito, el control de stock, la autenticación
y los módulos administrativos; las plantillas de Stitch se usan como referencia
visual y no se ejecutan directamente.

**DESDE EL ARCHIVO APP.PY CORREMOS EL PROYECTO**
