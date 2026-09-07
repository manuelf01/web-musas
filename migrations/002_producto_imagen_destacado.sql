-- 002 · Imagen y badge de producto (para la carta / home)
-- Aplicar en db_musuas. Recomendado: correr vía pymysql o
-- mysql --default-character-set=utf8mb4 (por la ñ del proyecto).

ALTER TABLE producto ADD COLUMN imagen    VARCHAR(255) NULL AFTER existencias;
ALTER TABLE producto ADD COLUMN destacado VARCHAR(40)  NULL AFTER imagen;
