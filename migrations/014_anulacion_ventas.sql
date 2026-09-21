-- RS 14: anular ventas realizadas (el comprobante se conserva, queda marcado).
-- Ejecutar una sola vez sobre una base creada antes de esta migración.

ALTER TABLE comprobante
  ADD anulado TINYINT(1) NOT NULL DEFAULT 0,
  ADD motivoAnulacion VARCHAR(255) NULL,
  ADD fechaAnulacion DATETIME NULL,
  ADD idAnulador INT(11) NULL,
  ADD stockDevuelto TINYINT(1) NOT NULL DEFAULT 0,
  ADD CONSTRAINT fk_comprobante_anulador FOREIGN KEY (idAnulador) REFERENCES usuario (idUsuario);
