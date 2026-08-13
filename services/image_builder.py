# ============================================================
#  services/image_builder.py
#  Aynan foydalanuvchining shablonidagi kabi (Logotip, Pechat,
#  Imzo va Barcha Qalin/Qiya formatlar bilan) 300 DPI TINIQ RASM
# ============================================================

import os
import zipfile
from PIL import Image, ImageDraw, ImageFont
from config import BASE_DIR, FONT_FILE

# Shablon .docx ichidagi asl rasmlarni (Logo va Pechat/Imzo) ajratib olish
STAMPS_DIR = os.path.join(BASE_DIR, "templates", "stamps")
os.makedirs(STAMPS_DIR, exist_ok=True)

def _extract_docx_images():
    docx_path = os.path.join(BASE_DIR, "templates", "malumotnoma.docx")
    if not os.path.exists(docx_path):
        return
    try:
        with zipfile.ZipFile(docx_path) as z:
            for filename in z.namelist():
                if filename.startswith("word/media/"):
                    data = z.read(filename)
                    fname = os.path.basename(filename)
                    out_file = os.path.join(STAMPS_DIR, fname)
                    with open(out_file, "wb") as f:
                        f.write(data)
    except Exception:
        pass

# Har safar rasm tayyorlanayotganda rasmlarni tekshiramiz
_extract_docx_images()


def _get_font(size: int, bold: bool = False, italic: bool = False):
    font_path = FONT_FILE
    if not os.path.exists(font_path):
        sys_fonts = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/times.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/TTF/DejaVuSans.ttf",
        ]
        for f in sys_fonts:
            if os.path.exists(f):
                font_path = f
                break

    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()


def build_document_image(output_path: str, template_name: str, data: dict) -> None:
    """
    300 DPI ravshanlikda A4 hujjat rasmini yaratadi.
    data: {"FIO": "...", "YONALISH": "...", "OQUV_YILI": "...", "SANA": "..."}
    """
    _extract_docx_images()

    W, H = 2480, 3508
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Shriftlar
    f_hdr = _get_font(34, bold=True)
    f_sub = _get_font(44)
    f_title = _get_font(62, bold=True)
    f_body = _get_font(46)
    f_body_bold = _get_font(46, bold=True)
    f_note = _get_font(40, italic=True)
    f_foot = _get_font(44, bold=True)

    # ── 1. Header Table (3 Ustunli Nuqtali Ramka) ────────────────────
    margin_x = 180
    top_y = 150
    table_w = W - (margin_x * 2)
    table_h = 330

    # Nuqtali ramka (Dotted Box)
    draw.rectangle([margin_x, top_y, margin_x + table_w, top_y + table_h], outline=(160, 160, 160), width=3)
    col1_w = 880
    col2_w = 360
    col3_w = table_w - col1_w - col2_w

    # Tik nuqtali chiziqlar
    draw.line([margin_x + col1_w, top_y, margin_x + col1_w, top_y + table_h], fill=(160, 160, 160), width=3)
    draw.line([margin_x + col1_w + col2_w, top_y, margin_x + col1_w + col2_w, top_y + table_h], fill=(160, 160, 160), width=3)

    # Chap matn (Uzbek)
    txt_l = (
        "O’ZBEKISTON RESPUBLIKASI\n"
        "QASHQADARYO VILOYATI\n"
        "“QARSHI TIBBIYOT TEXNIKUMI”\n"
        "NODAVLAT TA’LIM MUASSASASI"
    )
    draw.multiline_text(
        (margin_x + col1_w // 2, top_y + table_h // 2),
        txt_l,
        fill=(0, 0, 0),
        font=f_hdr,
        anchor="mm",
        align="center",
        spacing=10
    )

    # O'rta (Asl Logotip Rasm)
    logo_file = os.path.join(STAMPS_DIR, "image1.png")
    if os.path.exists(logo_file):
        try:
            logo_img = Image.open(logo_file).convert("RGBA")
            logo_img = logo_img.resize((270, 270), Image.Resampling.LANCZOS)
            logo_x = margin_x + col1_w + (col2_w // 2) - 135
            logo_y = top_y + (table_h // 2) - 135
            img.paste(logo_img, (logo_x, logo_y), logo_img)
        except Exception:
            pass

    # O'ng matn (Russian)
    txt_r = (
        "РЕСПУБЛИКА УЗБЕКИСТАН\n"
        "КАШКАДАРЬИНСКАЯ ОБЛАСТЬ\n"
        "НЕГОСУДАРСТВЕННОЕ ОБРАЗОВАТЕЛЬНОЕ УЧРЕЖДЕНИЕ\n"
        "«КАРШИНСКИЙ МЕДИЦИНСКИЙ ТЕХНИКУМ»"
    )
    draw.multiline_text(
        (margin_x + col1_w + col2_w + col3_w // 2, top_y + table_h // 2),
        txt_r,
        fill=(0, 0, 0),
        font=f_hdr,
        anchor="mm",
        align="center",
        spacing=10
    )

    # ── 2. Qora Ajratuvchi Chiziq ─────────────────────────────────────
    line_y = top_y + table_h + 35
    draw.line([margin_x, line_y, W - margin_x, line_y], fill=(0, 0, 0), width=5)

    # ── 3. Shahar va Sana ──────────────────────────────────────────────
    meta_y = line_y + 45
    sana_val = data.get("SANA", "13.08.2026")
    if not sana_val.endswith("y.") and not sana_val.endswith("y"):
        sana_val += " y."

    draw.text((margin_x, meta_y), "Qarshi shahri", fill=(0, 0, 0), font=f_sub)
    draw.text((W - margin_x, meta_y), sana_val, fill=(0, 0, 0), font=f_sub, anchor="ra")

    # ── 4. Sarlavha (MA'LUMOTNOMA) ──────────────────────────────────
    title_y = meta_y + 260
    draw.text((W // 2, title_y), "MA’LUMOTNOMA", fill=(0, 0, 0), font=f_title, anchor="mm")

    # ── 5. Asosiy Matn (Qalin va Qiya formatlar bilan) ──────────────
    body_y = title_y + 180
    fio = data.get("FIO", "")
    yonalish = data.get("YONALISH", "")
    oquv_yili = data.get("OQUV_YILI", "")
    boshlash_yili = oquv_yili.split("/")[0] if "/" in oquv_yili else "2026"

    # Satr 1
    p1 = "Ushbu  ma’lumotnoma  shuni  tasdiqlaydiki,  haqiqatdan  ham"
    draw.text((W // 2, body_y), p1, fill=(0, 0, 0), font=f_body, anchor="mm")

    # Satr 2 (Qalin FIO, OQUV_YILI, YONALISH)
    body_y2 = body_y + 110
    p2_full = f"{fio}   {oquv_yili}-o‘quv yilida   {yonalish}"
    draw.text((W // 2, body_y2), p2_full, fill=(0, 0, 0), font=f_body_bold, anchor="mm")

    # Satr 3
    body_y3 = body_y2 + 95
    p3 = f"yo‘nalishiga shartnoma asosida o‘qishga qabul qilindi. Talaba o‘qishni {boshlash_yili}-yil sentyabr oyidan boshlaydi."
    draw.text((W // 2, body_y3), p3, fill=(0, 0, 0), font=f_body, anchor="mm")

    # ── 6. Note (Qiya/Italic matn) ──────────────────────────────────
    note_y = body_y3 + 140
    draw.text((W // 2, note_y), "Ma’lumotnoma so‘ralgan joyga taqdim etish uchun berildi", fill=(0, 0, 0), font=f_note, anchor="mm")

    # ── 7. Footer (Imzo, Pechat va Direktor ismi) ───────────────────
    foot_y = H - 650

    draw.text((margin_x, foot_y), "“Qarshi tibbiyot texnikumi”\nijrochi direktori:", fill=(0, 0, 0), font=f_foot, spacing=15)
    draw.text((W - margin_x, foot_y + 20), "Sh.Raxmonov", fill=(0, 0, 0), font=f_foot, anchor="ra")

    # Asl Pechat va Imzo rasmi (Shablon Word fayldan olingan)
    pechat_file = os.path.join(STAMPS_DIR, "image2.png")
    if os.path.exists(pechat_file):
        try:
            pechat_img = Image.open(pechat_file).convert("RGBA")
            # Proportsional o'lchamda imzo va pechatni ustma-ust joylash
            pechat_img = pechat_img.resize((650, 240), Image.Resampling.LANCZOS)
            stamp_x = W - margin_x - 850
            stamp_y = foot_y - 40
            img.paste(pechat_img, (stamp_x, stamp_y), pechat_img)
        except Exception:
            pass

    # Tayyor PNG rasmni saqlash
    img.save(output_path, "PNG", quality=95)
