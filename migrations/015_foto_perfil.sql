-- Foto de perfil del usuario (ruta relativa dentro de static/img/, p. ej. perfiles/ab12.jpg).
-- Ejecutar una sola vez sobre una base creada antes de esta migración.

ALTER TABLE usuario ADD fotoPerfil VARCHAR(255) NULL;
