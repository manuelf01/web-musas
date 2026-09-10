@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo No se encuentra el entorno Python .venv.
    pause
    exit /b 1
)
set FLASK_DEBUG=1
set MUSAS_DEMO=
if /I "%~1"=="demo" set MUSAS_DEMO=1
echo Verifica que MySQL este iniciado en XAMPP.
echo Abre http://127.0.0.1:5000 en tu navegador.
".venv\Scripts\python.exe" app.py
pause
