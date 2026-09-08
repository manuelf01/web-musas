from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def admin_required():
    """Exige un JWT válido cuyo claim de rol sea administrador."""

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            if get_jwt().get("rol") != "admin":
                return jsonify({"success": False, "message": "Permisos insuficientes"}), 403
            return function(*args, **kwargs)

        return wrapper

    return decorator
