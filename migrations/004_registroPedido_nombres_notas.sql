-- 004 · registroPedido: nombre de quien recoge + notas de cocina
-- El modelo Pedido.diccionario_pedidos YA asume una columna `nombres` en la
-- posición 4 (índice 3); sin ella el indexado quedaba corrido y reventaba en
-- keyPedido. Esta migración la agrega (arregla ese bug) y suma `notas`.
-- Aplicar en db_musuas vía pymysql o mysql --default-character-set=utf8mb4.

ALTER TABLE registroPedido ADD COLUMN nombres VARCHAR(120) NULL AFTER dniNoRegistrado;
ALTER TABLE registroPedido ADD COLUMN notas   VARCHAR(255) NULL AFTER keyPedido;
