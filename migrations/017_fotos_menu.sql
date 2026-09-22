-- Agrega fotos reales a 17 productos del menú (antes sin imagen, mostraban
-- un ícono). Los archivos van en static/img/menu/ y ya están en el repo.
-- Ejecutar una sola vez.

UPDATE producto SET imagen = 'menu/simple-de-pollo.jpg' WHERE idProducto = 1;
UPDATE producto SET imagen = 'menu/simple-de-carne.jpg' WHERE idProducto = 2;
UPDATE producto SET imagen = 'menu/carne-con-huevo.jpg' WHERE idProducto = 6;
UPDATE producto SET imagen = 'menu/carne-huevo-tocino.jpg' WHERE idProducto = 12;
UPDATE producto SET imagen = 'menu/carne-queso-jamon-pina.jpg' WHERE idProducto = 15;
UPDATE producto SET imagen = 'menu/carne-huevo-platano.jpg' WHERE idProducto = 21;
UPDATE producto SET imagen = 'menu/a-lo-pobre-especial-pollo.jpg' WHERE idProducto = 27;
UPDATE producto SET imagen = 'menu/salchipapa.jpg' WHERE idProducto = 31;
UPDATE producto SET imagen = 'menu/pollipapa.jpg' WHERE idProducto = 32;
UPDATE producto SET imagen = 'menu/salchipollo.jpg' WHERE idProducto = 33;
UPDATE producto SET imagen = 'menu/salchitodo.jpg' WHERE idProducto = 34;
UPDATE producto SET imagen = 'menu/salchimusas.jpg' WHERE idProducto = 35;
UPDATE producto SET imagen = 'menu/combo-salchimusas.jpg' WHERE idProducto = 36;
UPDATE producto SET imagen = 'menu/chicha-morada-natural.jpg' WHERE idProducto = 37;
UPDATE producto SET imagen = 'menu/agua-san-carlos.jpg' WHERE idProducto = 38;
UPDATE producto SET imagen = 'menu/coca-cola.jpg' WHERE idProducto = 39;
UPDATE producto SET imagen = 'menu/inca-kola.jpg' WHERE idProducto = 40;
