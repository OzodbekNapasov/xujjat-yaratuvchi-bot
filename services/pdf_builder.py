# ============================================================
#  services/pdf_builder.py
#  reportlab yordamida to'g'ridan-to'g'ri PDF yaratish
#  + PyMuPDF bilan pechat/imzo qo'shish
#  (LibreOffice kerak emas — Vercel da ishlaydi!)
# ============================================================

import os
import io
import fitz  # PyMuPDF
from PIL import Image
import tempfile

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

from config import PECHAT_FILE, IMZO_FILE, FONT_FILE


# ── Shrift ro'yxatdan o'tkazish (kirill/lotin uchun) ─────────────────────────
_FONT_REGISTERED = False

def _register_font():
    global _FONT_REGISTERED
    if _FONT_REGISTERED:
        return
    try:
        if os.path.exists(FONT_FILE):
            pdfmetrics.registerFont(TTFont("FreeSans", FONT_FILE))
            _FONT_REGISTERED = True
    except Exception:
        pass  # Standart shrift ishlatiladi


def _font():
    _register_font()
    return "FreeSans" if _FONT_REGISTERED else "Helvetica"


# ── Asosiy PDF yaratish funksiyasi ────────────────────────────────────────────

def build_pdf(
    output_path: str,
    template_name: str,
    data: dict,
    stamp_config: dict,
) -> None:
    """
    data misoli: {"FIO": "Aliyev Ali", "SANA": "01.01.2025", ...}
    """
    _register_font()
    font = _font()

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4  # 595 x 842 pt

    # ── Sahifa chegarasi ─────────────────────────────────────────────────────
    margin_left  = 25 * mm
    margin_right = 25 * mm
    margin_top   = 25 * mm
    text_width   = w - margin_left - margin_right

    y = h - margin_top  # yuqoridan boshlaymiz

    def write_line(text, font_size=12, bold=False, align="left", gap_after=6):
        nonlocal y
        fn = font
        c.setFont(fn, font_size)
        if align == "center":
            c.drawCentredString(w / 2, y, text)
        elif align == "right":
            c.drawRightString(w - margin_right, y, text)
        else:
            c.drawString(margin_left, y, text)
        y -= (font_size + gap_after)

    def write_gap(pt=10):
        nonlocal y
        y -= pt

    def write_field(label, value, font_size=11):
        nonlocal y
        c.setFont(font, font_size)
        c.drawString(margin_left, y, f"{label}: {value}")
        # Tag chizig'i (underline)
        line_x = margin_left + c.stringWidth(f"{label}: ", font, font_size)
        c.line(line_x, y - 2, w - margin_right, y - 2)
        y -= (font_size + 8)

    # ── Sarlavha ─────────────────────────────────────────────────────────────
    c.setFont(font, 14)
    c.drawCentredString(w / 2, y, template_name.replace("📄 ", ""))
    y -= 20

    c.line(margin_left, y, w - margin_right, y)
    y -= 15

    # ── Ma'lumotlar ───────────────────────────────────────────────────────────
    field_labels = {
        "FIO":          "F.I.O",
        "PASSPORT":     "Passport",
        "TUGILGAN_SANA":"Tug'ilgan sana",
        "MANZIL":       "Manzil",
        "TELEFON":      "Telefon",
        "TASHKILOT":    "Tashkilot",
        "SANA":         "Sana",
        "MAZMUN":       "Murojaat mazmuni",
    }

    for field, value in data.items():
        label = field_labels.get(field, field)
        if field == "MAZMUN" and len(value) > 60:
            # Uzun matn uchun ko'p satr
            c.setFont(font, 11)
            c.drawString(margin_left, y, f"{label}:")
            y -= 14
            # Matnni qatorlarga bo'lish
            words = value.split()
            line, lines = "", []
            for word in words:
                test = f"{line} {word}".strip()
                if c.stringWidth(test, font, 10) < text_width:
                    line = test
                else:
                    lines.append(line)
                    line = word
            if line:
                lines.append(line)
            c.setFont(font, 10)
            for ln in lines:
                c.drawString(margin_left + 10, y, ln)
                y -= 13
            y -= 5
        else:
            write_field(label, value)

    # ── Imzo joyi ─────────────────────────────────────────────────────────────
    write_gap(20)
    c.setFont(font, 10)
    sign_y = 30 * mm  # sahifaning pastidan 30mm yuqorida
    c.drawString(margin_left, sign_y + 15, "Mas'ul shaxs:  ___________________")
    c.drawString(margin_left + 100*mm, sign_y + 15, "M.O.")

    c.save()

    # ── Pechat va imzoni qo'shish ─────────────────────────────────────────────
    pdf_bytes = buf.getvalue()
    _add_stamps(pdf_bytes, output_path, stamp_config)


def _add_stamps(pdf_bytes: bytes, output_path: str, stamp_config: dict) -> None:
    """PyMuPDF bilan pechat va imzoni PDF ga qo'shadi"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[-1]  # oxirgi sahifa

    PT = 2.8346  # 1 mm = 2.8346 pt

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
