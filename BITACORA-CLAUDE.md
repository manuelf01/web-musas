# Bitácora del proyecto — web-musas (Las Musas)

> Archivo de memoria de trabajo. Se actualiza cada vez que se cambia algo, se
> rompe algo, o se detecta código redundante. **Última actualización: 2026-09-07.**
> Rama de trabajo: `Ramirez` (nunca tocar `main` directamente).

---

## 0. División del trabajo + integración (IMPORTANTE)

- **Ramirez (esta rama):** tienda completa (inicio, carta, detalle, carrito, checkout,
  mis pedidos), login/registro unificado, **CRUD de pedidos** + dashboard, e infra
  transversal (sistema de diseño CSS, seguridad/CSRF, migraciones, anti no-show,
  animaciones).
- **Compañero (rama `origin/Manuelf`, commit `4ce46ae`):** backoffice de **productos,
  categorías, usuarios, ventas, detalle de venta y comprobantes** — pero además rehízo
  en paralelo la tienda/login/checkout/esquema con otro diseño y migraciones.

**2026-09-07 — INTEGRACIÓN HECHA.** Decisión del usuario: la base es `Ramirez`; se
porta la *lógica* del panel de `Manuelf` a este diseño/esquema. NO se hizo `git merge`
(incompatibles: `keyPedido` numérico vs VARCHAR(64), `precio` FLOAT vs DECIMAL, auth
distinta, sin no-show en su rama). Lo integrado:
- CRUD productos/categorías/usuarios con subida de imagen (`subidas.py`), sobre `admin/base.html`.
- Ventas/comprobantes con paginación (`flask_paginate`); el comprobante se emite al
  **entregar** el pedido (`Pedido._emitir_comprobante` en `marcar_recogido`), porque el pago es al recojo.
- Migraciones 007 (`categoriaProducto.imagen`) y 008 (`comprobante.dniNoRegistrado` CHAR(8)).
- CSRF ya NO tiene módulos exentos: todos los formularios del panel llevan `{{ campo_csrf() }}`.
Ver `MERGE_NOTES.md` para el detalle y qué NO se tomó de `Manuelf`.

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
| 2026-09-07 | **Auditoría del flujo completo + tanda de correcciones** (18 hallazgos). Ver sección "Auditoría 2026-09-07" abajo. | `git revert` de los commits |
| 2026-09-07 | **2ª auditoría**: seguridad (CSRF/cabeceras/throttle), responsive (nav inferior móvil, desbordes), captcha admin solo si el DNI es admin. | `git revert` |
| 2026-09-07 | **Cancelación de pedidos + anti no-show** (migración 006). Ver "No-show 2026-09-07" abajo. | `git revert` + revertir 006 |
| 2026-09-07 | **Inicio rediseñado como landing** (distinto de la Carta) + **subida de imágenes desde el panel** (migración 007). Ver "Inicio + imágenes 2026-09-07". | `git revert` + revertir 007 |
| 2026-09-07 | **Ancho + animaciones**: contenedores más anchos, banda "Explora" a todo el ancho, grillas fluidas, aparición al scroll. Ver "Ancho + animaciones 2026-09-07". | `git revert` |
| 2026-09-07 | **Separación del trabajo de Betancurt**: toda su zona vuelve a `main`. Ver `MERGE_NOTES.md` + sección 0. | — |
| 2026-09-07 | **Fixes: horario de recojo, admin en tienda, carrito compartido**. Ver "Fixes checkout/sesión 2026-09-07" abajo. | `git revert` |
| 2026-09-07 | **Integración del panel del compañero** (`Manuelf`): CRUD productos/categorías/usuarios + ventas/comprobantes sobre el diseño de esta rama; comprobante al entregar; migraciones 007–008; CSRF sin exentos. Ver sección 0 + `MERGE_NOTES.md`. | `git revert` |
| 2026-09-08 | **Estados de pedido + pedidos solo de registrados** (migración 009). Ver "Estados de pedido 2026-09-08" abajo. | `git revert` + revertir 009 |
| 2026-09-08 | **Rediseño del panel (Stitch)**: productos/categorías/usuarios/ventas + detalle de comprobante con el look de las pantallas de Stitch. Ver "Panel Stitch 2026-09-08" abajo. | `git revert` |
| 2026-09-08 | **Roles (super/admin/usuario) + estado "dar de baja" + perfil + filtros/autocompletado** (migración 010). Ver "Roles y estado 2026-09-08" abajo. | `git revert` + revertir 010 |
| 2026-09-08 | **Modal de confirmación en todos los CRUD** (dar de baja / reactivar / guardar / entregar / cancelar pedido). Ver "Modal de confirmación 2026-09-08" abajo. | `git revert` |
| 2026-09-08 | **Inicio: sección "Anatomía de Las Musas"** — hamburguesa SVG que se despieza al pasar el cursor / tocar. Ver "Anatomía 2026-09-08" abajo. | `git revert` |
| 2026-09-08 | **Agregar al carrito con micro-interacción + preview al compartir + placeholders por categoría.** Ver "Carrito + previews 2026-09-08" abajo. | `git revert` |
| 2026-09-08 | **Pantalla de cocina en vivo**: el panel de Pedidos se refresca solo y avisa (pitido + banner) cuando entra un pedido nuevo. Ver "Cocina en vivo 2026-09-08" abajo. | `git revert` |
| 2026-09-08 | **`idPedido` / `idDetalleOrden` → AUTO_INCREMENT** (migración 011). Ver "AUTO_INCREMENT 2026-09-08" abajo. | `git revert` + revertir 011 |

### AUTO_INCREMENT 2026-09-08
- **Bug:** `Pedido.crear_pedido_completo` asignaba `idPedido` e `idDetalleOrden`
  con `SELECT COALESCE(MAX(id),0)+1`. Con **dos pedidos entrando a la vez** ambos
  calculaban el mismo id → uno de los INSERT fallaba o dejaba líneas sueltas.
- **Fix:** `migrations/011_autoincrement_pedidos.sql` — `ALTER TABLE` para poner
  `AUTO_INCREMENT` en `registroPedido.idPedido` y `detalleOrden.idDetalleOrden`
  (los ids viejos NO cambian). Aplicada a `db_musuas` y plegada en `sql.sql`.
- `model/Pedido.py`: el INSERT de `registroPedido` ya no manda `idPedido`; el id
  sale de `cursor.lastrowid`. Igual para cada línea de `detalleOrden` → su
  `lastrowid` alimenta el FK de `detalleCremas`. `comprobante` ya usaba
  `lastrowid` (no se tocó).
- Probado en `db_musuas` con pedido real (2 líneas + cremas duplicadas): ids
  asignados por la base, 0 cremas huérfanas, stock correcto, todo limpiado.
- **Legacy sin tocar:** `model/Transaccion.py` + `APIS/transacciones.py`
  (`/transaccion_compra`) siguen con `MAX(id)+1`, pero es el checkout viejo que
  **la tienda no usa** (y ya estaba desalineado del esquema). Anotado en AGENTS.md.

> ⚠️ **Incidente 2026-09-08**: durante estas pruebas se ejecutó `sql.sql` por
> línea de comandos y, como el archivo lleva `USE db_musuas` dentro, **recreó la
> base real** (se perdieron pedidos/comprobantes). Se restauró completa desde
> `db/backup_db_musuas.sql` (backup de las 01:24). **`sql.sql` y el backup solo
> deben correrse desde phpMyAdmin, nunca con `mysql < archivo` apuntando a otra BD.**

### Cocina en vivo 2026-09-08
- **Endpoint** `GET /admin/pedidos/pulso` (`admin_pedidos.pulso`) → JSON
  `{firma, pendientes:[ids]}`. `firma` = huella de `id:estado:recogido` de todos
  los pedidos de hoy; cambia si entra uno nuevo o si alguno avanza / se recoge.
- **`static/js/pedidos-cocina.js`** (cargado solo en `admin/pedidos/index.html`):
  sondea `/pulso` cada **15 s**. Si la `firma` cambió, re-descarga la página y
  reemplaza **solo** `#ped-lista` y `#ped-chips` (no recarga entera: no salta el
  scroll ni pierde lo tecleado en el buscador).
  - Si aparece un `idPedido` que no estaba → **pitido** (2 tonos con WebAudio,
    sin archivo), **banner** `#ped-nuevo` flotante, **título** de la pestaña
    parpadeando y la tarjeta nueva resaltada (`.ped-card--nuevo`).
  - Botón **«Sonido»** en la barra de filtros para activar/probar el audio
    (los navegadores exigen un gesto del usuario antes de reproducir).
- `data-*` que alimentan el JS van en `<div id="ped-cocina">` (no se reemplaza).
  `templates`: `id="ped-chips"` en `.adm-filtros`, `data-pedido-id` en `.ped-card`.
- `ui-comun.js`: el filtro en vivo ahora **re-consulta el DOM en cada tecla**
  (antes cacheaba los nodos) para seguir funcionando tras el reemplazo de lista.
- Respeta `prefers-reduced-motion` (sin animaciones, el aviso igual aparece).

### Carrito + previews 2026-09-08
- **Micro-interacción "agregar al carrito"** (`static/js/carrito.js`, CSS
  "Micro-interacción"): al agregar, una bolsita vuela del botón al pill del
  carrito, el pill rebota y sale un **toast** ("Agregado al carrito · Ver
  carrito"). API nueva: `MusasCarrito.agregarConAnim(item, origenEl, opts)`,
  `.toast(msg, {href, accion})`, `.volar(el)`, `.rebotar()`.
- **Detalle de producto** ya **no redirige** al carrito al agregar: se queda en
  la página, el botón muestra "¡Agregado!" 1.4 s y la cantidad vuelve a 1
  (`static/js/detalle-producto.js`). Igual en "Repetir pedido" de Mis pedidos.
- **Vista previa al compartir el enlace** (WhatsApp/redes): meta `og:*` +
  `twitter:card` + `description` en `templates/client/base.html` (bloques
  `meta_desc`, `og_title`, `og_desc`, `og_image`). `seleccion-producto.html`
  los sobreescribe con nombre/precio/imagen del producto. Imagen por defecto:
  `img/hamburguesas/h-2.jpg`. `url_for(..., _external=True)`.
- **Placeholders de producto por categoría**: si un producto no tiene foto, en
  vez del ícono de fuego genérico se muestra el ícono de su categoría
  (`bi-cup-straw` bebidas, `bi-cake2-fill` postres, etc.) con un tinte suave
  (`_producto_card.html`, `seleccion-producto.html`, CSS `.producto-card__ph[data-cat]`).
  **Sigue faltando la foto real por producto** (se sube desde el panel).

### Anatomía 2026-09-08
- Sección nueva en `templates/client/index.html` entre el hero y "Cómo funciona":
  hamburguesa dibujada **100 % en SVG** (sin fotos), 6 capas (`.anat-capa`) que
  se separan en el aire con etiquetas (`.anat-tag`) al hacer `:hover`/`:focus`
  sobre el `<button class="anat-burger">`, o con la clase `.abierto`.
- Cada capa lleva `--step` (cuánto se aleja, ×20 px) y `--d` (retardo escalonado).
  Solo se anima `transform: translateY` → 60 fps. CSS en `musas-theme.css`
  (bloque "Anatomía de Las Musas").
- `static/js/animaciones.js`: clic = fija/suelta el despiece; en pantallas sin
  hover (`matchMedia("(hover: none)")`) un `IntersectionObserver` lo abre solo al
  entrar en pantalla.
- Móvil (`≤900px`): se ocultan las etiquetas del SVG y se muestra una lista
  HTML `.anat-lista` con los 6 ingredientes + descripción corta.
- `prefers-reduced-motion`: se muestra ya despiezada y etiquetada, sin movimiento.
- Sin backend ni BD.

### Modal de confirmación 2026-09-08
- Componente reutilizable en `static/js/ui-comun.js` (+ CSS `.musa-confirm*` en
  `musas-theme.css`): un modal **bonito y animado** (icono con "pop", tarjeta con
  entrada tipo resorte, backdrop con desenfoque) que pide confirmación antes de
  ejecutar una acción. Reemplaza los `window.confirm()` / `onsubmit="return confirm()"`.
- **Cómo se marca una acción** (en el `<form>`, en su `<button type=submit>` o en un `<a>`):
  `data-confirm="texto"` + opcionales `data-confirm-titulo`, `data-confirm-ok`,
  `data-confirm-cancelar`, `data-confirm-tono="peligro"` (rojo), `data-confirm-icono`.
  El JS intercepta el `submit`/`click` en captura, muestra el modal y solo reenvía
  el formulario si el usuario acepta (bandera `dataset.confirmHecho`). Teclado:
  Esc = cancelar, Enter = aceptar, Tab atrapado entre los 2 botones. `Promise`
  expuesta como `window.MusaConfirm(opts)`.
- **Dónde se aplica**: Productos (dar de baja / reactivar / guardar), Categorías
  (íd.), Usuarios (dar de baja / reactivar / cambiar rol / crear), Pedidos admin
  (empezar preparación / marcar listo / entregar+facturar / no recogió / cancelar),
  y Mis pedidos del cliente (cancelar). Los paneles deslizantes fijan el texto del
  modal según crear/editar en su propio JS.
- Sin cambios de backend ni de BD.

### Política de contraseña + admin solo cambia rol 2026-09-08
- **Contraseña (una sola regla en todo el proyecto)**: mínimo 8 caracteres, con
  al menos una **mayúscula** y un **número**. `seguridad.py` → `password_valida(pw)`
  (None | texto de error), `REGLA_PASSWORD`, `PASSWORD_PATTERN` (para el
  `pattern=` del `<input>`). Registrados como globals de Jinja en `app.py`.
  Se usa en: registro (`autenticacion.py`), alta de usuario (`admin_usuarios.py`),
  Mi perfil (`admin_perfil.py`), Mi cuenta (`cliente.py`), y como red de seguridad
  en `Usuario.insertar_usuario`. Templates: hint visible + `pattern` + `title`;
  el registro además muestra un checklist en vivo (`#pw-check`).
  - **Nota**: la contraseña de ejemplo de `sql.sql` pasó de `musas2026` a `Musas2026`
    (la anterior no cumplía). El login solo valida el hash, así que cuentas viejas
    con contraseña débil siguen entrando; solo se exige la regla al **cambiarla**.
- **Gestión de usuarios: el administrador SOLO cambia el rol y da de baja.**
  El correo/teléfono/contraseña de cada persona los edita ella misma en «Mi perfil».
  `Usuario.actualizar_por_admin(...)` → reemplazado por `Usuario.cambiar_rol(id, rol)`
  (solo toca `rol` + `tipoUsuario`; conserva las protecciones de superusuario).
  `admin_usuarios.actualizar` solo lee `rol`. El panel de edición muestra solo el
  selector de Rol + un aviso; el botón de la fila dice «Cambiar rol».
- **Ventas**: el nombre del comprobante ahora es `rp.nombres` (el de quien recoge,
  que se pide en el checkout) y si no, el nombre completo de la cuenta — antes
  mostraba solo el primer nombre de la cuenta.
- Flujo completo re-verificado E2E (compra → confirmación → CRUD pedidos con los
  3 vistos buenos → comprobante → Ventas): 60+ checks, 0 fallos. Aritmética
  (27×2=54, 18×3=54, total 108), IGV (91.53+16.47), stock (resta y devolución),
  estados, palabra clave, KPIs y gráfico — todo cuadra.

### QA adversarial + fixes 2026-09-08
Batería de ~120 casos (3 roles) contra una BD limpia `db_musuas_qa`. No había
nada crítico (auth, CSRF, roles, aritmética, IGV, stock, no-show, cancelación
todo correcto). Se arreglaron 14 hallazgos:

- **Checkout: 500 ante carrito malformado** → `controllers/cliente.py`: nuevo
  `_leer_carrito()` que sanea `carrito_json` del localStorage (valida que es
  lista, `int()` tolerante por ítem, cremas → lista + dedupe + solo ids válidos,
  cantidad 1..99). Ya no revienta con `idProducto`/`cantidad`/crema no numéricos,
  ni con `carrito_json` que no es lista, ni con cremas duplicadas.
- **`Pedido.crear_pedido_completo`**: `dict.fromkeys` en las cremas (por si acaso).
- **Cremas**: `Producto.precios_por_ids(ids, solo_cremas=True)` — una hamburguesa
  ya no cuela como "crema" y suma su precio.
- **CRUD productos: 500 ante datos malos** → `model/Producto.py`: helpers
  `_a_precio` / `_a_stock` (nunca lanzan, rechazan negativos), `categoria_existe`.
  `insertar_producto` / `actualizar_producto` devuelven `None` | texto de error.
  `PRECIO_MAX = 100000`. Ya no se guardan precio/stock negativos ni se revienta
  con precio "gratis" o categoría inexistente. Controladores muestran el flash.
- **Categoría dada de baja**: ahora SÍ saca sus productos de la tienda —
  `obtener_productos(solo_activos)`, `getProductosCategoria`, `precios_por_ids`,
  `contar_por_categoria(solo_activos)` filtran `cp.activo = 1`;
  `obtener_producto_por_id` expone `disponibleTienda`; `comprar_producto` lo usa.
- **Categoría nombre vacío** → `insertar_categoria` / `actualizar_categoria`
  validan (mín. 2 chars) y devuelven error.
- **CSRF**: `<meta name="csrf-token">` en ambos `base.html` (token siempre disponible).
- **Paginación productos**: `per_page` 9 → 60 (el filtro en vivo cubre todo el
  catálogo sin recargar) + guard `page < 1`.

### Entrega para el compañero 2026-09-08
- **`sql.sql` reescrito**: crea `db_musuas` desde cero con TODO el esquema
  (migraciones 001–010 ya incluidas) + datos de ejemplo (6 categorías, 20
  productos, 3 cuentas: superusuario 12345678 / admin 87654321 / cliente
  12345679, **contraseña `musas2026`**). Copiar y pegar en phpMyAdmin.
- **`db/backup_db_musuas.sql`**: `mysqldump` del estado real de trabajo
  (referencia; los hashes de contraseña de esas cuentas no se conocen).
- **`AGENTS.md`** (NUEVO): contexto para Codex — qué es el proyecto, reglas de
  negocio, arquitectura, cómo levantarlo, esquema de BD, convenciones y estado
  actual. Es la "bitácora para Codex".

### Ajustes UX 2026-09-08 (búsqueda viva, ver contraseña, carrito con login)
- **`static/js/ui-comun.js`** (nuevo, cargado en ambos `base.html`):
  - Filtrado **en vivo sin Enter**: `<input data-filtro-vivo="#scope">` oculta los
    `[data-filtro-item]` que no coinciden mientras se escribe (con `[data-filtro-seccion]`
    y `[data-filtro-vacio]` opcionales). Aplicado en carta de la tienda y CRUDs de
    productos / categorías / usuarios / pedidos. El `<form method=get>` sigue como
    respaldo (Enter) para búsquedas más allá de la página actual.
  - Mostrar/ocultar contraseña por delegación (`[data-toggle-pass="<id>"]`). Se quitó
    el JS inline duplicado de login.html y registro.html.
- **Botón "ver contraseña"** en: agregar/editar usuario, Mi perfil y Mi cuenta
  (`.musa-pass` + `.musa-toggle`).
- **Cuadros de imagen simétricos**: dropzone y previsualización comparten
  `190px` de alto y bordes; separador "o pega un enlace"; el preview grande llena
  el espacio y al clicarlo abre el selector de archivo.
- **Carrito solo con sesión**: `/carrito` y `/compra` redirigen a `/login?next=…`
  si no hay `cliente.auth`. El detalle de producto muestra "Inicia sesión para pedir"
  en vez del botón de agregar; el ícono de carrito del header/tabbar apunta al login.

### Roles y estado 2026-09-08
Migración **010**: `usuario.rol` ('superusuario'|'administrador'|'usuario') + `usuario.activo`,
`producto.activo`, `categoriaProducto.activo`. `rol` se deriva del `tipoUsuario`
previo y el primer admin queda como superusuario. `tipoUsuario` se mantiene
sincronizado (0 = panel, 1 = cliente) por compatibilidad.

- **3 roles.** `model/Usuario.py`: `ROLES`, `ETIQUETA_ROL`, `_tipo_de_rol`, y métodos
  `obtener_todos`, `obtener_dict`, `contar_por_rol`, `actualizar_por_admin` (super
  edita otras cuentas + rol; **rechaza** editar a otro superusuario y promover a
  superusuario por edición), `actualizar_perfil` (auto-edición), `cambiar_estado`,
  `login_por_dni`, `existe_dni(dni, excepto_id)`.
- `model/Autenticacion.py`: `dni_es_admin` y `login_unificado` usan `rol` + `activo`
  (cuenta dada de baja no inicia sesión).
- `controllers/admin.py`: el blueprint `admin.usuarios.*` es **solo superusuario**;
  el administrador entra al panel pero no ve Usuarios.
- **Gestión de usuarios** (`admin/usuarios/index.html`): chips por rol + "de baja",
  panel con **selector de rol**, "Dar de baja"/"Reactivar", fila del superusuario
  protegida (sin editar/baja; solo "Mi perfil" si es la propia).
- **Perfil**: `controllers/admin_perfil.py` (`/admin/perfil`) para super/admin y
  `cliente.mi_cuenta` (`/mi-cuenta`) para el rol usuario. Ambos corrigen
  nombres/apellidos/DNI/correo/teléfono/contraseña y refrescan la sesión.
- **Estado en productos/categorías**: chips (En carta / Sin stock / De baja / Todos),
  botón "Dar de baja"/"Reactivar" (reemplaza a Eliminar). La tienda solo muestra lo
  activo: `Producto.obtener_productos(solo_activos=True)`, `getProductosCategoria`
  filtra, `precios_por_ids` bloquea inactivos, `CategoriaProducto.obtener_categorias(solo_activas=True)`.
- **Imagen por enlace**: `subidas.guardar_desde_url(url, subcarpeta)` descarga la
  imagen de un link de internet (valida esquema, bloquea IPs privadas/SSRF, límite
  5 MB, verifica con Pillow). El panel de producto/categoría acepta archivo **o** enlace,
  con **previsualización grande** (`.adm-foto-grande`).
- **Autocompletado**: `<datalist>` nativo en todas las barras de búsqueda — carta
  de la tienda y CRUDs de productos/categorías/usuarios/pedidos.
- **Pedidos**: chips por estado (Por entregar / Recibidos / En cocina / Listos /
  Recogidos / Todos) + búsqueda server-side con datalist.

### Panel Stitch 2026-09-08
Las 4 pantallas del panel + el detalle de comprobante se rehicieron para calzar
con `C:\Users\JUAN RAMIREZ\Downloads\Musas`:
- **Productos**: cabecera con pill de conteo, buscador, chips (En carta / Sin stock
  / Categorías), tabla con miniatura + badge de categoría + stock, "Mostrando X–Y",
  paginación. Alta y edición en **panel deslizante** (`.adm-panel`) con zona de
  imagen, no en página aparte (`agregar_producto.html`/`editar_producto.html`
  BORRADOS; sus rutas redirigen a la lista).
- **Categorías**: grilla de tarjetas (emoji, N° productos, descripción, editar/borrar)
  + tarjeta "Crear nueva categoría". Alta/edición en **modal** (`.adm-modal`).
  Sin slug/ícono/color/estado/orden (regla del rediseño). `agregar.html`/`editar.html`
  BORRADOS.
- **Usuarios**: `Usuario.obtener_todos()` + `contar_por_rol()`. Tabla con avatar,
  DNI, correo, teléfono, badge de rol. Chips Todos/Admin/Cliente. Panel deslizante:
  alta de admin (DNI+datos) o edición (correo/tel/contraseña). Clientes solo lectura.
  `agregar.html`/`editar.html` BORRADOS.
- **Ventas**: 3 KPIs (facturado / N° comprobantes / ticket) desde `Comprobante.kpis()`,
  gráfico de barras 7 días (`Comprobante.ventas_por_dia`), tabla de comprobantes
  (`Comprobante.listado_paginado`) con badge de forma de pago.
- **Detalle de comprobante**: boleta con cinta degradada, datos del cliente,
  líneas con miniatura, totales, **importe en letras** (`formato.py` →
  `soles_en_letras`), panel lateral con estado del pedido y notas. Botón Imprimir
  (CSS `@media print`). Sin RUC/SUNAT/QR (regla del rediseño).
- CSS nuevo en `musas-theme.css` (`.adm-list-head`, `.adm-chip2`, `.adm-panel`,
  `.adm-drop`, `.adm-cat-grid`, `.adm-modal`, `.adm-vent-kpi`, `.adm-recibo*`).
- Modelos: `Comprobante` (+kpis, ventas_por_dia, listado_paginado, detalle),
  `Usuario` (+obtener_todos, contar_por_rol). Nuevo `formato.py`.

### Estados de pedido 2026-09-08
Tres pedidos del usuario:
1. **"Arreglar lo del no recogió"** — `_auto_no_show()` solo marca "no recogió" si el
   pedido estaba **LISTO** (`estadoPrep = 2`) y el cliente no vino + 45 min de gracia.
   Si nunca se preparó, es problema del local → se queda para que el admin lo resuelva
   a mano. (Sigue además el guard de `MUSAS_DEMO`.)
2. **Estados reales** (migración 009, columna `registroPedido.estadoPrep` al final):
   `0 recibido` → `1 en preparación` → `2 listo` → recogido / cancelado / no_show.
   - El cliente **solo puede cancelar mientras está "recibido"**. Apenas la cocina le
     da a "Empezar preparación", el botón Cancelar desaparece y sale "Ya en cocina".
   - El admin (panel Pedidos) tiene botón **"Empezar preparación" / "Marcar listo"**
     además de Entregar (con clave) / No recogió / Cancelar.
   - `model.Pedido.estado_pedido()` centraliza el estado canónico; lo usan
     `historial_cliente`, `pedidos_de_hoy`, `obtener_pedido_completo`, `diccionario_pedidos`.
3. **Pedidos solo de usuarios registrados** — `/compra` exige `session["cliente.auth"]`
   (redirige a `/login?next=/compra`). Se quitó todo el flujo de invitado: el captcha
   del checkout (`compra_captcha`, campo `captcha`), el `session["pedidos_propios"]`,
   y `_identidad()`. `crear_pedido_completo` siempre recibe `idUsuario`. Login ahora
   respeta `?next=` (solo rutas internas).

### Fixes checkout/sesión 2026-09-07
Reportes del usuario tras probar el flujo:

1. **"A qué hora recoger no funciona"** — NO era bug: probaba a las 11 p.m. y la
   tienda atiende 6–10 p.m., así que todas las franjas salían `pasada`.
   - `model/Pedido.py`: `HORA_APERTURA`/`HORA_CIERRE` ahora se pueden fijar con
     `MUSAS_HORA_APERTURA` / `MUSAS_HORA_CIERRE` (defecto 18 / 22).
   - Nuevo `MUSAS_DEMO=1`: ignora el corte por "hora ya pasada" para poder probar
     el checkout a cualquier hora. **Nunca activar en producción.**
   - Correr en local: `MUSAS_DEMO=1 python app.py`.

2. **Admin en la tienda parecía deslogueado y el checkout le pedía captcha.**
   La tienda solo miraba `session["cliente.auth"]`; el admin vive en
   `session["admin.auth"]`.
   - `app.py`: context processor `admin_sesion` (disponible en todas las plantillas).
   - `templates/client/base.html`: el header muestra "Modo administrador · Ir al
     panel" en vez de "Iniciar sesión".
   - `controllers/cliente.py`: nuevo `_identidad()` (cliente **o** admin). El
     captcha del checkout solo se exige a visitantes sin ninguna cuenta.
   - Que un cliente logueado no vea captcha y un invitado sí **es intencional**
     (anti-bot / anti no-show), no un bug.

3. **El carrito (localStorage) se quedaba para el siguiente que usara el equipo.**
   - `controllers/autenticacion.py`: `logout` marca `session["limpiar_carrito"]`.
   - `templates/client/base.html`: consume la marca una vez y hace
     `localStorage.removeItem("musas_carrito")`.
   - Al **iniciar** sesión el carrito se conserva a propósito (invitado que arma
     el carrito y luego entra a su cuenta para pagar).

### Ancho + animaciones 2026-09-07
**Problema**: en pantallas grandes sobraba mucho aire a los lados.

- `.musa-shell` 1200 → **1320 px** (padding 32 → 40). `.cx-wrap` 1100 → 1240. `.adm-content` 1240 → 1440.
- `.producto-grid` pasa a `repeat(auto-fill, minmax(250px, 1fr))` → llena el ancho con más columnas.
  En el inicio, `.musa-favs .producto-grid` se fija a 4 columnas.
- `.mp-lista` (Mis pedidos) pasa a grilla `auto-fill minmax(460px, 1fr)` → 2 columnas en desktop.
- **"Explora"** ahora es una banda a todo el ancho (`background` + `border-block`), con un
  `.musa-shell` interno — rompe el vacío lateral. Estructura: `<section class="musa-explora"><div class="musa-shell">…`.
- **Aparición al scroll** (`static/js/animaciones.js`, IntersectionObserver, ~30 líneas):
  `[data-reveal]` empieza en `opacity:0; translateY` y pasa a `.is-visible`. `data-reveal-delay="1..3"` escalona.
  Failsafe a 2.5 s + respeta `prefers-reduced-motion`. Cargado en `client/base.html`.
- Micro-interacciones (solo CSS): hover con elevación + zoom de la foto en `.producto-card`,
  `:active` en botones, zoom lento del fondo del hero, pulso del punto "abierto ahora".

### Inicio + imágenes 2026-09-07
**Problema**: Inicio y Carta eran casi idénticas (ambas = secciones por categoría + tarjetas).

- **Inicio (`/`)** ahora es un *landing* de marketing, NO un catálogo:
  hero → fila horizontal "Los favoritos de la noche" (`Producto.destacados()`) →
  banda de promo → mosaicos de categoría (`.musa-tiles`, enlazan a `/productos/<cat>`) →
  reseñas / prueba social (`.musa-resenas`, texto estático) → pilares → sede + mapa.
  Ya NO lista la carta completa.
- **Carta (`/carta`)** gana **buscador** (`?q=`) y **ordenar** (`?orden=`); con búsqueda
  activa muestra una sola grilla sin secciones ni catbar.
- ⚠️ Colisión de clases resuelta: `.musa-social` ya existía (iconos del footer).
  La sección de reseñas usa `.musa-resenas`. **No reusar `.musa-social` para bloques.**

**Migración 007**: `categoriaProducto.imagen VARCHAR(255) NULL`.

- **Subida de imágenes** (`subidas.py` → `guardar_imagen(archivo, subcarpeta)`):
  valida extensión + que sea imagen real (Pillow `verify()`), guarda en
  `static/img/<productos|categorias>/` con nombre aleatorio, devuelve la ruta relativa.
- Formularios admin de producto y categoría: `enctype="multipart/form-data"` + `<input type="file" name="imagen">`.
  Al editar: se muestra la imagen actual; si no subes una nueva, se conserva.
- `Producto.insertar_producto` / `actualizar_producto` y `CategoriaProducto.insertar/actualizar_categoria`
  aceptan `imagen=None`.
- Las listas del panel muestran miniatura (`.adm-foto-mini`).
- `MAX_CONTENT_LENGTH = 5 MB` en `app.py`.
- **`static/img/productos/` y `static/img/categorias/` están en `.gitignore`**: las
  imágenes subidas son datos de cada entorno, no código. Para el demo compartido,
  subir las fotos por el panel en cada equipo o pasar un zip.

### Seguridad 2026-09-07
- **CSRF**: token de sesión propio (`seguridad.py` → `campo_csrf()` / `csrf_valido()`), validado en `app.before_request` para todo POST de formulario. APIs JSON (JWT, `/api/*`) exentas por content-type. `{{ campo_csrf() }}` en los 15 formularios.
- Cabeceras: `X-Frame-Options=SAMEORIGIN`, `X-Content-Type-Options=nosniff`, `Referrer-Policy=same-origin` (`after_request`).
- Cookie de sesión: `HttpOnly`, `SameSite=Lax`, `Secure` cuando no hay debug.
- `debug` → `FLASK_DEBUG` (1 por defecto en local; **apagar en producción**, el depurador de Werkzeug ejecuta código).
- Login: bloqueo por IP tras 6 fallos en 5 min (`_intentos_login` en memoria del proceso).
- Captcha admin: se muestra **solo si el DNI es de administrador** (`mostrar_captcha` desde el servidor). Antes salía tras cualquier login fallido.
- `SECRET_KEY` desde `cfg.py` (`secret_key`, con fallback).

### Responsive 2026-09-07
- **Tienda móvil (≤768px)**: barra de navegación inferior (Inicio · Carta · Carrito · Pedidos) — antes los enlaces del navbar desaparecían sin reemplazo. `overflow-x` contenido; `min-width:0` en contenedores flex con scroll (`.musa-catbar__chips`, `.dp-badges`); filas de acción con `flex-wrap`. Se retira `.dp-mobile-bar` en móvil.
- **Backoffice**: enlaces del sidebar en `<span>` → el rail de 64px colapsa bien en tablet/móvil (antes las etiquetas se salían sobre el contenido).
- ⚠️ Nota de testing: Edge headless renderiza a un mínimo de ~500px de ancho; para verificar <500px hay que usar un navegador real o emulación de dispositivo.

### No-show 2026-09-07 (control "básico" elegido por el usuario)
**Migración 006**: `registroPedido.cancelado` + `registroPedido.noShow` (TINYINT), `comprobante.dniNoRegistrado` → CHAR(8) (los DNI pueden empezar por 0), `usuario.noShows` (contador).

- **Cancelar pedido** (cliente y admin): `Pedido.cancelar_pedido()` — solo si sigue pendiente; devuelve el stock y libera el cupo de la franja. Cliente: `POST /mis-pedidos/<id>/cancelar` (valida propiedad por sesión/idUsuario). Admin: botón en cada tarjeta de "Gestionar pedidos".
- **Límite de pedidos activos**: máx. `Pedido.MAX_PEDIDOS_ACTIVOS = 2` sin recoger por DNI (registrado) o por DNI+fecha (invitado). Lanza `LimitePedidos`.
- **Captcha en checkout de invitados**: `/compra/captcha` (imagen Pillow, `session['captcha_compra']`). Los clientes con cuenta se lo saltan.
- **Auto no-show**: `Pedido._auto_no_show()` (llamado al leer franjas / panel / dashboard) marca `noShow=1` los pedidos de hoy vencidos > `GRACIA_NOSHOW_MIN = 45` min, devuelve stock y suma `usuario.noShows`.
- **Admin**: botones "No recogió" y "Cancelar pedido" por tarjeta; aviso "N pedidos no recogidos antes" si el cliente tiene historial; contador de no-shows del día en el dashboard.
- **Comprobante**: ahora se emite en `marcar_recogido()` (al cobrar), no al hacer el pedido. Serie `B001-` (con boleta) o `NV01-` (nota de venta). `/admin/ventas/` = ventas realmente cobradas.
- Franjas, KPIs, dashboard, "top productos" y "ventas 7 días" **excluyen** cancelados y no-shows.
- **Ideas NO implementadas** (necesitan servicios externos): OTP por SMS/WhatsApp, prepago real / pasarela, depósito reembolsable, bloqueo por reputación (3 strikes → solo prepago), confirmación "voy en camino" antes de cocinar.

### Auditoría 2026-09-07 — flujo revisado de punta a punta y corregido

Se probó E2E (cliente + invitado + admin) con `test_client`. Correcciones aplicadas:

**Seguridad / lógica (crítico)**
1. **Fuga de la palabra clave.** `GET /pedido-confirmado/<id>` era público → cualquiera enumeraba IDs y leía la `keyPedido` + DNI/teléfono de otros clientes. Ahora `pedido_confirmado` exige que el pedido esté en `session['pedidos_propios']` (invitado) o que el `idUsuario` logueado sea el dueño; si no, redirige a `/mis-pedidos`.
2. **"Mis pedidos" mostraba total con precios ACTUALES.** `Pedido.historial_cliente` ahora suma el snapshot `detalleOrden.precioTotal` (lo que el cliente pagó); el precio/imagen actual solo se usa para "repetir pedido". Se añadió campo `pagado` por línea.
3. **Módulo Ventas desconectado.** `Pedido.crear_pedido_completo` ahora inserta `comprobante` + `detalleComprobante` (agrupado por producto, PK es `idComprobante+idProducto`) dentro de la misma transacción. `numeroComprobante` = `B001-<id>` (boleta) o `NV01-<id>`. subTotal = total/1.18, igv = resto. `/admin/ventas/` ya lista ventas reales.
4. **Sin control de stock.** `crear_pedido_completo` bloquea las filas de `producto` (`FOR UPDATE`), valida `existencias >= cantidad` (lanza `StockInsuficiente(nombre, disponible)`) y descuenta `existencias` al confirmar. `_procesar_compra` captura la excepción y re-muestra el checkout con el aviso.
5. **`marcar_recogido` no atómico.** El `UPDATE` ahora lleva `WHERE idPedido=%s AND estadoRecojo=0 AND keyPedido=%s` y se valida `rowcount == 1`.
6. **Flashes invisibles.** `carrito/carta/index/mis-pedidos/productos` no renderizaban `get_flashed_messages`. Nuevo `templates/client/_flash.html` incluido en `base.html` vía `{% block flash %}`. `login/registro/compra` lo sobre-escriben (tienen su alerta propia dentro de la tarjeta).
7. **Race en IDs** (`SELECT MAX+1` para `idPedido`/`idDetalleOrden`): documentado, sin cambio (bajo volumen real no colisiona; `comprobante` sí usa `AUTO_INCREMENT` + `lastrowid`).

**Navegación / UX**
8. Breadcrumb "Carta" y botón "Volver a la carta" en `productos.html` ahora apuntan a `cliente.carta` (antes a `/`).
9. Errores de validación en checkout/registro/login **conservan lo escrito** (`form=request.form.to_dict()` → prefill de dni/nombres/apellidos/teléfono/notas/hora/pago/boleta).
10. "Repetir pedido" ahora **suma** al carrito en vez de reemplazarlo (`mis-pedidos.js`).
11. El selector de cremas solo aparece para `Hamburguesas` y `Salchipapas` (`CATEGORIAS_CON_CREMAS` en `controllers/cliente.py`).
12. **Migración 005**: `producto.precio` y `producto.existencias` → `NOT NULL DEFAULT 0`. Plantillas con `precio or 0` por si acaso.
13. Login: link muerto "¿Olvidaste tu contraseña?" → texto ("Recupérala en el local").
14. Registro bloquea DNI ya existente con **cualquier** tipo de usuario (`Usuario.existe_dni`).
15. `Token/usuario.py`: ya no consulta la BD en el import (rompía el arranque si MySQL no estaba listo); `authenticate`/`identity` consultan al vuelo con `try/except`.
16. **Pantallas admin viejas migradas** a `admin/base.html` (Productos, Categorías, Usuarios, Ventas + sus formularios). Ver commit aparte.
17. `SECRET_KEY` ahora viene de `cfg.py` (`secret_key`, con fallback). Eliminado el doble `app.secret_key`. Añadido a `cfg.example.py`.
18. `Pedido.franjas_recojo` usa `date.today()` de la app (no `CURDATE()` de MySQL) para alinear el conteo de cupos con la hora de corte. Resto de queries por fecha siguen con `CURDATE()` (consistentes entre sí; solo importa si el server de app y MySQL tienen distinta zona horaria).

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

- **[2026-09-07 · HECHO]** Borrados por quedar huérfanos tras el rediseño:
  `templates/admin/main.html`, `templates/client/main.html`, y los JS del flujo viejo
  (`static/js/admin/pedidos.js`, `guardarProductos.js`, `mostrarProductos.js`,
  `mostrarProductosCompra.js`, `comprarProductos.js`, `fetchApis.js`, `pedidosUsuario.js`,
  `personalizar.js`, `categorias.js`, `header.js`). Ya nada los referenciaba.
- Pendiente: limpiar `static/styles/*.css` (13 archivos del diseño viejo, ya sin uso salvo `admin/*`).
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
