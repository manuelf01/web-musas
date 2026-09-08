# Notas para integrar `Ramirez` + `Betancurt` → `main`

**Fecha:** 2026-09-07

## División acordada

| Zona | Dueño |
|---|---|
| Tienda (inicio, carta, detalle, carrito, checkout, mis pedidos) | Ramirez |
| Login / registro unificado + captcha + contraseñas cifradas | Ramirez |
| CRUD de **pedidos** + dashboard + layout del panel (`admin/base.html`) | Ramirez |
| Infra: diseño (`musas-theme.css`), seguridad (CSRF), migraciones 001–006, anti no-show, animaciones | Ramirez |
| CRUD de **productos, categorías, usuarios, ventas, reportes, detalle de venta, comprobantes** | **Betancurt** |

## Qué se REVIRTIÓ en `Ramirez` para no tocar lo de Betancurt (2026-09-07)

Todos estos archivos están **idénticos a `main`** en la rama `Ramirez`:

- `controllers/admin_productos.py`
- `controllers/admin_categoria_producto.py`
- `controllers/admin_usuarios.py`
- `controllers/admin_ventas.py`
- `templates/admin/productos/` (index, agregar_producto, editar_producto)
- `templates/admin/categoria/` (index, agregar, editar)
- `templates/admin/usuarios/` (index, agregar, editar)
- `templates/admin/ventas/` (index, detalle_comprobante)
- `templates/admin/main.html` (restaurado — las 4 pantallas de arriba lo extienden)
- `static/js/admin/pedidos.js` (restaurado)
- `model/CategoriaProducto.py` (idéntico a `main`)

También se quitó de `Ramirez`:
- **Migración 007** (`categoriaProducto.imagen`) — es del módulo de categorías de Betancurt.
- De la **migración 006** se quitaron los cambios a `comprobante` (`dniNoRegistrado CHAR(8)`).
  006 ahora solo toca `registroPedido` y `usuario`.
- `subidas.py` (subida de imágenes de producto/categoría) — feature del panel de Betancurt.
- La generación de `comprobante` / `detalleComprobante` en `model/Pedido.py`
  (`_emitir_comprobante`) — pertenece al módulo de Ventas de Betancurt.

## Cosas transversales que SÍ afectan la zona de Betancurt

1. **CSRF**: `app.py` valida un token en todos los POST de formulario. Los blueprints
   `admin.productos`, `admin.categoria`, `admin.usuarios`, `admin.ventas` están **exentos
   temporalmente** (ver `_CSRF_MODULOS_PENDIENTES` en `app.py`).
   → Al integrar, Betancurt debe poner `{{ campo_csrf() }}` dentro de cada `<form method="post">`
   suyo y quitar esos blueprints de la lista de exentos.

2. **Auth del panel**: `controllers/admin.py` → `before_request` ahora **exige** estar
   logueado como admin (antes el panel estaba abierto sin login). Esto protege también
   las rutas de Betancurt — es correcto, no hay que revertirlo.

3. **Migraciones que corren columnas de `registroPedido`** (las necesita la tienda):
   - 004 agrega `nombres` (posición 3) y `notas` (final).
   - 006 agrega `cancelado` y `noShow` (posiciones 6 y 7).
   - **Efecto:** cualquier código que lea filas de `registroPedido` por índice numérico
     (`fila[8]`, `fila[9]`…) más allá de la posición 5 queda corrido.
   - El código de Betancurt en `admin_ventas.show_detalle` hace `datos_comprobante[9]`
     para "forma de pago" → tras las migraciones eso ya no es `billeteraDigital`
     (ahora está en `[11]`). **Betancurt debe usar nombres de columna o ajustar el índice.**

4. **`model/Producto.py`, `model/Usuario.py`**: la rama `Ramirez` los amplió (métodos que
   usa la tienda: `destacados`, `precios_por_ids`, `contar_por_categoria`, columnas
   `imagen/destacado/nota` en los SELECT; hash de contraseña en `insertar_usuario`).
   Las firmas de `insertar_producto` / `actualizar_producto` / `insertar_categoria` /
   `actualizar_categoria` se dejaron **igual que en `main`** (sin parámetro `imagen`),
   así que el código revertido de Betancurt las llama sin problema.
   → Si Betancurt reescribe estos modelos, hay que fusionar: su versión de los métodos
     de CRUD + los métodos nuevos que usa la tienda.

5. **Comprobante al recoger vs al pedir**: la tienda de `Ramirez` registra en
   `registroPedido` los flags `estadoBoleta` y `billeteraDigital`. El módulo de Ventas
   de Betancurt decide **cuándo** generar el `comprobante` (al entregar el pedido en
   `Pedido.marcar_recogido`, o desde su propio flujo) y **con qué esquema** de tabla.

## Flujo de merge recomendado

1. Betancurt sube su código: `git push origin Betancurt`.
2. En `Ramirez`: `git merge origin/Betancurt`.
   - Los archivos revertidos NO deberían dar conflicto (están iguales a `main`).
   - Si dan conflicto, **gana la versión de Betancurt** en su zona.
3. Aplicar los 4 puntos transversales de arriba sobre el código de Betancurt.
4. Correr las migraciones 001–006 (ver `migrations/`) + las que traiga Betancurt.
5. Probar: tienda + pedidos + su CRUD + ventas.
6. **Un solo PR `Ramirez` → `main`**. El asesor revisa y mergea. Nadie commitea directo a `main`.
