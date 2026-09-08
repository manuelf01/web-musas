$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

# flask-jwt 0.3.2 usa PyJWT 1.x y no puede convivir con
# Flask-JWT-Extended. El proyecto ya no importa el paquete antiguo.
python -m pip uninstall --yes flask-jwt
python -m pip install --upgrade -r (Join-Path $projectRoot "requirements.txt")
python -m pip check
