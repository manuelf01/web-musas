# Ejecutar Las Musas en Windows

El proyecto está en la rama `Ramirez`. El entorno `.venv` usa Python 3.10 y las dependencias de `requirements.txt`.

1. En XAMPP, inicia **MySQL**. Apache no es necesario para Flask.
2. Ejecuta `iniciar.bat` con doble clic.
3. Abre http://127.0.0.1:5000.

Para detener el servidor iniciado con ese archivo, presiona Ctrl+C en su ventana.

Para probar pedidos fuera del horario habitual, ejecuta en PowerShell:

```powershell
.\iniciar.bat demo
```

## Cuentas de ejemplo

En esta base local se conserva la contraseña `musas2026`. La versión nueva de `sql.sql` utiliza `Musas2026` (con mayúscula) para instalaciones desde cero.

| DNI | Rol |
| --- | --- |
| 12345678 | Superusuario |
| 87654321 | Administrador |
| 12345679 | Cliente |

El acceso al panel requiere completar el captcha.

## Configuración preparada

- `cfg.py`: conexión a MariaDB local, puerto 3306, base `db_musuas`, usuario `root` sin contraseña y clave de sesión aleatoria. Está excluido de Git.
- Base inicializada desde `sql.sql`: 20 productos y 3 usuarios.
- Actualizada a `43198ae` de `Ramirez`, con migración 011 aplicada sin recrear los datos. El respaldo previo está en `.local-runtime/db_musuas-antes-43198ae-20260908-173927.sql`.
- La funcionalidad de comprobantes requiere `migrations/012_comprobantes_pdf.sql`. Aplícala desde phpMyAdmin sobre una base existente después de crear un respaldo. Las instalaciones nuevas ya la incluyen en `sql.sql`.
- No vuelvas a importar `sql.sql` si quieres conservar tus datos: elimina y recrea las tablas.
- `.local-runtime/` contiene archivos auxiliares locales y está excluido de Git.

El servidor inicial se dejó en segundo plano. Para detenerlo antes de iniciar otra instancia, ejecuta en PowerShell desde esta carpeta:

```powershell
$musasServerId = [int](Get-Content .local-runtime\server.pid)
$musasProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $musasServerId"
if ($musasProcess.ExecutablePath -eq (Join-Path $PWD '.venv\Scripts\python.exe') -and $musasProcess.CommandLine -like '*flask --app app run*') {
    Stop-Process -Id $musasServerId
}
```
