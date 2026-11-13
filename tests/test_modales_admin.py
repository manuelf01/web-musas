from pathlib import Path


RAIZ = Path(__file__).resolve().parents[1]


def test_cruds_principales_comparten_patron_modal(admin_client):
    casos = {
        "/admin/productos/": ("panelProducto", "Gestión de carta"),
        "/admin/categorias/": ("panelCategoria", "Organización de carta"),
        "/admin/usuarios/": ("panelUsuario", "Gestión de accesos"),
        "/admin/medios-pago/": ("panelMedio", "Configuración de cobro"),
        "/admin/proveedores/": ("proveedorModal", "Directorio de abastecimiento"),
        "/admin/compras/": ("recepcionModal", "Ingreso definitivo"),
        "/admin/devoluciones/": ("devolucionModal", "Trazabilidad de inventario"),
        "/admin/inventario/movimientos/": ("movInventarioModal", "Movimiento manual"),
    }
    for url, (modal_id, encabezado) in casos.items():
        respuesta = admin_client.get(url)
        html = respuesta.get_data(as_text=True)
        assert respuesta.status_code == 200, url
        assert f'id="{modal_id}"' in html, url
        assert encabezado in html, url


def test_operaciones_sensibles_se_resuelven_en_modales_con_formulario():
    pedidos = (RAIZ / "templates/admin/pedidos/index.html").read_text(encoding="utf-8")
    compras = (RAIZ / "templates/admin/compras/index.html").read_text(encoding="utf-8")
    devoluciones = (RAIZ / "templates/admin/devoluciones/index.html").read_text(encoding="utf-8")
    ventas = (RAIZ / "templates/admin/ventas/detalle_comprobante.html").read_text(encoding="utf-8")

    assert 'id="cobroPedido{{ p.idPedido }}"' in pedidos
    assert 'id="recepcionModal"' in compras
    assert 'id="reversionModal"' in devoluciones
    assert 'name="motivo"' in devoluciones
    assert 'id="anularVentaModal"' in ventas
    assert 'name="devolver_stock"' in ventas


def test_modal_propio_tiene_semantica_y_soporte_de_teclado(admin_client):
    html = admin_client.get("/admin/productos/").get_data(as_text=True)
    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert "js/admin-modales.js" in html
    script = (RAIZ / "static/js/admin-modales.js").read_text(encoding="utf-8")
    assert 'ev.key !== "Tab"' in script
    assert 'ev.key !== "Escape"' in script
