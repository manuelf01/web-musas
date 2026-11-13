-- Comandas térmicas de cocina.
-- Conserva cuándo y quién envió el pedido a cocina, además de los intentos
-- de impresión/reimpresión. Los datos del pedido permanecen en sus tablas.

ALTER TABLE registroPedido
  ADD COLUMN fechaEnvioCocina DATETIME NULL AFTER estadoPrep,
  ADD COLUMN idUsuarioComanda INT NULL AFTER fechaEnvioCocina,
  ADD COLUMN impresionesComanda INT NOT NULL DEFAULT 0 AFTER idUsuarioComanda,
  ADD COLUMN fechaUltimaImpresion DATETIME NULL AFTER impresionesComanda,
  ADD KEY idx_pedido_comanda_usuario (idUsuarioComanda),
  ADD CONSTRAINT fk_pedido_comanda_usuario
    FOREIGN KEY (idUsuarioComanda) REFERENCES usuario(idUsuario);
