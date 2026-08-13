# ============================================================
#  services/image_builder.py
#  Pillow yordamida A4 300 DPI o'lchamdagi o'ta tiniq hujjat
#  rasmini (PNG) yaratish — Vercel bilan 100% mos va juda tez!
# ============================================================

import os
from PIL import Image, ImageDraw, ImageFont
from config import LOGO_FILE, PECHAT_FILE, IMZO_FILE, FONT_FILE


def _get_font(size: int, bold: bool = False):
    """Sistemadagi yoki loyihadagi TTF shriftni yuklash"""
    font_path = FONT_FILE
    if not os.path.exists(font_path):
        # Fallback to system fonts
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
    A4 300 DPI (2480 x 3508 piksel) ravshanlikda hujjat rasmini yaratadi.
    data: {"FIO": "...", "YONALISH": "...", "OQUV_YILI": "...", "SANA": "..."}
    """
    # 1. Oq A4 Canvas (2480 x 3508 px)
    W, H = 2480, 3508
    img = Image.new("RGB", (W, H), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Shriftlar
    f_hdr = _get_font(36, bold=True)
    f_sub = _get_font(44)
    f_title = _get_font(64, bold=True)
    f_body = _get_font(48)
    f_body_bold = _get_font(48, bold=True)
    f_note = _get_font(42)
    f_foot = _get_font(44, bold=True)

    # ── 1. Tepa Jadval Ramkasi (Header Table) ─────────────────────────
    margin_x = 180
    top_y = 150
    table_w = W - (margin_x * 2)
    table_h = 320

    # Jadvalning tashqi va ichki kulrang nuqtali/ingichka chiziqlari
    draw.rectangle([margin_x, top_y, margin_x + table_w, top_y + table_h], outline=(150, 150, 150), width=3)
    col1_w = 880
    col2_w = 360
    col3_w = table_w - col1_w - col2_w

    # Tik chiziqlar
    draw.line([margin_x + col1_w, top_y, margin_x + col1_w, top_y + table_h], fill=(150, 150, 150), width=3)
    draw.line([margin_x + col1_w + col2_w, top_y, margin_x + col1_w + col2_w, top_y + table_h], fill=(150, 150, 150), width=3)

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
        spacing=12
    )

    # O'rta (Logo rasm)
    logo_x = margin_x + col1_w + (col2_w // 2)
    if os.path.exists(LOGO_FILE):
        try:
            logo_img = Image.open(LOGO_FILE).convert("RGBA")
            logo_img = logo_img.resize((260, 260), Image.Resampling.LANCZOS)
            img.paste(logo_img, (logo_x - 130, top_y + (table_h // 2) - 130), logo_img)
        except Exception:
            draw.text((logo_x, top_y + table_h // 2), "LOGO", fill=(0, 51, 153), font=f_hdr, anchor="mm")
    else:
        draw.text((logo_x, top_y + table_h // 2), "Qarshi tibbiyot\ntexnikumi", fill=(0, 51, 153), font=f_hdr, anchor="mm", align="center")

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
        spacing=12
    )

    # ── 2. Qora Ajratuvchi Chiziq ─────────────────────────────────────
    line_y = top_y + table_h + 40
    draw.line([margin_x, line_y, W - margin_x, line_y], fill=(0, 0, 0), width=6)

    # ── 3. Shahar va Sana ──────────────────────────────────────────────
    meta_y = line_y + 50
    sana_val = data.get("SANA", "13.08.2026")
    if not sana_val.endswith("y.") and not sana_val.endswith("y"):
        sana_val += " y."

    draw.text((margin_x, meta_y), "Qarshi shahri", fill=(0, 0, 0), font=f_sub)
    draw.text((W - margin_x, meta_y), sana_val, fill=(0, 0, 0), font=f_sub, anchor="ra")

    # ── 4. Sarlavha (MA'LUMOTNOMA) ──────────────────────────────────
    title_y = meta_y + 250
    draw.text((W // 2, title_y), "MA’LUMOTNOMA", fill=(0, 0, 0), font=f_title, anchor="mm")

    # ── 5. Asosiy Matn (Qalin va Qiya joylari bilan) ───────────────
    body_y = title_y + 200
    fio = data.get("FIO", "")
    yonalish = data.get("YONALISH", "")
    oquv_yili = data.get("OQUV_YILI", "")
    boshlash_yili = oquv_yili.split("/")[0] if "/" in oquv_yili else "2026"

    # Satr 1
    p1 = "Ushbu  ma’lumotnoma  shuni  tasdiqlaydiki,  haqiqatdan  ham"
    draw.text((W // 2, body_y), p1, fill=(0, 0, 0), font=f_body, anchor="mm")

    # Satr 2 (Qalin o'zgaruvchilar)
    body_y2 = body_y + 120
    p2_full = f"{fio}   {oquv_yili}-o‘quv yilida   {yonalish}"
    draw.text((W // 2, body_y2), p2_full, fill=(0, 0, 0), font=f_body_bold, anchor="mm")

    # Satr 3
    body_y3 = body_y2 + 100
    p3 = f"yo‘nalishiga shartnoma asosida o‘qishga qabul qilindi. Talaba o‘qishni {boshlash_yili}-yil sentyabr oyidan boshlaydi."
    draw.text((W // 2, body_y3), p3, fill=(0, 0, 0), font=f_body, anchor="mm")

    # ── 6. Note (Qiya matn) ──────────────────────────────────────────
    note_y = body_y3 + 160
    draw.text((W // 2, note_y), "Ma’lumotnoma so‘ralgan joyga taqdim etish uchun berildi", fill=(0, 0, 0), font=f_note, anchor="mm")

    # ── 7. Footer (Imzo, Pechat va Direktor ismi) ───────────────────
    foot_y = H - 600

    draw.text((margin_x, foot_y), "“Qarshi tibbiyot texnikumi”\nijrochi direktori:", fill=(0, 0, 0), font=f_foot, spacing=15)
    draw.text((W - margin_x, foot_y + 20), "Sh.Raxmonov", fill=(0, 0, 0), font=f_foot, anchor="ra")

    # Pechat va Imzo rasmlarini ustma-ust tiniq qilib qo'yish
    stamp_x = W - margin_x - 750
    stamp_y = foot_y - 80

    if os.path.exists(PECHAT_FILE):
        try:
            pechat_img = Image.open(PECHAT_FILE).convert("RGBA")
            pechat_img = pechat_img.resize((380, 380), Image.Resampling.LANCZOS)
            img.paste(pechat_img, (stamp_x, stamp_y), pechat_img)
        except Exception:
            pass

    if os.path.exists(IMZO_FILE):
        try:
            imzo_img = Image.open(IMZO_FILE).convert("RGBA")
            imzo_img = imzo_img.resize((380, 200), Image.Resampling.LANCZOS)
            img.paste(imzo_img, (stamp_x + 180, stamp_y + 80), imzo_img)
        except Exception:
            pass

    # Tayyor PNG rasmni saqlash
    img.save(output_path, "PNG", quality=95)
