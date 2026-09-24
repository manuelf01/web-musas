from math import ceil

from flask import request
from flask_paginate import Pagination, get_page_parameter


def paginar(lista, por_pagina, nombre="registros"):
    """Corta `lista` en páginas. Devuelve (items_de_la_pagina, pagination, (desde, hasta)).
    `pagination.links` pinta las flechas y los números; conserva los demás filtros de la URL."""
    total = len(lista)
    paginas = max(1, ceil(total / por_pagina))
    pagina = request.args.get(get_page_parameter(), type=int, default=1)
    pagina = min(max(1, pagina), paginas)
    inicio = (pagina - 1) * por_pagina
    items = lista[inicio:inicio + por_pagina]
    pagination = Pagination(page=pagina, total=total, per_page=por_pagina,
                            record_name=nombre, css_framework="bootstrap5")
    return items, pagination, (inicio + 1 if total else 0, inicio + len(items))
