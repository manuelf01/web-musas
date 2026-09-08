-- 009 — estados de preparación del pedido.
-- La columna va al final de la tabla para NO correr los índices posicionales
-- que ya usan otros módulos (diccionario_pedidos, admin_ventas).
--   0 = recibido (aún se puede cancelar)
--   1 = en preparación (el cliente ya NO puede cancelar)
--   2 = listo para recojo

ALTER TABLE registroPedido
  ADD COLUMN estadoPrep TINYINT NOT NULL DEFAULT 0;
