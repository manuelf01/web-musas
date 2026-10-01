from math import ceil

from flask import request
from flask_paginate import Pagination, get_page_parameter


def paginar(lista, por_pagina, nombre="registros", page_param=None):
    """Corta `lista` en páginas. Devuelve (items_de_la_pagina, pagination, (desde, hasta)).
    `pagination.links` pinta las flechas y los números; conserva los demás filtros de la URL.
    `page_param` permite un nombre de parámetro distinto de "page" (por ejemplo, cuando dos
    listas paginadas conviven en la misma pantalla, como pendientes/recogidos en Pedidos)."""
    page_param = page_param or get_page_parameter()
    total = len(lista)
    paginas = max(1, ceil(total / por_pagina))
    pagina = request.args.get(page_param, type=int, default=1)
    pagina = min(max(1, pagina), paginas)
    inicio = (pagina - 1) * por_pagina
    items = lista[inicio:inicio + por_pagina]
    pagination = Pagination(page=pagina, total=total, per_page=por_pagina,
                            page_parameter=page_param,
                            record_name=nombre, css_framework="bootstrap5")
    return items, pagination, (inicio + 1 if total else 0, inicio + len(items))
