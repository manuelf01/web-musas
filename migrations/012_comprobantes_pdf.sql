-- Ejecutar una sola vez sobre la base existente, después del respaldo.
-- Si hay duplicados en idPedido/numeroComprobante, resolverlos antes de migrar.
ALTER TABLE producto MODIFY precio DECIMAL(12,2) NOT NULL DEFAULT 0;
ALTER TABLE detalleOrden
  MODIFY precioUnidad DECIMAL(12,2) NOT NULL,
  MODIFY precioTotal DECIMAL(12,2) NOT NULL,
  ADD adicionales TEXT NULL;
ALTER TABLE comprobante
  MODIFY subTotal DECIMAL(12,2) NOT NULL,
  MODIFY montoTotal DECIMAL(12,2) NOT NULL,
  MODIFY igv DECIMAL(12,2) NOT NULL,
  MODIFY numeroComprobante VARCHAR(25) NULL,
  ADD medioPago VARCHAR(20) NOT NULL DEFAULT 'No registrado',
  ADD idCajero INT NULL,
  ADD datosEmision LONGTEXT NULL,
  ADD CONSTRAINT uq_comprobante_pedido UNIQUE (idPedido),
  ADD CONSTRAINT uq_comprobante_numero UNIQUE (numeroComprobante),
  ADD CONSTRAINT fk_comprobante_cajero FOREIGN KEY (idCajero) REFERENCES usuario(idUsuario);
-- Añadir un índice antes de sustituir la PK: sostiene la FK idComprobante.
ALTER TABLE detalleComprobante
  ADD INDEX idx_detalle_comprobante (idComprobante),
  DROP PRIMARY KEY,
  ADD idLinea INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  MODIFY precioUnidad DECIMAL(12,2) NOT NULL,
  MODIFY precioTotal DECIMAL(12,2) NOT NULL,
  ADD adicionales TEXT NULL;
