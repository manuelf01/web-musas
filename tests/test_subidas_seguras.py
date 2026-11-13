from io import BytesIO

from PIL import Image
from werkzeug.datastructures import FileStorage

import subidas


def _png(ancho=900, alto=600):
    salida = BytesIO()
    Image.new("RGB", (ancho, alto), "#DB4200").save(salida, "PNG")
    salida.seek(0)
    return salida


def test_subida_recodifica_webp_y_genera_miniatura(tmp_path, monkeypatch):
    base = tmp_path / "img"
    monkeypatch.setattr(subidas, "_BASE", str(base))
    archivo = FileStorage(stream=_png(), filename="producto.png", content_type="image/png")
    ruta = subidas.guardar_imagen(archivo, "productos")
    assert ruta and ruta.endswith(".webp")
    detalle = base / ruta
    mini = base / subidas.miniatura_imagen(ruta)
    assert detalle.is_file() and mini.is_file()
    with Image.open(detalle) as imagen:
        assert imagen.format == "WEBP"
        assert imagen.width <= 1600 and imagen.height <= 1600
        assert not imagen.getexif()
    with Image.open(mini) as imagen:
        assert imagen.width <= 480 and imagen.height <= 480


def test_extension_y_numero_magico_deben_coincidir(tmp_path, monkeypatch):
    monkeypatch.setattr(subidas, "_BASE", str(tmp_path / "img"))
    falso_jpg = FileStorage(stream=_png(), filename="engaño.jpg", content_type="image/jpeg")
    assert subidas.guardar_imagen(falso_jpg, "productos") is None


def test_borrado_no_puede_salir_de_static_img(tmp_path, monkeypatch):
    base = tmp_path / "img"
    base.mkdir()
    fuera = tmp_path / "fuera.webp"
    fuera.write_bytes(b"no borrar")
    monkeypatch.setattr(subidas, "_BASE", str(base))
    subidas.borrar_imagen("../fuera.webp")
    assert fuera.exists()
