# ============================================================
#  handlers/dialog.py
#  FSM — savol-javob zanjiri va hujjat yaratish
# ============================================================

import os
import uuid
import asyncio

from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import TEMPLATES, PECHAT_FILE, IMZO_FILE, TEMP_DIR
from services.docx_filler import fill_template
from services.pdf_maker import docx_to_pdf, add_stamp_to_pdf

dialog_router = Router()


class Form(StatesGroup):
    answering = State()


# ── Dialogni boshlash (start.py dan chaqiriladi) ─────────────────────────────
async def begin_dialog(message: Message, state: FSMContext, tpl_index: int):
    tpl = TEMPLATES[tpl_index]
    await state.set_state(Form.answering)
    await state.update_data(tpl_index=tpl_index, step=0, answers={})
    await message.answer(
        f"✅ <b>{tpl['name']}</b> tanlandi.\n\n"
        f"Savollarga navbat bilan javob bering.\n"
        f"Bekor qilish: /cancel\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>(1/{len(tpl['questions'])})</b> {tpl['questions'][0]}",
        parse_mode="HTML"
    )


# ── Har bir javobni qabul qilish ─────────────────────────────────────────────
@dialog_router.message(Form.answering, F.text)
async def handle_answer(message: Message, state: FSMContext):
    data      = await state.get_data()
    tpl_index = data["tpl_index"]
    step      = data["step"]
    answers   = data["answers"]
    tpl       = TEMPLATES[tpl_index]

    # Javobni saqlaymiz
    answers[tpl["fields"][step]] = message.text.strip()
    step += 1

    if step < len(tpl["questions"]):
        await state.update_data(step=step, answers=answers)
        await message.answer(
            f"<b>({step + 1}/{len(tpl['questions'])})</b> {tpl['questions'][step]}",
            parse_mode="HTML"
        )
    else:
        # Barcha savollar tugadi
        await state.clear()
        await _generate_and_send(message, tpl, answers)


# ── Hujjat yaratish va yuborish ───────────────────────────────────────────────
async def _generate_and_send(message: Message, tpl: dict, answers: dict):
    uid           = uuid.uuid4().hex[:8]
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    template_path = os.path.join(templates_dir, tpl["file"])
    docx_out      = os.path.join(TEMP_DIR, f"doc_{uid}.docx")
    pdf_raw       = os.path.join(TEMP_DIR, f"doc_{uid}_raw.pdf")
    pdf_final     = os.path.join(TEMP_DIR, f"doc_{uid}.pdf")

    wait_msg = await message.answer("⏳ Hujjat tayyorlanmoqda...")

    try:
        # 1. Shablonni to'ldirish
        fill_template(template_path, docx_out, answers)

        # 2. DOCX → PDF (LibreOffice, thread pool da)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, docx_to_pdf, docx_out, pdf_raw)

        # 3. Pechat va imzoni PDF ustiga qo'shish
        pechat = PECHAT_FILE if os.path.exists(PECHAT_FILE) else None
        imzo   = IMZO_FILE   if os.path.exists(IMZO_FILE)   else None
        await loop.run_in_executor(
            None, add_stamp_to_pdf,
            pdf_raw, pdf_final, pechat, imzo, tpl.get("stamp", {})
        )

        # 4. Yuborish
        await wait_msg.delete()
        send_path = pdf_final if os.path.exists(pdf_final) else pdf_raw
        fio       = answers.get("FIO", "hujjat")

        await message.answer_document(
            FSInputFile(send_path, filename=f"{fio}.pdf"),
            caption=(
                f"✅ <b>{tpl['name']}</b> tayyor!\n"
                f"📄 PDF formatida yuborildi.\n\n"
                f"Yangi hujjat: /start"
            ),
            parse_mode="HTML"
        )

    except Exception as e:
        await wait_msg.delete()
        await message.answer(
            f"❌ Xatolik:\n<code>{e}</code>\n\n"
            f"Qayta urinib ko'ring yoki adminga murojaat qiling.",
            parse_mode="HTML"
        )

    finally:
        # Vaqtinchalik fayllarni tozalash
        for f in [docx_out, pdf_raw, pdf_final]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception:
                pass
