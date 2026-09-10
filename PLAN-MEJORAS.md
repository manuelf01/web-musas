# Plan de mejoras — Las Musas (web-musas)

> Revisión hecha el 2026-09-09 sobre el commit `4c6b12d` (rama `Ramirez`), leyendo
> `controllers/cliente.py`, `controllers/admin_pedidos.py`, `model/Pedido.py`,
> `negocio.py`, `static/css/musas-theme.css`, `static/js/*` y las plantillas de
> `templates/client/`. Complementa [`docs/arquitectura.html`](docs/arquitectura.html).
>
> Tres bloques: **A)** fallos de lógica del proceso de compra/venta · **B)** UI/UX y
> espacios en blanco · **C)** rediseño de la hamburguesa "Anatomía".
> Al final hay una tabla de prioridad (impacto / esfuerzo / riesgo).

---

## A. Lógica del proceso de compra y venta

El flujo es: carrito en `localStorage` → `POST /compra` re-cotiza y crea el pedido
(`Pedido.crear_pedido_completo`) → cocina avanza estados (`avanzar_preparacion`) →
en caja `POST /pedidos/confirmar` cobra y emite el comprobante (`marcar_recogido` →
`_emitir_comprobante`). Es un diseño sólido. Los puntos a corregir:

### A1 · El reloj no es consistente en todo el modelo  ⚠️ importante
`Pedido.franjas_recojo()` usa `datetime.now(HORA_PERU)`, pero `Pedido._auto_no_show()`
usa `datetime.now()` (hora **local del servidor**, sin zona) y la rama de invitado de
`crear_pedido_completo` usa `datetime.now().date()`. Además `registroPedido.fechaPedido`
lo pone la BD con `DEFAULT (CURRENT_DATE)` — la fecha de **MySQL**, no la de la app.

- **Problema:** en local (una sola PC) todo coincide. En un servidor en UTC (o si XAMPP
  y la app quedan en zonas distintas) el conteo de cupos, el corte "franja pasada" y
  el auto-no-show se desalinean hasta 5 h. Un pedido podría contarse en el día
  equivocado o marcarse no-show antes de tiempo.
- **Arreglo:** una sola función `ahora_peru()` en `negocio.py` y usarla en todo
  `Pedido`. Pasar `fechaPedido` explícito en el `INSERT` (`ahora_peru().date()`) en
  vez de depender del `DEFAULT`. Revisar cada `datetime.now(` del modelo.
- **Archivos:** [model/Pedido.py](model/Pedido.py) (líneas ~96, 168, 172, 239, 355),
  [negocio.py](negocio.py).

### A2 · El cupo de la franja no se re-valida dentro de la transacción  ⚠️ importante
`_procesar_compra` llama `Pedido.franja_disponible(hora)` **antes** de
`crear_pedido_completo`, pero la creación del pedido solo bloquea las filas de
`producto` (`FOR UPDATE`) — **no** vuelve a contar los pedidos de la franja.

- **Problema (TOCTOU):** dos clientes que piden el último cupo de las 20:00 al mismo
  tiempo pasan los dos. El `CUPO_POR_FRANJA = 8` se puede exceder.
- **Arreglo:** dentro de `crear_pedido_completo`, después del control de stock, hacer
  `SELECT COUNT(*) ... WHERE fechaPedido = %s AND horaRecojo = %s AND {_OCUPA_CUPO}`
  y si `>= CUPO_POR_FRANJA` lanzar una excepción `FranjaLlena` que
  `_procesar_compra` traduzca a "esa franja se llenó, elige otra".
- **Archivos:** [model/Pedido.py](model/Pedido.py) (`crear_pedido_completo`),
  [controllers/cliente.py](controllers/cliente.py) (`_procesar_compra`).

### A3 · El total que ve el cliente en el checkout puede mentir  ⚠️ importante
`checkout.js` pinta el resumen y el "Total a pagar" con los precios **guardados en
`localStorage`** (se copiaron cuando el producto se agregó al carrito). El servidor
re-cotiza contra la BD en `/compra` y crea el pedido con **el precio actual**.

- **Problema:** si el admin cambió un precio mientras el cliente tenía el carrito
  abierto, el checkout muestra S/ 45 y la página de confirmación (que ya usa el total
  del servidor) muestra S/ 48, sin ningún aviso. Se rompe la confianza.
- **Arreglo:** endpoint `GET /compra/cotizar?carrito=…` que devuelva el total real; el
  checkout lo llama al cargar y muestra el total del servidor (y un aviso "ajustamos
  el precio de X" si difiere del local). Alternativa mínima: en `_procesar_compra`,
  si el total re-cotizado difiere del que mandó el form (`total_cliente` en un hidden),
  no crear el pedido: volver al checkout con "el precio de X cambió, revísalo".
- **Archivos:** [static/js/checkout.js](static/js/checkout.js),
  [controllers/cliente.py](controllers/cliente.py).

### A4 · "Pago digital" es decorativo y los mensajes se contradicen
El checkout ofrece "Billetera digital (Yape/Plin)" con el texto *"Coordinamos el pago
al confirmar"*, pero el pago real siempre ocurre en caja al recoger (`marcar_recogido`
recibe `medio_pago` del cajero; el hero de la home dice *"pagas al recoger"*; la boleta
dice *"se genera al pagar y recoger"*). No hay carga de comprobante de Yape ni
conciliación.

- **Problema:** el cliente cree que ya "coordinó" el pago y no lo hizo; el `billeteraDigital`
  solo se usa como valor por defecto del medio de pago.
- **Arreglo (barato):** cambiar el copy — la opción digital pasa a ser *"Pagaré con
  Yape/Plin al recoger"* vs *"Pagaré en efectivo/tarjeta al recoger"*. Quitar
  "coordinamos el pago al confirmar" de [compra.html](templates/client/compra.html) y
  de [pedido-confirmado.html](templates/client/pedido-confirmado.html).
- **Arreglo (completo, si lo quieren):** subida opcional de captura de Yape en el
  checkout y un estado "pago verificado" que el cajero ve antes de entregar.

### A5 · El carrito solo se vacía si el cliente llega a `/pedido-confirmado`
`pedido-confirmado.html` ejecuta `MusasCarrito.vaciar()` en un `<script>`. Si el
`POST /compra` tiene éxito pero el cliente cierra la pestaña / pierde conexión antes
de que cargue esa página, el carrito sigue lleno.

- **Problema:** el cliente vuelve, ve el carrito con lo mismo y puede pedir dos veces.
- **Arreglo:** marcar en la sesión `session["limpiar_carrito"] = True` al crear el
  pedido (ya existe ese mecanismo en [base.html](templates/client/base.html) para el
  logout, viene de `autenticacion.py:209`), así el vaciado ocurre en el siguiente
  render pase lo que pase. Mantener también el vaciado en `pedido-confirmado`.
- **Archivos:** [controllers/cliente.py](controllers/cliente.py) (`_procesar_compra`,
  antes del `redirect`).

### A6 · Pedidos que la cocina nunca marca "listo" quedan zombis
`_auto_no_show()` solo marca no-show los pedidos que llegaron a `estadoPrep = PREP_LISTO`.
Si la cocina se olvida de avanzar un pedido, se queda "preparando" para siempre:
ocupa cupo de su franja, nunca se auto-limpia y no aparece como problema en ningún lado.

- **Arreglo:** en el dashboard y en el panel de Pedidos, una sección **"Vencidos sin
  resolver"** = pedidos de hoy no recogidos cuya `horaRecojo` ya pasó hace > X min y
  que **no** están listos. El admin decide: cancelar, no-show o entregar igual.
- **Archivos:** [model/Pedido.py](model/Pedido.py) (`resumen_dashboard`,
  `pedidos_de_hoy`), [templates/admin/dashboard.html](templates/admin/dashboard.html),
  [templates/admin/pedidos/index.html](templates/admin/pedidos/index.html).

### A7 · La ventana de cancelación del cliente depende de la rapidez de la cocina
El cliente solo puede cancelar mientras `estadoPrep = 0` (recibido). En cuanto la
cocina pulsa "preparando" pierde esa opción — puede ser 10 s después de pedir.

- **Arreglo:** permitir cancelar durante los primeros **N minutos** desde que se creó
  el pedido *aunque* la cocina ya lo haya tomado (salvo que ya esté "listo"). O al
  revés: que "preparando" no se pueda pulsar hasta X min después de creado. Elegir una.
- **Archivos:** [model/Pedido.py](model/Pedido.py) (`cancelar_pedido`) — hace falta la
  columna `fechaHoraPedido`/`creadoEn` con hora real (hoy solo hay `fechaPedido` DATE).

### A8 · "Ventas de hoy" del dashboard ≠ dinero realmente cobrado
`resumen_dashboard()` calcula `ventas_hoy` = suma de `detalleOrden.precioTotal` de
**todos** los pedidos de hoy no cancelados (incluidos los pendientes que aún nadie
pagó). El módulo de Ventas (comprobantes) solo cuenta lo entregado/cobrado.

- **Problema:** los dos números no cuadran y "ticket promedio" mezcla pedidos pagados
  y no pagados.
- **Arreglo:** o renombrar el KPI a **"Valor de pedidos de hoy"**, o calcularlo desde
  `comprobante` (dinero de verdad). Recomiendo mostrar los dos: "Pedidos de hoy: S/ X"
  y "Cobrado: S/ Y".
- **Archivos:** [model/Pedido.py](model/Pedido.py) (`resumen_dashboard`).

### A9 · Se calcula IGV en toda "nota de venta"
`_emitir_comprobante` siempre hace `sub_total = total / 1.18` e `igv = total - sub_total`,
tanto para la boleta (`B001`) como para la nota de venta interna (`NV01`). Una nota de
venta interna normalmente **no** desglosa IGV.

- **Arreglo:** si `boleta` es falso, guardar `igv = 0` y `subTotal = total`, y que la
  plantilla del comprobante no muestre la línea de IGV para `NV01`. Confirmar con quien
  pide el proyecto qué representa cada documento.
- **Archivos:** [model/Pedido.py](model/Pedido.py) (`_emitir_comprobante`),
  [templates/client/comprobante.html](templates/client/comprobante.html),
  [services/comprobante_pdf.py](services/comprobante_pdf.py).

### A10 · Redondeo `float` al crear el pedido vs `Decimal` al emitir
`_procesar_compra` calcula `precio_unidad = round(p["precio"] + cremas_extra, 2)` con
`float`, y `crear_pedido_completo` lo inserta en columnas `DECIMAL(12,2)`.
`_emitir_comprobante` en cambio usa `dinero()` (Decimal, `ROUND_HALF_UP`).

- **Problema:** diferencias de 1 céntimo entre lo que ve el cliente al pedir y lo que
  sale en el comprobante en pedidos con varias cremas.
- **Arreglo:** usar `dinero()` también en `_procesar_compra` (importar de `dinero.py`)
  para armar `precioUnidad` / `precioTotal`.
- **Archivos:** [controllers/cliente.py](controllers/cliente.py),
  [model/Producto.py](model/Producto.py) (`precios_por_ids`).

### A11 · `keyPedido` sin restricción única en la BD
`crear_pedido_completo` busca una clave de 4 dígitos libre entre los pedidos con
`estadoRecojo = 0` con un bucle de 40 intentos, pero `registroPedido.keyPedido` es
`smallint(6)` **sin índice UNIQUE**. Si el bucle se agota (mucha concurrencia) inserta
una clave repetida sin error.

- **Arreglo:** índice único parcial no existe en MariaDB, así que: subir el rango a
  6 dígitos, o validar en `marcar_recogido` que la `(idPedido, key)` sea exacta (ya lo
  hace: el `UPDATE` lleva `AND keyPedido = %s AND idPedido = %s`) — con eso el riesgo
  real es bajo, pero conviene registrar en la bitácora que la clave **no** es única y
  por eso el cajero siempre teclea también el N° de pedido.
- **Archivos:** [model/Pedido.py](model/Pedido.py) (`crear_pedido_completo`).

### A12 · Se pueden pegar cremas a productos que no las admiten (POST directo)
El JS solo muestra cremas para `CATEGORIAS_CON_CREMAS = ("Hamburguesas", "Salchipapas")`,
pero `_procesar_compra` acepta cualquier `idCrema` válido de la categoría "Cremas" y lo
adjunta a cualquier línea. Un `POST` manual puede mandar "Cremas" con una Bebida.

- **Problema:** integridad de datos (el comprobante mostraría "Gaseosa + Ají de la
  casa"). No hay fraude de precio grave porque la crema se cobra igual, pero ensucia.
- **Arreglo:** en `_procesar_compra`, adjuntar cremas solo si
  `p["nombreCategoria"] in CATEGORIAS_CON_CREMAS`.
- **Archivos:** [controllers/cliente.py](controllers/cliente.py) (`_procesar_compra`).

### A13 · DNI editable libremente + `dniNoRegistrado` mal nombrado
En "Mi cuenta" el cliente puede cambiar su DNI cuando quiera (`Usuario.actualizar_perfil`)
sin verificar que no exista ya en otra cuenta. Y `registroPedido.dniNoRegistrado`
hoy guarda **siempre** el DNI de quien recoge (registrado o no), así que el nombre de
la columna miente.

- **Arreglo:** validar DNI único al actualizar el perfil; documentar (o renombrar en
  una migración futura) `dniNoRegistrado` → `dniRecojo`.
- **Archivos:** [model/Usuario.py](model/Usuario.py), [controllers/cliente.py](controllers/cliente.py).

### A14 · El checkout y el carrito no funcionan sin JavaScript
`carrito.html` (`#carrito-lleno`) y `compra.html` (`#ck-contenido`) arrancan con
`hidden` y solo se muestran cuando el JS los pinta desde `localStorage`. Sin JS
(o si el JS revienta) el cliente ve una página en blanco y no puede pedir.

- **Arreglo:** no es realista renderizar el carrito en el servidor (vive en el
  navegador), pero sí poner un `<noscript>` claro ("necesitas activar JavaScript para
  armar tu pedido") y un fallback visible si a los ~2 s el carrito sigue oculto.
- **Archivos:** [templates/client/carrito.html](templates/client/carrito.html),
  [templates/client/compra.html](templates/client/compra.html).

### A15 · "No hay franjas" cuando en realidad el local está cerrado
Fuera del horario, `franjas_recojo()` devuelve todo como `motivo: "pasada"` y la
plantilla dice *"cocina llena o sin tiempo suficiente para preparar tu pedido"*. El
motivo real es "estamos cerrados".

- **Arreglo:** si `estado_local()["abierto"]` es falso, mensaje específico: *"Ahora
  estamos cerrados. Abrimos {{ horario_hoy }}."* y ofrecer avisar / volver luego.
  (De paso, evaluar permitir **pre-pedir para el día siguiente** — hoy solo se puede
  pedir para hoy.)
- **Archivos:** [templates/client/compra.html](templates/client/compra.html),
  [controllers/cliente.py](controllers/cliente.py) (`pag_compra`).

---

## B. UI/UX y espacios en blanco

### B1 · Causa raíz de la asimetría: cada página tiene un ancho distinto  ⚠️ importante
No hay un contenedor único. Hoy conviven:

| Zona | max-width |
|---|---|
| navbar / footer `.inner` | 1440 px |
| `.musa-shell` (home, carta) | 1320 px |
| hero `.musa-hero__inner`, catbar | 1200 px |
| `.cx-wrap` (carrito, checkout, mis-pedidos, comprobante) | 1240 px |
| `.dp-wrap` (detalle producto) | 1000 px |
| `#mis-pedidos` | 760 px |
| `.conf-wrap` (confirmación) | 720 px |
| `.adm-content` (panel) | 1440 px |

- **Efecto:** en pantallas anchas el contenido "salta" de ancho y de margen al navegar,
  el hero queda **indentado ~60 px** respecto de las secciones de abajo, y sobran
  franjas de crema a los lados que se ven como huecos.
- **Arreglo:** un token `--musa-ancho: 1200px` y una sola clase `.musa-container`
  (`max-width: var(--musa-ancho); margin-inline: auto; padding-inline: clamp(16px, 4vw, 40px)`).
  Migrar `.musa-shell`, `.cx-wrap`, hero y catbar a ese contenedor. Dejar solo dos
  anchos legítimos: el general (1200) y el "lectura" (720, para confirmación y
  comprobante). El navbar/footer pueden seguir a 1440 pero su contenido interno
  alineado al de 1200.
- **Archivos:** [static/css/musas-theme.css](static/css/musas-theme.css)
  (`:root`, líneas 93, 171, 459, 486, 542, 1233, 1025, 1534, 1598, 1849).

### B2 · No hay ritmo vertical: cada sección trae su propio padding
`.musa-anatomia` 76px, `.musa-favs` `padding-top:60px`, `.musa-pilares` `margin:64px 0`,
`.musa-promo`/`.musa-explora`/`.musa-local` cada una lo suyo. Mezcla de secciones
full-bleed y secciones dentro de `.musa-shell`.

- **Arreglo:** escala de espaciado (`--esp-1: 8px … --esp-7: 96px`) y **una sola**
  utilidad de sección (`.musa-seccion { padding-block: var(--esp-7) }`). Alternar
  fondo (crema / blanco) para separar en vez de aire vacío.

### B3 · Contenido repetido y "de relleno" en la home y la carta
`musa-pilares` (Angus / Brioche / Brasas) aparece **igual** en `index.html` y en
`carta.html`. La promo *"2x1 en Cervezas Artesanales"* está **hardcodeada** en la
plantilla y no corresponde a ninguna promo real ni a productos de la BD. El bloque
"Cómo funciona" (3 pasos) y "Pilares" ocupan mucho alto sin aportar en la carta.

- **Arreglo:** en la carta quitar "Cómo funciona" y dejar los pilares solo en la home.
  Sustituir la promo hardcodeada por: (a) un bloque real alimentado por un producto
  marcado como destacado/oferta, o (b) quitarla. Rellenar el hueco de la home con algo
  con sustancia: reseñas cortas, foto real del local, "los favoritos de esta semana"
  (ya tienes `Producto.destacados`).

### B4 · Checkout: la columna derecha corta deja un hueco grande
`.ck-grid` es `1.4fr / 1fr` con `align-items: start`. La columna izquierda (datos +
pago + notas) es larga; el resumen de la derecha es corto y deja medio metro de crema
debajo.

- **Arreglo:** `position: sticky; top: calc(var(--musa-nav-h) + 16px)` en `.ck-summary`
  (y en `.cart-summary`) para que el resumen "acompañe" el scroll; en móvil, resumen
  arriba colapsable o barra fija inferior con el total + botón (como ya hace el detalle
  de producto con `.dp-mobile-bar`).
- **Archivos:** [static/css/musas-theme.css](static/css/musas-theme.css) (líneas 1246,
  1417), [templates/client/compra.html](templates/client/compra.html).

### B5 · "Mis pedidos": la línea de tiempo se ve vacía y descentrada
`#mis-pedidos` ya está a 760px (bien), pero la `.mp-timeline` de 4 pasos con solo
puntos y etiquetas cortas ("Recibido / En cocina / Listo / Recogido") ocupa una banda
ancha con mucho aire entre puntos.

- **Arreglo:** timeline más compacta (línea + 4 nodos con check), horas reales de cada
  hito si las guardas, y estado destacado con color de marca. Que la tarjeta tenga
  jerarquía: N° pedido + estado grande arriba, ítems, total, acciones.

### B6 · Footer: enlaces e íconos muertos
Instagram / TikTok / WhatsApp con `href="#"`; "Términos" y "Política" abren modales
(ok) pero los sociales no llevan a ningún lado.

- **Arreglo:** URLs reales o quitar los íconos. Un footer con enlaces falsos resta
  seriedad al proyecto.

### B7 · Tarjetas de producto de altura desigual
`.producto-grid` con descripciones de largo variable → tarjetas de distinta altura en
la misma fila, el botón "Comprar" queda a distinta altura.

- **Arreglo:** `.producto-card { display:flex; flex-direction:column }` +
  `.producto-card__body { flex:1 }` + `.producto-card__desc` con `min-height` de 2
  líneas (`line-clamp: 2`). Así el pie (precio + botón) queda alineado en toda la fila.

### B8 · El panel arrastra los mismos problemas
`.adm-content` a 1440 (más ancho que la tienda a 1200) y varias tablas ocultan
columnas en pantallas medianas (`.adm-reciente__hora`, `.adm-reciente__dni`,
`.ped-*`). El dashboard tiene 3 secciones apiladas con mucho aire.

- **Arreglo:** alinear el panel al mismo `--musa-ancho`, y en el dashboard usar una
  grilla de 2 columnas para KPIs + gráfico en pantallas grandes en vez de 3 bloques a
  todo el ancho.

### B9 · Plan concreto de layout (orden sugerido)
1. Tokens en `:root`: `--musa-ancho`, `--musa-ancho-lectura`, escala `--esp-*`.
2. Clase `.musa-container` + `.musa-seccion`; migrar `.musa-shell` a alias de
   `.musa-container` (no romper plantillas).
3. Unificar hero y catbar al mismo ancho/padding.
4. `sticky` en los resúmenes de carrito y checkout.
5. Igualar alturas de `.producto-card`.
6. Limpiar contenido de relleno (B3) y footer (B6).
7. Pasar el panel al mismo contenedor.

Cada paso es independiente y reversible con `git revert`. Probar en Chrome, Brave,
Firefox y móvil (ya hay precedente en la sección "Fixes UI 2026-09-09" de la bitácora).

---

## C. La hamburguesa "Anatomía" — de curiosidad a pieza central

### C1 · Por qué hoy se ve pobre
Mirando [index.html](templates/client/index.html) (líneas 32-137),
[musas-theme.css](static/css/musas-theme.css) (3007-3156) y
[animaciones.js](static/js/animaciones.js) (36-75):

1. **El SVG es pequeño y chato.** `viewBox="-60 -6 600 300"` → relación ~2:1, y las
   capas reales ocupan de y≈30 a y≈240. En una celda de grid alta y centrada
   (`align-items: center`) sobra aire arriba y abajo: **eso es el "se ve vacío"**.
2. **El `viewBox` recorta las etiquetas.** Las `.anat-tag` apuntan a `x=-60` y `x=460`,
   justo en el borde del `viewBox` → los textos "Salsa de la casa", "Angus a la brasa"
   quedan pegados al borde o cortados. Y `.musa-anatomia { overflow: hidden }` recorta
   lo que se salga al abrir.
3. **El despiece es tímido.** `translateY(calc(var(--step) * 20px))` con `--step` de
   -3.2 a 3 → separación total ~124px sobre un dibujo de ~210px de alto. Se "abre"
   poquito.
4. **Fondo plano.** Un degradado crema y nada más. Para un "burger joint nocturno"
   la pieza tendría que ser oscura y dramática.
5. **Sin vida en reposo.** Antes de pasar el mouse no pasa nada; el único indicio es
   un pill "Pasa el cursor". No invita.
6. **No tiene protagonismo.** Es media pantalla en una sección más, entre el hero y
   "Cómo funciona".

### C2 · Rediseño visual propuesto
- **Sección full-bleed oscura** (`background: var(--musa-carbon)` con textura sutil /
  vignette), altura ~`min(88vh, 720px)`, la hamburguesa **centrada y grande**
  (60-70% del alto), texto a un lado como sobreimpreso.
- **Escena, no ícono:** una tabla / plato bajo la hamburguesa, sombra de contacto
  real, un halo cálido de brasa detrás (radial naranja desenfocado, ya existe el
  patrón en `.musa-promo::before`), y humo/vapor con 2-3 `<path>` que suben en loop.
- **Dibujo mejor:** rehacer el SVG con más capas y detalle (pepinillos, cebolla
  caramelizada, doble carne opcional), cada capa con su propio `filter: drop-shadow`
  para que al separarse "floten" de verdad. `viewBox` con margen suficiente para las
  etiquetas (p. ej. `-160 -40 820 460`) y **sin `overflow: hidden`** en la sección.
- **Etiquetas de verdad:** línea guía que se "dibuja" (`stroke-dasharray` animado) +
  número (1…6) + nombre + micro-nota. Aparecen escalonadas al abrir. En pantallas
  chicas → la lista `.anat-lista` que ya tienes (mantener el fallback).
- **Contador / gancho:** "6 capas · montadas a mano cada tarde" y CTA "Probar la
  original" bien visible.

### C3 · Animación propuesta
- **Reposo (idle):** cada `.anat-capa` flota en loop con un `@keyframes` suave
  (`translateY` ±3px) y `animation-delay` distinto por capa (efecto "respira").
  El humo sube en loop. Nada agresivo.
- **Al activarse** (hover en desktop, o entrar al viewport en móvil/scroll):
  - separación mayor (`--step * 34px`), con `cubic-bezier` elástico (ya usas
    `cubic-bezier(.34,1.3,.4,1)`, subir un poco el rebote).
  - leve inclinación 3D: envolver el SVG en un contenedor con
    `perspective: 1200px` y aplicar `rotateX(8deg)` al abrir → se ve "explosión"
    en vez de solo subir/bajar.
  - etiquetas: `opacity` + `stroke-dashoffset` → 0 escalonado (`transition-delay`
    por capa, ya tienes `--d`).
- **Opción "scroll-scrub" (la más llamativa):** el despiece sigue el scroll. Con
  `IntersectionObserver` + un handler de `scroll` que calcula el progreso de la
  sección (0→1) y lo mete en una CSS var `--abierto`; las capas interpolan
  `translateY(calc(var(--step) * var(--abierto) * 34px))`. La hamburguesa se arma y
  se desarma mientras haces scroll por la sección. Es el patrón "Apple AirPods".
  Cae de pie sin librería; con `will-change: transform` va fluido.
- **`prefers-reduced-motion`:** igual que hoy — hamburguesa **armada**, sin flotación,
  se muestra `.anat-lista`. Ya está resuelto en el CSS (líneas 3270-3283), mantenerlo.

### C4 · Compatibilidad (el motivo del bug de Brave)
- Mover el despiece con **JS además de `:hover`** (ya se hace desde el fix anterior):
  añadir/quitar una clase en el `<button>`, no depender de que el navegador propague
  `:hover` a los `<g>`. Mantener.
- `transform` en elementos SVG `<g>`: soportado en todos los navegadores objetivo,
  pero si se quiere el `rotateX` 3D, aplicarlo al **contenedor HTML** del SVG, no a un
  `<g>` (Safari/WebKit es irregular con `perspective` dentro de SVG).
- El humo y el halo: SVG/CSS puros, sin `filter` de SVG pesado (Brave con escudos a
  veces los bloquea) — usar `filter: blur()` de CSS y `drop-shadow`.
- Probar `will-change` solo mientras la sección está en viewport (quitarlo al salir)
  para no cargar memoria en móvil.

### C5 · Pasos de implementación
1. Sacar la sección de la home a un `include` propio (`_anatomia.html`) para iterar sin
   tocar el resto de `index.html`.
2. Rehacer el SVG (más capas, `viewBox` con margen, `drop-shadow` por capa).
3. Sección oscura full-bleed + halo + plato + humo en CSS.
4. Idle float en CSS.
5. `animaciones.js`: sustituir el IIFE de "Anatomía" por el de scroll-scrub
   (mantener el fallback táctil y `prefers-reduced-motion`).
6. Etiquetas con línea que se dibuja.
7. QA en Chrome / Brave (con escudos) / Firefox / iOS Safari / Android.

**Alcance sugerido:** C1-C3 y C5.1-5.4 primero (impacto visual alto, riesgo bajo). El
scroll-scrub (C3 opción) como segunda pasada.

---

## D. Prioridad

| # | Tema | Impacto | Esfuerzo | Riesgo | Cuándo |
|---|---|---|---|---|---|
| A1 | Reloj/zona horaria consistente | Alto (deploy) | Medio | Medio | Antes de subir a un servidor |
| A2 | Cupo de franja en la transacción | Alto | Bajo | Bajo | Ya |
| A3 | Total del checkout fiable | Alto (confianza) | Medio | Bajo | Ya |
| A5 | Vaciar carrito vía sesión | Medio | Bajo | Bajo | Ya |
| A12 | Cremas solo en categorías válidas | Medio | Bajo | Nulo | Ya |
| B1 | Contenedor y ancho único | Alto (lo que se ve) | Medio | Bajo | Sprint UI |
| B2/B3 | Ritmo vertical + quitar relleno | Alto | Medio | Bajo | Sprint UI |
| B4 | Resúmenes `sticky` | Medio | Bajo | Nulo | Sprint UI |
| B7 | Alturas de tarjetas | Medio | Bajo | Nulo | Sprint UI |
| C1-C5 | Rediseño Anatomía | Alto (marca) | Alto | Medio | Sprint dedicado |
| A4/A9/A15 | Copys y semántica de pago/IGV/cerrado | Medio | Bajo | Bajo | Con el sprint UI |
| A6 | "Vencidos sin resolver" en el panel | Medio | Medio | Bajo | Después |
| A7 | Ventana de cancelación | Bajo | Medio (migración) | Medio | Después |
| A8 | KPI ventas vs cobrado | Bajo | Bajo | Bajo | Después |
| A10/A11/A13/A14/B5/B6/B8 | Deuda menor | Bajo | Bajo | Bajo | Oportunista |

## E. Qué NO tocar
- El esquema de la BD sin migración numerada (ver bitácora sección 3).
- `seguridad.py` / CSRF sin avisar al otro dev.
- El módulo de comprobantes/ventas es del compañero (Codex): coordinar A9 con él.
- No meter frameworks JS ni build step — la regla del proyecto es CSS/JS a mano.
