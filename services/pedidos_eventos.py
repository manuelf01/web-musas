"""Señal en memoria para despertar las conexiones SSE de la cocina.

La base de datos sigue siendo la fuente de verdad. Esta condición solamente
evita esperar al siguiente latido cuando una petición del mismo proceso cambia
un pedido.
"""

from threading import Condition


_condicion = Condition()
_version = 0


def version_actual():
    with _condicion:
        return _version


def notificar_cambio_pedidos():
    """Despierta todas las pantallas de cocina conectadas."""
    global _version
    with _condicion:
        _version += 1
        _condicion.notify_all()


def esperar_cambio_pedidos(version, timeout=15):
    """Espera una señal o el latido periódico y devuelve la versión actual."""
    with _condicion:
        _condicion.wait_for(lambda: _version != version, timeout=timeout)
        return _version
