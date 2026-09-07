-- 005 — evita precios/existencias NULL que rompían la carta y el checkout.
UPDATE producto SET precio = 0 WHERE precio IS NULL;
UPDATE producto SET existencias = 0 WHERE existencias IS NULL;

ALTER TABLE producto MODIFY precio      FLOAT       NOT NULL DEFAULT 0;
ALTER TABLE producto MODIFY existencias SMALLINT(6) NOT NULL DEFAULT 0;
