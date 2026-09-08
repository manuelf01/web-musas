"""Utilidades de formato para comprobantes."""

_UNIDADES = ("", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho", "nueve",
             "diez", "once", "doce", "trece", "catorce", "quince", "dieciséis",
             "diecisiete", "dieciocho", "diecinueve", "veinte")
_DECENAS = ("", "", "veinti", "treinta", "cuarenta", "cincuenta", "sesenta",
            "setenta", "ochenta", "noventa")
_CENTENAS = ("", "ciento", "doscientos", "trescientos", "cuatrocientos", "quinientos",
             "seiscientos", "setecientos", "ochocientos", "novecientos")


def _cientos(n):
    if n == 0:
        return ""
    if n == 100:
        return "cien"
    c, resto = divmod(n, 100)
    partes = []
    if c:
        partes.append(_CENTENAS[c])
    if resto:
        if resto <= 20:
            partes.append(_UNIDADES[resto])
        else:
            d, u = divmod(resto, 10)
            if d == 2:
                partes.append("veinti" + _UNIDADES[u] if u else "veinte")
            else:
                partes.append(_DECENAS[d] + (" y " + _UNIDADES[u] if u else ""))
    return " ".join(partes)


def _entero_a_texto(n):
    if n == 0:
        return "cero"
    if n < 0:
        return "menos " + _entero_a_texto(-n)
    millones, resto = divmod(n, 1_000_000)
    miles, cientos = divmod(resto, 1000)
    partes = []
    if millones:
        partes.append("un millón" if millones == 1 else _entero_a_texto(millones) + " millones")
    if miles:
        partes.append("mil" if miles == 1 else _cientos(miles) + " mil")
    if cientos:
        partes.append(_cientos(cientos))
    return " ".join(partes)


def soles_en_letras(monto):
    """1234.5 -> 'MIL DOSCIENTOS TREINTA Y CUATRO CON 50/100 SOLES'."""
    try:
        monto = round(float(monto), 2)
    except (TypeError, ValueError):
        monto = 0.0
    entero = int(monto)
    centavos = int(round((monto - entero) * 100))
    texto = _entero_a_texto(entero).strip() or "cero"
    return f"{texto} con {centavos:02d}/100 soles".upper()
