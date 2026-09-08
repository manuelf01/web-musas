-- 010 — tres roles de cuenta + estado (activo / dado de baja) en las entidades
-- que el panel administra. Columnas al final para no correr índices posicionales.

-- Rol: 'superusuario' | 'administrador' | 'usuario'.
-- Se deriva del tipoUsuario actual (0 = admin, 1 = cliente) y el primer admin
-- (idUsuario más bajo) queda como superusuario.
ALTER TABLE usuario
  ADD COLUMN rol   VARCHAR(20) NOT NULL DEFAULT 'usuario',
  ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1;

UPDATE usuario SET rol = 'administrador' WHERE tipoUsuario = 0;
UPDATE usuario SET rol = 'usuario'       WHERE tipoUsuario = 1;
UPDATE usuario
  SET rol = 'superusuario'
  WHERE tipoUsuario = 0
  ORDER BY idUsuario
  LIMIT 1;

-- Estado para "dar de baja" (no se borra, deja de mostrarse / operar).
ALTER TABLE producto          ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1;
ALTER TABLE categoriaProducto ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1;
