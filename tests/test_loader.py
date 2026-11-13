"""El loader global se incluye en las dos interfaces sin bloquear a quien no usa JS."""

from pathlib import Path


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
    assert 'musa-sin-loader-inicial' in js
    assert 'querySelector("input[data-buscar-auto]")' in js
    assert 'musaFocoBuscar' in client.get("/").get_data(as_text=True)
    assert '.musa-loader { display: none; }' in css
    assert '.musa-sin-loader-inicial .musa-loader' in css
    assert '.musa-js .musa-loader:not([hidden])' in css
    assert '@media (prefers-reduced-motion: reduce)' in css


def test_busquedas_automaticas_actualizan_solo_el_listado(admin_client):
    casos = {
        "/admin/productos/": "#prod-lista",
        "/admin/categorias/": "#cat-lista",
        "/admin/usuarios/": "#usr-lista",
        "/admin/pedidos/": "#ped-lista",
    }
    for url, destino in casos.items():
        html = admin_client.get(url).get_data(as_text=True)
        assert f'data-buscar-destino="{destino}"' in html
        assert "ui-comun.js?v=20261106-2" in html

    plantilla_cliente = (Path(__file__).resolve().parent.parent /
                          "templates/client/mis-pedidos.html").read_text(encoding="utf-8")
    assert 'data-buscar-destino="#mp-lista"' in plantilla_cliente

    js = admin_client.get("/static/js/ui-comun.js").get_data(as_text=True)
    assert "buscarSinRecargar" in js
    assert "new DOMParser()" in js
    assert 'history.replaceState(null, "", url)' in js
    assert "setTimeout(function ()" not in js[js.index("input[data-buscar-auto]"):js.index("// --- Modal de confirmacion")]
