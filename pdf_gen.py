from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io, os

# Register fonts
pdfmetrics.registerFont(TTFont("LiberationSans", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("LiberationSans-Bold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))

# Colors
COLOR_TURQUOISE = colors.HexColor('#E0F7FA')      # светло-бирюзовый
COLOR_LIGHT_BLUE = colors.HexColor('#E3F2FD')     # светло-голубой
COLOR_ACCENT = colors.HexColor('#26A69A')      # менее насыщенный бирюзовый (на 40% светлее)
COLOR_ACCENT_LIGHT = colors.HexColor('#4DB6AC')  # для градиентов
COLOR_TEXT = colors.HexColor('#263238')            # тёмно-серый текст
COLOR_WHITE = colors.white
COLOR_BORDER = colors.HexColor('#B0BEC5')           # светло-серый бордюр

def generate_pdf(obs) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()

    # Styles
    style_title = ParagraphStyle(
        'Title', fontName='LiberationSans-Bold', fontSize=20,
        textColor=COLOR_ACCENT, spaceAfter=12, leading=24
    )
    style_child_name = ParagraphStyle(
        'ChildName', fontName='LiberationSans-Bold', fontSize=14,
        textColor=COLOR_ACCENT, leading=18
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
        textColor=COLOR_WHITE, leading=16
    )
    style_function = ParagraphStyle(
        'Function', fontName='LiberationSans', fontSize=11,
        textColor=COLOR_TEXT, leading=16
    )

    elements = []

    # === TITLE ===
    elements.append(Paragraph("📘 Дневник наблюдения ABC", style_title))
    elements.append(Spacer(1, 0.3*cm))

    # === CHILD NAME HIGHLIGHT BLOCK ===
    child_data = [
        [Paragraph("👤 Имя ребёнка:", style_label),
         Paragraph(obs.child_name, style_child_name)],
    ]
    child_table = Table(child_data, colWidths=[4*cm, 14*cm])
    child_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_TURQUOISE),
        ('BOX', (0, 0), (-1, -1), 1.5, COLOR_ACCENT),
        ('LEFTPADDING', (0, 0), (0, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(child_table)
    elements.append(Spacer(1, 0.4*cm))

    # === HEADER INFO (light blue background) ===
    header_data = [
        [Paragraph("Имя наблюдателя:", style_label), Paragraph(obs.observer_name, style_normal),
         Paragraph("Дата:", style_label), Paragraph(obs.obs_date, style_normal)],
        [Paragraph("Время:", style_label), Paragraph(obs.obs_time, style_normal),
         Paragraph("Место:", style_label), Paragraph(obs.location, style_normal)],
    ]
    header_table = Table(header_data, colWidths=[4*cm, 5.5*cm, 3*cm, 5.5*cm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLOR_LIGHT_BLUE),
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

    # === ABC TABLE ===
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
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), COLOR_WHITE),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_WHITE),
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
        ('BACKGROUND', (0, 0), (-1, 0), COLOR_TURQUOISE),
        ('BACKGROUND', (0, 1), (-1, 1), COLOR_WHITE),
        ('BOX', (0, 0), (-1, -1), 1, COLOR_ACCENT),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, COLOR_BORDER),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('MINROWHEIGHT', (0, 1), (-1, 1), 2.5*cm),
    ]))
    elements.append(func_table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer.read()
