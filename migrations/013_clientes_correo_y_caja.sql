-- Clientes identificados por correo y comprobante definido al entregar.
-- Ejecutar una sola vez sobre una base creada antes de esta migración.

ALTER TABLE usuario
  MODIFY dni CHAR(8) NULL,
  ADD CONSTRAINT uq_usuario_correo UNIQUE (correo);

ALTER TABLE registroPedido
  MODIFY dniNoRegistrado VARCHAR(11) NULL,
  MODIFY estadoBoleta TINYINT(1) NOT NULL DEFAULT 0,
  ADD correoRecojo VARCHAR(200) NULL AFTER nombres,
  ADD medioPagoElegido VARCHAR(20) NOT NULL DEFAULT 'efectivo' AFTER billeteraDigital;

UPDATE registroPedido rp
INNER JOIN usuario u ON u.idUsuario = rp.idUsuario
SET rp.correoRecojo = u.correo
WHERE rp.correoRecojo IS NULL;

ALTER TABLE comprobante
  MODIFY dniNoRegistrado VARCHAR(11) NULL,
  ADD tipoComprobante VARCHAR(10) NOT NULL DEFAULT 'boleta' AFTER dniNoRegistrado,
  ADD razonSocial VARCHAR(200) NULL AFTER tipoComprobante;
