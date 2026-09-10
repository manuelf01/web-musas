"""El loader global se incluye en las dos interfaces sin bloquear a quien no usa JS."""


def test_loader_aparece_en_tienda(client):
    respuesta = client.get("/")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'data-musa-loader' in html
    assert 'img/marca/v1/simbolo.svg' in html
    assert 'Encendiendo las brasas' in html
    assert 'js/loader.js' in html
    assert 'classList.add("musa-js")' in html


def test_loader_aparece_en_panel(admin_client):
    respuesta = admin_client.get("/admin/")
    html = respuesta.get_data(as_text=True)
    assert respuesta.status_code == 200
    assert 'data-musa-loader' in html
    assert 'Preparando el panel' in html
    assert 'js/loader.js' in html


def test_assets_del_loader_tienen_fallback_y_recuperacion(client):
    js = client.get("/static/js/loader.js").get_data(as_text=True)
    css = client.get("/static/css/musas-theme.css").get_data(as_text=True)
    assert 'window.addEventListener("load"' in js
    assert 'window.addEventListener("pageshow"' in js
    assert 'data-confirm' in js
    assert 'loaderSkip' in js
    assert '.musa-loader { display: none; }' in css
    assert '.musa-js .musa-loader:not([hidden])' in css
    assert '@media (prefers-reduced-motion: reduce)' in css
