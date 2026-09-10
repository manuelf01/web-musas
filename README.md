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
el checkout.

### Cuentas de ejemplo (contraseña de todas: `Musas2026`)

| DNI | Rol |
|---|---|
| `12345678` | superusuario (panel completo + gestión de usuarios) |
| `87654321` | administrador (panel sin usuarios) |
| `12345679` | usuario (cliente de la tienda) |

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

Si actualizas una base existente hasta esta versión, respáldala y aplica
`migrations/012_comprobantes_pdf.sql` desde phpMyAdmin antes de iniciar Flask.

## Contraseñas

Regla en todo el proyecto: **mínimo 8 caracteres, con al menos una mayúscula y un
número** (`seguridad.password_valida`). Se guardan con `pbkdf2:sha256`.
