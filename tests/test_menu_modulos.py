"""Menú lateral: solo pantallas de destino (los filtros y botones viven dentro de cada pantalla)."""

import re


def _menu(html):
    return re.search(r'<nav class="adm-nav".*?</nav>', html, re.S).group(0)


def _activos(menu):
    return re.findall(r'class="(?:adm-nav__item|adm-sub__item)[^"]*is-active[^"]*"[^>]*>\s*(?:<i[^>]*></i>)?\s*(?:<span>)?([^<]+)', menu)


def test_el_menu_solo_lista_pantallas(admin_client):
    menu = _menu(admin_client.get("/admin/").get_data(as_text=True))
    assert menu.count('data-grupo=') == 2                     # solo módulos con 2 o más pantallas
    for texto in ("Resumen", "Pedidos", "Gestión", "Productos", "Categorías", "Ventas y caja",
                  "Ventas", "Pagos", "Usuarios", "Mi perfil"):
        assert texto in menu, texto
    # Filtros y botones NO van en el menú.
    for sobra in ("Control de stock", "Sin stock", "Por entregar", "Listos para cobrar", "Entregados",
                  "Todos los pedidos", "Anulaciones", "Agregar usuario", "Clientes", "Personal del panel",
                  "estado=", "rol=", "nuevo="):
        assert sobra not in menu, sobra


def test_el_modulo_y_la_pantalla_activa_se_marcan(admin_client):
    casos = {
        "/admin/productos/?estado=sin_stock": ("gestion", "Productos"),   # el filtro no cambia el ítem
        "/admin/categorias/": ("gestion", "Categorías"),
        "/admin/ventas/?estado=anulado": ("ventas", "Ventas"),
        "/admin/pagos/": ("ventas", "Pagos"),
    }
    for url, (modulo, item) in casos.items():
        menu = _menu(admin_client.get(url).get_data(as_text=True))
        assert re.search(r'class="adm-grupo is-activo is-abierto" data-grupo="%s"' % modulo, menu), url
        assert _activos(menu) == [item], (url, _activos(menu))
    for url, item in {"/admin/": "Resumen", "/admin/pedidos/?estado=listo": "Pedidos",
                      "/admin/usuarios/?rol=usuario": "Usuarios", "/admin/perfil/": "Mi perfil"}.items():
        menu = _menu(admin_client.get(url).get_data(as_text=True))
        assert _activos(menu) == [item] and "is-activo" not in menu, url
