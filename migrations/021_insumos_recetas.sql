-- Inventario de ingredientes y recetas para calcular produccion y consumo.
-- Aplicar despues de 020_comandas_cocina.sql. No asigna existencias ficticias:
-- el stock inicial se registra mediante conteo fisico desde el panel.

CREATE TABLE IF NOT EXISTS insumo (
  idInsumo INT NOT NULL AUTO_INCREMENT,
  nombre VARCHAR(120) NOT NULL,
  categoria VARCHAR(80) NOT NULL DEFAULT 'General',
  unidad VARCHAR(12) NOT NULL DEFAULT 'unidad',
  stockMinimo DECIMAL(12,3) NOT NULL DEFAULT 0,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  fechaRegistro DATETIME NOT NULL,
  PRIMARY KEY (idInsumo),
  UNIQUE KEY uq_insumo_nombre (nombre),
  CONSTRAINT chk_insumo_minimo CHECK (stockMinimo >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS saldoInsumo (
  idInsumo INT NOT NULL,
  idAlmacen SMALLINT NOT NULL,
  stockFisico DECIMAL(12,3) NOT NULL DEFAULT 0,
  stockReservado DECIMAL(12,3) NOT NULL DEFAULT 0,
  costoPromedio DECIMAL(12,4) NOT NULL DEFAULT 0,
  version INT NOT NULL DEFAULT 0,
  fechaActualizacion DATETIME NOT NULL,
  PRIMARY KEY (idInsumo,idAlmacen),
  CONSTRAINT fk_saldo_insumo FOREIGN KEY (idInsumo) REFERENCES insumo(idInsumo),
  CONSTRAINT fk_saldo_insumo_almacen FOREIGN KEY (idAlmacen) REFERENCES almacen(idAlmacen),
  CONSTRAINT chk_saldo_insumo_no_negativo CHECK
    (stockFisico >= 0 AND stockReservado >= 0 AND stockReservado <= stockFisico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS recetaInsumo (
  idRecetaInsumo BIGINT NOT NULL AUTO_INCREMENT,
  idProducto INT NOT NULL,
  tipoUso VARCHAR(12) NOT NULL DEFAULT 'producto',
  idInsumo INT NOT NULL,
  cantidad DECIMAL(12,3) NOT NULL,
  PRIMARY KEY (idRecetaInsumo),
  UNIQUE KEY uq_receta_producto_insumo (idProducto,tipoUso,idInsumo),
  KEY idx_receta_insumo (idInsumo),
  CONSTRAINT fk_receta_producto FOREIGN KEY (idProducto) REFERENCES producto(idProducto),
  CONSTRAINT fk_receta_insumo FOREIGN KEY (idInsumo) REFERENCES insumo(idInsumo),
  CONSTRAINT chk_receta_tipo CHECK (tipoUso IN ('producto','opcion')),
  CONSTRAINT chk_receta_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pedidoInsumo (
  idPedido INT NOT NULL,
  idInsumo INT NOT NULL,
  idAlmacen SMALLINT NOT NULL,
  cantidad DECIMAL(12,3) NOT NULL,
  costoUnitario DECIMAL(12,4) NOT NULL DEFAULT 0,
  estado VARCHAR(12) NOT NULL DEFAULT 'reservado',
  PRIMARY KEY (idPedido,idInsumo,idAlmacen),
  CONSTRAINT fk_pedido_insumo_pedido FOREIGN KEY (idPedido) REFERENCES registroPedido(idPedido),
  CONSTRAINT fk_pedido_insumo_insumo FOREIGN KEY (idInsumo) REFERENCES insumo(idInsumo),
  CONSTRAINT fk_pedido_insumo_almacen FOREIGN KEY (idAlmacen) REFERENCES almacen(idAlmacen),
  CONSTRAINT chk_pedido_insumo_cantidad CHECK (cantidad > 0),
  CONSTRAINT chk_pedido_insumo_estado CHECK (estado IN ('reservado','consumido','liberado'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS movimientoInsumo (
  idMovimientoInsumo BIGINT NOT NULL AUTO_INCREMENT,
  idInsumo INT NOT NULL,
  idAlmacen SMALLINT NOT NULL,
  tipo VARCHAR(30) NOT NULL,
  cantidad DECIMAL(12,3) NOT NULL,
  stockAnterior DECIMAL(12,3) NOT NULL,
  stockPosterior DECIMAL(12,3) NOT NULL,
  reservadoAnterior DECIMAL(12,3) NOT NULL DEFAULT 0,
  reservadoPosterior DECIMAL(12,3) NOT NULL DEFAULT 0,
  costoUnitario DECIMAL(12,4) DEFAULT NULL,
  costoTotal DECIMAL(12,2) DEFAULT NULL,
  referenciaTipo VARCHAR(30) DEFAULT NULL,
  idReferencia BIGINT DEFAULT NULL,
  documento VARCHAR(100) DEFAULT NULL,
  claveOperacion VARCHAR(140) DEFAULT NULL,
  motivo VARCHAR(255) DEFAULT NULL,
  idUsuario INT DEFAULT NULL,
  fechaHora DATETIME NOT NULL,
  PRIMARY KEY (idMovimientoInsumo),
  UNIQUE KEY uq_mov_insumo_operacion (claveOperacion),
  KEY idx_mov_insumo_fecha (idInsumo,idAlmacen,fechaHora),
  KEY idx_mov_insumo_referencia (referenciaTipo,idReferencia),
  CONSTRAINT fk_mov_insumo FOREIGN KEY (idInsumo) REFERENCES insumo(idInsumo),
  CONSTRAINT fk_mov_insumo_almacen FOREIGN KEY (idAlmacen) REFERENCES almacen(idAlmacen),
  CONSTRAINT fk_mov_insumo_usuario FOREIGN KEY (idUsuario) REFERENCES usuario(idUsuario),
  CONSTRAINT chk_mov_insumo_cantidad CHECK (cantidad > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS detalleCompraInsumo (
  idDetalleCompraInsumo BIGINT NOT NULL AUTO_INCREMENT,
  idCompra BIGINT NOT NULL,
  idInsumo INT NOT NULL,
  cantidad DECIMAL(12,3) NOT NULL,
  costoUnitario DECIMAL(12,4) NOT NULL,
  subtotal DECIMAL(12,2) NOT NULL,
  PRIMARY KEY (idDetalleCompraInsumo),
  UNIQUE KEY uq_compra_insumo (idCompra,idInsumo),
  CONSTRAINT fk_det_compra_insumo_compra FOREIGN KEY (idCompra) REFERENCES compra(idCompra),
  CONSTRAINT fk_det_compra_insumo FOREIGN KEY (idInsumo) REFERENCES insumo(idInsumo),
  CONSTRAINT chk_det_compra_insumo CHECK (cantidad > 0 AND costoUnitario >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
