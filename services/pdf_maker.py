# ============================================================
#  services/pdf_maker.py
#  .docx → .pdf va pechat/imzoni PDF ustiga qo'yish
# ============================================================

import os
import subprocess
import tempfile
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image


# ── DOCX → PDF ───────────────────────────────────────────────────────────────

def docx_to_pdf(docx_path: str, pdf_path: str) -> None:
    """
    LibreOffice headless yordamida .docx ni .pdf ga o'giradi.
    LibreOffice o'rnatilgan bo'lishi kerak:
      Windows: https://www.libreoffice.org/download/download/
      Linux  : sudo apt install libreoffice
    """
    out_dir = str(Path(pdf_path).parent)

    # LibreOffice yo'llari (Windows va Linux)
    lo_paths = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        "soffice",        # Linux / PATH da bo'lsa
        "libreoffice",
    ]

    soffice = None
    for path in lo_paths:
        if os.path.exists(path) or _command_exists(path):
            soffice = path
            break

    if soffice is None:
        raise RuntimeError(
            "LibreOffice topilmadi!\n"
            "O'rnating: https://www.libreoffice.org/download/download/\n"
            "Yoki Windows da: winget install LibreOffice.LibreOffice"
        )

    result = subprocess.run(
        [soffice, "--headless", "--convert-to", "pdf", "--outdir", out_dir, docx_path],
        capture_output=True, text=True, timeout=60
    )
    if result.returncode != 0:
        raise RuntimeError(f"LibreOffice xatosi:\n{result.stderr}")

    # LibreOffice chiqargan fayl nomini aniqlaymiz
    generated = Path(out_dir) / (Path(docx_path).stem + ".pdf")
    if str(generated) != pdf_path:
        generated.rename(pdf_path)


def _command_exists(cmd: str) -> bool:
    try:
        subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
        return True
    except Exception:
        return False


# ── Pechat va imzoni PDF ustiga qo'yish ──────────────────────────────────────

def add_stamp_to_pdf(
    pdf_path: str,
    output_path: str,
    pechat_img_path: str | None,
    imzo_img_path:   str | None,
    stamp_config: dict,
    page_index: int = -1,        # -1 = oxirgi sahifa
) -> None:
    """
    stamp_config misoli:
      {
        "pechat": {"x_mm": 30, "y_mm": 240, "w_mm": 40, "h_mm": 40},
        "imzo":   {"x_mm": 100, "y_mm": 248, "w_mm": 50, "h_mm": 15},
      }
    """
    doc = fitz.open(pdf_path)
    page_idx = page_index if page_index >= 0 else len(doc) - 1
    page = doc[page_idx]

    mm = 2.8346  # 1 mm = 2.8346 pt (PDF birlik)

    def place_image(img_path: str, cfg: dict) -> None:
        if not img_path or not os.path.exists(img_path):
            return
        x0 = cfg["x_mm"] * mm
        y0 = cfg["y_mm"] * mm
        x1 = x0 + cfg["w_mm"] * mm
        y1 = y0 + cfg["h_mm"] * mm
        rect = fitz.Rect(x0, y0, x1, y1)

        # PNG ni to'g'ri o'qib, alpha kanalini saqlaymiz
        img = Image.open(img_path).convert("RGBA")
        tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        img.save(tmp.name)
        tmp.close()

        page.insert_image(rect, filename=tmp.name, overlay=True)
        os.unlink(tmp.name)

    if pechat_img_path:
        place_image(pechat_img_path, stamp_config.get("pechat", {}))
    if imzo_img_path:
        place_image(imzo_img_path,   stamp_config.get("imzo",   {}))

    doc.save(output_path, deflate=True)
    doc.close()
