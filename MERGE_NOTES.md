# Integración `Ramirez` + `Manuelf` → `main`

**Fecha:** 2026-09-07

## Qué pasó

El compañero (rama `origin/Manuelf`, commit `4ce46ae`) no subió solo "su parte":
rehízo en paralelo la tienda, el login, el checkout (por API) y el esquema de BD,
con **otro sistema de diseño** (`musas-design.css`) y **migraciones incompatibles**
(su `keyPedido VARCHAR(64)` vs. la palabra clave numérica de 4 dígitos de esta
rama; `precio DECIMAL` vs `FLOAT`; columnas de bloqueo de admin en `usuario`;
sin cancelación ni no-show).

**Decisión (del usuario):** la base es `Ramirez`. Se porta la *lógica* del panel
de administración de `Manuelf` a este diseño y este esquema. No se hace `git merge`
(dejaría dos diseños, dos checkouts y migraciones que se pisan).

## Qué se integró en esta rama

| Trae | De dónde | Estado |
|---|---|---|
| CRUD de **productos** (con subida de imagen) | recuperado de `e779f62` (mi trabajo previo) | ✅ sobre `admin/base.html` |
| CRUD de **categorías** (con imagen) | ídem | ✅ |
| CRUD de **usuarios / administradores** | ídem | ✅ |
| **Ventas / comprobantes / detalle** con paginación (`flask_paginate`) | ídem + modelos originales `Comprobante`, `DetalleComprobante` | ✅ |
| Generación del **comprobante al entregar** el pedido (`Pedido._emitir_comprobante`, llamado en `marcar_recogido`) | recuperado de `e779f62` | ✅ el pago es al recojo, así que la venta se registra ahí |
| `subidas.py` (guardar/validar imágenes) | recuperado | ✅ JPG/PNG/WEBP, verifica contenido con Pillow |
| Migración **007** (`categoriaProducto.imagen`) | recuperada | correr en BD |
| Migración **008** (`comprobante.dniNoRegistrado` → CHAR(8)) | nueva | correr en BD |

## Qué NO se tomó de `Manuelf` (y por qué)

- Su **diseño de panel** (`admin/main.html`, `musas-design.css`) → se usa el sidebar
  oscuro Neo-brasa de esta rama.
- Su **auth de admin** (usuario generado `m74228`, bloqueo en BD, Flask-JWT-Extended,
  `scripts/crear_admin`) → se mantiene el login unificado por DNI + captcha + throttle
  en memoria de esta rama.
- Su **checkout por API** (`Transaccion.py`, `comprarProductos.js`) → se mantiene el
  checkout server-rendered con re-cotización y control de stock/cupo/no-show.
- Sus **migraciones 001–002** → esta rama usa 001–008. La columna
  `registroPedido.nombres` la añaden ambas (compatible).
- `precio DECIMAL(10,2)` → se mantiene `FLOAT NOT NULL` (migración 005). Todo el
  código castea con `float()`. Cambiar a DECIMAL es una mejora futura, no bloquea.
- Sus cambios masivos a `APIS/*` y modelos `Autenticacion`/`Transaccion` → no se
  tocaron las APIs de esta rama.

## Estado de las migraciones (para el asesor / BD limpia)

Correr **en orden**, una sola vez, con phpMyAdmin o pymysql (el cliente `mysql`
rompe la `ñ` de `contraseña`; usar `--default-character-set=utf8mb4` si es por CLI):

```
migrations/001_ampliar_contrasena.sql
migrations/002_producto_imagen_destacado.sql
migrations/003_producto_nota.sql
migrations/004_registroPedido_nombres_notas.sql
migrations/005_producto_precio_stock_no_nulo.sql
migrations/006_cancelacion_y_noshow.sql
migrations/007_categoria_imagen.sql
migrations/008_comprobante_dni.sql
migrations/009_estado_preparacion.sql
migrations/010_roles_y_estado.sql
```

## Roles y estado (2026-09-08)

`usuario.rol`: superusuario / administrador / usuario (+ `usuario.activo`).
`producto.activo` y `categoriaProducto.activo` para "dar de baja". La gestión de
usuarios y la asignación de roles son **solo del superusuario**; los CRUD de
producto/categoría/usuario usan estado en vez de borrar. Perfil editable en
`/admin/perfil` (panel) y `/mi-cuenta` (tienda).

## Estados de pedido (2026-09-08)

`registroPedido.estadoPrep`: 0 recibido · 1 en preparación · 2 listo. El cliente
solo cancela en "recibido"; el admin avanza el estado desde el panel de Pedidos.
Los pedidos son **solo de usuarios registrados** (se quitó el checkout de invitado
y su captcha).

## Flujo de entrega

1. Un solo PR `Ramirez` → `main`. El asesor revisa y mergea.
2. La rama `Manuelf` queda como referencia del trabajo del compañero; su lógica de
   panel está integrada aquí (atribución conjunta en el commit de integración).
3. Nadie commitea directo a `main`.
