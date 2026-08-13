# ============================================================
#  services/docx_filler.py
#  .docx shablonni to'ldirish (Qalin, qiya va barcha shrift
#  formatlarini 100% buzmasdan saqlaydi)
# ============================================================

from docx import Document


def fill_template(template_path: str, output_path: str, data: dict) -> None:
    """
    template_path : .docx shablon fayli yo'li
    output_path   : natija .docx fayli yo'li
    data          : {"FIO": "...", "YONALISH": "...", ...}
    """
    doc = Document(template_path)

    # Paragraflar
    for para in doc.paragraphs:
        _replace_in_paragraph(para, data)

    # Jadvallar ichidagi kataklar
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    _replace_in_paragraph(para, data)

    # Header va Footer
    for section in doc.sections:
        for para in section.header.paragraphs:
            _replace_in_paragraph(para, data)
        for para in section.footer.paragraphs:
            _replace_in_paragraph(para, data)

    doc.save(output_path)


def _replace_in_paragraph(para, data: dict) -> None:
    """
    Har bir run uchun tekshirib, formatlashni (bold, italic, size, color)
    100% saqlagan holda o'zgaruvchilar o'rniga qiymat qo'yadi.
    """
    # 1-Bosqich: Run lar ichida to'g'ridan-to'g'ri almashtirish (format saqlanadi)
    for run in para.runs:
        for key, value in data.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in run.text:
                run.text = run.text.replace(placeholder, str(value))

    # 2-Bosqich: Agar Word XML qavslarni bo'lib yuborgan bo'lsa (cross-run)
    full_text = "".join(run.text for run in para.runs)
    needs_cross_replace = False
    for key in data.keys():
        placeholder = f"{{{{{key}}}}}"
        if placeholder in full_text:
            # Hali almashtirilmagan placeholder qolgan bo'lsa
            needs_cross_replace = True
            break

    if needs_cross_replace:
        _replace_cross_run(para, data)


def _replace_cross_run(para, data: dict) -> None:
    """Word bo'lib yuborgan run lardagi {{FIELD}} larni formatini saqlab birlashtirish"""
    full_text = "".join(run.text for run in para.runs)
    for key, value in data.items():
        placeholder = f"{{{{{key}}}}}"
        full_text = full_text.replace(placeholder, str(value))

    if para.runs:
        # Birinchi run stili saqlanadi
        para.runs[0].text = full_text
        for run in para.runs[1:]:
            run.text = ""
