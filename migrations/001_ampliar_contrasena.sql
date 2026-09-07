-- 001 · Ampliar usuario.contraseña para que quepa el hash de werkzeug
-- El hash pbkdf2:sha256 mide ~102 caracteres; varchar(100) lo truncaba
-- y el login siempre fallaba. Aplicar en db_musuas.

ALTER TABLE usuario MODIFY contraseña VARCHAR(255) NOT NULL;
