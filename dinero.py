"""Importes de la venta: céntimos y redondeo comercial consistente."""
from decimal import Decimal, ROUND_HALF_UP


def dinero(valor):
    return Decimal(str(valor or 0)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
