-- MariaDB dump 10.19  Distrib 10.4.32-MariaDB, for Win64 (AMD64)
--
-- Host: localhost    Database: db_musuas
-- ------------------------------------------------------
-- Server version	10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `db_musuas`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `db_musuas` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;

USE `db_musuas`;

--
-- Table structure for table `categoriaproducto`
--

DROP TABLE IF EXISTS `categoriaproducto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `categoriaproducto` (
  `idCategoria` smallint(6) NOT NULL AUTO_INCREMENT,
  `nombreCategoria` varchar(50) NOT NULL,
  `descripcion` varchar(255) DEFAULT NULL,
  `imagen` varchar(255) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`idCategoria`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categoriaproducto`
--

LOCK TABLES `categoriaproducto` WRITE;
/*!40000 ALTER TABLE `categoriaproducto` DISABLE KEYS */;
INSERT INTO `categoriaproducto` VALUES (1,'Hamburguesas','Carne Angus a la brasa, pan brioche artesanal.',NULL,1),(2,'Salchipapas','Papas nativas crocantes, embutidos artesanales seleccionados y variedad de cremas limeñas de la casa.',NULL,1),(3,'Bebidas','Refrescos de la casa, gaseosas heladas y cervezas artesanales limeñas.',NULL,1),(4,'Combos','Combos nocturnos: hamburguesa o salchipapa + acompañamiento + bebida.',NULL,1),(5,'Postres','Postres recién hechos para cerrar la noche.',NULL,1),(6,'Cremas','Salsas artesanales de la casa para personalizar tu pedido.',NULL,1);
/*!40000 ALTER TABLE `categoriaproducto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comprobante`
--

DROP TABLE IF EXISTS `comprobante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comprobante` (
  `idComprobante` int(11) NOT NULL AUTO_INCREMENT,
  `idPedido` int(11) NOT NULL,
  `idUsuario` int(11) DEFAULT NULL,
  `dniNoRegistrado` char(8) NOT NULL,
  `fechaComprobante` date NOT NULL,
  `horaComprobante` time NOT NULL,
  `subTotal` float NOT NULL,
  `montoTotal` float NOT NULL,
  `igv` float NOT NULL,
  `numeroComprobante` varchar(25) NOT NULL,
  PRIMARY KEY (`idComprobante`),
  KEY `FKcomprobant749904` (`idUsuario`),
  KEY `FKcomprobant506863` (`idPedido`),
  CONSTRAINT `FKcomprobant506863` FOREIGN KEY (`idPedido`) REFERENCES `registropedido` (`idPedido`),
  CONSTRAINT `FKcomprobant749904` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comprobante`
--

LOCK TABLES `comprobante` WRITE;
/*!40000 ALTER TABLE `comprobante` DISABLE KEYS */;
INSERT INTO `comprobante` VALUES (9,35,10,'12345679','2026-09-08','00:16:06',15.25,18,2.75,'NV01-00000009');
/*!40000 ALTER TABLE `comprobante` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detallecomprobante`
--

DROP TABLE IF EXISTS `detallecomprobante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detallecomprobante` (
  `idComprobante` int(11) NOT NULL,
  `idProducto` int(11) NOT NULL,
  `nombreProducto` varchar(100) NOT NULL,
  `precioUnidad` float NOT NULL,
  `cantidad` smallint(6) NOT NULL,
  `precioTotal` float NOT NULL,
  PRIMARY KEY (`idComprobante`,`idProducto`),
  KEY `FKdetalleCom611488` (`idProducto`),
  CONSTRAINT `FKdetalleCom611488` FOREIGN KEY (`idProducto`) REFERENCES `producto` (`idProducto`),
  CONSTRAINT `FKdetalleCom998263` FOREIGN KEY (`idComprobante`) REFERENCES `comprobante` (`idComprobante`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detallecomprobante`
--

LOCK TABLES `detallecomprobante` WRITE;
/*!40000 ALTER TABLE `detallecomprobante` DISABLE KEYS */;
INSERT INTO `detallecomprobante` VALUES (9,2,'Smash Las Musas',18,1,18);
/*!40000 ALTER TABLE `detallecomprobante` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detallecremas`
--

DROP TABLE IF EXISTS `detallecremas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detallecremas` (
  `idPedido` int(11) NOT NULL,
  `idCrema` int(11) NOT NULL,
  `idDetalleOrden` int(11) NOT NULL,
  PRIMARY KEY (`idPedido`,`idCrema`,`idDetalleOrden`),
  KEY `FKdetalleCre999352` (`idDetalleOrden`,`idPedido`),
  KEY `FKdetalleCre352772` (`idCrema`),
  CONSTRAINT `FKdetalleCre352772` FOREIGN KEY (`idCrema`) REFERENCES `producto` (`idProducto`),
  CONSTRAINT `FKdetalleCre999352` FOREIGN KEY (`idDetalleOrden`, `idPedido`) REFERENCES `detalleorden` (`idDetalleOrden`, `idPedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detallecremas`
--

LOCK TABLES `detallecremas` WRITE;
/*!40000 ALTER TABLE `detallecremas` DISABLE KEYS */;
/*!40000 ALTER TABLE `detallecremas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalleorden`
--

DROP TABLE IF EXISTS `detalleorden`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `detalleorden` (
  `idDetalleOrden` int(11) NOT NULL,
  `idPedido` int(11) NOT NULL,
  `idProducto` int(11) NOT NULL,
  `nombreProducto` varchar(100) NOT NULL,
  `precioUnidad` float NOT NULL,
  `cantidad` smallint(6) NOT NULL,
  `precioTotal` float NOT NULL,
  PRIMARY KEY (`idDetalleOrden`,`idPedido`),
  KEY `FKdetalleOrd26951` (`idProducto`),
  KEY `FKdetalleOrd726046` (`idPedido`),
  CONSTRAINT `FKdetalleOrd26951` FOREIGN KEY (`idProducto`) REFERENCES `producto` (`idProducto`),
  CONSTRAINT `FKdetalleOrd726046` FOREIGN KEY (`idPedido`) REFERENCES `registropedido` (`idPedido`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalleorden`
--

LOCK TABLES `detalleorden` WRITE;
/*!40000 ALTER TABLE `detalleorden` DISABLE KEYS */;
INSERT INTO `detalleorden` VALUES (4,3,1,'Doble Tocino & Cheddar',24,1,24),(5,4,2,'Smash Las Musas',18,1,18),(6,5,12,'Combo Clásico Nocturno',28,1,28),(7,6,2,'Smash Las Musas',18,2,36),(8,7,3,'La Trufada Nocturna',26.5,1,26.5),(9,8,3,'La Trufada Nocturna',26.5,2,53),(10,9,2,'Smash Las Musas',18,2,36),(11,10,2,'Smash Las Musas',18,2,36),(12,11,5,'Salchipapa Monumental',21,2,42),(13,12,1,'Doble Tocino & Cheddar',24,1,24),(14,13,6,'Salchichedar & Tocino',23.5,1,23.5),(15,14,5,'Salchipapa Monumental',21,1,21),(16,15,1,'Doble Tocino & Cheddar',24,1,24),(17,16,2,'Smash Las Musas',18,1,18),(18,17,3,'La Trufada Nocturna',26.5,1,26.5),(19,18,2,'Smash Las Musas',18,1,18),(20,19,1,'Doble Tocino & Cheddar',24,1,24),(21,20,2,'Smash Las Musas',18,1,18),(22,21,2,'Smash Las Musas',18,2,36),(23,22,1,'Doble Tocino & Cheddar',24,2,48),(24,23,5,'Salchipapa Monumental',21,1,21),(25,24,5,'Salchipapa Monumental',21,1,21),(26,25,3,'La Trufada Nocturna',26.5,1,26.5),(27,26,2,'Smash Las Musas',18,2,36),(28,27,2,'Smash Las Musas',18,2,36),(29,28,6,'Salchichedar & Tocino',23.5,2,47),(30,29,12,'Combo Clásico Nocturno',28,1,28),(31,30,1,'Doble Tocino & Cheddar',24,1,24),(32,31,2,'Smash Las Musas',18,1,18),(33,32,2,'Smash Las Musas',18,1,18),(34,33,2,'Smash Las Musas',18,1,18),(35,34,2,'Smash Las Musas',18,1,18),(36,35,2,'Smash Las Musas',18,1,18);
/*!40000 ALTER TABLE `detalleorden` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto`
--

DROP TABLE IF EXISTS `producto`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `producto` (
  `idProducto` int(11) NOT NULL AUTO_INCREMENT,
  `idCategoria` smallint(6) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `precio` float NOT NULL DEFAULT 0,
  `existencias` smallint(6) NOT NULL DEFAULT 0,
  `imagen` varchar(255) DEFAULT NULL,
  `destacado` varchar(40) DEFAULT NULL,
  `nota` varchar(40) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`idProducto`),
  KEY `FKproducto802442` (`idCategoria`),
  CONSTRAINT `FKproducto802442` FOREIGN KEY (`idCategoria`) REFERENCES `categoriaproducto` (`idCategoria`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto`
--

LOCK TABLES `producto` WRITE;
/*!40000 ALTER TABLE `producto` DISABLE KEYS */;
INSERT INTO `producto` VALUES (1,1,'Doble Tocino & Cheddar','Doble carne Angus 180g, queso cheddar fundido, tocino crocante ahumado y salsa secreta de la casa.',24,20,'hamburguesas/ha-1.jpg','Más vendida','Brasas',1),(2,1,'Smash Las Musas','Carne crujiente smasheada, cebolla caramelizada al vino tinto, pepinillos y mayonesa trufada.',18,24,'hamburguesas/h-2.jpg','Especial de la casa','Smash 120g',1),(3,1,'La Trufada Nocturna','Champiñones salteados a la parrilla, queso suizo fundido y crema de trufa negra.',26.5,18,'hamburguesas/ha-1.jpg','Nueva','Trufa Negra',1),(4,1,'Clásica Parrillera','Carne a las brasas 160g, lechuga fresca de estación, tomate y queso edam.',20,30,'hamburguesas/h-2.jpg',NULL,'Carne 160g',1),(5,2,'Salchipapa Monumental','Salchicha frankfurter, papas amarillas fritas al punto, huevos de codorniz y lluvia de ají amarillo.',21,20,'hamburguesas/h-2.jpg','Favorito de Lima','Papa Amarilla',1),(6,2,'Salchichedar & Tocino','Chorizo parrillero artesanal, baño de queso cheddar líquido y trozos crujientes de tocino ahumado.',23.5,19,'hamburguesas/ha-1.jpg','Para compartir','Chorizo & Bacon',1),(7,2,'Salchipapa Mixta Las Musas','Doble porción de papas nativas con frankfurter y chorizo amazónico.',25,15,'hamburguesas/h-2.jpg',NULL,'Doble porción',1),(8,2,'Salchipapa Clásica','Papas nativas seleccionadas con salchicha frankfurter dorada y cremas de la casa.',17,30,'hamburguesas/ha-1.jpg',NULL,'La Tradicional',1),(9,3,'Chicha Morada 500ml','Preparada en casa con maíz morado, piña y especias.',8,40,NULL,NULL,'500 ml',1),(10,3,'Limonada Frozen','Limón fresco licuado con hielo, servida bien helada.',10,40,NULL,NULL,'Frozen',1),(11,3,'Cerveza Artesanal IPA','Cerveza limeña de barril, notas cítricas y amargor equilibrado.',16,24,NULL,'Barra','Barril',1),(12,4,'Combo Clásico Nocturno','Clásica Parrillera + papas nativas + bebida de la casa.',28,22,'hamburguesas/h-2.jpg','Rinde para 1','Rinde 1',1),(13,4,'Combo Doble Brasa','Doble Tocino & Cheddar + salchipapa personal + chicha morada.',34,15,'hamburguesas/ha-1.jpg','Más pedido','Rinde 1-2',1),(14,5,'Cookie Rellena de Nutella','Galleta tibia con centro fundido de avellanas.',12,20,NULL,NULL,'Tibia',1),(15,5,'Cheesecake de Maracuyá','Base de galleta, crema de queso y coulis de maracuyá.',14,16,NULL,NULL,'Frío',1),(16,6,'Mayonesa de la Casa','Mayonesa artesanal batida a diario.',1,100,'personalizar/mayonesa.jpg',NULL,NULL,1),(17,6,'Chimichurri Ahumado','Hierbas frescas, ajo y un toque ahumado.',1,100,'personalizar/mayonesa.jpg',NULL,NULL,1),(18,6,'Crema de Rocoto','Rocoto arequipeño licuado con un toque de queso.',1,100,'personalizar/mayonesa.jpg',NULL,NULL,1),(19,6,'Cheddar Fundido','Queso cheddar cremoso para bañar tus papas.',2,100,'personalizar/mayonesa.jpg',NULL,NULL,1),(20,6,'Alioli de Ajos Asados','Ajos asados al carbón emulsionados en aceite de oliva.',1,100,'personalizar/mayonesa.jpg',NULL,NULL,1),(28,1,'Internet','Velocidad de internet',30,50,'productos/3ff87c98291846a2.jpg',NULL,NULL,1);
/*!40000 ALTER TABLE `producto` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `registropedido`
--

DROP TABLE IF EXISTS `registropedido`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `registropedido` (
  `idPedido` int(11) NOT NULL,
  `idUsuario` int(11) DEFAULT NULL,
  `dniNoRegistrado` char(8) NOT NULL,
  `nombres` varchar(120) DEFAULT NULL,
  `numeroTelefono` char(9) NOT NULL,
  `estadoRecojo` tinyint(1) NOT NULL DEFAULT 0,
  `cancelado` tinyint(1) NOT NULL DEFAULT 0,
  `noShow` tinyint(1) NOT NULL DEFAULT 0,
  `horaRecojo` time NOT NULL,
  `fechaPedido` date NOT NULL DEFAULT curdate(),
  `estadoBoleta` tinyint(1) NOT NULL,
  `billeteraDigital` tinyint(1) NOT NULL,
  `keyPedido` smallint(6) NOT NULL,
  `notas` varchar(255) DEFAULT NULL,
  `estadoPrep` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`idPedido`),
  KEY `FKregistroPe851289` (`idUsuario`),
  CONSTRAINT `FKregistroPe851289` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `registropedido`
--

LOCK TABLES `registropedido` WRITE;
/*!40000 ALTER TABLE `registropedido` DISABLE KEYS */;
INSERT INTO `registropedido` VALUES (3,NULL,'77502489','Valeria Alarcón','998168813',1,0,0,'20:00:00','2026-09-06',0,1,7813,NULL,0),(4,NULL,'75737561','Valeria Alarcón','942427443',1,0,0,'20:00:00','2026-09-06',0,1,8853,NULL,0),(5,NULL,'76940704','Carlos Mendoza','969905511',1,0,0,'20:00:00','2026-09-06',0,1,7165,NULL,0),(6,NULL,'71959046','Diego Torres','936398925',1,0,0,'20:00:00','2026-09-06',0,1,8895,NULL,0),(7,NULL,'71386608','Mateo Rivas','960113903',1,0,0,'20:00:00','2026-09-05',0,1,3584,NULL,0),(8,NULL,'79268620','Diego Torres','975435098',1,0,0,'20:00:00','2026-09-05',0,0,7190,NULL,0),(9,NULL,'77475213','Camila Silva','917524138',1,0,0,'20:00:00','2026-09-05',0,1,2657,NULL,0),(10,NULL,'74646551','Lucía Ramírez','993638021',1,0,0,'20:00:00','2026-09-05',0,0,8478,NULL,0),(11,NULL,'77807841','Diego Torres','995865289',1,0,0,'20:00:00','2026-09-05',0,1,1852,NULL,0),(12,NULL,'75665652','Mateo Rivas','978958338',1,0,0,'20:00:00','2026-09-04',0,1,7704,NULL,0),(13,NULL,'72482123','Diego Torres','929435670',1,0,0,'20:00:00','2026-09-04',0,0,2483,NULL,0),(14,NULL,'76526880','Valeria Alarcón','945327700',1,0,0,'20:00:00','2026-09-04',0,1,5242,NULL,0),(15,NULL,'72335991','Camila Silva','977643608',1,0,0,'20:00:00','2026-09-04',0,0,9831,NULL,0),(16,NULL,'77127016','Mateo Rivas','965024602',1,0,0,'20:00:00','2026-09-04',0,1,1241,NULL,0),(17,NULL,'73110620','Camila Silva','973548085',1,0,0,'20:00:00','2026-09-03',0,1,7830,NULL,0),(18,NULL,'72199070','Camila Silva','947809871',1,0,0,'20:00:00','2026-09-03',0,1,6300,NULL,0),(19,NULL,'77650549','Lucía Ramírez','921250180',1,0,0,'20:00:00','2026-09-03',0,0,3849,NULL,0),(20,NULL,'75402288','Camila Silva','973941063',1,0,0,'20:00:00','2026-09-03',0,0,4697,NULL,0),(21,NULL,'75809360','Carlos Mendoza','984940863',1,0,0,'20:00:00','2026-09-03',0,0,9451,NULL,0),(22,NULL,'75010171','Sofía Paredes','993044286',1,0,0,'20:00:00','2026-09-02',0,0,5082,NULL,0),(23,NULL,'79355206','Valeria Alarcón','927418171',1,0,0,'20:00:00','2026-09-02',0,1,8877,NULL,0),(24,NULL,'72830752','Sofía Paredes','910131345',1,0,0,'20:00:00','2026-09-02',0,1,5104,NULL,0),(25,NULL,'71296299','Diego Torres','940276418',1,0,0,'20:00:00','2026-09-02',0,1,6750,NULL,0),(26,NULL,'77865735','Valeria Alarcón','935483794',1,0,0,'20:00:00','2026-09-02',0,0,6700,NULL,0),(27,NULL,'73799211','Sofía Paredes','934664581',1,0,0,'20:00:00','2026-09-02',0,0,1965,NULL,0),(28,NULL,'75039287','Carlos Mendoza','931927364',1,0,0,'20:00:00','2026-09-01',0,1,9046,NULL,0),(29,NULL,'76792166','Lucía Ramírez','967988011',1,0,0,'20:00:00','2026-09-01',0,0,1634,NULL,0),(30,NULL,'79390918','Lucía Ramírez','917715882',1,0,0,'20:00:00','2026-09-01',0,1,2479,NULL,0),(31,10,'12345679','Cliente Prueba','912345678',1,0,0,'18:00:00','2026-09-07',0,1,7168,NULL,0),(32,10,'12345679','Cliente Prueba','912345678',1,0,0,'18:30:00','2026-09-07',0,1,7389,NULL,0),(33,10,'12345679','Cliente Prueba','912345678',0,0,1,'18:00:00','2026-09-07',0,1,4175,NULL,0),(34,10,'12345679','Cliente Prueba','912345678',0,0,0,'18:00:00','2026-09-07',0,1,3303,NULL,0),(35,10,'12345679','Cliente Prueba','912345678',1,0,0,'18:00:00','2026-09-08',0,1,4135,NULL,2);
/*!40000 ALTER TABLE `registropedido` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `usuario` (
  `idUsuario` int(11) NOT NULL AUTO_INCREMENT,
  `dni` char(8) NOT NULL,
  `nombres` varchar(100) NOT NULL,
  `apellidos` varchar(100) NOT NULL,
  `correo` varchar(200) NOT NULL,
  `numTelf` char(9) NOT NULL,
  `contraseña` varchar(255) NOT NULL,
  `tipoUsuario` tinyint(1) NOT NULL,
  `noShows` smallint(6) NOT NULL DEFAULT 0,
  `rol` varchar(20) NOT NULL DEFAULT 'usuario',
  `activo` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario`
--

LOCK TABLES `usuario` WRITE;
/*!40000 ALTER TABLE `usuario` DISABLE KEYS */;
INSERT INTO `usuario` VALUES (7,'12345678','Piero','Ramirez','admin@lasmusas.pe','987654321','pbkdf2:sha256:260000$9NdZxBoiwU7Glat1$e30d355548649eb50634a016565eef0ddf7e624233fc092986ce06bd4cc59d1f',0,0,'superusuario',1),(10,'12345679','Cliente','Prueba','cliente.prueba@correo.com','912345678','pbkdf2:sha256:260000$i1kyMBydXQW3MKyU$5a36ac78a5b80d9491d394a3bed7f99499c641d3886617ee0214e4d550d7307c',1,0,'usuario',1),(11,'87654321','Admin','Prueba','admin.prueba@lasmusas.pe','987654321','pbkdf2:sha256:260000$giZ9CIte9ylcNGUc$60a482b267b2aa943e1dd978bfbb2d6052c4e306c9ab4da6bb10b5183f3f238f',0,0,'administrador',1),(17,'12365478','Mnuel','Pureba','prueba@gmail.com','123654789','pbkdf2:sha256:260000$DR46H3IFDWMBkBlw$697125d4126ba30ff184ce0e249927dbfa359b8dae04161a3d205508d40c2e31',0,0,'superusuario',1);
/*!40000 ALTER TABLE `usuario` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-08  1:24:05
