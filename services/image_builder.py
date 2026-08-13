# ============================================================
#  services/image_builder.py
#  Sizning asl Word (.docx) shabloningizni to'ldirib, uni
#  Gotenberg + pypdfium2 yordamida 300 DPI TINIQ PNG RASMGA
#  aylantiruvchi mukammal konvertor
# ============================================================

import os
import requests
import pypdfium2 as pdfium
from services.docx_filler import fill_template
from config import find_template_file

GOTENBERG_URL = "https://demo.gotenberg.dev/forms/libreoffice/convert"


def render_docx_template_to_image(
    template_filename: str,
    output_png_path: str,
    data: dict,
    temp_dir: str
) -> bool:
    """
    1. Sizning asl Word (.docx) faylingizni to'ldiradi (barcha logotip, pechat, imzo, bold, italic 100% saqlanadi).
    2. Gotenberg LibreOffice API orqali uni PDF ga o'tkazadi.
    3. pypdfium2 yordamida 300 DPI o'ta tiniq PNG rasmga aylantiradi.
    """
    template_path = find_template_file(template_filename)
    if not os.path.exists(template_path):
        return False

    temp_docx = os.path.join(temp_dir, f"temp_{os.path.basename(output_png_path)}.docx")

    try:
        # 1. Asl Word shablonni to'ldirish
        fill_template(template_path, temp_docx, data)

        # 2. Gotenberg orqali PDF ga aylantirish
        with open(temp_docx, "rb") as f:
            res = requests.post(
                GOTENBERG_URL,
                files={"files": (template_filename, f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
                timeout=30
            )

        if res.status_code == 200 and len(res.content) > 100:
            # 3. PDF ni 300 DPI tiniq PNG rasmga o'tkazish
            pdf = pdfium.PdfDocument(res.content)
            page = pdf[0]
            # scale=4 -> 300 DPI tiniqlik
            pil_image = page.render(scale=4).to_pil()
            pil_image.save(output_png_path, "PNG", quality=95)
            pdf.close()
            return True
        else:
            return False

    except Exception as e:
        print(f"Konversiya xatosi: {e}")
        return False
    finally:
        try:
            if os.path.exists(temp_docx):
                os.remove(temp_docx)
        except Exception:
            pass
