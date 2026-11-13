-- Garantiza que una persona no tenga varias cuentas identificadas con el mismo DNI.
-- Los clientes que aún no registran DNI conservan NULL; MySQL permite múltiples NULL en un índice UNIQUE.
ALTER TABLE usuario
  ADD UNIQUE KEY uq_usuario_dni (dni);
