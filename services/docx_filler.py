# ============================================================
#  services/docx_filler.py
#  .docx shablonni to'ldirish
#  - Matnlarni 100% Times New Roman shriftiga o'tkazadi
#  - Faqat FIO, YONALISH, OQUV_YILI ni QALIN (Bold) qiladi
#  - Qolgan so'zlarni oddiy (normal) qiladi
#  - Qiya (Italic) va boshqa formatlarni buzmasdan saqlaydi
# ============================================================

from docx import Document


def fill_template(template_path: str, output_path: str, data: dict) -> None:
    """
    template_path : .docx shablon fayli yo'li
    output_path   : natija .docx fayli yo'li
    data          : {"FIO": "...", "YONALISH": "...", "OQUV_YILI": "...", "SANA": "..."}
    """
    doc = Document(template_path)

    # 1. Paragraflar
    for para in doc.paragraphs:
        _process_paragraph(para, data)

    # 2. Jadvallar ichidagi kataklar
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    _process_paragraph(para, data)

    # 3. Header va Footer
    for section in doc.sections:
        for para in section.header.paragraphs:
            _process_paragraph(para, data)
        for para in section.footer.paragraphs:
            _process_paragraph(para, data)

    doc.save(output_path)


def _process_paragraph(para, data: dict) -> None:
    if not para.text:
        return

    # Shriftni Times New Roman qilish
    for run in para.runs:
        run.font.name = "Times New Roman"

    # 1. Har bir run ichida replace qilish
    for run in para.runs:
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in run.text:
                run.text = run.text.replace(placeholder, str(value))
                if key in ["FIO", "YONALISH", "OQUV_YILI"]:
                    run.font.bold = True
                run.font.name = "Times New Roman"

    # 2. Agar qavslar XML ichida bo'lingan bo'lsa (cross-run)
    full_text = "".join(r.text for r in para.runs)
    has_unreplaced = any(f"{{{{{key}}}}}" in full_text for key in data.keys())

    if has_unreplaced:
        _replace_and_format_paragraph(para, data)


def _replace_and_format_paragraph(para, data: dict) -> None:
    """
    Paragraf matnini almashtirib, faqat FIO, YONALISH va OQUV_YILI ni BOLD qiladi.
    Barcha matnlarga Times New Roman shriftini beradi.
    """
    text = "".join(r.text for r in para.runs)
    
    # Placeholder larni almashtirish
    fio_val = data.get("FIO", "")
    yon_val = data.get("YONALISH", "")
    oq_val  = data.get("OQUV_YILI", "")
    sana_val = data.get("SANA", "")

    # Barcha placeholder larni almashtiramiz
    text = text.replace("{{FIO}}", fio_val)
    text = text.replace("{{YONALISH}}", yon_val)
    text = text.replace("{{OQUV_YILI}}", oq_val)
    text = text.replace("{{SANA}}", sana_val)

    # Paragrafdagi eski runlarni tozalash
    is_italic = any(r.italic for r in para.runs)
    p_element = para._p
    for r in para.runs:
        p_element.remove(r._r)

    # Matnni segmentlarga bo'lib, FIO, YONALISH, OQUV_YILI larni BOLD bilan qayta qo'shish
    bold_tokens = [fio_val, yon_val, oq_val]
    # bo'sh bo'lmagan bold so'zlar
    bold_tokens = [t for t in bold_tokens if t]

    current_text = text
    while current_text:
        # Eng birinchi uchraydigan bold token ni topamiz
        first_pos = len(current_text)
        found_token = None

        for tok in bold_tokens:
            pos = current_text.find(tok)
            if pos != -1 and pos < first_pos:
                first_pos = pos
                found_token = tok

        if found_token is not None:
            # Token gacha bo'lgan oddiy matn
            if first_pos > 0:
                r_norm = para.add_run(current_text[:first_pos])
                r_norm.font.name = "Times New Roman"
                r_norm.font.bold = False
                if is_italic:
                    r_norm.font.italic = True

            # Bold token
            r_bold = para.add_run(found_token)
            r_bold.font.name = "Times New Roman"
            r_bold.font.bold = True
            if is_italic:
                r_bold.font.italic = True

            current_text = current_text[first_pos + len(found_token):]
        else:
            # Qolgan oddiy matn
            r_rest = para.add_run(current_text)
            r_rest.font.name = "Times New Roman"
            r_rest.font.bold = False
            if is_italic:
                r_rest.font.italic = True
            break
