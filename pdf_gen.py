from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, os

pdfmetrics.registerFont(TTFont("LiberationSans", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LiberationSans-Bold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))

# Светло-голубая палитра
COLOR_HEADER_DARK  = colors.HexColor('#1565C0')   # тёмно-синий — заголовки ABC
COLOR_HEADER_MID   = colors.HexColor('#1976D2')   # средний синий
COLOR_BLUE_LIGHT   = colors.HexColor('#BBDEFB')   # светло-голубой фон (было бирюзовое)
COLOR_BLUE_PALE    = colors.HexColor('#E3F2FD')   # очень светлый голубой
COLOR_BLUE_ACCENT  = colors.HexColor('#42A5F5')   # голубой акцент рамки
COLOR_TEXT         = colors.HexColor('#1A237E')   # тёмно-синий текст
COLOR_WHITE        = colors.white
COLOR_BORDER       = colors.HexColor('#90CAF9')   # голубая рамка

def generate_pdf(obs) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()

    style_title = ParagraphStyle(
        'Title', fontName='LiberationSans-Bold', fontSize=20,
        textColor=COLOR_HEADER_DARK, spaceAfter=12, leading=24
    )
    style_child_name = ParagraphStyle(
        'ChildName', fontName='LiberationSans-Bold', fontSize=14,
        textColor=COLOR_HEADER_DARK, leading=18
    )
    style_label = ParagraphStyle(
        'Label', fontName='LiberationSans-Bold', fontSize=10,
        textColor=COLOR_TEXT, leading=14
    )
    style_normal = ParagraphStyle(
        'Normal', fontName='LiberationSans', fontSize=10,
        textColor=COLOR_TEXT, leading=14
    )
    style_cell = ParagraphStyle(
        'Cell', fontName='LiberationSans', fontSize=10,
        textColor=COLOR_TEXT, leading=14
    )
    style_cell_header = ParagraphStyle(
        'CellHeader', fontName='LiberationSans-Bold', fontSize=11,
        textColor=COLOR_TEXT, leading=16
    )
    style_function = ParagraphStyle(
        'Function', fontName='LiberationSans', fontSize=11,
        textColor=COLOR_TEXT, leading=16
    )

    elements = []

    # === TITLE ===
    elements.append(Paragraph("📘 Дневник наблюдения ABC", style_title))
    elements.append(Spacer(1, 0.3*cm))

    # === CHILD NAME — светло-голубой блок ===
    child_data = [
        [Paragraph("👤 Имя ребёнка:", style_label),
         Paragraph(obs.child_name, style_child_name)],
    ]
    child_table = Table(child_data, colWidths=[4*cm, 14*cm])
    child_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_BLUE_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1.5, COLOR_BLUE_ACCENT),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(child_table)
    elements.append(Spacer(1, 0.4*cm))

    # === HEADER INFO — очень светлый голубой ===
    header_data = [
        [Paragraph("Имя наблюдателя:", style_label), Paragraph(obs.observer_name, style_normal),
         Paragraph("Дата:", style_label), Paragraph(obs.obs_date, style_normal)],
        [Paragraph("Время:", style_label), Paragraph(obs.obs_time, style_normal),
         Paragraph("Место:", style_label), Paragraph(obs.location, style_normal)],
    ]
    header_table = Table(header_data, colWidths=[4*cm, 5.5*cm, 3*cm, 5.5*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_BLUE_PALE),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_WHITE),
        ('BOX', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 0.6*cm))

    # === ABC TABLE — градиент через чередование строк ===
    abc_data = [
        [
            Paragraph("<b>A — Предшествующее событие</b><br/><font size=9>(Antecedent)</font><br/>Что произошло до поведения", style_cell_header),
            Paragraph("<b>B — Поведение</b><br/><font size=9>(Behavior)</font><br/>Как себя повёл ребёнок", style_cell_header),
            Paragraph("<b>C — Последствия</b><br/><font size=9>(Consequence)</font><br/>Что произошло после", style_cell_header),
        ],
        [
            Paragraph(obs.antecedent, style_cell),
            Paragraph(obs.behavior, style_cell),
            Paragraph(obs.consequence, style_cell),
        ]
    ]
    abc_table = Table(abc_data, colWidths=[6*cm, 6*cm, 6*cm])
    abc_table.setStyle(TableStyle([
        # Заголовок — светлый голубой градиент (60% светлее)
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#90CAF9')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#BBDEFB')),
        ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#90CAF9')),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_TEXT),
        # Содержимое — чередование оттенков голубого
        ('BACKGROUND', (0, 1), (0, 1), COLOR_BLUE_PALE),
        ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#E8F4FD')),
        ('BACKGROUND', (2, 1), (2, 1), COLOR_BLUE_PALE),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BORDER),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('MINROWHEIGHT', (0, 1), (-1, 1), 5*cm),
    ]))
    elements.append(abc_table)
    elements.append(Spacer(1, 0.6*cm))

    # === FUNCTION BLOCK ===
    func_data = [
        [Paragraph("<b>🎯 Предполагаемая функция поведения:</b>", style_label)],
        [Paragraph(obs.function or "—", style_function)],
    ]
    func_table = Table(func_data, colWidths=[18*cm])
    func_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_BLUE_LIGHT),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_WHITE),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_BLUE_ACCENT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('MINROWHEIGHT', (0, 1), (-1, 1), 2.5*cm),
    ]))
    elements.append(func_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
