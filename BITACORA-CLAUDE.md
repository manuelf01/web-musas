# Bitácora del proyecto — web-musas (Las Musas)

> Archivo de memoria de trabajo. Se actualiza cada vez que se cambia algo, se
> rompe algo, o se detecta código redundante. **Última actualización: 2026-09-06.**
> Rama de trabajo: `Ramirez` (nunca tocar `main` directamente).

---

## 1. Estado del entorno (local)

| Cosa | Estado | Detalle |
|---|---|---|
| Python | ✅ 3.10.11 | Instalado con `winget install Python.Python.3.10 --source winget`. El origen `msstore` de winget tiene un **certificado roto** en este equipo → siempre usar `--source winget`. Sigue existiendo Python 3.13 en el sistema; el proyecto usa el 3.10 del `.venv`. |
| `.venv` | ✅ | Creado con `py -3.10 -m venv .venv`. |
| Dependencias | ✅ | Flask 2.2.3, Werkzeug 2.2.3, pymysql 1.2.0, cryptography, Flask-JWT 0.3.2, flask-swagger-ui, flask-paginate. |
| `pip` | ⚠️ | Este equipo **intercepta SSL** (antivirus/proxy) → `pip install` falla con `CERTIFICATE_VERIFY_FAILED`. Workaround: `pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.python.org ...` |
| `cfg.py` | ✅ (no versionado) | Está en `.gitignore`. Contenido: `host='localhost' port=3306 db='db_musuas' username='root' password=''`. |
| XAMPP | ✅ 8.2 | `C:\xampp`. Trae **MariaDB 10.4.32**. Descargado manualmente por el usuario (winget se colgaba con SourceForge). |
| Base `db_musuas` | ✅ creada | UTF-8 (`utf8mb4`). Importado `sql.sql` → 8 tablas. **La BD NO tiene datos** (tabla `usuario` vacía → no se puede iniciar sesión hasta insertar un usuario). |
| App | ✅ corre | `python app.py` → http://127.0.0.1:5000 (probado: `/` 200, `/admin/` 200, `/api/docs` OK). Requiere MySQL encendido. |

### Cómo levantar el proyecto
1. XAMPP Control Panel → **Start** en MySQL.
2. `cd "C:\Users\JUAN RAMIREZ\Desktop\web-musas"` → `.\.venv\Scripts\activate` → `python app.py`

> Nota: en una sesión anterior se dejó un `mysqld.exe` corriendo en segundo plano
> que ya fue detenido. Usar siempre el panel de XAMPP para arrancar MySQL.

---

## 2. Cambios hechos hasta ahora

| Fecha | Cambio | Reversible |
|---|---|---|
| 2026-09-05 | Clonado el repo `manuelf01/web-musas` en `Desktop/web-musas`. | — |
| 2026-09-05 | Creada y publicada la rama `Ramirez` desde `main` (sin cambios de código). | `git push origin --delete Ramirez` |
| 2026-09-05 | Creado `cfg.py` local (no versionado). | Borrar archivo |
| 2026-09-06 | Creado este `BITACORA-CLAUDE.md`. | Borrar archivo |
| 2026-09-06 | **Login + registro rediseñados (Neo-brasa), fieles a las plantillas de Stitch.** Ver detalle abajo. Controladores **sin tocar** (se respetan rutas y `name` de campos). | `git checkout` de los archivos |
| 2026-09-06 | Añadidos `requirements.txt` (`pip freeze`) y `cfg.example.py`. | Borrar archivos |
| 2026-09-06 | **Datos de prueba** en `db_musuas.usuario`: admin DNI `12345678` / `admin123` (tipoUsuario 0), cliente DNI `87654321` / `cliente123` (tipoUsuario 1). | `DELETE FROM usuario WHERE dni IN ('12345678','87654321');` |

### Archivos del login/registro (2026-09-06, 2ª iteración — fieles a Stitch)
| Archivo | Qué es |
|---|---|
| `static/css/musas-theme.css` | **Sistema de diseño base de Dev 1.** Tokens Neo-brasa + capa Bootstrap 5: navbar, footer, `.btn-brasa`, `.musa-input` (+ variante con ícono), `.musa-card`, badges, `.auth-split`, medidor de contraseña. CSS puro (sin build). |
| `templates/client/base.html` | **NUEVO. Layout base de la tienda.** `<head>` (fuentes + Bootstrap 5.2.3 + bootstrap-icons + tema), **navbar superior real** (wordmark, Inicio/Carta/Mis pedidos, pill de carrito, Iniciar sesión/usuario), **footer de 4 columnas**, bloques `{% block content/head/scripts %}`. Incluye el `bootstrap.bundle.js` (antes estaba comentado). |
| `templates/client/login.html` | Reescrito. `extends client/base.html`. Split-screen: hero izquierdo "Pasión, Fuego & Sazón" + pill de local, formulario derecho con eyebrow "Área clientes", DNI + contraseña (ícono + ver/ocultar), "Recordar sesión", link a registro. |
| `templates/client/registro.html` | Reescrito. `extends client/base.html`. Split-screen con grid de beneficios; tarjeta con DNI, Nombres/Apellidos (2 col), Correo/Teléfono (+51) (2 col), Contraseña con **medidor de fuerza**, checkbox T&C. `name` de campos: `dni, nombres, apellidos, correo, telefono, contraseña` (lo que espera el controlador). |
| `templates/admin/login.html` | Reescrito. **Standalone** (sin navbar), split a pantalla completa. Izquierda carbón con textura de puntos + badge "SISTEMA PRIVADO" + "Módulo de control" + grid "Sede activa / Acceso". Derecha: tarjeta 380px con ícono, "Sesiones auditadas por IP", footer. **Sin captcha.** |

### Estado (probado 2026-09-06)
- `GET /login`, `GET /registro` (y `/formulario_registro_cliente`), `GET /admin/` → 200 con el diseño nuevo.
- `POST /login` `87654321`/`cliente123` → redirige a `/`. Credenciales malas → vuelve a `/login` con alerta. `POST /admin/login` `12345678`/`admin123` → `/admin/`.
- `POST /registro` con los 6 campos → crea el usuario (tipoUsuario 1) y muestra el login.
- ⚠️ La página de login admin se sirve en **`/admin/`**, NO en `/admin/login` (ruteo actual del proyecto).
- El login compara la contraseña **en texto plano** (P3) — sin cambios, pendiente.
- No hay constraint UNIQUE en `usuario.dni` — se permite el mismo DNI con distinto `tipoUsuario`.

### Login UNIFICADO + captcha + hash (2026-09-06, 3ª iteración)
Decisión del usuario: **una sola puerta de login**. El sistema mira `tipoUsuario`:
- DNI de **cliente** → entra directo a la tienda.
- DNI de **admin** → aparece un **captcha de imagen** (Pillow) y va a `/admin`.

| Archivo | Cambio |
|---|---|
| `seguridad.py` | **NUEVO.** Genera el texto y la imagen PNG del captcha (Pillow). |
| `migrations/001_ampliar_contrasena.sql` | **NUEVO + APLICADO.** `usuario.contraseña` pasó de `VARCHAR(100)` → `VARCHAR(255)` (el hash pbkdf2 mide ~102 y se truncaba → login siempre fallaba). |
| `controllers/autenticacion.py` | Reescrito. `/login` unificado con validación server-side (regex DNI/tel/correo, `request.form.get`). Nuevas rutas `GET /login/captcha` (PNG, guarda respuesta en `session['captcha_login']`) y `GET /login/tipo-dni?dni=` (JSON `{admin: bool}`). Flash con categorías (`ok`/`error`). `/registro` con validación completa + flash de éxito. `/admin/login` y `/admin/logout` redirigen al login unificado. |
| `controllers/admin.py` | `home()` sin sesión → `redirect` al login unificado (antes renderizaba `admin/login.html`). `before_request` ahora **bloquea** todo `/admin/*` si no hay sesión admin (antes solo seteaba `g.user`). |
| `model/Autenticacion.py` | `verificar_password()` (usa `check_password_hash`, con fallback a texto plano para datos viejos). `login_unificado(dni, pass)` → `(fila, 'admin'|'cliente')` o string de error. `dni_es_admin(dni)`. El `login()` clásico ahora también usa hash. |
| `model/Usuario.py` | `insertar_usuario` hace `generate_password_hash`. `actualizar_usuario`: arregladas las comparaciones `is ""` → `== ""` (P2 resuelto) y hashea la contraseña nueva si se envía. |
| `Token/usuario.py` | `authenticate` (JWT) usa `Autenticacion.verificar_password`. |
| `templates/client/login.html` | Bloque de captcha oculto; JS consulta `/login/tipo-dni` al escribir el DNI (8 díg.) y lo muestra solo si es admin. Flash con categorías. |
| `templates/admin/login.html` | **BORRADO** (ya no hay login admin separado). |
| `requirements.txt` | + `pillow==12.3.0`. |

**Datos de prueba** (con hash `pbkdf2:sha256`), estado actual de `usuario`:
| DNI | Contraseña | Tipo |
|---|---|---|
| `12345678` | `admin123` | Admin |
| `87654321` | `hola1` | Admin |
| `12345679` | `hola1` | Cliente |

Notas: el usuario pidió cliente con DNI `123456789` — son 9 dígitos y `usuario.dni` es `char(8)` (DNI peruano = 8), se usó `12345679`. `hola1` (5 chars) sirve para login pero **no se puede crear desde el formulario de registro** (exige ≥ 8).

**Probado E2E (2026-09-06):** cliente login→`/`; admin sin captcha→rechazado; admin + captcha correcto (case-insensitive)→`/admin/` con sesión; captcha malo→rechazado; `/admin/*` sin sesión→redirige al login; registro válido→crea cliente + flash; registro inválido→flash de error.

**P3 (contraseña en texto plano) → RESUELTO.** Queda el fallback en `verificar_password` para cuentas viejas; recrear cualquier usuario hecho antes de hoy.

### Consideraciones de seguridad anotadas
- `/login/tipo-dni` revela si un DNI es de un admin (necesario para el flujo que pidió el usuario). Para producción: rate-limit o quitar el endpoint y mostrar el captcha siempre.
- No hay constraint UNIQUE en `usuario.dni`. `login_unificado` ordena por `tipoUsuario ASC` (admin gana si el DNI existe en ambos).
- El captcha se valida case-insensitive y se consume (un solo uso).
- Aplicar migraciones con ñ vía `pymysql` o `mysql --default-character-set=utf8mb4` (el pipe `mysql < archivo.sql` en Windows manga la ñ del nombre de columna).

### Ajustes login/registro (2026-09-06, 4ª iteración)
- **Términos y Condiciones + Política de Privacidad**: `templates/client/_legal_modales.html` (NUEVO) — 2 modales de Bootstrap, incluidos desde `client/base.html`. Se abren desde el checkbox del registro y desde el footer. Contenido real (retiro en tienda, IGV, Ley N° 29571, Ley N° 29733 de datos personales).
- **Registro → "Volver"**: el link ahora apunta a `cliente.auth.login` (antes iba a `cliente.home`). Texto: "Volver a iniciar sesión".
- **"Recordar sesión en este equipo"** ahora funciona: `controllers/autenticacion.py` hace `session.permanent = bool(request.form.get("recordar"))`; `app.py` define `app.permanent_session_lifetime = timedelta(days=30)`. Marcado → cookie de 30 días (`Set-Cookie` con `Expires`). Sin marcar → cookie de sesión (se borra al cerrar el navegador).

### Admin · Gestión de pedidos + confirmar recojo (2026-09-07)
- `templates/admin/pedidos/index.html` **reescrito**, `extends admin/base.html` (antes `main.html` viejo).
- Fiel al Stitch `las_musas_gesti_n_de_pedidos`: header con contador de pendientes, **chips de filtro** (Todos/Pendientes/Recogidos via `?estado=`), grilla 2-col de tarjetas. Pendiente = borde ember; Recogido = borde verde + atenuada.
- Cada tarjeta: avatar/iniciales, cliente + `#idPedido`, DNI enmascarado + teléfono, chip "Recojo HH:MM" (mostaza), líneas (miniatura, nombre, precio, `xN`, `S/ x c/u`, chips de cremas), notas de cocina si hay, footer con Total + método de pago + (si pendiente) **input de 4 dígitos "0000" + botón "Marcar recogido"**; si recogido → "Entregado · Key N".
- **Confirmar recojo**: `POST /admin/pedidos/confirmar` → `Pedido.marcar_recogido(idPedido, key)` que devuelve `'ok' | 'clave_mal' | 'no_existe'`. Chequeo atómico (`WHERE idPedido = %s AND estadoRecojo = 0`), evita doble confirmación. Flash con el resultado. **Sin JWT ni JS** (el `pedidos.js` viejo dependía de `config.js` roto).
- Modelo: `Pedido.pedidos_de_hoy(estado)`, `Pedido.marcar_recogido(id, key)`, `Pedido.contadores_hoy()`.
- Probado: clave mala → flash "no coincide"; clave buena → estado a recogido + flash; reintento → "ya recogido".

**2ª pasada — legibilidad para muchos pedidos (2026-09-07):**
- Ancho del contenido admin capado a **1240px** (antes se estiraba a 1400+).
- Grilla `auto-fill minmax(330px)` → 2–3 columnas según pantalla.
- **Default = "Por entregar"** (no "Todos"). Filtros: Por entregar / Recogidos / Todos.
- **Buscador** client-side (cliente / DNI / N° pedido) — filtra tarjetas y filas.
- **Recogidos** ya NO son tarjetas grandes: **tabla compacta** (Pedido, Cliente, Hora, Detalle, Total, Clave). Solo historial, sin acciones.
- El bloque de confirmación quedó **explícito**: label "Palabra clave del cliente" + texto "Pídele su número de 4 dígitos y escríbelo para entregar el pedido" + input grande + botón "Entregar pedido".
- Pendientes ordenados por `horaRecojo` (`Pedido.pedidos_de_hoy` → `ORDER BY estadoRecojo, horaRecojo`).

### Dashboard admin (2026-09-07)
- `templates/admin/base.html` **NUEVO** — layout del backoffice: sidebar carbón (wordmark, nav Resumen/Pedidos/Productos/Categorías/Usuarios/Ventas, estado "Abierto", usuario + logout), topbar, `{% block content %}`. Es la base de TODAS las páginas admin (las demás — pedidos/productos/etc. — **aún usan `admin/main.html` viejo**, migrar después).
- `templates/admin/dashboard.html` (`admin.home` → ya no `main.html`): "Resumen · En vivo" + botón "Nuevo producto"; **4 KPIs** (pedidos hoy, pendientes de recojo, ventas hoy, ticket promedio); **Pedidos recientes** (avatar, DNI enmascarado, detalle, hora, total, estado); **Top productos 7 días** (con barra); **gráfico de barras Ventas 7 días** (CSS puro, sin librería).
- `Pedido.resumen_dashboard()` — todo en una llamada. Métricas basadas en `registroPedido` + `detalleOrden` (NO en `comprobante`, que puede estar vacío). MariaDB `CURDATE() - INTERVAL n DAY`.
- **Bug repetido**: en el dict de "recientes" la clave `items` chocaba con `dict.items` en Jinja → mostraba `<built-in method...>`. Renombrada a `detalle`. (Ya pasó con `pedido.lineas`; **regla: nunca una clave `items` en dicts que van a Jinja**.)
- Hay **datos de prueba** sembrados en `db_musuas` (pedidos de hoy y de días anteriores) para que el dashboard/pedidos/ventas muestren algo. Borrar con `DELETE FROM detalleCremas; DELETE FROM detalleOrden; DELETE FROM registroPedido;` cuando estorben.

### Mis pedidos (historial + repetir) (2026-09-07)
- Nav "Mis pedidos" ahora → `/mis-pedidos` (`cliente.mis_pedidos`, `templates/client/mis-pedidos.html`, `static/js/mis-pedidos.js`).
- **Sin sesión** → tarjeta "Inicia sesión para ver tu historial". **Con sesión, sin pedidos** → estado vacío. **Con pedidos** → filtros (Todos / Pendientes / Recogidos) + tarjetas.
- Cada tarjeta: N° pedido, fecha · hora, chip estado (Pendiente brasa / Recogido verde), líneas (cantidad × nombre + cremas), Total.
- **Ver palabra clave** (solo pendientes) → modal con el `keyPedido`.
- **Repetir pedido** → el botón lleva un `data-repetir` con los ítems armados con **precios/nombres/imágenes ACTUALES** de la BD (no el snapshot); JS hace `MusasCarrito.guardar(...)` y va a `/carrito`. Ítems cuyo producto ya no existe se marcan "(ya no está en carta)" y se excluyen del repetir.
- `Pedido.historial_cliente(idUsuario)` → cabeceras + `detalleOrden` + `detalleCremas` con `LEFT JOIN producto` (datos actuales). Clave del dict de líneas: `lineas` (NO `items`).
- Confirmación de pedido: botón "Ver mis pedidos" ahora enlaza de verdad.

### Checkout — datos precargados + franjas de recojo con cupo (2026-09-07)
- **Cliente logueado**: el checkout precarga **DNI / Nombres / Apellidos / Teléfono** con `session["cliente.auth"]` (`sesion.dni` etc.), **editables** (puede recoger otra persona). El controlador ahora siempre lee del form; `idUsuario` sale de la sesión si existe.
- **Franjas de recojo con cupo** (`model/Pedido.py`):
  - Constantes: `HORA_APERTURA=18`, `HORA_CIERRE=22`, `FRANJA_MINUTOS=30`, `CUPO_POR_FRANJA=8`, `ANTICIPACION_MIN=20`.
  - `Pedido.franjas_recojo()` → lista de 8 franjas del día con `disponible`, `restantes`, `motivo` ('llena' si ya hay 8 pedidos con esa `horaRecojo` hoy, 'pasada' si la franja es antes de `ahora + 20 min`).
  - `Pedido.franja_disponible(hora)` → re-chequea en el POST (una franja puede llenarse entre que cargas la página y confirmas).
  - Checkout: chips de franja (la primera libre pre-seleccionada = "Antes posible"), las llenas/pasadas salen rayadas y `disabled`. Hidden `hora_recojo`. Si no hay ninguna libre → aviso "cocina llena o fuera de horario".
  - POST valida la franja server-side → si se llenó: flash "Esa franja se llenó, elige otra".
  - Probado: llené 20:00 con 8 pedidos → la franja pasa a `disponible=False, motivo='llena'` y el POST la rechaza.

### Carrito + Checkout + Confirmación (2026-09-07)
**Carrito** (`templates/client/carrito.html`, `static/js/carrito-pagina.js`): renderizado 100% desde `localStorage` (`musas_carrito`). Líneas con miniatura, chips de cremas, stepper (± actualiza y re-guarda), quitar, "vaciar todo". Resumen: Subtotal neto (`total/1.18`), IGV (18% incluido), Total. Estado vacío. **Quitado del Stitch**: barra de envío gratis, cupón, "añadir antojo", "simulador de estado".

**Checkout** (`templates/client/compra.html`, `static/js/checkout.js`, ruta `/compra` GET+POST): 2 columnas.
- Izq: "Datos de quien recoge" (si hay sesión → datos bloqueados de la cuenta; si invitado → DNI/Nombres/Apellidos/Teléfono). Hora de recojo: chips ("Lo antes posible" = ahora+30min, 8:30/9:00/9:30) + `<input type=time>` que se sincronizan. "Comprobante y forma de pago": checkbox boleta, radios "Billetera digital (Yape/Plin)" / "Pagar al recoger", textarea notas.
- Der (sticky): resumen del pedido desde localStorage + Subtotal/IGV/Total + "Confirmar pedido — S/ X".
- **Quitado del Stitch**: factura RUC, cupón NOCHEBRASA, QR dinámico WhatsApp, "Musas Club".
- El form manda `carrito_json` (hidden, serializado por JS). El servidor **re-cotiza todo contra la BD** (`Producto.precios_por_ids`) — no confía en los precios del cliente.

**Confirmación** (`templates/client/pedido-confirmado.html`, ruta `/pedido-confirmado/<id>`): **PALABRA CLAVE gigante** (`keyPedido`), N° de pedido, hora de recojo, local, instrucción de pago según método, nota de boleta, detalle plegable, botones. Un `<script>` vacía el carrito local al cargar.

**Modelo (`model/Pedido.py`):**
- `crear_pedido_completo(idUsuario, dni, nombres, telefono, hora, boleta, digital, notas, items)` → inserta `registroPedido` + `detalleOrden` (1 por línea, con `nombreProducto`/`precioUnidad`/`precioTotal` snapshot) + `detalleCremas`, en **una transacción**. Genera `keyPedido` de 4 dígitos único entre pedidos no recogidos. Devuelve `(idPedido, keyPedido)`.
- `obtener_pedido_completo(id)` → dict con `lineas` (ojo: NO `items`, choca con `dict.items` en Jinja), cremas por línea, total.
- `Producto.precios_por_ids(ids)`.

**Migración 004** (`registroPedido.nombres` + `.notas`) — **APLICADA**. `nombres` estaba implícito en `Pedido.diccionario_pedidos` (indexaba como si existiera) → sin ella `Pedido.get_pedidos()` **reventaba** en `keyPedido`. Ahora arreglado; el admin de Pedidos ya puede leer.

**Probado E2E**: cliente vacío → agregar producto+cremas en detalle → `/carrito` muestra líneas y totales → `/compra` → POST crea pedido (re-cotizado) → `/pedido-confirmado/N` con la clave. Validaciones (DNI 8, tel 9, hora HH:MM, carrito no vacío) → flash. Server-side pricing verificado (total S/ 52 = 24×2 + cremas×2).

### Detalle de producto + elegir cremas (2026-09-07)
`templates/client/seleccion-producto.html` **reescrito**, `extends client/base.html`. Fiel al Stitch `las_musas_detalle_de_producto`:
- Breadcrumb Inicio / {categoría} / {producto}.
- Columna izquierda: foto grande + flag `destacado` + 3 badges de calidad (genéricos) + nota "El secreto de la casa" (genérica).
- Columna derecha: eyebrow (categoría), pill "Disponible ahora / Agotado" (según `existencias`), título, precio base, descripción.
- Card "Personaliza tu pedido · Opcional": grilla de **cremas reales** (`getProductosCategoria("Cremas")`), cada una con imagen redonda + nombre + `+ S/ x.xx` + checkbox. El `<label>` se resalta con `:has(:checked)`.
- Stepper de cantidad + botón "Agregar al carrito — S/ x.xx" con **total en vivo** (base + cremas) × cantidad. Barra flotante en móvil.
- **Omitido** del Stitch: "Término de la carne" (no está en `detalleOrden`), galería de miniaturas (1 sola imagen por producto), "Maduración 21 días", allergens.

**Carrito nuevo (localStorage) — reemplaza el flujo roto anterior:**
- ⚠️ `static/js/config.js` **NO existe** en el repo (está en `.gitignore`). Todos los JS viejos que hacen `import ... from "./config.js"` (`guardarProductos.js`, `mostrarProductos*.js`, `fetchApis.js`, `comprarProductos.js`) están **rotos** en un clon limpio.
- Nuevo `static/js/carrito.js` (sin imports, se carga en `base.html`): API `window.MusasCarrito` (leer/guardar/agregar/vaciar/total/cantidadTotal) + actualiza el pill del navbar (`[data-carrito-count]`, `[data-carrito-total]`).
- Clave localStorage: **`musas_carrito`** = array de `{ idProducto, nombre, precio, imagen, cantidad, cremas:[{idProducto,nombre,precio}] }`. Subtotal de línea = (precio + Σ cremas) × cantidad.
- Nuevo `static/js/detalle-producto.js`: stepper, total en vivo, "Agregar" → `MusasCarrito.agregar(...)` → redirige a `/carrito`.
- El "Agregar al carrito" ya **NO** usa JWT ni la API `/get_producto` — toda la data sale de `data-*` en la página.

**Modelo:** `Producto.obtener_producto_por_id` ahora devuelve `imagen`, `destacado`, `nota`.

⚠️ **PENDIENTE INMEDIATO**: `templates/client/carrito.html` sigue con el diseño viejo y `mostrarProductos.js` (roto). Tras "Agregar al carrito" el ítem SE GUARDA (el pill del navbar lo cuenta) pero la página `/carrito` todavía no lo muestra. Es la siguiente tarea.

### Carta completa + páginas de info + fix (2026-09-07)
- **"Carta" del navbar** antes iba a la home. Ahora → nueva ruta **`/carta`** (`cliente.carta` + `templates/client/carta.html`): menú completo, todas las categorías con **todos** sus productos (reusa `_catbar` + `_producto_card`). El navbar marca "Carta" activa (bloque `nav_carta` en `base.html`).
- **`/nosotros`** (`templates/client/nosotros.html`): secciones Historia, Locales y horarios (2 tarjetas), Sostenibilidad, **FAQ** (acordeón `<details>`), y bloque Libro de Reclamaciones. Anclas `#historia #locales #sostenibilidad #faq`.
- **`/libro-de-reclamaciones`** (`templates/client/reclamaciones.html`): aviso legal (Ley 29571) + formulario (nombres, DNI, correo, teléfono, tipo, N° pedido, detalle, petición). POST valida y hace `flash` de confirmación — **NO persiste** (no hay tabla; es informativo para la tesis, así lo dice la propia página).
- **Footer** (`base.html`): los links ahora funcionan → Historia/Locales/Sostenibilidad a `/nosotros#…`, Preguntas frecuentes a `/nosotros#faq`, Libro de Reclamaciones a `/libro-de-reclamaciones`.
- CSS: bloque "PÁGINAS DE CONTENIDO" en `musas-theme.css`.

**BUG corregido** (lo introduje con las migraciones 002/003): `Producto.obtener_productos()` y `obtener_productos_paginacion()` leían `producto[6]` como `nombreCategoria`, pero al agregar `imagen`/`destacado`/`nota` esa posición pasó a ser `imagen`. En el admin la columna "Categoría" mostraba el nombre del archivo de imagen. Ahora usan lista de columnas explícita + helper `Producto._fila_a_dict`.

### Carta / listado de categoría (2026-09-06)
`templates/client/productos.html` **reescrito**, `extends client/base.html`. Fiel al Stitch `las_musas_listado_de_categor_a`:
- Barra de categorías pegajosa (chip de la categoría actual activo) + badge "Recojo en".
- Breadcrumb "Carta / {categoría}".
- Encabezado: `<h1>` + conteo "N productos" + **select "Ordenar por"** (Recomendados / Menor precio / Mayor precio / Nombre A–Z) — `<form method=get>` que se envía `onchange`, el orden lo hace el controlador con `request.args.get('orden')`.
- Grid de tarjetas (mismo componente que la home).
- **Estado vacío**: tarjeta centrada con ícono + "No hay productos en esta categoría" + "Volver a la carta" (se muestra solo si la categoría no tiene productos).
- Franja de garantías.
- **Se omitió** el toggle "Vista con productos / Estado Vacío" del Stitch — es un demo para previsualizar, no tiene sentido en producción.

**Refactor**: se crearon 2 parciales reutilizados por home y carta:
- `templates/client/_producto_card.html` — la tarjeta de producto (espera `p`).
- `templates/client/_catbar.html` — la barra de categorías (espera `categorias`, `modo` "anclas"|"links", `activa`).

**Modelo/controlador:**
- `Producto.getProductosCategoria` ahora devuelve `idCategoria`, `imagen`, `destacado`, `nota` (antes solo id/nombre/desc/precio/existencias). Query pasó a `SELECT p.*` con `ORDER BY`.
- `cliente.productos_categoria` acepta `?orden=` (recomendados | precio-asc | precio-desc | nombre) y pasa `orden` a la plantilla.

### Home — 2ª pasada (más fiel al Stitch, 2026-09-06)
Faltaban elementos del `code.html`. Agregados:
- **Banda de promo** ("Promo nocturna · 2x1 Cervezas de Barril" + botón "Aprovechar promo") tras la 1ª categoría. Es contenido **estático** (no hay sistema de promos en la BD).
- **Etiqueta corta junto al precio** en cada tarjeta ("Brasas", "Smash 120g", "Papa Amarilla"…) → `migrations/003_producto_nota.sql` (NUEVO + aplicado): `producto.nota VARCHAR(40)`.
- **Badges con color** según el texto: mostaza (default), verde menta ("Nueva"), durazno ("Especial de la casa"/"Para compartir").
- **"Ver más (N)"** con el total real de la categoría → `Producto.contar_por_categoria()`, el controlador pasa `totales`.
- Badge de ubicación **"Recojo en: Miraflores, Lima"** a la derecha de la barra de chips.
- Tarjetas con altura pareja: bloque `.producto-card__foot` con `margin-top:auto` (botones alineados).

### Home / página de inicio (2026-09-06, 5ª iteración)
- `templates/client/index.html` **reescrito**, ahora `extends client/base.html` (ya no `main.html`). Estructura fiel al Stitch desktop: hero full-width oscuro + pill "Abierto ahora", barra de categorías **pegajosa** (chips, excluye "Cremas"), una sección por categoría (eyebrow + título + descripción + "Ver todo" → página de categoría) con grid de **4 tarjetas** de producto (imagen 4:3, badge `destacado`, precio `S/ 0.00`, botón "Comprar" → `cliente.comprar_producto`), franja de 3 garantías, estado vacío.
- `migrations/002_producto_imagen_destacado.sql` **NUEVO + APLICADO**: `producto.imagen VARCHAR(255) NULL`, `producto.destacado VARCHAR(40) NULL` (texto del badge).
- `model/Producto.obtener_productos_limite()` reescrito: JOIN con categoría, devuelve `imagen`/`destacado`/`nombreCategoria`, límite configurable (default 4 por categoría), `ORDER BY`.
- CSS: bloque "HOME / TIENDA" en `musas-theme.css` (`.musa-hero`, `.musa-catbar`, `.musa-chip`, `.producto-card`, `.musa-pilares`, placeholder de imagen de marca, estado vacío).
- **Datos sembrados** en `db_musuas`: 6 categorías (Hamburguesas, Salchipapas, Bebidas, Combos, Postres, Cremas) y 20 productos con precios/descripciones tipo Stitch. Imágenes: hamburguesas/salchipapas/combos usan `ha-1.jpg`/`h-2.jpg` (solo hay 2 fotos reales); bebidas/postres/cremas → placeholder de marca (columna `imagen` NULL). Dev 2 subirá fotos reales desde el admin.
- Probado: `GET /` → 200, 15 tarjetas, 5 chips (Cremas excluida), navbar con nombre al loguearse, `/productos/<cat>` sigue OK (aún con diseño viejo).

### Pendiente
- `productos.html`, `seleccion-producto.html`, `carrito.html`, `compra.html` **siguen con `client/main.html`** (viejo). Migrar a `client/base.html`.
- El pill del carrito en la navbar muestra `S/ 0.00` fijo (falta cablear el localStorage del carrito).
- Solo hay 2 fotos de comida reales en `static/img/`. Falta `img/productos/` con fotos por producto.
- Links `href="#"` sin ruta: "¿Olvidaste tu contraseña?", "Mis pedidos".
- `Token/usuario.py` consulta la BD al importar (P1).

---

## 3. Problemas conocidos del código (heredados, sin corregir aún)

| # | Archivo / zona | Problema |
|---|---|---|
| P1 | `Token/usuario.py:22` | `users = User.obtener_usuarios()` se ejecuta **al importar** → si MySQL está apagado, la app ni arranca. |
| P2 | `model/Usuario.py:76,78,80` | `SyntaxWarning: "is" with a literal` (usa `is ""` en vez de `== ""`). |
| P3 | `model/Autenticacion.py` | El login compara la contraseña **en texto plano** (`user[0][6] != contraseña`). Sin hash. |
| P4 | `templates/admin/*.html` | Usan clases muertas de **Bulma** (`columns`, `column`, `section`, `is-size-3`) pero Bulma **no está cargado**. |
| P5 | `templates/*/main.html` | El JS de Bootstrap está **comentado** → offcanvas, dropdowns y modales no funcionan. |
| P6 | `templates/client/main.html` (menú lateral) | Links rotos: `index.html`, `pag-inicio-sesion.html` (no existen). Ítems de placeholder "Nombre item". |
| P7 | Toda la tienda | Imágenes de producto **hardcodeadas** (`img/hamburguesas/ha-1.jpg`, `h-2.jpg`). No hay columna `imagen` en la BD. |
| P8 | `templates` + `static/styles` | 13 hojas CSS sueltas sin sistema; footer con links `#`. |

---

## 4. Redundancias / cosas a limpiar

- **CSS**: `static/styles/` tiene 13 archivos (`global.css`, `styles.css` comentado, `header.css`, `footer.css`, `button-carrito.css`, `categorias.css`, `seccion-presentacion.css`, `mostrar-productos.css`, `compra-producto.css`, `normalize.css`, `admin/global.css`, `admin/auth.css`). Consolidar en 2–3 al migrar a Bootstrap 5.
- `static/styles/styles.css` ya está comentado en todos los `main.html` → candidato a borrar.
- `animate.css` se carga por CDN en el cliente y casi no se usa.
- Clases Bulma en admin (ver P4): eliminar todas.
- `templates/client/main.html` y `templates/admin/main.html` repiten los mismos 10 `<link>` de CSS → deberían heredar de un `base.html` único.

---

## 5. Rediseño (Stitch → Bootstrap 5) — decisiones

**Tema:** "Neo-brasa" (ver `DESIGN.md` exportado por Stitch, fuera del repo, en `Downloads/Musas`).
Paleta: brasa `#DB4200`, mostaza `#F5C842`, carbón `#1A1512`, crema `#FBF7F0`.
Fuentes: Space Grotesk (títulos) + Inter (cuerpo).

**Regla de oro:** el negocio es **solo retiro en tienda**. Pago **presencial o Yape/Plin manual** (no hay pasarela). La confirmación del pedido es la **palabra clave = `registroPedido.keyPedido`**.

### NO implementar (Stitch lo inventó, no está en la BD ni en el alcance)
- Delivery / costo de envío / "entregar en Miraflores"
- Cupones / códigos de descuento
- Programa de puntos / "Club Nocturno" / "Musas Points"
- Factura con RUC / integración SUNAT / hash / QR de comprobante
- Captcha en el login admin
- "Término de la carne" en el detalle de producto
- Slug URL / ícono / color / estado activo / orden manual en categorías

### Cambios recomendados a la BD (mínimos, aún NO aplicados)
| Campo | Tabla | Motivo |
|---|---|---|
| `imagen VARCHAR(255)` | `producto` | Fotos de producto (Stitch las usa en todas las pantallas). |
| `imagen VARCHAR(255)` NULL | `categoriaProducto` | Ícono/foto de categoría (opcional). |
| `destacado TINYINT(1) DEFAULT 0` | `producto` | Badges "Más vendida" (opcional). |
| `notas VARCHAR(255)` NULL | `registroPedido` | Campo "indicaciones para cocina" del checkout. Si no se agrega → quitar ese campo del diseño. |
| `disponible TINYINT(1) DEFAULT 1` | `producto` | Toggle "Disponible en carta". Alternativa: usar `existencias > 0`. |

### Pantallas
- **Dejar como están:** Home (desktop/mobile/offcanvas), Listado de categoría, Pedidos admin, Usuarios admin + agregar usuario, Ventas admin, Dashboard admin.
- **Regenerar en Stitch (prompts R1–R8):** Carrito, Checkout, Detalle de producto, Categorías (x3), Detalle de venta, Login/registro cliente, Login admin, Home/listado (ajuste imágenes).
- **Crear nuevas (prompts N1–N6):** Confirmación de pedido + palabra clave ⭐, Mis pedidos (historial + repetir) ⭐, Productos admin (tabla completa), Editar producto, Confirmar recojo (modal con validación de key) ⭐, Editar usuario.
- **Descartar:** "Acceso administrador renovado" (tiene captcha).

### Flujo cliente (resumen)
Home → Listado categoría → Detalle + cremas → Carrito (localStorage) → Finalizar pedido (login autocompleta datos, o invitado) → elige hora de recojo + boleta sí/no + método de pago → Confirmar → **pantalla con la PALABRA CLAVE** → (Mis pedidos / Repetir pedido) → va al local, da la clave, paga, recibe.

### Flujo admin (resumen)
Login → Dashboard → Pedidos (llega cliente → escribe la palabra clave → modal valida contra `keyPedido` → `estadoRecojo=1`) → Productos / Categorías / Usuarios (CRUD contra sus tablas) → Ventas → Detalle de comprobante.

---

## 6. Mapa BD ↔ funcionalidad (referencia rápida)

- `categoriaProducto` → categorías de la carta. La categoría **"Cremas"** se excluye de la carta pública; sus productos son las salsas del paso "personalizar".
- `producto` → ítems de la carta y cremas (según `idCategoria`).
- `usuario.tipoUsuario`: **0 = Admin**, **1 = Cliente**.
- `registroPedido`: `idUsuario` NULL = pedido de invitado (usa `dniNoRegistrado` + `numeroTelefono`). `billeteraDigital` 1 = Yape/Plin, 0 = pago en tienda. `estadoBoleta` = quiere boleta. `estadoRecojo` 0 = pendiente, 1 = recogido. `keyPedido` = **palabra clave** (número).
- `detalleOrden` → líneas del pedido (guarda snapshot de nombre/precio).
- `detalleCremas` → cremas elegidas por línea (`idDetalleOrden` + `idPedido` + `idCrema`).
- `comprobante` / `detalleComprobante` → boleta interna generada del pedido. `subTotal` + `igv` = `montoTotal` (IGV 18%).
