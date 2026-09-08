-- Precio decimal, imagen referencial y usuario administrativo.
-- Ejecutar una sola vez sobre bd_musuas.

USE bd_musuas;

ALTER TABLE producto
    MODIFY COLUMN precio DECIMAL(10,2) NOT NULL,
    MODIFY COLUMN existencias INT UNSIGNED NOT NULL DEFAULT 0,
    ADD COLUMN imagen VARCHAR(255) NULL AFTER existencias;

ALTER TABLE usuario
    ADD COLUMN nombreUsuario VARCHAR(20) NULL AFTER tipoUsuario,
    ADD COLUMN intentosFallidos TINYINT UNSIGNED NOT NULL DEFAULT 0 AFTER nombreUsuario,
    ADD COLUMN bloqueadoHasta DATETIME NULL AFTER intentosFallidos,
    ADD COLUMN bloqueoPermanente TINYINT(1) NOT NULL DEFAULT 0 AFTER bloqueadoHasta;

UPDATE usuario
SET nombreUsuario = CONCAT(LOWER(LEFT(nombres, 1)), LEFT(dni, 5))
WHERE tipoUsuario = 0 AND nombreUsuario IS NULL;

ALTER TABLE usuario
    DROP INDEX uq_usuario_dni_tipo,
    ADD UNIQUE KEY uq_usuario_dni (dni),
    ADD UNIQUE KEY uq_usuario_nombreUsuario (nombreUsuario);
