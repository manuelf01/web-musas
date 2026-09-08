-- Requisitos para contraseñas con hash, IDs seguros y claves de pedido.
-- Ejecutar una sola vez sobre bd_musuas.

USE bd_musuas;

ALTER TABLE usuario
    MODIFY COLUMN contraseña VARCHAR(255) NOT NULL;

ALTER TABLE registroPedido
    MODIFY COLUMN idPedido INT NOT NULL AUTO_INCREMENT,
    ADD COLUMN nombres VARCHAR(100) NOT NULL AFTER dniNoRegistrado,
    MODIFY COLUMN keyPedido VARCHAR(64) NOT NULL,
    ADD UNIQUE KEY uq_registroPedido_keyPedido (keyPedido),
    ADD KEY idx_registroPedido_fechaPedido (fechaPedido),
    ADD KEY idx_registroPedido_estadoRecojo (estadoRecojo);

ALTER TABLE detalleOrden
    MODIFY COLUMN idDetalleOrden INT NOT NULL AUTO_INCREMENT;
