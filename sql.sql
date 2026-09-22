-- =====================================================================
--  Las Musas — Base de datos completa (crear desde cero)
-- =====================================================================
--  Este archivo YA incluye todos los cambios de migrations/001..013.
--  Para levantar el proyecto desde cero:
--    1. Abre phpMyAdmin (XAMPP) → pestaña "SQL"
--    2. Copia y pega TODO este archivo y ejecútalo.
--  Crea la base `db_musuas` (nombre que espera cfg.py) con datos de ejemplo.
--
--  Cuentas de ejemplo (contraseña de todas: Musas2026)
--    DNI 12345678  → superusuario  (acceso total al panel + gestión de usuarios)
--    DNI 87654321  → administrador (panel sin la sección Usuarios)
--    cliente@correo.com → usuario  (cliente de la tienda; inicia por correo)
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
  `dni`         char(8)      DEFAULT NULL,
  `nombres`     varchar(100) NOT NULL,
  `apellidos`   varchar(100) NOT NULL,
  `correo`      varchar(200) NOT NULL,
  `numTelf`     char(9)      NOT NULL,
  `contraseña`  varchar(255) NOT NULL,          -- hash werkzeug (pbkdf2:sha256)
  `tipoUsuario` tinyint(1)   NOT NULL,          -- 0 = panel, 1 = cliente
  `noShows`     smallint(6)  NOT NULL DEFAULT 0,-- veces que no recogió su pedido
  `rol`         varchar(20)  NOT NULL DEFAULT 'usuario',
  `activo`      tinyint(1)   NOT NULL DEFAULT 1,
  `fotoPerfil`  varchar(255) DEFAULT NULL,      -- p. ej. perfiles/ab12.jpg (static/img/)
  PRIMARY KEY (`idUsuario`),
  UNIQUE KEY `uq_usuario_correo` (`correo`)
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
  `precio`      decimal(12,2) NOT NULL DEFAULT 0,
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
--  registroPedido  — cabecera del pedido. idPedido = AUTO_INCREMENT
--  (lo asigna la base; ver migración 011).
--    estadoRecojo 0/1  = pendiente / entregado
--    cancelado    0/1  = lo canceló el cliente o el admin
--    noShow       0/1  = el cliente no vino a recogerlo
--    estadoPrep   0/1/2 = recibido / en preparación / listo para recojo
--    keyPedido    = palabra clave de 4 dígitos que el cliente da al recoger
--    medioPagoElegido = efectivo / tarjeta / yape / plin
--    correoRecojo / nombres / numeroTelefono = snapshot de la cuenta
--    dniNoRegistrado se solicita en caja al emitir boleta o factura
-- ---------------------------------------------------------------------
CREATE TABLE `registroPedido` (
  `idPedido`         int(11)     NOT NULL AUTO_INCREMENT,
  `idUsuario`        int(11)     DEFAULT NULL,
  `dniNoRegistrado`  varchar(11) DEFAULT NULL,
  `nombres`          varchar(120) DEFAULT NULL,
  `correoRecojo`     varchar(200) DEFAULT NULL,
  `numeroTelefono`   char(9)     NOT NULL,
  `estadoRecojo`     tinyint(1)  NOT NULL DEFAULT 0,
  `cancelado`        tinyint(1)  NOT NULL DEFAULT 0,
  `noShow`           tinyint(1)  NOT NULL DEFAULT 0,
  `horaRecojo`       time        NOT NULL,
  `fechaPedido`      date        NOT NULL DEFAULT (CURRENT_DATE),
  `estadoBoleta`     tinyint(1)  NOT NULL DEFAULT 0,
  `billeteraDigital` tinyint(1)  NOT NULL,
  `medioPagoElegido` varchar(20) NOT NULL DEFAULT 'efectivo',
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
  `idDetalleOrden` int(11)      NOT NULL AUTO_INCREMENT,
  `idPedido`       int(11)      NOT NULL,
  `idProducto`     int(11)      NOT NULL,
  `nombreProducto` varchar(100) NOT NULL,
  `precioUnidad`   decimal(12,2) NOT NULL,
  `cantidad`       smallint(6)  NOT NULL,
  `precioTotal`    decimal(12,2) NOT NULL,
  `adicionales`    text         DEFAULT NULL,
  PRIMARY KEY (`idDetalleOrden`,`idPedido`),
  KEY `FKdetalleOrd26951` (`idProducto`),
  KEY `FKdetalleOrd726046` (`idPedido`),
  CONSTRAINT `FKdetalleOrd26951`  FOREIGN KEY (`idProducto`) REFERENCES `producto` (`idProducto`),
  CONSTRAINT `FKdetalleOrd726046` FOREIGN KEY (`idPedido`)   REFERENCES `registroPedido` (`idPedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- ---------------------------------------------------------------------
--  comprobante / detalleComprobante  — venta emitida al ENTREGAR el
--  pedido (Pedido._emitir_comprobante). numeroComprobante usa B001 para
--  boleta y F001 para factura. El documento admite DNI (8) o RUC (11).
-- ---------------------------------------------------------------------
CREATE TABLE `comprobante` (
  `idComprobante`     int(11)      NOT NULL AUTO_INCREMENT,
  `idPedido`          int(11)      NOT NULL,
  `idUsuario`         int(11)      DEFAULT NULL,
  `dniNoRegistrado`   varchar(11)  DEFAULT NULL,
  `tipoComprobante`   varchar(10)  NOT NULL DEFAULT 'boleta',
  `razonSocial`       varchar(200) DEFAULT NULL,
  `fechaComprobante`  date         NOT NULL,
  `horaComprobante`   time         NOT NULL,
  `subTotal`          decimal(12,2) NOT NULL,
  `montoTotal`        decimal(12,2) NOT NULL,
  `igv`               decimal(12,2) NOT NULL,
  `numeroComprobante` varchar(25)  DEFAULT NULL,
  `medioPago`         varchar(20)  NOT NULL DEFAULT 'No registrado',
  `idCajero`          int(11)      DEFAULT NULL,
  `datosEmision`      longtext     DEFAULT NULL,
  `anulado`           tinyint(1)   NOT NULL DEFAULT 0,
  `motivoAnulacion`   varchar(255) DEFAULT NULL,
  `fechaAnulacion`    datetime     DEFAULT NULL,
  `idAnulador`        int(11)      DEFAULT NULL,
  `stockDevuelto`     tinyint(1)   NOT NULL DEFAULT 0,
  PRIMARY KEY (`idComprobante`),
  KEY `FKcomprobant749904` (`idUsuario`),
  UNIQUE KEY `uq_comprobante_pedido` (`idPedido`),
  UNIQUE KEY `uq_comprobante_numero` (`numeroComprobante`),
  KEY `FKcomprobant506863` (`idPedido`),
  KEY `fk_comprobante_cajero` (`idCajero`),
  CONSTRAINT `FKcomprobant506863` FOREIGN KEY (`idPedido`)  REFERENCES `registroPedido` (`idPedido`),
  CONSTRAINT `FKcomprobant749904` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`),
  CONSTRAINT `fk_comprobante_cajero` FOREIGN KEY (`idCajero`) REFERENCES `usuario` (`idUsuario`),
  CONSTRAINT `fk_comprobante_anulador` FOREIGN KEY (`idAnulador`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE `detalleComprobante` (
  `idLinea`        int(11)      NOT NULL AUTO_INCREMENT,
  `idComprobante`  int(11)      NOT NULL,
  `idProducto`     int(11)      NOT NULL,
  `nombreProducto` varchar(100) NOT NULL,
  `precioUnidad`   decimal(12,2) NOT NULL,
  `cantidad`       smallint(6)  NOT NULL,
  `precioTotal`    decimal(12,2) NOT NULL,
  `adicionales`    text         DEFAULT NULL,
  PRIMARY KEY (`idLinea`),
  KEY `idx_detalle_comprobante` (`idComprobante`),
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
-- Categorías y productos: menú real del negocio (verificado en su
-- plataforma de pedidos en línea), no ficticio. Salsas/Papas/Agregados
-- (13/12/11) son categorías ocultas: se usan para personalizar cada
-- hamburguesa (salsa obligatoria, papas obligatorias, agregados de pago
-- opcionales) y nunca se muestran en la carta pública.
INSERT INTO `categoriaProducto` (`idCategoria`,`nombreCategoria`,`descripcion`,`imagen`,`activo`) VALUES
  (1,'Hamburguesas Simples','Hamburguesa sencilla con papas y tu salsa a elección.',NULL,1),
  (2,'Hamburguesas Royal','Hamburguesa con huevo frito, papas y tu salsa a elección.',NULL,1),
  (3,'Hamburguesas Mixtas','Hamburguesa con hot dog o tocino, huevo, papas y tu salsa a elección.',NULL,1),
  (4,'Hamburguesas Hawaianas','Hamburguesa con queso, jamón y piña o durazno, papas y tu salsa a elección.',NULL,1),
  (5,'Hamburguesas a lo Pobre','Hamburguesa con huevo y plátano frito, papas y tu salsa a elección.',NULL,1),
  (6,'Hamburguesas Especiales','Hamburguesa con queso, jamón y hot dog o salame, papas y tu salsa a elección.',NULL,1),
  (7,'Maxi Burgers','Las hamburguesas más grandes de la casa, para el hambre de verdad.',NULL,1),
  (8,'Platos Especiales','Salchipapas y platos para compartir.',NULL,1),
  (9,'Combos','Combos que rinden para más de una persona.',NULL,1),
  (10,'Bebidas','Gaseosas, chicha morada y agua, bien heladas.',NULL,1),
  (11,'Salsas','Elige la salsa de tu hamburguesa. No se muestra en la carta pública.',NULL,1),
  (12,'Papas','Elige el tipo de papas de tu hamburguesa. No se muestra en la carta pública.',NULL,1),
  (13,'Agregados','Extras de pago para tu hamburguesa. No se muestra en la carta pública.',NULL,1);

-- Productos
INSERT INTO `producto` (`idProducto`,`idCategoria`,`nombre`,`descripcion`,`precio`,`existencias`,`imagen`,`destacado`,`nota`,`activo`) VALUES
  (1,1,'Simple de Pollo','Hamburguesa de pollo con papas y tu salsa a elección.',7.00,30,'menu/simple-de-pollo.jpg',NULL,NULL,1),
  (2,1,'Simple de Carne','Hamburguesa de carne con papas y tu salsa a elección.',8.50,30,'menu/simple-de-carne.jpg',NULL,NULL,1),
  (3,1,'Simple de Chorizo','Hamburguesa de chorizo con papas y tu salsa a elección.',7.00,30,NULL,NULL,NULL,1),
  (4,1,'Simple de Filete de Pollo','Hamburguesa de filete de pollo con papas y tu salsa a elección.',8.50,30,NULL,NULL,NULL,1),
  (5,2,'Pollo con Huevo','Hamburguesa de pollo con huevo frito, papas y tu salsa a elección.',9.00,30,NULL,NULL,NULL,1),
  (6,2,'Carne con Huevo','Hamburguesa de carne con huevo frito, papas y tu salsa a elección.',10.50,30,'menu/carne-con-huevo.jpg',NULL,NULL,1),
  (7,2,'Chorizo con Huevo','Hamburguesa de chorizo con huevo frito, papas y tu salsa a elección.',9.00,30,NULL,NULL,NULL,1),
  (8,2,'Filete de Pollo con Huevo','Hamburguesa de filete de pollo con huevo frito, papas y tu salsa a elección.',10.50,30,NULL,NULL,NULL,1),
  (9,3,'Pollo, Huevo y Hot Dog','Hamburguesa de pollo con huevo y hot dog, papas y tu salsa a elección.',11.00,25,NULL,NULL,NULL,1),
  (10,3,'Carne, Huevo y Hot Dog','Hamburguesa de carne con huevo y hot dog, papas y tu salsa a elección.',12.50,25,NULL,NULL,NULL,1),
  (11,3,'Pollo, Huevo y Tocino','Hamburguesa de pollo con huevo y tocino, papas y tu salsa a elección.',11.00,25,NULL,NULL,NULL,1),
  (12,3,'Carne, Huevo y Tocino','Hamburguesa de carne con huevo y tocino, papas y tu salsa a elección.',12.50,25,'menu/carne-huevo-tocino.jpg',NULL,NULL,1),
  (13,3,'Filete de Pollo, Huevo y Hot Dog','Hamburguesa de filete de pollo con huevo y hot dog, papas y tu salsa a elección.',12.50,25,NULL,NULL,NULL,1),
  (14,4,'Pollo, Queso, Jamón y Piña','Hamburguesa hawaiana de pollo con queso, jamón y piña, papas y tu salsa a elección.',13.00,25,NULL,NULL,NULL,1),
  (15,4,'Carne, Queso, Jamón y Piña','Hamburguesa hawaiana de carne con queso, jamón y piña, papas y tu salsa a elección.',14.50,25,'menu/carne-queso-jamon-pina.jpg',NULL,NULL,1),
  (16,4,'Pollo, Queso, Jamón y Durazno','Hamburguesa hawaiana de pollo con queso, jamón y durazno, papas y tu salsa a elección.',13.00,25,NULL,NULL,NULL,1),
  (17,4,'Carne, Queso, Jamón y Durazno','Hamburguesa hawaiana de carne con queso, jamón y durazno, papas y tu salsa a elección.',14.50,25,NULL,NULL,NULL,1),
  (18,4,'Filete de Pollo, Queso, Jamón y Piña','Hamburguesa hawaiana de filete de pollo con queso, jamón y piña, papas y tu salsa a elección.',14.50,25,NULL,NULL,NULL,1),
  (19,4,'Filete de Pollo, Queso, Jamón y Durazno','Hamburguesa hawaiana de filete de pollo con queso, jamón y durazno, papas y tu salsa a elección.',14.50,25,NULL,NULL,NULL,1),
  (20,5,'Pollo, Huevo y Plátano','Hamburguesa a lo pobre de pollo con huevo y plátano frito, papas y tu salsa a elección.',11.00,25,NULL,NULL,NULL,1),
  (21,5,'Carne, Huevo y Plátano','Hamburguesa a lo pobre de carne con huevo y plátano frito, papas y tu salsa a elección.',12.50,25,'menu/carne-huevo-platano.jpg',NULL,NULL,1),
  (22,5,'Filete de Pollo, Huevo y Plátano','Hamburguesa a lo pobre de filete de pollo con huevo y plátano frito, papas y tu salsa a elección.',12.50,25,NULL,NULL,NULL,1),
  (23,6,'Filete de Pollo, Queso, Jamón y Hot Dog','Hamburguesa especial de filete de pollo con queso, jamón y hot dog, papas y tu salsa a elección.',14.50,20,NULL,NULL,NULL,1),
  (24,6,'Filete de Pollo, Queso, Jamón y Salame','Hamburguesa especial de filete de pollo con queso, jamón y salame, papas y tu salsa a elección.',14.50,20,NULL,NULL,NULL,1),
  (25,6,'Pollo, Queso, Jamón y Hot Dog','Hamburguesa especial de pollo con queso, jamón y hot dog, papas y tu salsa a elección.',13.00,20,NULL,NULL,NULL,1),
  (26,6,'Carne, Queso, Jamón y Hot Dog','Hamburguesa especial de carne con queso, jamón y hot dog, papas y tu salsa a elección.',14.50,20,NULL,NULL,NULL,1),
  (27,7,'A lo Pobre Especial Pollo','Pollo deshilachado, huevo, plátano, queso, jamón y hot dog.',17.00,15,'menu/a-lo-pobre-especial-pollo.jpg',NULL,NULL,1),
  (28,7,'A lo Pobre Especial Carne','Carne, huevo, plátano, queso, jamón y hot dog.',18.50,15,NULL,NULL,NULL,1),
  (29,7,'Carnívora','Carne, jamón, queso, chorizo parrillero, tocino y salame.',18.00,15,NULL,NULL,NULL,1),
  (30,7,'Las Musas','Carne o pollo, chorizo, huevo, queso, jamón, hot dog, salame y piña.',20.00,15,NULL,NULL,NULL,1),
  (31,8,'Salchipapa','Papas fritas con hot dog y ensalada.',12.00,25,'menu/salchipapa.jpg',NULL,NULL,1),
  (32,8,'Pollipapa','Papas fritas con presa de pollo y ensalada.',13.00,25,'menu/pollipapa.jpg',NULL,NULL,1),
  (33,8,'Salchipollo','Papas fritas con presa de pollo, ensalada y hot dog.',15.00,20,'menu/salchipollo.jpg',NULL,NULL,1),
  (34,8,'Salchitodo','Chorizo parrillero, huevo, queso, hot dog ahumado, pollo deshilachado, ensalada y papas.',18.00,15,'menu/salchitodo.jpg',NULL,NULL,1),
  (35,8,'Salchimusas','Papas, ensalada, chorizo parrillero, hot dog ahumado, tocino y queso derretido. Para 2 personas.',27.00,10,'menu/salchimusas.jpg',NULL,NULL,1),
  (36,9,'Combo Salchimusas','1 Salchimusas + 2 Chicha Morada.',30.00,10,'menu/combo-salchimusas.jpg',NULL,NULL,1),
  (37,10,'Chicha Morada Natural','500 ml hecha con 100% ingredientes naturales, sin saborizantes ni preservantes.',3.00,50,'menu/chicha-morada-natural.jpg',NULL,NULL,1),
  (38,10,'Agua San Carlos','Agua San Carlos 500 ml.',2.00,50,'menu/agua-san-carlos.jpg',NULL,NULL,1),
  (39,10,'Coca-Cola','Coca-Cola 600 ml.',4.00,50,'menu/coca-cola.jpg',NULL,NULL,1),
  (40,10,'Inca Kola','Inca Kola 600 ml.',4.00,50,'menu/inca-kola.jpg',NULL,NULL,1),
  (41,11,'Mayonesa','Salsa clásica para tu hamburguesa.',0.00,999,NULL,NULL,NULL,1),
  (42,11,'Ketchup','Salsa clásica para tu hamburguesa.',0.00,999,NULL,NULL,NULL,1),
  (43,11,'Ají','Salsa picante de la casa.',0.00,999,NULL,NULL,NULL,1),
  (44,11,'Salsa Golf','Mezcla de mayonesa y ketchup.',0.00,999,NULL,NULL,NULL,1),
  (45,11,'Aceituna','Salsa de aceituna.',0.00,999,NULL,NULL,NULL,1),
  (46,11,'Mostaza','Salsa clásica para tu hamburguesa.',0.00,999,NULL,NULL,NULL,1),
  (47,11,'Tártara','Salsa tártara de la casa.',0.00,999,NULL,NULL,NULL,1),
  (48,12,'Papas al hilo','Papas cortadas finas y crocantes.',0.00,999,NULL,NULL,NULL,1),
  (49,12,'Papas Gruesas','Papas cortadas gruesas.',0.00,999,NULL,NULL,NULL,1),
  (50,12,'Sin papas','Tu hamburguesa sin papas.',0.00,999,NULL,NULL,NULL,1),
  (51,13,'Hot Dog','Agrega un hot dog a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (52,13,'Jamón','Agrega jamón a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (53,13,'Piña','Agrega piña a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (54,13,'Durazno','Agrega durazno a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (55,13,'Plátano','Agrega plátano frito a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (56,13,'Salame','Agrega salame a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (57,13,'Queso','Agrega queso a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (58,13,'Tocino','Agrega tocino a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (59,13,'Huevo','Agrega un huevo frito a tu hamburguesa.',2.00,999,NULL,NULL,NULL,1),
  (60,13,'Presa de Pollo','Agrega una presa de pollo a tu hamburguesa.',6.00,999,NULL,NULL,NULL,1);

-- (sin pedidos ni comprobantes: se generan probando la tienda y el panel)
