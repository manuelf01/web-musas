"""Generación del comprobante de venta en PDF, listo para descargar."""

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from svglib.svglib import svg2rlg

from formato import soles_en_letras


BRASA = colors.HexColor("#DB4200")
MOSTAZA = colors.HexColor("#F5C842")
CARBON = colors.HexColor("#1A1512")
CREMA = colors.HexColor("#FBF7F0")
BORDE = colors.HexColor("#E7DFD5")
SUAVE = colors.HexColor("#6B6157")
RAIZ = Path(__file__).resolve().parent.parent
LOGO = RAIZ / "static" / "img" / "marca" / "v1" / "logo.svg"
FUENTE_INTER = RAIZ / "static" / "fonts" / "Inter-Variable.ttf"
FUENTE_TITULOS = RAIZ / "static" / "fonts" / "SpaceGrotesk-Variable.ttf"

pdfmetrics.registerFont(TTFont("InterMusas", str(FUENTE_INTER)))
pdfmetrics.registerFont(TTFont("SpaceMusas", str(FUENTE_TITULOS)))
pdfmetrics.registerFontFamily(
    "InterMusas", normal="InterMusas", bold="SpaceMusas",
    italic="InterMusas", boldItalic="SpaceMusas",
)


def _texto(valor):
    return escape(str(valor or ""))


def _logo():
    dibujo = svg2rlg(str(LOGO))
    if dibujo is None:
        return Paragraph("LAS MUSAS", ParagraphStyle(
            "logo-fallback", fontName="SpaceMusas", fontSize=22, textColor=CARBON,
        ))
    ancho = 73 * mm
    escala = ancho / dibujo.width
    dibujo.width = ancho
    dibujo.height *= escala
    dibujo.scale(escala, escala)
    return dibujo


def _pie(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(BORDE)
    canvas.line(18 * mm, 14 * mm, 192 * mm, 14 * mm)
    canvas.setFont("InterMusas", 8)
    canvas.setFillColor(SUAVE)
    canvas.drawString(18 * mm, 9 * mm, "Las Musas · Comprobante interno de venta")
    canvas.drawRightString(192 * mm, 9 * mm, f"Página {doc.page}")
    canvas.restoreState()


def generar_comprobante_pdf(comprobante):
    """Devuelve el PDF del comprobante como bytes."""
    salida = BytesIO()
    doc = SimpleDocTemplate(
        salida,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=15 * mm,
        bottomMargin=20 * mm,
        title=f"Comprobante {comprobante['numero']}",
        author="Las Musas - Chiclayo",
        subject=f"Venta del pedido {comprobante['idPedido']}",
    )
    base = getSampleStyleSheet()
    normal = ParagraphStyle(
        "musas-normal", parent=base["BodyText"], fontName="InterMusas",
        fontSize=9.5, leading=13, textColor=CARBON,
    )
    pequeno = ParagraphStyle(
        "musas-small", parent=normal, fontSize=8, leading=10.5, textColor=SUAVE,
    )
    etiqueta = ParagraphStyle(
        "musas-label", parent=pequeno, fontName="SpaceMusas",
        spaceAfter=2,
    )
    tipo = ParagraphStyle(
        "musas-tipo", parent=normal, alignment=TA_RIGHT, fontName="SpaceMusas",
        fontSize=11, leading=14,
    )
    numero = ParagraphStyle(
        "musas-numero", parent=tipo, fontSize=14, textColor=BRASA,
    )
    total_style = ParagraphStyle(
        "musas-total", parent=normal, alignment=TA_RIGHT, fontName="SpaceMusas",
        fontSize=14, textColor=BRASA,
    )

    negocio = comprobante.get("negocio") or {}
    cabecera_derecha = [
        Paragraph(_texto(comprobante["tipoDoc"]), tipo),
        Paragraph(_texto(comprobante["numero"]), numero),
        Paragraph(f"{_texto(comprobante['fecha'])} · {_texto(comprobante['hora'])}", pequeno),
    ]
    cabecera = Table(
        [[_logo(), cabecera_derecha]], colWidths=[98 * mm, 76 * mm],
        style=TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 1, BORDE),
            ("BACKGROUND", (1, 0), (1, 0), CREMA),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]),
    )

    direccion = Paragraph(
        f"<b>{_texto(negocio.get('nombre', 'Las Musas - Chiclayo'))}</b><br/>"
        f"{_texto(negocio.get('direccion'))}<br/>"
        f"<font color='#6B6157'>{_texto(negocio.get('referencia'))}</font>",
        normal,
    )
    datos = [
        [Paragraph("CLIENTE", etiqueta), Paragraph("DNI", etiqueta), Paragraph("PEDIDO", etiqueta)],
        [Paragraph(_texto(comprobante["cliente"]), normal),
         Paragraph(_texto(comprobante["dni"] or "—"), normal),
         Paragraph(f"N.° {_texto(comprobante['idPedido'])}", normal)],
        [Paragraph("TELÉFONO", etiqueta), Paragraph("RECOJO", etiqueta), Paragraph("PAGO", etiqueta)],
        [Paragraph(_texto(comprobante["telefono"] or "—"), normal),
         Paragraph(_texto(comprobante["horaRecojo"] or "—"), normal),
         Paragraph(_texto(comprobante["formaPago"]), normal)],
    ]
    tabla_datos = Table(datos, colWidths=[72 * mm, 48 * mm, 54 * mm])
    tabla_datos.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), .8, BORDE),
        ("INNERGRID", (0, 0), (-1, -1), .4, BORDE),
        ("BACKGROUND", (0, 0), (-1, 0), CREMA),
        ("BACKGROUND", (0, 2), (-1, 2), CREMA),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    filas = [[
        Paragraph("Producto", etiqueta), Paragraph("Cant.", etiqueta),
        Paragraph("P. unit.", etiqueta), Paragraph("Importe", etiqueta),
    ]]
    for linea in comprobante["lineas"]:
        nombre = f"<b>{_texto(linea['nombre'])}</b>"
        if linea.get("adicionales"):
            nombre += "<br/><font size='7.5' color='#6B6157'>Cremas: " + _texto(", ".join(linea["adicionales"])) + "</font>"
        filas.append([
            Paragraph(nombre, normal),
            Paragraph(str(linea["cantidad"]), ParagraphStyle("cant", parent=normal, alignment=TA_CENTER)),
            Paragraph(f"S/ {linea['precioUnidad']:.2f}", ParagraphStyle("pu", parent=normal, alignment=TA_RIGHT)),
            Paragraph(f"S/ {linea['precioTotal']:.2f}", ParagraphStyle("pt", parent=normal, alignment=TA_RIGHT)),
        ])
    tabla_lineas = Table(filas, colWidths=[91 * mm, 20 * mm, 30 * mm, 33 * mm], repeatRows=1)
    tabla_lineas.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), CARBON),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), .45, BORDE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CREMA]),
    ]))

    totales = Table([
        [Paragraph("Op. gravada", normal), Paragraph(f"S/ {comprobante['subTotal']:.2f}", normal)],
        [Paragraph("IGV (18 %) incluido", normal), Paragraph(f"S/ {comprobante['igv']:.2f}", normal)],
        [Paragraph("TOTAL PAGADO", total_style), Paragraph(f"S/ {comprobante['montoTotal']:.2f}", total_style)],
    ], colWidths=[50 * mm, 38 * mm], hAlign="RIGHT")
    totales.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, 2), (-1, 2), 1.2, BRASA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    historia = [cabecera, Spacer(1, 7 * mm), direccion, Spacer(1, 5 * mm), tabla_datos,
                Spacer(1, 6 * mm), tabla_lineas, Spacer(1, 5 * mm), totales]
    historia.append(Spacer(1, 5 * mm))
    historia.append(Paragraph(
        f"<b>Son:</b> {_texto(soles_en_letras(comprobante['montoTotal']))}", normal,
    ))
    if comprobante.get("notas"):
        historia.extend([Spacer(1, 4 * mm), Paragraph(
            f"<b>Nota del pedido:</b> {_texto(comprobante['notas'])}", normal,
        )])
    historia.extend([
        Spacer(1, 7 * mm),
        KeepTogether([
            Paragraph("Gracias por elegir Las Musas.", ParagraphStyle(
                "gracias", parent=normal, fontName="SpaceMusas", fontSize=12,
                alignment=TA_CENTER, textColor=BRASA,
            )),
            Spacer(1, 2 * mm),
            Paragraph(
                "Comprobante interno de la operación. No es un comprobante electrónico enviado a SUNAT.",
                ParagraphStyle("aviso", parent=pequeno, alignment=TA_CENTER),
            ),
        ]),
    ])
    doc.build(historia, onFirstPage=_pie, onLaterPages=_pie)
    return salida.getvalue()
