"""Horario público en Perú y datos de la sede compartidos entre vistas."""

from datetime import datetime, timezone

import pytest

from negocio import HORA_PERU, SEDE, estado_local


@pytest.mark.parametrize('hora,abierto', [
    ('00:00:00', False), ('17:59:59', False), ('18:00:00', True),
    ('22:00:00', True), ('23:29:59', True), ('23:30:00', False), ('23:59:59', False),
])
@pytest.mark.parametrize('dia', [7, 8, 9, 10, 11, 12])
def test_limites_horario_peru(dia, hora, abierto):
    ahora = datetime.fromisoformat(f'2026-09-{dia:02d}T' + hora).replace(tzinfo=HORA_PERU)
    estado = estado_local(ahora)
    assert estado['abierto'] is abierto
    assert estado['cambia_en'] > 0


def test_horario_no_depende_del_reloj_del_servidor_ni_modo_demo(monkeypatch):
    monkeypatch.setenv('MUSAS_DEMO', '1')
    monkeypatch.setenv('MUSAS_HORA_APERTURA', '0')
    monkeypatch.setenv('MUSAS_HORA_CIERRE', '24')
    # 23:00 UTC = 18:00 Perú; 04:30 UTC del día siguiente = 23:30 Perú.
    assert estado_local(datetime(2026, 9, 8, 23, tzinfo=timezone.utc))['abierto']
    assert not estado_local(datetime(2026, 9, 9, 4, 30, tzinfo=timezone.utc))['abierto']


def test_proxima_apertura_al_dia_siguiente():
    estado = estado_local(datetime(2026, 9, 8, 23, 30, tzinfo=HORA_PERU))
    assert estado['cambia_en'] == (18 * 60 + 30) * 60


@pytest.mark.parametrize('hora,texto', [(18, 'Abierto'), (17, 'Cerrado')])
def test_estado_en_inicio_panel_y_endpoint(client, admin_client, monkeypatch, hora, texto):
    import app as app_module
    estado = estado_local(datetime(2026, 9, 8, hora, tzinfo=HORA_PERU))
    monkeypatch.setattr(app_module, 'estado_local', lambda: estado)
    respuesta = client.get('/estado-local')
    assert respuesta.get_json() == estado
    assert respuesta.headers['Cache-Control'] == 'no-store'
    for navegador, ruta in [(client, '/'), (admin_client, '/admin/')]:
        html = navegador.get(ruta).get_data(as_text=True)
        assert f'data-estado-texto>{texto}</span>' in html
        assert 'js/estado-local.js' in html


def test_sede_y_mapa_en_inicio(client):
    html = client.get('/').get_data(as_text=True)
    assert SEDE['direccion'] in html
    assert SEDE['nombre'] in html
    assert '<iframe' in html and 'output=embed' in html
    assert 'title="Mapa de Sede Chiclayo:' in html
    assert 'Miraflores' not in html and 'Barranco' not in html
    assert 'Balta Sur 006' in html and 'Hotel Colibrí' in html
    assert '11:30 p.m.' in html and '9:00 a.m.' in html


@pytest.mark.parametrize('hora,abierto', [
    ('08:59:59', False), ('09:00:00', True), ('17:00:00', True),
    ('22:59:59', True), ('23:00:00', False), ('23:30:00', False),
])
def test_domingo(hora, abierto):
    ahora = datetime.fromisoformat('2026-09-13T' + hora).replace(tzinfo=HORA_PERU)
    assert estado_local(ahora)['abierto'] is abierto


@pytest.mark.parametrize('fecha,espera', [
    ('2026-09-12T23:30:00-05:00', 9.5),
    ('2026-09-13T23:00:00-05:00', 19),
    ('2026-09-14T00:00:00-05:00', 18),
])
def test_transiciones_fin_de_semana(fecha, espera):
    assert estado_local(datetime.fromisoformat(fecha))['cambia_en'] == espera * 3600


@pytest.mark.parametrize('dia,primera,ultima,total', [
    (12, '18:00', '23:00', 11), (13, '09:00', '22:30', 28),
])
def test_franjas_respetan_horario_semanal(monkeypatch, bd_limpia, dia, primera, ultima, total):
    import importlib
    modulo = importlib.import_module('model.Pedido')
    pedido = modulo.Pedido

    fijo = datetime(2026, 9, dia, 8, tzinfo=HORA_PERU)
    monkeypatch.setattr(modulo, 'ahora_peru', lambda: fijo)
    monkeypatch.setattr(pedido, 'HORA_APERTURA', None)
    monkeypatch.setattr(pedido, 'HORA_CIERRE', None)
    monkeypatch.setattr(pedido, 'DEMO', True)
    franjas = pedido.franjas_recojo()
    assert len(franjas) == total
    assert franjas[0]['hora'] == primera and franjas[-1]['hora'] == ultima
    assert all(f['disponible'] for f in franjas)
    # La anticipación de cocina también se conserva en modo normal.
    monkeypatch.setattr(pedido, 'DEMO', False)
    monkeypatch.setattr(pedido, '_auto_no_show', lambda: None)
    assert all(f['disponible'] for f in pedido.franjas_recojo())
