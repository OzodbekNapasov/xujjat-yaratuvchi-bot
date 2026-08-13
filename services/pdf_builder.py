# ============================================================
#  services/pdf_builder.py
#  Qarshi Tibbiyot Texnikumi Hujjat Generator (ReportLab + PyMuPDF)
# ============================================================

import os
import io
import tempfile
import fitz  # PyMuPDF
from PIL import Image

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib import colors

from config import LOGO_FILE, PECHAT_FILE, IMZO_FILE, FONT_FILE

_FONT_REGISTERED = False

def _register_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    try:
        if os.path.exists(FONT_FILE):
            pdfmetrics.registerFont(TTFont("FreeSans", FONT_FILE))
            pdfmetrics.registerFont(TTFont("FreeSans-Bold", FONT_FILE)) # oddiy va bold
            _FONT_REGISTERED = True
    except Exception:
        pass

def _font(bold=False):
    _register_font()
    if _FONT_REGISTERED:
        return "FreeSans-Bold" if bold else "FreeSans"
    return "Helvetica-Bold" if bold else "Helvetica"


def build_pdf(
    output_path: str,
    template_name: str,
    data: dict,
    stamp_config: dict,
) -> None:
    _register_font()
    fn = _font(bold=False)
    fn_b = _font(bold=True)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    story = []

    # ── 1. Tepa qism (Header Table: Uzbek Text | Logo | Russian Text) ─────────
    style_hdr_left = ParagraphStyle(
        'HdrLeft',
        fontName=fn_b,
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.black
    )
    style_hdr_right = ParagraphStyle(
        'HdrRight',
        fontName=fn_b,
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.black
    )

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

    cell_left = Paragraph(text_left, style_hdr_left)
    cell_right = Paragraph(text_right, style_hdr_right)

    if os.path.exists(LOGO_FILE):
        logo_img = RLImage(LOGO_FILE, width=28 * mm, height=28 * mm)
    else:
        logo_img = Paragraph("<b>LOGO</b>", style_hdr_left)

    header_table = Table(
        [[cell_left, logo_img, cell_right]],
        colWidths=[70 * mm, 30 * mm, 70 * mm]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.gray), # ramka chegarasi
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.gray),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))

    story.append(header_table)
    story.append(Spacer(1, 4 * mm))

    # ── 2. Gorizontal chiziq ───────────────────────────────────────────────
    # Qora qalin chiziq
    divider = Table([['']], colWidths=[170 * mm], rowHeights=[1.5])
    divider.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.black),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(divider)
    story.append(Spacer(1, 3 * mm))

    # ── 3. Shahar va Sana qatori ─────────────────────────────────────────────
    style_meta = ParagraphStyle('Meta', fontName=fn, fontSize=11, leading=14)
    meta_left = Paragraph("Qarshi shahri", style_meta)
    meta_right = Paragraph(f"{data.get('SANA', '12.07.2026 y.')}", ParagraphStyle('MetaR', parent=style_meta, alignment=TA_RIGHT))

    meta_table = Table([[meta_left, meta_right]], colWidths=[85 * mm, 85 * mm])
    meta_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 15 * mm))

    # ── 4. MA'LUMOTNOMA Sarlavhasi ──────────────────────────────────────────
    style_title = ParagraphStyle(
        'Title',
        fontName=fn_b,
        fontSize=15,
        leading=18,
        alignment=TA_CENTER
    )
    story.append(Paragraph("MA’LUMOTNOMA", style_title))
    story.append(Spacer(1, 12 * mm))

    # ── 5. Asosiy Matn ───────────────────────────────────────────────────────
    fio = data.get('FIO', 'Napasov Ozodbek Zafar o’g’li')
    yonalish = data.get('YONALISH', 'Hamshiralik ishi')
    oquv_yili = data.get('OQUV_YILI', '2026/2027')
    boshlash_yili = oquv_yili.split('/')[0] if '/' in oquv_yili else '2026'

    style_body = ParagraphStyle(
        'BodyText',
        fontName=fn,
        fontSize=12,
        leading=22,
        alignment=TA_JUSTIFY,
        firstLineIndent=15 * mm
    )

    body_html = (
        f"Ushbu ma’lumotnoma shuni tasdiqlaydiki, haqiqatdan ham "
        f"<b>{fio}</b> {oquv_yili}-o‘quv yilida <b>{yonalish}</b> "
        f"yo‘nalishiga shartnoma asosida o‘qishga qabul qilindi. Talaba o‘qishni {boshlash_yili}-yil "
        f"sentyabr oyidan boshlaydi."
    )
    story.append(Paragraph(body_html, style_body))
    story.append(Spacer(1, 8 * mm))

    # ── 6. Ma'lumotnoma berilish maqsadi ─────────────────────────────────────
    style_note = ParagraphStyle(
        'NoteText',
        fontName=fn,
        fontSize=11,
        leading=15,
        alignment=TA_CENTER
    )
    story.append(Paragraph("<i>Ma’lumotnoma so‘ralgan joyga taqdim etish uchun berildi</i>", style_note))
    story.append(Spacer(1, 25 * mm))

    # ── 7. Imzo qismi (Footer Table) ─────────────────────────────────────────
    style_footer_l = ParagraphStyle('FootL', fontName=fn_b, fontSize=11, leading=14, alignment=TA_LEFT)
    style_footer_r = ParagraphStyle('FootR', fontName=fn_b, fontSize=11, leading=14, alignment=TA_RIGHT)

    foot_l = Paragraph("“Qarshi tibbiyot texnikumi”<br/>ijrochi direktori:", style_footer_l)
    foot_r = Paragraph("<u>Sh.Raxmonov</u>", style_footer_r)

    foot_table = Table([[foot_l, foot_r]], colWidths=[100 * mm, 70 * mm])
    foot_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(foot_table)

    # Qurish
    doc.build(story)

    # ── 8. Pechat va imzo qo'yish (PyMuPDF) ────────────────────────────────
    pdf_bytes = buf.getvalue()
    _add_stamps(pdf_bytes, output_path, stamp_config)


def _add_stamps(pdf_bytes: bytes, output_path: str, stamp_config: dict) -> None:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[-1]

    PT = 2.8346

    def place_img(img_path: str, cfg: dict):
        if not img_path or not os.path.exists(img_path):
            return
        x0 = cfg["x_mm"] * PT
        y0 = cfg["y_mm"] * PT
        x1 = x0 + cfg["w_mm"] * PT
        y1 = y0 + cfg["h_mm"] * PT
        rect = fitz.Rect(x0, y0, x1, y1)

        img = Image.open(img_path).convert("RGBA")
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        tmp.close()
        page.insert_image(rect, filename=tmp.name, overlay=True)
        os.unlink(tmp.name)

    pechat_cfg = stamp_config.get("pechat", {})
    imzo_cfg   = stamp_config.get("imzo",   {})

    if pechat_cfg:
        place_img(PECHAT_FILE, pechat_cfg)
    if imzo_cfg:
        place_img(IMZO_FILE, imzo_cfg)

    doc.save(output_path, deflate=True)
    doc.close()
