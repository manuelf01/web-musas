-- 003 · Etiqueta corta del producto (el tag que va junto al precio en la carta:
-- "Brasas", "Smash 120g", "Papa Amarilla"...). Aplicar en db_musuas.

ALTER TABLE producto ADD COLUMN nota VARCHAR(40) NULL AFTER destacado;
