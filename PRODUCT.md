# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Personal de Las de Siempre:** cajeros y administradores usan el panel durante la operación diaria para recibir pedidos, enviarlos a cocina, registrar entregas y cobros, controlar caja y consultar inventario. El administrador gestiona además los catálogos y operaciones que requieren permisos superiores.
- **Clientes:** usan la tienda web, desde escritorio o móvil, para consultar la carta, personalizar hamburguesas, elegir una hora de recojo, hacer pedidos y seguir su estado.
- **Cocina:** recibe una comanda impresa con el detalle necesario para preparar cada pedido. El flujo del sistema lo actualiza el cajero; no se ha definido una cuenta independiente para cocina.

## Product Purpose

Sistema web para organizar las ventas y la operación de Las de Siempre, hamburguesería en Chiclayo. Conecta el pedido del cliente con su preparación, entrega y cobro, y ofrece al personal registros para administrar caja e inventario. El éxito del producto se mide por la posibilidad de completar y consultar esos flujos con datos relacionados y trazables, de acuerdo con las reglas del negocio.

## Positioning

El sistema concentra en un mismo flujo el pedido para recojo, la comanda de cocina, la validación de entrega y el cobro presencial; sus módulos administrativos vinculan las operaciones de caja e inventario con sus movimientos e historial. Es una herramienta operativa propia del negocio, no una plataforma de delivery ni un procesador de pagos.

## Operating Context

- El negocio opera desde su sede en Chiclayo y el servicio modelado es **recojo en tienda**.
- Cliente confirma el pedido; el personal lo recibe, lo envía a cocina e imprime una comanda; cocina lo prepara; caja lo marca listo, valida la clave de recojo, registra el pago y entrega el pedido.
- El pago se realiza al recoger. Efectivo, tarjeta, Yape y Plin se registran en caja; Yape y Plin se gestionan manualmente y no usan una pasarela integrada.
- El comprobante se emite al entregar el pedido. Cliente y personal autorizado pueden consultarlo y descargar el PDF interno correspondiente.
- El horario de atención y las franjas de recojo se configuran para el negocio. El horario oficial debe confirmarse antes de presentarlo como dato definitivo: las notas del proyecto y la configuración actual del código no coinciden completamente para el sábado.
- La aplicación se desarrolla y prueba localmente en Windows con Python, Flask, MariaDB y XAMPP. La operación pública en la nube no está establecida como parte del entorno actual.

## Capabilities and Constraints

- Tienda de productos activos, personalización, carrito, selección de franjas de recojo, confirmación con clave y seguimiento del pedido. Los pedidos requieren una cuenta de cliente.
- Autenticación diferenciada: clientes ingresan con correo; personal del panel con DNI y captcha. Los roles internos `superusuario`, `administrador` y `usuario` se muestran en la interfaz como **Administrador**, **Cajero** y **Cliente**.
- Flujo de preparación: **Recibido → En cocina → Listo para recojo → Entregado**. El cajero envía el pedido a cocina e imprime la comanda; caja valida la clave y registra el cobro al entregar.
- El comprobante es interno y descargable en PDF. No se emite electrónicamente ni se integra con SUNAT.
- Caja incluye apertura, fondo inicial, aportes, gastos, retiros, conciliación por medio de pago, cierre e historial. Una caja cerrada no se edita; las correcciones deben registrarse como movimientos auditables.
- Inventario representa productos terminados. Los cambios de saldo se registran en Kardex y se vinculan con pedidos, compras, devoluciones o ajustes. Proveedores y recepción de compras actualizan las existencias y el costo promedio ponderado.
- Las devoluciones distinguen productos reincorporables de productos no vendibles o merma. Una hamburguesa devuelta no debe reincorporarse automáticamente al inventario disponible.
- La aplicación usa Flask y MariaDB; la interfaz web se sirve con plantillas Jinja, CSS propio y JavaScript sin framework. Bootstrap 5.2.3 aporta utilidades y componentes puntuales.
- La interfaz debe funcionar en escritorio y móvil. Los permisos dependen del rol; las operaciones de caja e inventario conservan responsable e historial.
- No forman parte del alcance definido: delivery, pasarela de pago, integración SUNAT, inventario de insumos y recetas, cupones ni programa de puntos.
- Se pueden administrar datos reales de contacto, catálogo y cobro mediante la configuración correspondiente. No inventar números de pago, QR, datos tributarios, precios, testimonios, métricas comerciales ni horarios oficiales.

## Brand Commitments

- El nombre comercial confirmado es **Las de Siempre**.
- El proyecto cuenta con un símbolo de hamburguesa vectorial en `static/img/marca/v1/simbolo.svg` y con fotografías de productos en `static/img/`. Debe conservarse la identidad existente salvo que el usuario apruebe un cambio de marca.

## Evidence on Hand

- El repositorio contiene las vistas de tienda y panel, la lógica de pedidos, caja e inventario, y los datos del negocio centralizados en `negocio.py`.
- `sql.sql` contiene el esquema y los datos de catálogo usados para crear el entorno local de desarrollo; estos datos no deben tratarse como métricas de ventas reales.
- Hay un símbolo SVG de marca y fotografías de menú en el repositorio. No se han proporcionado testimonios, estudios de mercado, benchmarks ni una línea base cuantitativa de ventas o tiempos operativos.

## Product Principles

1. Mantener conectado el pedido con su preparación, entrega y cobro.
2. Hacer visible al usuario qué debe hacer y cuál es el estado de su pedido u operación.
3. Conservar trazabilidad de caja e inventario: registrar correcciones como movimientos, no borrar operaciones confirmadas.
4. Aplicar permisos según la responsabilidad de cada rol y exponer solo las acciones necesarias para su tarea.
5. Priorizar un flujo claro de recojo en tienda, en escritorio y móvil, sin prometer funciones que el negocio no ofrece.

## Accessibility & Inclusion

- La tienda debe ser utilizable desde teléfonos y computadoras, con formularios y estados comprensibles para clientes y personal.
- La interfaz contempla preferencias de movimiento reducido. No se ha acordado todavía un nivel de conformidad WCAG específico.
