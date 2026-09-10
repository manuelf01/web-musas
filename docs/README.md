# docs/

## `arquitectura.html`

Diagrama de arquitectura del proyecto. **Abrir con doble clic** en el navegador
(no necesita servidor ni dependencias). Tiene 4 vistas guiadas:

1. **Flujo de compra** — del navegador al pedido guardado (carrito en `localStorage`,
   el servidor re-cotiza en `/compra`).
2. **Panel de administración** — cocina, ventas y los CRUD.
3. **Seguridad** — CSRF de sesión en cada POST, captcha del panel, `pbkdf2:sha256`.
4. **Comprobante PDF** — al entregar el pedido se emite el comprobante y se congela
   un snapshot (`datosEmision`) para el PDF.

### Regenerar

La fuente es [`arquitectura.archify.json`](arquitectura.archify.json). Se genera con
la skill [`tt-a1i/archify`](https://github.com/tt-a1i/archify) (MIT, Node ≥ 18):

```bash
# desde una copia de tt-a1i/archify
node bin/archify.mjs validate architecture <ruta>/docs/arquitectura.archify.json --quality showcase
node bin/archify.mjs deliver  architecture <ruta>/docs/arquitectura.archify.json <ruta>/docs/arquitectura.html --quality showcase
```
