-- Catálogo de medios, pagos históricos, sesiones de caja y Kardex.

CREATE TABLE IF NOT EXISTS medioPago (
  idMedioPago SMALLINT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(20) NOT NULL,
  nombre VARCHAR(60) NOT NULL,
  tipo VARCHAR(20) NOT NULL,
  descuentoPorcentaje DECIMAL(5,2) NOT NULL DEFAULT 0,
  comisionPorcentaje DECIMAL(5,2) NOT NULL DEFAULT 0,
  comisionFija DECIMAL(12,2) NOT NULL DEFAULT 0,
  imagen VARCHAR(255) DEFAULT NULL,
  afectaEfectivo TINYINT(1) NOT NULL DEFAULT 0,
  activo TINYINT(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (idMedioPago),
  UNIQUE KEY uq_medio_pago_codigo (codigo),
  UNIQUE KEY uq_medio_pago_nombre (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO medioPago
  (idMedioPago, codigo, nombre, tipo, afectaEfectivo, activo) VALUES
  (1, 'efectivo', 'Efectivo', 'efectivo', 1, 1),
  (2, 'tarjeta', 'Tarjeta', 'tarjeta', 0, 1),
  (3, 'yape', 'Yape', 'billetera', 0, 1),
  (4, 'plin', 'Plin', 'billetera', 0, 1)
ON DUPLICATE KEY UPDATE nombre=VALUES(nombre), tipo=VALUES(tipo),
  afectaEfectivo=VALUES(afectaEfectivo);

ALTER TABLE comprobante
  ADD montoBruto DECIMAL(12,2) NULL AFTER igv,
  ADD descuento DECIMAL(12,2) NOT NULL DEFAULT 0 AFTER montoBruto;
UPDATE comprobante SET montoBruto = montoTotal WHERE montoBruto IS NULL;
ALTER TABLE comprobante MODIFY montoBruto DECIMAL(12,2) NOT NULL;

CREATE TABLE IF NOT EXISTS sesionCaja (
  idSesionCaja INT NOT NULL AUTO_INCREMENT,
  fechaApertura DATETIME NOT NULL,
  idUsuarioApertura INT NOT NULL,
  fondoInicial DECIMAL(12,2) NOT NULL DEFAULT 0,
  fechaCierre DATETIME DEFAULT NULL,
  idUsuarioCierre INT DEFAULT NULL,
  efectivoEsperado DECIMAL(12,2) DEFAULT NULL,
  efectivoContado DECIMAL(12,2) DEFAULT NULL,
  diferencia DECIMAL(12,2) DEFAULT NULL,
  observaciones VARCHAR(500) DEFAULT NULL,
  estado VARCHAR(10) NOT NULL DEFAULT 'abierta',
  PRIMARY KEY (idSesionCaja),
  KEY idx_sesion_caja_estado (estado, fechaApertura),
  CONSTRAINT fk_sesion_caja_apertura FOREIGN KEY (idUsuarioApertura) REFERENCES usuario(idUsuario),
  CONSTRAINT fk_sesion_caja_cierre FOREIGN KEY (idUsuarioCierre) REFERENCES usuario(idUsuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS pagoVenta (
  idPago INT NOT NULL AUTO_INCREMENT,
  idComprobante INT NOT NULL,
  idSesionCaja INT DEFAULT NULL,
  idMedioPago SMALLINT NOT NULL,
  medioNombre VARCHAR(60) NOT NULL,
  montoBruto DECIMAL(12,2) NOT NULL,
  descuento DECIMAL(12,2) NOT NULL DEFAULT 0,
  montoCobrado DECIMAL(12,2) NOT NULL,
  comision DECIMAL(12,2) NOT NULL DEFAULT 0,
  montoNeto DECIMAL(12,2) NOT NULL,
  porcentajeDescuento DECIMAL(5,2) NOT NULL DEFAULT 0,
  porcentajeComision DECIMAL(5,2) NOT NULL DEFAULT 0,
  comisionFija DECIMAL(12,2) NOT NULL DEFAULT 0,
  referencia VARCHAR(100) DEFAULT NULL,
  fechaHora DATETIME NOT NULL,
  idCajero INT DEFAULT NULL,
  anulado TINYINT(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (idPago),
  UNIQUE KEY uq_pago_venta_comprobante (idComprobante),
  KEY idx_pago_venta_sesion (idSesionCaja, idMedioPago),
  CONSTRAINT fk_pago_venta_comprobante FOREIGN KEY (idComprobante) REFERENCES comprobante(idComprobante),
  CONSTRAINT fk_pago_venta_sesion FOREIGN KEY (idSesionCaja) REFERENCES sesionCaja(idSesionCaja),
  CONSTRAINT fk_pago_venta_medio FOREIGN KEY (idMedioPago) REFERENCES medioPago(idMedioPago),
  CONSTRAINT fk_pago_venta_cajero FOREIGN KEY (idCajero) REFERENCES usuario(idUsuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT IGNORE INTO pagoVenta
  (idComprobante, idMedioPago, medioNombre, montoBruto, descuento,
   montoCobrado, comision, montoNeto, fechaHora, idCajero, anulado)
SELECT c.idComprobante, mp.idMedioPago, mp.nombre, c.montoTotal, 0,
       c.montoTotal, 0, c.montoTotal,
       TIMESTAMP(c.fechaComprobante, c.horaComprobante), c.idCajero, c.anulado
FROM comprobante c
JOIN medioPago mp ON mp.codigo = LOWER(c.medioPago);

CREATE TABLE IF NOT EXISTS movimientoCaja (
  idMovimientoCaja INT NOT NULL AUTO_INCREMENT,
  idSesionCaja INT NOT NULL,
  tipo VARCHAR(20) NOT NULL,
  idMedioPago SMALLINT DEFAULT NULL,
  monto DECIMAL(12,2) NOT NULL,
  categoria VARCHAR(60) NOT NULL DEFAULT 'General',
  concepto VARCHAR(255) NOT NULL,
  documento VARCHAR(100) DEFAULT NULL,
  evidencia VARCHAR(255) DEFAULT NULL,
  idUsuario INT NOT NULL,
  fechaHora DATETIME NOT NULL,
  anulado TINYINT(1) NOT NULL DEFAULT 0,
  motivoAnulacion VARCHAR(255) DEFAULT NULL,
  fechaAnulacion DATETIME DEFAULT NULL,
  idAnulador INT DEFAULT NULL,
  PRIMARY KEY (idMovimientoCaja),
  KEY idx_movimiento_caja_sesion (idSesionCaja, fechaHora),
  CONSTRAINT fk_movimiento_caja_sesion FOREIGN KEY (idSesionCaja) REFERENCES sesionCaja(idSesionCaja),
  CONSTRAINT fk_movimiento_caja_medio FOREIGN KEY (idMedioPago) REFERENCES medioPago(idMedioPago),
  CONSTRAINT fk_movimiento_caja_usuario FOREIGN KEY (idUsuario) REFERENCES usuario(idUsuario),
  CONSTRAINT fk_movimiento_caja_anulador FOREIGN KEY (idAnulador) REFERENCES usuario(idUsuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS movimientoInventario (
  idMovimientoInventario BIGINT NOT NULL AUTO_INCREMENT,
  idProducto INT NOT NULL,
  tipo VARCHAR(30) NOT NULL,
  cantidad INT NOT NULL,
  stockAnterior INT NOT NULL,
  stockPosterior INT NOT NULL,
  costoUnitario DECIMAL(12,2) DEFAULT NULL,
  referenciaTipo VARCHAR(30) DEFAULT NULL,
  idReferencia INT DEFAULT NULL,
  motivo VARCHAR(255) DEFAULT NULL,
  idUsuario INT DEFAULT NULL,
  fechaHora DATETIME NOT NULL,
  PRIMARY KEY (idMovimientoInventario),
  KEY idx_kardex_producto_fecha (idProducto, fechaHora),
  KEY idx_kardex_referencia (referenciaTipo, idReferencia),
  CONSTRAINT fk_kardex_producto FOREIGN KEY (idProducto) REFERENCES producto(idProducto),
  CONSTRAINT fk_kardex_usuario FOREIGN KEY (idUsuario) REFERENCES usuario(idUsuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO movimientoInventario
  (idProducto, tipo, cantidad, stockAnterior, stockPosterior, referenciaTipo,
   motivo, fechaHora)
SELECT idProducto, 'saldo_inicial', existencias, 0, existencias, 'migracion',
       'Saldo registrado al activar el Kardex', NOW()
FROM producto
WHERE NOT EXISTS (SELECT 1 FROM movimientoInventario LIMIT 1);
