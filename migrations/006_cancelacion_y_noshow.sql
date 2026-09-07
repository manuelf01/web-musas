-- 006 — cancelación de pedidos + control de "no recogió" (anti no-show).

ALTER TABLE registroPedido
  ADD COLUMN cancelado TINYINT(1) NOT NULL DEFAULT 0 AFTER estadoRecojo,
  ADD COLUMN noShow    TINYINT(1) NOT NULL DEFAULT 0 AFTER cancelado;

-- El DNI del comprobante debe conservar los 8 dígitos (los DNI pueden empezar por 0).
UPDATE comprobante SET dniNoRegistrado = LPAD(dniNoRegistrado, 8, '0');
ALTER TABLE comprobante MODIFY dniNoRegistrado CHAR(8) NOT NULL;

-- Contador de veces que un cliente registrado no recogió su pedido.
ALTER TABLE usuario ADD COLUMN noShows SMALLINT NOT NULL DEFAULT 0;
