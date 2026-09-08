-- 006 — cancelación de pedidos + control de "no recogió" (anti no-show).
-- Solo toca registroPedido y usuario (parte de pedidos / clientes).

ALTER TABLE registroPedido
  ADD COLUMN cancelado TINYINT(1) NOT NULL DEFAULT 0 AFTER estadoRecojo,
  ADD COLUMN noShow    TINYINT(1) NOT NULL DEFAULT 0 AFTER cancelado;

-- Contador de veces que un cliente registrado no recogió su pedido.
ALTER TABLE usuario ADD COLUMN noShows SMALLINT NOT NULL DEFAULT 0;
