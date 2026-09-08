-- =====================================================================
--  011 — idPedido e idDetalleOrden pasan a AUTO_INCREMENT
-- =====================================================================
--  Motivo: la app asignaba el id con SELECT COALESCE(MAX(id),0)+1. Con dos
--  pedidos entrando a la vez, ambos calculaban el mismo id y uno de los
--  INSERT fallaba (o dejaba líneas huérfanas). Ahora lo asigna la base.
--
--  Los ids existentes NO cambian; el AUTO_INCREMENT arranca en MAX+1.
--  Aplicar en phpMyAdmin (XAMPP) sobre la base `db_musuas`.
-- =====================================================================

SET FOREIGN_KEY_CHECKS = 0;

ALTER TABLE `registroPedido`
  MODIFY `idPedido` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `detalleOrden`
  MODIFY `idDetalleOrden` int(11) NOT NULL AUTO_INCREMENT;

SET FOREIGN_KEY_CHECKS = 1;
