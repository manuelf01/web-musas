-- 007 — imagen opcional para las categorías (mosaicos del inicio, cabeceras).
ALTER TABLE categoriaProducto ADD COLUMN imagen VARCHAR(255) NULL AFTER descripcion;
