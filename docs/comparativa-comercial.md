# Comparativa con apps comerciales — ¿nuestro método de compra/venta se sostiene?

> Revisión 2026-09-09. Contrasta el flujo de web-musas con cómo resuelven lo mismo
> **PedidosYa**, **Rappi** y sobre todo **OlaClick** (el SaaS que usan muchos
> restaurantes en Perú para "pedido para recojo + pago en el local", que es
> exactamente nuestro modelo). Restricción del cliente: **sin pasarela de pago,
> se paga al recoger.** Complementa [`../PLAN-MEJORAS.md`](../PLAN-MEJORAS.md).

---

## 1. Veredicto

**El modelo se sostiene.** "Recojo en tienda + hora reservada + pago en caja
(efectivo / tarjeta / Yape / Plin) + control de no-shows" es exactamente el modo
"pickup / pago contra entrega" de OlaClick y de la mayoría de hamburgueserías
peruanas que no usan pasarela. La mecánica interna está bien resuelta: precio
congelado en `detalleOrden`, stock reservado al crear el pedido, comprobante
emitido al cobrar, CSRF, throttle de login, franjas con cupo.

**Lo que hace frágil el "pago al recojo" y hay que reforzar** (las apps comerciales
que no cobran por adelantado se apoyan justo en esto):

| Riesgo | Cómo lo cubre una app comercial | Estado en web-musas |
|---|---|---|
| El cliente no viene (no-show) | Verificación de teléfono, penalización/bloqueo por historial, tarjeta en archivo | Cuenta `noShows` y auto-marca… **pero nada la usa**. `MAX_PEDIDOS_ACTIVOS=2` es otra cosa (pedidos sin recoger a la vez, no historial). |
| La cocina se satura | Botón "pausar tienda" / "no aceptar pedidos" | **No existe.** Solo se frena cuando se llenan los cupos de la franja. |
| El cliente no se entera de que está listo | Push / SMS / WhatsApp | La UI promete *"te avisaremos por WhatsApp"* pero **no hay ningún aviso**; solo la página de seguimiento si la deja abierta. |

Resolviendo esos tres puntos, el modelo es viable para una sede en producción.

---

## 2. Recorrido del cliente, paso a paso

### 2.1 Carta / descubrimiento
Comercial: agregar al carrito **desde la lista** con un "+", foto por producto,
"lo más pedido", agotados en gris, combos armables.

En web-musas:
- ✅ Categorías, buscador, orden, favoritos, placeholders por categoría.
- ⚠️ **Todo producto obliga a entrar a su página de detalle.** Para una hamburguesa
  con cremas tiene sentido; para una **bebida / postre / combo** es fricción pura.
  PedidosYa/Rappi resuelven eso con un "+" en la tarjeta.
  → *Agregar rápido desde `_producto_card.html` para productos sin personalización.*
- ⚠️ **Un producto con `existencias = 0` se ve normal** en la carta; recién en el
  detalle dice "Agotado". Comercial lo pinta en gris con "Agotado" en la tarjeta.
  → *Badge "Agotado" en `_producto_card.html` cuando el stock es 0.*
- ⚠️ **Combos** existen como producto suelto, no como "arma tu combo"
  (hamburguesa + papas + bebida con descuento), que es lo que empujan las apps.
- 📷 Faltan fotos reales en bebidas, postres y cremas. Contenido, pero pesa: las
  apps comerciales son muy foto-primero.
- 🗑️ Sigue el producto basura **"Internet — S/ 30.00"** en la BD (categoría
  Hamburguesas). Borrarlo.

### 2.2 Carrito
Comercial: carrito atado a la cuenta (cross-device), editar personalización,
upsell, mínimo de pedido, total con impuestos.

En web-musas:
- ✅ Carrito en `localStorage`, upsell "Completa tu pedido", IGV visible, editar
  cantidad, re-cotiza contra la BD en `/compra` (arreglado en Bloque A).
- ⚠️ **El carrito vive solo en ese navegador.** Empiezas en el celular, terminas
  en la laptop → carrito perdido. Comercial lo ata a la cuenta.
  → *Guardar el carrito por usuario en la BD (sin pasarela, es solo persistencia).*
- ⚠️ **Para cambiar las cremas hay que quitar la línea y volver a agregar.**
- ❓ **No hay mínimo de pedido.** Un pedido de 1 crema de S/ 1 ocupa un cupo de
  franja igual que uno de S/ 80. Definir con el cliente si se pone un mínimo
  (p. ej. S/ 12) o se deja así a propósito.

### 2.3 Checkout y hora de recojo
Comercial (recojo): "Lo antes posible (~20 min)" **primero y destacado**, luego
"programar". Nombre + teléfono. Método de pago (acá: en el local). Notas.

En web-musas:
- ✅ Franjas de 30 min con cupo (como OlaClick), boleta opcional, medio de pago,
  notas, mensaje "cerrado" correcto (Bloque B).
- ⚠️ **Pide DNI en todos los pedidos.** Ninguna app comercial pide DNI para pedir
  una hamburguesa. Está para el no-show y la boleta. Pero: si el cliente está
  logueado ya tenemos su DNI; y si no quiere boleta, nombre + teléfono alcanzan.
  → *Pedir DNI solo si marca "quiero boleta"; el resto, precargado o sin DNI.*
- ⚠️ **No hay "Lo antes posible".** Todas las franjas son horarios fijos. El código
  ya calcula la primera libre y le pone "Antes posible" como etiqueta chica, pero
  no está presentado como el botón principal.
  → *Botón grande "Lo antes posible (~20 min)" que elige la franja más cercana.*
- ⚠️ **Solo se puede pedir para hoy.** No hay pre-pedido para mañana / días
  siguientes (comercial sí). Menor para un local nocturno, pero anotarlo.
- ⚠️ El teléfono **no se verifica** (sin OTP). El no-show se rastrea por cuenta
  (`idUsuario`), así que es aceptable, pero el teléfono de "quien recoge" es libre.

### 2.4 Pago — la restricción del cliente
Comercial sin pasarela (OlaClick, pedidos por WhatsApp): la app **solo registra**
el medio de pago que el cliente elige; el local cobra al entregar. **web-musas hace
exactamente eso** (después del arreglo A4). ✅ Patrón validado.

Ideas que **no** son pasarela y reducen el no-show:
- **Pre-pago opcional por Yape/Plin con captura.** El cliente que quiere, sube la
  foto de la confirmación de Yape en el checkout; el cajero la ve y la marca como
  verificada antes de entregar. Es una imagen + verificación manual, cero gateway.
- **Tras N no-shows**, exigir que el cliente llame o bloquear pedidos por X días.
  Hoy la cuenta `noShows` sube y **nadie hace nada con ella**.

### 2.5 Confirmación y seguimiento
Comercial: número de pedido, hora estimada, estado en vivo, mapa, "llamar al
local", recibo.

En web-musas:
- ✅ Página de confirmación con palabra clave + N° pedido + hora + local; línea de
  tiempo en vivo en "Mis pedidos" (sondea cada 20 s); comprobante tras el recojo.
- ⚠️ **El aviso "te avisaremos por WhatsApp" no ocurre.** Es una promesa que el
  sistema no cumple. Opciones:
  1. Link **"Escríbenos por WhatsApp"** (wa.me) en la confirmación y el seguimiento
     — cero infraestructura, honesto.
  2. **Notificación del navegador** (Web Push / `Notification` API) cuando el
     pedido pasa a "listo" — el cliente ya tiene la pestaña; con permiso, le
     salta el aviso aunque esté en otra pestaña.
  3. Suavizar el copy a "sigue tu pedido acá" y quitar la promesa de WhatsApp.
- ⚠️ **La palabra clave se dice de viva voz.** Un **QR** con el N° de pedido que el
  cajero escanea es más rápido y sin errores (opcional).
- ⚠️ El seguimiento **exige tener la página abierta** (polling, sin push).

### 2.6 Después del pedido / fidelización
Comercial: reordenar, **calificar**, puntos/loyalty, "pedí de nuevo", favoritos.

En web-musas:
- ✅ "Repetir pedido", historial.
- ⚠️ **No hay calificación ni feedback positivo.** Solo el Libro de Reclamaciones
  (obligatorio en Perú, para quejas). Falta el "¿qué tal tu pedido?" de 1-5
  estrellas que toda app comercial pide tras la entrega. Le da señal al cliente.
- ⚠️ **Sin loyalty** ("la 10ª hamburguesa gratis" / puntos). Es la palanca de
  retención #1 de las apps. Puede que el cliente no lo quiera — preguntarle.
- ⚠️ Sin "pedir lo de siempre" / favoritos por cliente (solo `destacado` que pone
  el admin).

---

## 3. El lado del negocio (cocina + caja)

Referencia: OlaClick, Fudo, PedidosYa Manager.

- ✅ Tablero de cocina en vivo (`pedidos-cocina.js`, sondeo 15 s, pitido + banner),
  máquina de estados recibido → preparando → listo → recogido, dashboard con KPIs,
  módulo de ventas/comprobantes, stock por producto, comprobante PDF con snapshot.
- ⚠️ **No hay "pausar pedidos".** Si la cocina está reventada, no se puede cortar
  la entrada salvo esperar a que se llenen los cupos. Comercial tiene un botón
  grande "pausar tienda". **Es el hueco operativo más importante.**
- ⚠️ **La cocina no puede empujar la hora.** Las franjas son fijas de 30 min; si
  van atrasados no hay forma de decir "la próxima franja disponible es 45 min
  después". OlaClick deja ajustar el tiempo de preparación.
- ⚠️ **No hay cierre de turno / arqueo de caja.** Los comprobantes ya guardan
  `medioPago` e `idCajero`, así que falta poco: un reporte "cierre de turno" con
  total efectivo / tarjeta / Yape / Plin y por cajero. Hoy `Comprobante.kpis()`
  da total/cantidad/ticket **de todo el histórico**, sin filtro de fecha ni
  desglose por medio de pago.
- ⚠️ **La cuenta de no-shows no se aplica** (ver 1 y 2.4).
- ⚠️ "Ventas de hoy" del dashboard suma pedidos **no cobrados** (hallazgo A8 del
  plan, pendiente).
- ℹ️ Sin impresión de ticket de cocina — puede ser a propósito (pantalla), anotarlo.

---

## 4. Prioridad

| # | Mejora | Por qué (comercial) | Esfuerzo | Sin pasarela |
|---|---|---|---|---|
| 1 | Botón **"Lo antes posible"** en el checkout | Es lo primero en PedidosYa/Rappi | Bajo | ✅ |
| 2 | **Pausar pedidos** en el panel | Hueco operativo real | Medio (migración: flag en config/sede) | ✅ |
| 3 | **Aplicar el contador de no-shows** (bloqueo temporal / aviso) | Lo que hace viable el pago al recojo | Bajo-Medio | ✅ |
| 4 | **Aviso real de "listo"** (Web Push o link WhatsApp) + honestar el copy | La promesa incumplida | Medio (push) / Bajo (wa.me) | ✅ |
| 5 | **DNI solo si pide boleta** | Fricción anómala en checkout | Bajo | ✅ |
| 6 | **Agregar rápido desde la carta** (bebidas/postres/combos) | "+" en la tarjeta | Bajo-Medio | ✅ |
| 7 | **Badge "Agotado"** en la tarjeta de producto | Estándar comercial | Bajo | ✅ |
| 8 | **Calificación post-recojo** (1-5 estrellas) | Toda app lo pide | Medio (tabla + vista) | ✅ |
| 9 | **Cierre de turno / caja** (totales por medio de pago y cajero) | Operación diaria | Medio | ✅ |
| 10 | Pre-pago Yape opcional con captura | Baja no-shows sin gateway | Medio (subida de imagen, ya existe `subidas.py`) | ✅ |
| 11 | Carrito por usuario en la BD (cross-device) | Estándar comercial | Medio | ✅ |
| 12 | "Arma tu combo" | Ticket promedio | Alto | ✅ |
| 13 | Loyalty / puntos | Retención #1 | Alto | ✅ (preguntar al cliente) |
| 14 | Fotos reales, arreglar redes del footer, borrar producto basura | Confianza | Bajo (contenido) | ✅ |

**Sugerencia de arranque:** 1, 5, 7 (bajo riesgo, puro front + validación) →
3, 2, 4 (los que sostienen el modelo) → el resto.

---

## 5. Qué NO hacer
- **Pasarela de pago / cobro por adelantado con tarjeta.** El cliente lo descartó y
  el modelo "pago al recojo" es válido para una sede.
- Delivery / reparto. El alcance es recojo en tienda.
- App nativa / notificaciones por SMS pagas. Web Push alcanza.
- Meter un framework JS o build step (regla del proyecto).
- Tocar el esquema sin migración numerada ni el módulo de comprobantes sin avisar
  al compañero (ver `BITACORA-CLAUDE.md` secciones 0 y 3).
