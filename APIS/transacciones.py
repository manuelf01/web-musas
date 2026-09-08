from flask import Blueprint, jsonify, request, session
from model.Transaccion import DatosCompraInvalidos, Transaccion
transaccion = Blueprint('transaccion', __name__)

@transaccion.route('/transaccion_compra', methods=['POST'])
def transaccion_compra():
    try:
        datos = request.get_json(silent=True) or {}
        resultado = Transaccion.insertarCompra(
            datos.get("datosPedido"),
            datos.get("productos"),
            session.get("cliente.auth"),
        )
        return jsonify({
            "success": True,
            "mensaje": "Compra registrada correctamente",
            "status": "1",
            "pedido": resultado,
        }), 201
    except DatosCompraInvalidos as error:
        return jsonify({"success": False, "mensaje": str(error), "status": "0"}), 400
    except Exception:
        return jsonify({
            "success": False,
            "mensaje": "No se pudo registrar la compra",
            "status": "0",
        }), 500

@transaccion.route('/transaccion_comprobante', methods=['POST'])
def transaccion_comprobante():
    try:
        datos = request.get_json(silent=True) or {}
        idPedido = datos.get("idPedido")
        keyPedido = datos.get("keyPedido")
        rpta = Transaccion.insertarComprobante(idPedido, keyPedido)
        if rpta:
            return jsonify({"mensaje": "Comprobante registrado correctamente", "status":"1"})
        return jsonify({"mensaje": "KeyPedido incorrecto", "status":"0"})
    except Exception:
        return jsonify({"mensaje": "Error al registrar el comprobante", "status":"0"}), 500
