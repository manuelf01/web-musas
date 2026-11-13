-- Inventario auditable por almacén, compras/proveedores y devoluciones.
-- Aplicar después de 018_caja_medios_kardex.sql.

ALTER TABLE registroPedido
  ADD COLUMN IF NOT EXISTS idempotencia VARCHAR(64) DEFAULT NULL AFTER notas,
  ADD UNIQUE KEY IF NOT EXISTS uq_pedido_idempotencia (idempotencia);

CREATE TABLE IF NOT EXISTS almacen (
  idAlmacen SMALLINT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(100) NOT NULL,
  direccion VARCHAR(200) DEFAULT NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (idAlmacen),
  UNIQUE KEY uq_almacen_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT IGNORE INTO almacen (idAlmacen,nombre,direccion,activo)
VALUES (1,'Almacén principal','Av. José Balta Sur 006, Chiclayo',1);

CREATE TABLE IF NOT EXISTS inventarioSaldo (
  idProducto INT NOT NULL,
  idAlmacen SMALLINT NOT NULL,
  stockFisico INT NOT NULL DEFAULT 0,
  stockReservado INT NOT NULL DEFAULT 0,
  costoPromedio DECIMAL(12,4) NOT NULL DEFAULT 0,
  version INT NOT NULL DEFAULT 0,
  fechaActualizacion DATETIME NOT NULL,
  PRIMARY KEY (idProducto,idAlmacen),
  CONSTRAINT fk_saldo_producto FOREIGN KEY (idProducto) REFERENCES producto(idProducto),
  CONSTRAINT fk_saldo_almacen FOREIGN KEY (idAlmacen) REFERENCES almacen(idAlmacen),
  CONSTRAINT chk_saldo_no_negativo CHECK (stockFisico >= 0 AND stockReservado >= 0 AND stockReservado <= stockFisico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT IGNORE INTO inventarioSaldo
  (idProducto,idAlmacen,stockFisico,stockReservado,costoPromedio,version,fechaActualizacion)
SELECT p.idProducto,1,p.existencias+COALESCE(r.reservado,0),COALESCE(r.reservado,0),0,0,NOW()
FROM producto p
LEFT JOIN (
  SELECT d.idProducto,SUM(d.cantidad) reservado
  FROM detalleOrden d JOIN registroPedido rp ON rp.idPedido=d.idPedido
  WHERE rp.estadoRecojo=0 AND rp.cancelado=0 AND rp.noShow=0
  GROUP BY d.idProducto
) r ON r.idProducto=p.idProducto;

ALTER TABLE movimientoInventario
  ADD COLUMN IF NOT EXISTS idAlmacen SMALLINT NULL AFTER idProducto,
  ADD COLUMN IF NOT EXISTS stockReservadoAnterior INT NOT NULL DEFAULT 0 AFTER stockPosterior,
  ADD COLUMN IF NOT EXISTS stockReservadoPosterior INT NOT NULL DEFAULT 0 AFTER stockReservadoAnterior,
  ADD COLUMN IF NOT EXISTS costoTotal DECIMAL(12,2) DEFAULT NULL AFTER costoUnitario,
  ADD COLUMN IF NOT EXISTS documento VARCHAR(100) DEFAULT NULL AFTER idReferencia,
  ADD COLUMN IF NOT EXISTS claveOperacion VARCHAR(120) DEFAULT NULL AFTER documento,
  ADD COLUMN IF NOT EXISTS idMovimientoReversion BIGINT DEFAULT NULL AFTER claveOperacion,
  ADD KEY IF NOT EXISTS idx_kardex_almacen_fecha (idAlmacen,fechaHora),
  ADD UNIQUE KEY IF NOT EXISTS uq_kardex_operacion (claveOperacion),
  ADD CONSTRAINT fk_kardex_almacen FOREIGN KEY (idAlmacen) REFERENCES almacen(idAlmacen),
  ADD CONSTRAINT fk_kardex_reversion FOREIGN KEY (idMovimientoReversion) REFERENCES movimientoInventario(idMovimientoInventario);

UPDATE movimientoInventario SET idAlmacen=1 WHERE idAlmacen IS NULL;
ALTER TABLE movimientoInventario
  MODIFY idAlmacen SMALLINT NOT NULL DEFAULT 1,
  MODIFY costoUnitario DECIMAL(12,4) DEFAULT NULL;

CREATE TABLE IF NOT EXISTS proveedor (
  idProveedor INT NOT NULL AUTO_INCREMENT,
  ruc CHAR(11) DEFAULT NULL,
  razonSocial VARCHAR(180) NOT NULL,
  contacto VARCHAR(150) DEFAULT NULL,
  telefono VARCHAR(20) DEFAULT NULL,
  correo VARCHAR(150) DEFAULT NULL,
  direccion VARCHAR(220) DEFAULT NULL,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  fechaRegistro DATETIME NOT NULL,
  PRIMARY KEY (idProveedor),
  UNIQUE KEY uq_proveedor_ruc (ruc)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS compra (
  idCompra BIGINT NOT NULL AUTO_INCREMENT,
  idProveedor INT NOT NULL,
  idAlmacen SMALLINT NOT NULL,
  documento VARCHAR(100) NOT NULL,
  fechaDocumento DATE NOT NULL,
  fechaRecepcion DATETIME DEFAULT NULL,
  total DECIMAL(12,2) NOT NULL DEFAULT 0,
  estado VARCHAR(20) NOT NULL DEFAULT 'borrador',
  observaciones VARCHAR(500) DEFAULT NULL,
  idUsuarioRegistro INT NOT NULL,
  idUsuarioRecepcion INT DEFAULT NULL,
  PRIMARY KEY (idCompra),
  UNIQUE KEY uq_compra_proveedor_documento (idProveedor,documento),
  CONSTRAINT fk_compra_proveedor FOREIGN KEY (idProveedor) REFERENCES proveedor(idProveedor),
  CONSTRAINT fk_compra_almacen FOREIGN KEY (idAlmacen) REFERENCES almacen(idAlmacen),
  CONSTRAINT fk_compra_usuario_reg FOREIGN KEY (idUsuarioRegistro) REFERENCES usuario(idUsuario),
  CONSTRAINT fk_compra_usuario_rec FOREIGN KEY (idUsuarioRecepcion) REFERENCES usuario(idUsuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS detalleCompra (
  idDetalleCompra BIGINT NOT NULL AUTO_INCREMENT,
  idCompra BIGINT NOT NULL,
  idProducto INT NOT NULL,
  cantidad INT NOT NULL,
  costoUnitario DECIMAL(12,4) NOT NULL,
  subtotal DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (idDetalleCompra),
  UNIQUE KEY uq_compra_producto (idCompra,idProducto),
  CONSTRAINT fk_detalle_compra FOREIGN KEY (idCompra) REFERENCES compra(idCompra),
  CONSTRAINT fk_detalle_compra_producto FOREIGN KEY (idProducto) REFERENCES producto(idProducto),
  CONSTRAINT chk_detalle_compra_positivo CHECK (cantidad > 0 AND costoUnitario >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS devolucionInventario (
  idDevolucion BIGINT NOT NULL AUTO_INCREMENT,
  tipo VARCHAR(30) NOT NULL,
  idPedido INT DEFAULT NULL,
  idCompra BIGINT DEFAULT NULL,
  idProveedor INT DEFAULT NULL,
  resolucion VARCHAR(30) NOT NULL,
  documento VARCHAR(100) DEFAULT NULL,
  motivo VARCHAR(500) NOT NULL,
  estado VARCHAR(20) NOT NULL DEFAULT 'confirmada',
  idUsuario INT NOT NULL,
  fechaHora DATETIME NOT NULL,
  PRIMARY KEY (idDevolucion),
  CONSTRAINT fk_devolucion_pedido FOREIGN KEY (idPedido) REFERENCES registroPedido(idPedido),
  CONSTRAINT fk_devolucion_compra FOREIGN KEY (idCompra) REFERENCES compra(idCompra),
  CONSTRAINT fk_devolucion_proveedor FOREIGN KEY (idProveedor) REFERENCES proveedor(idProveedor),
  CONSTRAINT fk_devolucion_usuario FOREIGN KEY (idUsuario) REFERENCES usuario(idUsuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS detalleDevolucionInventario (
  idDetalleDevolucion BIGINT NOT NULL AUTO_INCREMENT,
  idDevolucion BIGINT NOT NULL,
  idProducto INT NOT NULL,
  cantidad INT NOT NULL,
  condicionProducto VARCHAR(20) NOT NULL,
  costoUnitario DECIMAL(12,4) NOT NULL DEFAULT 0,
  idMovimientoInventario BIGINT DEFAULT NULL,
  PRIMARY KEY (idDetalleDevolucion),
  CONSTRAINT fk_detalle_devolucion FOREIGN KEY (idDevolucion) REFERENCES devolucionInventario(idDevolucion),
  CONSTRAINT fk_detalle_devolucion_producto FOREIGN KEY (idProducto) REFERENCES producto(idProducto),
  CONSTRAINT fk_detalle_devolucion_mov FOREIGN KEY (idMovimientoInventario) REFERENCES movimientoInventario(idMovimientoInventario),
  CONSTRAINT chk_detalle_devolucion_positivo CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
