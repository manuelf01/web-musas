-- 008 — el comprobante se emite al entregar el pedido (módulo de Ventas).
-- El DNI debe conservar los 8 dígitos (los DNI peruanos pueden empezar por 0),
-- por eso pasa de INT a CHAR(8) igual que registroPedido.dniNoRegistrado.

UPDATE comprobante SET dniNoRegistrado = LPAD(dniNoRegistrado, 8, '0')
  WHERE dniNoRegistrado IS NOT NULL;

ALTER TABLE comprobante MODIFY dniNoRegistrado CHAR(8) NOT NULL;
