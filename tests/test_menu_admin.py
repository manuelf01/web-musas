"""Menú lateral del panel: la hamburguesa de la marca lo contrae y expande."""


def test_el_menu_tiene_boton_y_script(admin_client):
    html = admin_client.get("/admin/").get_data(as_text=True)
    assert 'data-adm-toggle' in html and 'aria-controls="menu-admin"' in html
    assert 'id="menu-admin"' in html and "js/admin-menu.js" in html
    assert 'localStorage.getItem("musa.adm.menu")' in html


def test_el_script_del_menu_se_sirve(client):
    r = client.get("/static/js/admin-menu.js")
    assert r.status_code == 200 and b"adm-colapsado" in r.data and b"adm-abierto" in r.data
