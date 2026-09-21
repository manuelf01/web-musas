# Las Musas — Burger Joint

Tienda web + panel de administración para una hamburguesería nocturna de Chiclayo
(pedidos para **recojo en tienda**, sin pasarela de pago). Flask (MVC) + MariaDB.

## Puesta en marcha (local)

Requiere **Python 3.10** y **MariaDB/MySQL** (XAMPP sirve).

```bash
# 1. Entorno + dependencias
python -m venv .venv
.venv\Scripts\activate          # Windows   ( . .venv/bin/activate en Linux )
pip install -r requirements.txt

# 2. Configuración local (no se versiona)
copy cfg.example.py cfg.py       # ajusta host/usuario/clave si hace falta

# 3. Base de datos
#    Abre phpMyAdmin y pega TODO sql.sql  ->  crea db_musuas con datos de ejemplo.
#    (Nunca correr sql.sql con `mysql < sql.sql`: lleva USE db_musuas dentro.)

# 4. Correr
python app.py                    # http://127.0.0.1:5000
```

Fuera del horario de atención usa `set MUSAS_DEMO=1 && python app.py` para probar
el checkout. Para mostrar los datos reales de pago digital en la confirmación:

```bash
set MUSAS_PAGO_NUMERO=999888777
set MUSAS_PAGO_TITULAR=Las de Siempre
set MUSAS_PAGO_QR=static/img/pagos/qr-yape-plin.png
```

`MUSAS_PAGO_QR` acepta una ruta servida por la aplicación (`static/...`) o una
URL HTTPS. Si se deja vacío, no se muestra un QR inventado.

### Cuentas de ejemplo (contraseña de todas: `Musas2026`)

| Acceso | Rol |
|---|---|
| DNI `12345678` | superusuario (panel completo + gestión de usuarios) |
| DNI `87654321` | administrador (panel sin usuarios) |
| correo `cliente@correo.com` | usuario (cliente de la tienda) |

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

Los tests levantan una base aparte (`db_musuas_test`); la base real no se toca.
CI en GitHub Actions corre `pytest` en cada push y PR.

## Documentación para los desarrolladores

- **`AGENTS.md`** — contexto y convenciones del proyecto (arquitectura, reglas,
  esquema de BD, división del trabajo).
- **`BITACORA-CLAUDE.md`** — bitácora detallada de todos los cambios, decisiones
  y problemas conocidos.
- **`migrations/`** — cambios de esquema numerados (ya incluidos en `sql.sql`).

Si actualizas una base existente hasta esta versión, respáldala y aplica en
orden `migrations/012_comprobantes_pdf.sql` y
`migrations/013_clientes_correo_y_caja.sql` desde phpMyAdmin antes de iniciar
Flask. Una instalación nueva solo necesita `sql.sql`.

## Contraseñas

Regla en todo el proyecto: **mínimo 8 caracteres, con al menos una mayúscula y un
número** (`seguridad.password_valida`). Se guardan con `pbkdf2:sha256`.
