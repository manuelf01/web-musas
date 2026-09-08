-- =====================================================================
--  Las Musas — Base de datos completa (crear desde cero)
-- =====================================================================
--  Este archivo YA incluye todos los cambios de migrations/001..010.
--  Para levantar el proyecto desde cero:
--    1. Abre phpMyAdmin (XAMPP) → pestaña "SQL"
--    2. Copia y pega TODO este archivo y ejecútalo.
--  Crea la base `db_musuas` (nombre que espera cfg.py) con datos de ejemplo.
--
--  Cuentas de ejemplo (contraseña de todas: Musas2026)
--    DNI 12345678  → superusuario  (acceso total al panel + gestión de usuarios)
--    DNI 87654321  → administrador (panel sin la sección Usuarios)
--    DNI 12345679  → usuario       (cliente de la tienda)
--
--  MariaDB 10.4 (XAMPP). Charset utf8mb4 en todo (la columna `contraseña`
--  lleva ñ y el hash pbkdf2 ocupa ~102 chars).
-- =====================================================================

CREATE DATABASE IF NOT EXISTS `db_musuas`
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE `db_musuas`;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `detalleCremas`;
DROP TABLE IF EXISTS `detalleComprobante`;
DROP TABLE IF EXISTS `comprobante`;
DROP TABLE IF EXISTS `detalleOrden`;
DROP TABLE IF EXISTS `registroPedido`;
DROP TABLE IF EXISTS `producto`;
DROP TABLE IF EXISTS `categoriaProducto`;
DROP TABLE IF EXISTS `usuario`;

-- ---------------------------------------------------------------------
--  usuario  — cuentas. rol: 'superusuario' | 'administrador' | 'usuario'
--            tipoUsuario se mantiene sincronizado (0 = panel, 1 = cliente).
--            activo = 0  ->  cuenta dada de baja (no inicia sesión).
-- ---------------------------------------------------------------------
CREATE TABLE `usuario` (
  `idUsuario`   int(11)      NOT NULL AUTO_INCREMENT,
  `dni`         char(8)      NOT NULL,
  `nombres`     varchar(100) NOT NULL,
  `apellidos`   varchar(100) NOT NULL,
  `correo`      varchar(200) NOT NULL,
  `numTelf`     char(9)      NOT NULL,
  `contraseña`  varchar(255) NOT NULL,          -- hash werkzeug (pbkdf2:sha256)
  `tipoUsuario` tinyint(1)   NOT NULL,          -- 0 = panel, 1 = cliente
  `noShows`     smallint(6)  NOT NULL DEFAULT 0,-- veces que no recogió su pedido
  `rol`         varchar(20)  NOT NULL DEFAULT 'usuario',
  `activo`      tinyint(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------------
--  categoriaProducto  — secciones de la carta. La categoría "Cremas"
--  no se muestra en la carta pública; sus productos son las salsas del
--  paso "personalizar". activo = 0 -> categoría dada de baja.
-- ---------------------------------------------------------------------
CREATE TABLE `categoriaProducto` (
  `idCategoria`     smallint(6)  NOT NULL AUTO_INCREMENT,
  `nombreCategoria` varchar(50)  NOT NULL,
  `descripcion`     varchar(255) DEFAULT NULL,
  `imagen`          varchar(255) DEFAULT NULL,  -- ruta relativa dentro de static/img/
  `activo`          tinyint(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (`idCategoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------------
--  producto  — ítems de la carta y también las cremas (según idCategoria).
--  destacado / nota: textos cortos para badges de la tarjeta (opcionales).
--  activo = 0 -> producto dado de baja (no aparece en la tienda).
-- ---------------------------------------------------------------------
CREATE TABLE `producto` (
  `idProducto`  int(11)      NOT NULL AUTO_INCREMENT,
  `idCategoria` smallint(6)  NOT NULL,
  `nombre`      varchar(100) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `precio`      float        NOT NULL DEFAULT 0,
  `existencias` smallint(6)  NOT NULL DEFAULT 0,
  `imagen`      varchar(255) DEFAULT NULL,
  `destacado`   varchar(40)  DEFAULT NULL,
  `nota`        varchar(40)  DEFAULT NULL,
  `activo`      tinyint(1)   NOT NULL DEFAULT 1,
  PRIMARY KEY (`idProducto`),
  KEY `FKproducto802442` (`idCategoria`),
  CONSTRAINT `FKproducto802442` FOREIGN KEY (`idCategoria`) REFERENCES `categoriaProducto` (`idCategoria`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------------
--  registroPedido  — cabecera del pedido. idPedido lo asigna la app
--  (MAX(idPedido)+1), no es AUTO_INCREMENT.
--    estadoRecojo 0/1  = pendiente / entregado
--    cancelado    0/1  = lo canceló el cliente o el admin
--    noShow       0/1  = el cliente no vino a recogerlo
--    estadoPrep   0/1/2 = recibido / en preparación / listo para recojo
--    keyPedido    = palabra clave de 4 dígitos que el cliente da al recoger
--    billeteraDigital 1 = Yape/Plin, 0 = paga en tienda
--    dniNoRegistrado / nombres / numeroTelefono = datos de quien recoge
--      (pueden diferir de la cuenta: puede recoger otra persona)
-- ---------------------------------------------------------------------
CREATE TABLE `registroPedido` (
  `idPedido`         int(11)     NOT NULL,
  `idUsuario`        int(11)     DEFAULT NULL,
  `dniNoRegistrado`  char(8)     NOT NULL,
  `nombres`          varchar(120) DEFAULT NULL,
  `numeroTelefono`   char(9)     NOT NULL,
  `estadoRecojo`     tinyint(1)  NOT NULL DEFAULT 0,
  `cancelado`        tinyint(1)  NOT NULL DEFAULT 0,
  `noShow`           tinyint(1)  NOT NULL DEFAULT 0,
  `horaRecojo`       time        NOT NULL,
  `fechaPedido`      date        NOT NULL DEFAULT (CURRENT_DATE),
  `estadoBoleta`     tinyint(1)  NOT NULL,
  `billeteraDigital` tinyint(1)  NOT NULL,
  `keyPedido`        smallint(6) NOT NULL,
  `notas`            varchar(255) DEFAULT NULL,
  `estadoPrep`       tinyint(4)  NOT NULL DEFAULT 0,
  PRIMARY KEY (`idPedido`),
  KEY `FKregistroPe851289` (`idUsuario`),
  CONSTRAINT `FKregistroPe851289` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------------
--  detalleOrden  — líneas del pedido (snapshot de nombre y precio).
-- ---------------------------------------------------------------------
CREATE TABLE `detalleOrden` (
  `idDetalleOrden` int(11)      NOT NULL,
  `idPedido`       int(11)      NOT NULL,
  `idProducto`     int(11)      NOT NULL,
  `nombreProducto` varchar(100) NOT NULL,
  `precioUnidad`   float        NOT NULL,
  `cantidad`       smallint(6)  NOT NULL,
  `precioTotal`    float        NOT NULL,
  PRIMARY KEY (`idDetalleOrden`,`idPedido`),
  KEY `FKdetalleOrd26951` (`idProducto`),
  KEY `FKdetalleOrd726046` (`idPedido`),
  CONSTRAINT `FKdetalleOrd26951`  FOREIGN KEY (`idProducto`) REFERENCES `producto` (`idProducto`),
  CONSTRAINT `FKdetalleOrd726046` FOREIGN KEY (`idPedido`)   REFERENCES `registroPedido` (`idPedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------------
--  comprobante / detalleComprobante  — venta emitida al ENTREGAR el
--  pedido (Pedido._emitir_comprobante). numeroComprobante = "B001-000000NN"
--  si el cliente pidió boleta, o "NV01-..." (nota de venta) si no.
--  dniNoRegistrado va como CHAR(8) para no perder el 0 inicial del DNI.
-- ---------------------------------------------------------------------
CREATE TABLE `comprobante` (
  `idComprobante`     int(11)      NOT NULL AUTO_INCREMENT,
  `idPedido`          int(11)      NOT NULL,
  `idUsuario`         int(11)      DEFAULT NULL,
  `dniNoRegistrado`   char(8)      NOT NULL,
  `fechaComprobante`  date         NOT NULL,
  `horaComprobante`   time         NOT NULL,
  `subTotal`          float        NOT NULL,
  `montoTotal`        float        NOT NULL,
  `igv`               float        NOT NULL,
  `numeroComprobante` varchar(25)  NOT NULL,
  PRIMARY KEY (`idComprobante`),
  KEY `FKcomprobant749904` (`idUsuario`),
  KEY `FKcomprobant506863` (`idPedido`),
  CONSTRAINT `FKcomprobant506863` FOREIGN KEY (`idPedido`)  REFERENCES `registroPedido` (`idPedido`),
  CONSTRAINT `FKcomprobant749904` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `detalleComprobante` (
  `idComprobante`  int(11)      NOT NULL,
  `idProducto`     int(11)      NOT NULL,
  `nombreProducto` varchar(100) NOT NULL,
  `precioUnidad`   float        NOT NULL,
  `cantidad`       smallint(6)  NOT NULL,
  `precioTotal`    float        NOT NULL,
  PRIMARY KEY (`idComprobante`,`idProducto`),
  KEY `FKdetalleCom611488` (`idProducto`),
  CONSTRAINT `FKdetalleCom611488` FOREIGN KEY (`idProducto`)    REFERENCES `producto` (`idProducto`),
  CONSTRAINT `FKdetalleCom998263` FOREIGN KEY (`idComprobante`) REFERENCES `comprobante` (`idComprobante`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------------
--  detalleCremas  — cremas elegidas por línea del pedido.
-- ---------------------------------------------------------------------
CREATE TABLE `detalleCremas` (
  `idPedido`       int(11) NOT NULL,
  `idCrema`        int(11) NOT NULL,
  `idDetalleOrden` int(11) NOT NULL,
  PRIMARY KEY (`idPedido`,`idCrema`,`idDetalleOrden`),
  KEY `FKdetalleCre999352` (`idDetalleOrden`,`idPedido`),
  KEY `FKdetalleCre352772` (`idCrema`),
  CONSTRAINT `FKdetalleCre352772` FOREIGN KEY (`idCrema`)                    REFERENCES `producto` (`idProducto`),
  CONSTRAINT `FKdetalleCre999352` FOREIGN KEY (`idDetalleOrden`,`idPedido`)  REFERENCES `detalleOrden` (`idDetalleOrden`,`idPedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- =====================================================================
--  DATOS DE EJEMPLO
-- =====================================================================

-- Cuentas (contraseña de todas: Musas2026)
INSERT INTO `usuario`
  (`idUsuario`,`dni`,`nombres`,`apellidos`,`correo`,`numTelf`,`contraseña`,`tipoUsuario`,`noShows`,`rol`,`activo`) VALUES
  (1,'12345678','Piero','Ramirez','superadmin@lasmusas.pe','987654321','pbkdf2:sha256:260000$vxtBrOTidMwkCp4V$dab206ee6109184d8e1c8c4eb65e8678aa8d13a7ebe150b2cef577f55cef51b3',0,0,'superusuario',1),
  (2,'87654321','Admin','Prueba','admin@lasmusas.pe','987654322','pbkdf2:sha256:260000$vxtBrOTidMwkCp4V$dab206ee6109184d8e1c8c4eb65e8678aa8d13a7ebe150b2cef577f55cef51b3',0,0,'administrador',1),
  (3,'12345679','Cliente','Prueba','cliente@correo.com','912345678','pbkdf2:sha256:260000$vxtBrOTidMwkCp4V$dab206ee6109184d8e1c8c4eb65e8678aa8d13a7ebe150b2cef577f55cef51b3',1,0,'usuario',1);

-- Categorías (la 6 "Cremas" no se muestra en la carta pública)
INSERT INTO `categoriaProducto` (`idCategoria`,`nombreCategoria`,`descripcion`,`imagen`,`activo`) VALUES
  (1,'Hamburguesas','Carne Angus a la brasa, pan brioche artesanal.',NULL,1),
  (2,'Salchipapas','Papas nativas crocantes, embutidos artesanales y variedad de cremas limeñas de la casa.',NULL,1),
  (3,'Bebidas','Refrescos de la casa, gaseosas heladas y cervezas artesanales limeñas.',NULL,1),
  (4,'Combos','Combos nocturnos: hamburguesa o salchipapa + acompañamiento + bebida.',NULL,1),
  (5,'Postres','Postres recién hechos para cerrar la noche.',NULL,1),
  (6,'Cremas','Salsas artesanales de la casa para personalizar tu pedido.',NULL,1);

-- Productos
INSERT INTO `producto` (`idProducto`,`idCategoria`,`nombre`,`descripcion`,`precio`,`existencias`,`imagen`,`destacado`,`nota`,`activo`) VALUES
  (1,1,'Doble Tocino & Cheddar','Doble carne Angus 180g, queso cheddar fundido, tocino crocante ahumado y salsa secreta de la casa.',24.0,20,'hamburguesas/ha-1.jpg','Más vendida','Brasas',1),
  (2,1,'Smash Las Musas','Carne crujiente smasheada, cebolla caramelizada al vino tinto, pepinillos y mayonesa trufada.',18.0,24,'hamburguesas/h-2.jpg','Especial de la casa','Smash 120g',1),
  (3,1,'La Trufada Nocturna','Champiñones salteados a la parrilla, queso suizo fundido y crema de trufa negra.',26.5,18,'hamburguesas/ha-1.jpg','Nueva','Trufa Negra',1),
  (4,1,'Clásica Parrillera','Carne a las brasas 160g, lechuga fresca de estación, tomate y queso edam.',20.0,30,'hamburguesas/h-2.jpg',NULL,'Carne 160g',1),
  (5,2,'Salchipapa Monumental','Salchicha frankfurter, papas amarillas fritas al punto, huevos de codorniz y lluvia de ají amarillo.',21.0,20,'hamburguesas/h-2.jpg','Favorito de Lima','Papa Amarilla',1),
  (6,2,'Salchichedar & Tocino','Chorizo parrillero artesanal, baño de queso cheddar líquido y trozos crujientes de tocino ahumado.',23.5,19,'hamburguesas/ha-1.jpg','Para compartir','Chorizo & Bacon',1),
  (7,2,'Salchipapa Mixta Las Musas','Doble porción de papas nativas con frankfurter y chorizo amazónico.',25.0,15,'hamburguesas/h-2.jpg',NULL,'Doble porción',1),
  (8,2,'Salchipapa Clásica','Papas nativas seleccionadas con salchicha frankfurter dorada y cremas de la casa.',17.0,30,'hamburguesas/ha-1.jpg',NULL,'La Tradicional',1),
  (9,3,'Chicha Morada 500ml','Preparada en casa con maíz morado, piña y especias.',8.0,40,NULL,NULL,'500 ml',1),
  (10,3,'Limonada Frozen','Limón fresco licuado con hielo, servida bien helada.',10.0,40,NULL,NULL,'Frozen',1),
  (11,3,'Cerveza Artesanal IPA','Cerveza limeña de barril, notas cítricas y amargor equilibrado.',16.0,24,NULL,'Barra','Barril',1),
  (12,4,'Combo Clásico Nocturno','Clásica Parrillera + papas nativas + bebida de la casa.',28.0,22,'hamburguesas/h-2.jpg','Rinde para 1','Rinde 1',1),
  (13,4,'Combo Doble Brasa','Doble Tocino & Cheddar + salchipapa personal + chicha morada.',34.0,15,'hamburguesas/ha-1.jpg','Más pedido','Rinde 1-2',1),
  (14,5,'Cookie Rellena de Nutella','Galleta tibia con centro fundido de avellanas.',12.0,20,NULL,NULL,'Tibia',1),
  (15,5,'Cheesecake de Maracuyá','Base de galleta, crema de queso y coulis de maracuyá.',14.0,16,NULL,NULL,'Frío',1),
  (16,6,'Mayonesa de la Casa','Mayonesa artesanal batida a diario.',1.0,100,'personalizar/mayonesa.jpg',NULL,NULL,1),
  (17,6,'Chimichurri Ahumado','Hierbas frescas, ajo y un toque ahumado.',1.0,100,'personalizar/mayonesa.jpg',NULL,NULL,1),
  (18,6,'Crema de Rocoto','Rocoto arequipeño licuado con un toque de queso.',1.0,100,'personalizar/mayonesa.jpg',NULL,NULL,1),
  (19,6,'Cheddar Fundido','Queso cheddar cremoso para bañar tus papas.',2.0,100,'personalizar/mayonesa.jpg',NULL,NULL,1),
  (20,6,'Alioli de Ajos Asados','Ajos asados al carbón emulsionados en aceite de oliva.',1.0,100,'personalizar/mayonesa.jpg',NULL,NULL,1);

-- (sin pedidos ni comprobantes: se generan probando la tienda y el panel)
