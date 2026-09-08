from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token

from model.Autenticacion import Autenticacion


api_autenticacion = Blueprint("api_autenticacion", __name__)


@api_autenticacion.post("/auth")
def crear_token():
    datos = request.get_json(silent=True) or {}
    dni = str(datos.get("username", "")).strip()
    password = str(datos.get("password", ""))
    tipo_recibido = datos.get("tipoUsuario", False)
    tipo = tipo_recibido if isinstance(tipo_recibido, bool) else str(tipo_recibido).lower() in {"1", "true", "cliente"}

    if not dni or not password:
        return jsonify({"success": False, "message": "Credenciales obligatorias"}), 400

    usuario = Autenticacion.autenticar_api(dni, password, tipo)
    if usuario is None:
        return jsonify({"success": False, "message": "Credenciales incorrectas"}), 401

    rol = "cliente" if usuario[7] else "admin"
    token = create_access_token(
        identity=str(usuario[0]),
        additional_claims={"rol": rol, "dni": usuario[1]},
    )
    return jsonify({"access_token": token, "token_type": "Bearer", "rol": rol})
