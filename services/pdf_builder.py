# ============================================================
#  services/pdf_builder.py
#  ReportLab yordamida to'liq va yengil PDF yaratish (Vercel-friendly)
# ============================================================

import os
import io

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import LOGO_FILE, PECHAT_FILE, IMZO_FILE, FONT_FILE

_FONT_REGISTERED = False

def _register_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    try:
        if os.path.exists(FONT_FILE):
            pdfmetrics.registerFont(TTFont("FreeSans", FONT_FILE))
            pdfmetrics.registerFont(TTFont("FreeSans-Bold", FONT_FILE))
            _FONT_REGISTERED = True
    except Exception:
        pass

def _font(bold=False):
    _register_font()
    if _FONT_REGISTERED:
        return "FreeSans-Bold" if bold else "FreeSans"
    return "Helvetica-Bold" if bold else "Helvetica"


def build_flattened_pdf(
    output_pdf_path: str,
    template_name: str,
    data: dict,
) -> None:
    """
    data: {"FIO": "Napasov Diyorbek", "YONALISH": "Hamshiralik ishi", "OQUV_YILI": "2026/2027", "SANA": "13.08.2026"}
    """
    _register_font()
    fn = _font(bold=False)
    fn_b = _font(bold=True)

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    # 1. Header Table (Uzbek | Logo | Russian)
    style_hdr = ParagraphStyle('Hdr', fontName=fn_b, fontSize=8.5, leading=11, alignment=TA_CENTER)

    text_left = (
        "O’ZBEKISTON RESPUBLIKASI<br/>"
        "QASHQADARYO VILOYATI<br/>"
        "“QARSHI TIBBIYOT TEXNIKUMI”<br/>"
        "NODAVLAT TA’LIM MUASSASASI"
    )

    text_right = (
        "РЕСПУБЛИКА УЗБЕКИСТАН<br/>"
        "КАШКАДАРЬИНСКАЯ ОБЛАСТЬ<br/>"
        "НЕГОСУДАРСТВЕННОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ<br/>"
        "«КАРШИНСКИЙ МЕДИЦИНСКИЙ ТЕХНИКУМ»"
    )

    cell_left = Paragraph(text_left, style_hdr)
    cell_right = Paragraph(text_right, style_hdr)

    if os.path.exists(LOGO_FILE):
        logo_img = RLImage(LOGO_FILE, width=28 * mm, height=28 * mm)
    else:
        logo_img = Paragraph("<b>Qarshi tibbiyot<br/>texnikumi</b>", style_hdr)

    header_table = Table(
        [[cell_left, logo_img, cell_right]],
        colWidths=[70 * mm, 30 * mm, 70 * mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.gray),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.gray),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # 2. Border Line
    divider = Table([['']], colWidths=[170 * mm], rowHeights=[1.5])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 3 * mm))

    # 3. Shahar va Sana
    sana_val = data.get('SANA', '13.08.2026')
    if not sana_val.endswith("y.") and not sana_val.endswith("y"):
        sana_val += " y."

    style_meta = ParagraphStyle('Meta', fontName=fn, fontSize=11, leading=14)
    meta_left = Paragraph("Qarshi shahri", style_meta)
    meta_right = Paragraph(f"{sana_val}", ParagraphStyle('MetaR', parent=style_meta, alignment=TA_RIGHT))

    meta_table = Table([[meta_left, meta_right]], colWidths=[85 * mm, 85 * mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15 * mm))

    # 4. Sarlavha
    style_title = ParagraphStyle('Title', fontName=fn_b, fontSize=15, leading=18, alignment=TA_CENTER)
    story.append(Paragraph("MA’LUMOTNOMA", style_title))
    story.append(Spacer(1, 12 * mm))

    # 5. Asosiy Matn
    fio = data.get('FIO', '')
    yonalish = data.get('YONALISH', '')
    oquv_yili = data.get('OQUV_YILI', '')
    boshlash_yili = oquv_yili.split('/')[0] if '/' in oquv_yili else '2026'

    style_body = ParagraphStyle(
        'BodyText',
        fontName=fn,
        fontSize=12,
        leading=22,
        alignment=TA_CENTER,
    )

    body_html = (
        f"Ushbu  ma’lumotnoma  shuni  tasdiqlaydiki,  haqiqatdan  ham<br/><br/>"
        f"<b>{fio}</b>  <b>{oquv_yili}</b>-o‘quv yilida  <b>{yonalish}</b>  yo‘nalishiga  shartnoma "
        f"asosida o‘qishga qabul qilindi. Talaba o‘qishni {boshlash_yili}-yil sentyabr oyidan boshlaydi."
    )
    story.append(Paragraph(body_html, style_body))
    story.append(Spacer(1, 10 * mm))

    # 6. Note
    style_note = ParagraphStyle('NoteText', fontName=fn, fontSize=10.5, leading=15, alignment=TA_CENTER)
    story.append(Paragraph("<i>Ma’lumotnoma so‘ralgan joyga taqdim etish uchun berildi</i>", style_note))
    story.append(Spacer(1, 25 * mm))

    # 7. Footer (Imzo va Pechat)
    style_footer_l = ParagraphStyle('FootL', fontName=fn_b, fontSize=11, leading=14, alignment=TA_LEFT)
    style_footer_r = ParagraphStyle('FootR', fontName=fn_b, fontSize=11, leading=14, alignment=TA_RIGHT)

    foot_l = Paragraph("“Qarshi tibbiyot texnikumi”<br/>ijrochi direktori:", style_footer_l)
    
    # Pechat va imzo rasmi mavjud bo'lsa jadval ichiga joylaymiz
    if os.path.exists(PECHAT_FILE):
        stamp_img = RLImage(PECHAT_FILE, width=35 * mm, height=35 * mm)
    else:
        stamp_img = Paragraph("", style_footer_r)

    foot_r = Paragraph("Sh.Raxmonov", style_footer_r)

    foot_table = Table([[foot_l, stamp_img, foot_r]], colWidths=[80 * mm, 40 * mm, 50 * mm])
    foot_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(foot_table)

    # PDF ni to'g'ridan-to'g meyoriy shaklda yaratish
    doc.build(story)
