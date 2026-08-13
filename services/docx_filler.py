# ============================================================
#  services/docx_filler.py
#  .docx shablonni ma'lumotlar bilan to'ldiradi
# ============================================================

from docx import Document
import copy


def fill_template(template_path: str, output_path: str, data: dict) -> None:
    """
    template_path : .docx shablon fayli yo'li
    output_path   : natija .docx fayli yo'li
    data          : {"FIO": "Aliyev Ali", "SANA": "01.01.2025", ...}
    """
    doc = Document(template_path)

    def replace_in_text(text: str) -> str:
        for key, value in data.items():
            text = text.replace(f"{{{{{key}}}}}", str(value))
        return text

    # Paragraflar
    for para in doc.paragraphs:
        _replace_paragraph(para, data)

    # Jadvallar ichidagi kataklar
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    _replace_paragraph(para, data)

    # Sarlavha va footer
    for section in doc.sections:
        for para in section.header.paragraphs:
            _replace_paragraph(para, data)
        for para in section.footer.paragraphs:
            _replace_paragraph(para, data)

    doc.save(output_path)


def _replace_paragraph(para, data: dict) -> None:
    """
    Paragraf ichidagi run larni birlashtirgan holda almashtiradi.
    Bu {{FIELD}} bir nechta run ga bo'linib ketgan holatlarni ham to'g'ri hal qiladi.
    """
    full_text = "".join(run.text for run in para.runs)
    new_text = full_text
    for key, value in data.items():
        new_text = new_text.replace(f"{{{{{key}}}}}", str(value))

    if new_text == full_text:
        return  # o'zgarmagan, chiqib ketamiz

    # Birinchi run ga yangi matnni qo'yib, qolganlarini tozalaymiz
    if para.runs:
        para.runs[0].text = new_text
        for run in para.runs[1:]:
            run.text = ""
