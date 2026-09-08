# AGENTS.md — Contexto para Codex (y cualquier asistente de IA)

> Este archivo es para **Codex**. Es el equivalente de `BITACORA-CLAUDE.md`
> (que llevó Claude) pero pensado para que un asistente entienda de una sola
> lectura **qué es el proyecto, cómo está construido, qué reglas respetar y
> cómo levantarlo**. Si cambias algo importante, anótalo también en
> `BITACORA-CLAUDE.md` para que el equipo lo vea.

---

## 1. Qué es

**Las Musas** — e-commerce de una hamburguesería nocturna en Lima (Miraflores).
Web MVC en **Flask** + **MariaDB** (XAMPP). Proyecto de tesis, 2 integrantes.

**Regla de oro del negocio:**
- El negocio es **solo retiro en tienda** (no hay delivery).
- El pago es **presencial** (efectivo/tarjeta) o **Yape/Plin manual** — **no hay
  pasarela de pago**.
- La confirmación del pedido es la **palabra clave** (`registroPedido.keyPedido`,
  un número de 4 dígitos). El cliente la muestra en el mostrador y con eso se le
  entrega el pedido.
- El comprobante (boleta / nota de venta) se emite **al entregar** el pedido,
  no al hacerlo (porque el pago es al recojo).

**NO implementar** (aparecen en los diseños de Stitch pero no van): delivery,
cupones, programa de puntos / "Club Nocturno", factura con RUC / SUNAT / QR,
"término de la carne", slug / ícono / color de categorías.

---

## 2. Cómo levantarlo (local, Windows + XAMPP)

```bash
# 1. Entorno
py -3.10 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 2. Config
copy cfg.example.py cfg.py      # ajusta si tu MySQL no es root sin password

# 3. Base de datos
#    XAMPP → Start MySQL. Luego en phpMyAdmin, pestaña SQL:
#    copia y pega TODO sql.sql  (crea db_musuas con datos de ejemplo)

# 4. Correr
python app.py                   # http://127.0.0.1:5000

# Para probar el checkout fuera del horario 6-10 p.m.:
set MUSAS_DEMO=1 && python app.py
```

**Cuentas de ejemplo** (creadas por `sql.sql`, contraseña de todas: `Musas2026`):

| DNI | Rol | Acceso |
|---|---|---|
| `12345678` | superusuario | Todo el panel + **Gestión de usuarios** |
| `87654321` | administrador | Panel sin la sección Usuarios |
| `12345679` | usuario | Tienda (cliente) |

**Backup del entorno de Ramirez:** `db/backup_db_musuas.sql` es un `mysqldump`
del estado real con el que se trabajó (incluye datos de prueba y hashes de
contraseña desconocidos — sirve de referencia, no para loguearse). Para empezar
limpio usa **`sql.sql`**.

### Quirks del equipo (heredados de la bitácora)
- Python del proyecto es **3.10** (en el `.venv`). Puede haber un 3.13 en el sistema.
- `pip install` puede fallar con `CERTIFICATE_VERIFY_FAILED` (antivirus intercepta SSL):
  `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org ...`
- Aplicar SQL con `ñ` (la columna `contraseña`): usar **phpMyAdmin**, `pymysql`,
  o `mysql --default-character-set=utf8mb4 < archivo.sql`. El pipe `mysql < x.sql`
  a secas en Windows corrompe la `ñ`.
- `MUSAS_DEMO=1` ignora el corte por "hora ya pasada" y desactiva el auto-no-show
  (para probar a cualquier hora). **Nunca en producción.**
- `MUSAS_HORA_APERTURA` / `MUSAS_HORA_CIERRE` (enteros 0-24) cambian el horario de
  recojo sin tocar código (por defecto 18 y 22).

---

## 3. Arquitectura

```
app.py                 # registra blueprints, CSRF, headers, JWT (heredado), swagger
bd.py                  # obtener_conexion() -> pymysql (lee cfg.py)
cfg.py                 # local, gitignored (host/port/db/user/pass/secret_key)
seguridad.py           # captcha (login admin) + CSRF de sesión (token propio)
subidas.py             # guardar imágenes: archivo subido o descarga desde URL
formato.py             # soles_en_letras() para el comprobante

controllers/
  cliente.py           # TIENDA: home, carta, /productos/<cat>, detalle,
                        #  carrito, /compra (checkout), mis-pedidos, /mi-cuenta
  autenticacion.py     # login unificado (DNI+clave, +captcha si es panel), registro, logout
  admin.py             # blueprint /admin + before_request (exige login; Usuarios = solo superusuario)
  admin_pedidos.py     # CRUD de PEDIDOS + confirmar recojo + avanzar preparación
  admin_productos.py   # CRUD de PRODUCTOS (panel deslizante, imagen archivo/URL, dar de baja)
  admin_categoria_producto.py  # CRUD de CATEGORÍAS (modal)
  admin_usuarios.py    # CRUD de USUARIOS + roles (solo superusuario)
  admin_ventas.py      # VENTAS: KPIs, gráfico, lista de comprobantes, detalle
  admin_perfil.py      # /admin/perfil: el admin corrige sus propios datos

model/                 # una clase por tabla, métodos estáticos, SQL a mano con pymysql
templates/client/*     # tienda   (extends client/base.html)
templates/admin/*      # panel    (extends admin/base.html — sidebar oscuro "Neo-brasa")
static/css/musas-theme.css   # TODO el CSS (sistema de diseño "Neo-brasa")
static/js/*            # vanilla JS, sin frameworks
migrations/00N_*.sql   # cambios de esquema numerados (ya están todos en sql.sql)
```

**Sistema de diseño "Neo-brasa"**: brasa `#DB4200`, mostaza `#F5C842`, carbón
`#1A1512`, crema `#FBF7F0`. Fuentes Space Grotesk + Inter. Bootstrap 5.2.3 por CDN
(se usa la grilla y algún modal; el resto es CSS propio en `musas-theme.css`).

**Sin dependencias JS nuevas.** El filtrado en vivo, el toggle de contraseña, el
carrito, el checkout, etc. son vanilla JS. Autocompletado = `<datalist>` nativo.

---

## 4. Reglas / convenciones del código

- **CSRF**: todo `<form method="post">` del navegador lleva `{{ campo_csrf() }}`.
  `app.py` valida el token en `before_request` para POST/PUT/PATCH/DELETE con
  content-type de formulario. Las APIs JSON (`/api/*`, JWT) están exentas.
- **Jinja**: nunca uses la clave `items` en un dict que va a una plantilla
  (choca con `dict.items`). Usa `lineas`, `detalle`, etc.
- **Contraseña — UNA regla en todo el proyecto**: mínimo **8 caracteres, con al
  menos una MAYÚSCULA y un NÚMERO**. Valídala con `seguridad.password_valida(pw)`
  (devuelve `None` o el texto del error). En plantillas: `{{ REGLA_PASSWORD }}`
  y `pattern="{{ PASSWORD_PATTERN }}"` (globals de Jinja). El login solo compara
  el hash — la regla se exige al **crear o cambiar** la contraseña.
- **Entradas del checkout**: el `carrito_json` viene del `localStorage` (no es de
  fiar). `controllers.cliente._leer_carrito()` lo sanea (lista de dicts, `int()`
  tolerante, cremas deduplicadas y solo de la categoría 'Cremas'). Nunca conviertas
  directo lo que llega del cliente.
- **CRUD de productos/categorías**: `Producto.insertar_producto` /
  `actualizar_producto` / `CategoriaProducto.insertar_categoria` /
  `actualizar_categoria` devuelven `None` (ok) o **texto de error** — el
  controlador lo pasa al flash. No lanzan excepciones ante datos malos
  (precio negativo/texto, categoría inexistente, nombre vacío).
- **Pedidos solo de usuarios registrados.** `/carrito` y `/compra` exigen
  `session["cliente.auth"]`; si no hay, redirigen a `/login?next=…`. El detalle
  de producto muestra "Inicia sesión para pedir" en vez del botón de agregar.
- **Estado / "dar de baja"** (no se borra): `usuario.activo`, `producto.activo`,
  `categoriaProducto.activo`. La tienda solo muestra lo activo
  (`obtener_productos(solo_activos=True)`, `obtener_categorias(solo_activas=True)`,
  `precios_por_ids` bloquea inactivos). Un `usuario.activo = 0` no inicia sesión.
- **Roles** (`usuario.rol`): `superusuario` | `administrador` | `usuario`.
  `tipoUsuario` se mantiene sincronizado (0 = panel, 1 = cliente) por compat.
  - Solo el **superusuario** entra a `/admin/usuarios/*` y asigna roles.
  - Desde Gestión de usuarios **solo se puede cambiar el ROL y dar de baja** una
    cuenta (`Usuario.cambiar_rol`, `Usuario.cambiar_estado`). El correo / teléfono
    / contraseña los edita **cada persona** en `/mi-cuenta` o `/admin/perfil`.
  - Un superusuario **no puede cambiarle el rol ni dar de baja a otro
    superusuario** — solo crear uno nuevo. No puede darse de baja a sí mismo.
- **Estados del pedido** (`registroPedido.estadoPrep`): 0 recibido → 1 en
  preparación → 2 listo. El cliente **solo puede cancelar mientras está
  "recibido"**. `model.Pedido.estado_pedido(recogido, cancelado, no_show, prep)`
  centraliza el estado canónico.
- **Auto no-show** (`Pedido._auto_no_show`): marca "no recogió" solo si el pedido
  estaba **listo** (`estadoPrep = 2`) y pasaron 45 min de la hora de recojo.
  Se salta con `MUSAS_DEMO=1`.
- **Comprobante**: se emite en `Pedido.marcar_recogido` (al entregar). Número
  `B001-000000NN` si pidió boleta, `NV01-...` si no.
- **Búsqueda en vivo**: `static/js/ui-comun.js`. Un `<input data-filtro-vivo="#scope">`
  oculta los `[data-filtro-item]` dentro de `#scope` conforme se teclea
  (sin Enter). Opcional `[data-filtro-seccion]` y `[data-filtro-vacio]`.
  El `<form method=get>` con `?q=` queda de respaldo para páginas paginadas.
- **Imágenes**: `subidas.guardar_imagen(archivo, subcarpeta)` (archivo subido) o
  `subidas.guardar_desde_url(url, subcarpeta)` (enlace de internet — valida
  esquema, bloquea IPs privadas/SSRF, 5 MB, `Image.verify()` de Pillow). Se
  guardan en `static/img/<subcarpeta>/` (gitignored) y la BD guarda la ruta
  relativa (`"productos/ab12.jpg"`).
- **Carrito**: 100% en `localStorage` del navegador (clave `musas_carrito`,
  API `window.MusasCarrito`). El servidor **re-cotiza todo contra la BD** al
  hacer checkout (`Producto.precios_por_ids`) — nunca confía en los precios del
  cliente. Al cerrar sesión se limpia el carrito.
- **keyPedido / idPedido / idDetalleOrden** los asigna la app (`MAX(...)+1`), no
  son AUTO_INCREMENT.

---

## 5. Base de datos (resumen)

`db_musuas`, InnoDB, utf8mb4. 8 tablas (todos los cambios de `migrations/001..010`
ya están en `sql.sql`):

| Tabla | Rol |
|---|---|
| `usuario` | cuentas. `rol`, `activo`, `tipoUsuario` (0 panel / 1 cliente), `noShows` |
| `categoriaProducto` | secciones de la carta. `activo`. "Cremas" no se muestra en la carta pública |
| `producto` | ítems de la carta + las cremas (según `idCategoria`). `activo`, `imagen`, `destacado`, `nota`, `precio FLOAT`, `existencias` |
| `registroPedido` | cabecera del pedido. `estadoRecojo`, `cancelado`, `noShow`, `estadoPrep`, `keyPedido`, `billeteraDigital`, `estadoBoleta`, datos de quien recoge |
| `detalleOrden` | líneas del pedido (snapshot de nombre/precio) |
| `detalleCremas` | cremas elegidas por línea |
| `comprobante` / `detalleComprobante` | venta emitida al entregar. `dniNoRegistrado CHAR(8)` |

- FK: `producto→categoriaProducto`, `registroPedido→usuario` (nullable),
  `detalleOrden→(producto, registroPedido)`, `detalleCremas→(producto, detalleOrden)`,
  `comprobante→(registroPedido, usuario)`, `detalleComprobante→(comprobante, producto)`.
- IGV 18% incluido en el precio: `subTotal = total/1.18`, `igv = total - subTotal`.
- MySQL en Windows es case-insensitive con los nombres de tabla; el código usa
  camelCase (`categoriaProducto`), la BD los guarda en minúscula. Funciona igual.

---

## 6. División del trabajo (para el merge — ver `MERGE_NOTES.md`)

- **Ramirez (rama `Ramirez`, la más completa):** tienda completa, login/registro,
  CRUD de pedidos + dashboard, infra (diseño, seguridad/CSRF, migraciones,
  roles, estados, perfil), y **la integración del panel** (productos / categorías
  / usuarios / ventas / comprobantes) sobre este diseño y este esquema.
- **Compañero (rama `Manuelf`):** hizo en paralelo su propia versión del panel +
  tienda + auth. **No se hizo `git merge`** porque los esquemas chocaban
  (`keyPedido` numérico vs texto, `precio` FLOAT vs DECIMAL, otra auth, sin
  no-show). Se decidió: **la base es `Ramirez`** y se portó la lógica del panel.

**Trabaja siempre sobre la rama `Ramirez`** (o una rama tuya a partir de ella).
Nunca commitees directo a `main`. La entrega es un solo PR `Ramirez → main` que
revisa el asesor.

---

## 7. Estado actual (qué ya funciona)

Todo esto está hecho y probado E2E en `Ramirez`:

- **Tienda**: inicio (landing), carta (con búsqueda en vivo + orden), listado por
  categoría, detalle de producto + cremas, carrito, checkout con franjas de
  recojo y cupo, confirmación con palabra clave, "mis pedidos" (historial +
  repetir + cancelar), "mi cuenta" (editar datos propios).
- **Login unificado**: una puerta, DNI + contraseña; si el DNI es de panel además
  pide captcha y va a `/admin`; si es cliente va a la tienda. Throttle anti
  fuerza-bruta en memoria. Cuenta dada de baja no entra.
- **Panel**: dashboard con KPIs y gráfico; CRUD de pedidos con estados
  (recibido / en cocina / listo / recogido) + confirmar con clave + no-show +
  cancelar; CRUD de productos y categorías (panel/modal, imagen archivo o URL,
  previsualización, dar de baja); CRUD de usuarios con 3 roles (solo
  superusuario); Ventas (KPIs, gráfico de barras, lista de comprobantes,
  detalle tipo boleta con importe en letras); Mi perfil.
- **Seguridad**: CSRF propio en todos los formularios, cabeceras
  (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`), cookies
  `HttpOnly` + `SameSite=Lax` + `Secure` en producción, `FLASK_DEBUG` desde env.
- **Responsive**: navegación inferior en móvil, sin desbordes horizontales.

### Cosas conocidas / pendientes
- `usuario.dni` no tiene constraint `UNIQUE` (el código lo valida en la app).
- `flask-jwt 0.3.2` es viejo; hay APIs `/api/*` heredadas con JWT que la tienda
  y el panel **no usan** (el checkout es server-rendered). No las borres sin
  revisar `app.py`.
- `model/Transaccion.py` existe (era el checkout-por-API del compañero) pero
  la tienda de esta rama **no lo usa**.
- El detalle de comprobante lee `registroPedido` por nombre de columna (no por
  índice) — está bien tras las migraciones 004/006/009.

---

## 8. Migraciones (histórico — ya están todas en `sql.sql`)

Si alguien tiene una BD vieja, se aplican en orden. En una BD nueva **no hace
falta**: `sql.sql` ya las incluye.

| # | Qué hace |
|---|---|
| 001 | `usuario.contraseña` a `VARCHAR(255)` (hash) |
| 002 | `producto.imagen`, `producto.destacado` |
| 003 | `producto.nota` |
| 004 | `registroPedido.nombres`, `registroPedido.notas` |
| 005 | `producto.precio`/`existencias` NOT NULL DEFAULT 0 |
| 006 | `registroPedido.cancelado`/`noShow`, `usuario.noShows` |
| 007 | `categoriaProducto.imagen` |
| 008 | `comprobante.dniNoRegistrado` a `CHAR(8)` |
| 009 | `registroPedido.estadoPrep` (0/1/2) |
| 010 | `usuario.rol`/`activo`, `producto.activo`, `categoriaProducto.activo` |
