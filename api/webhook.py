# ============================================================
#  api/webhook.py — Vercel Serverless Webhook Handler
#  Hujjatni PDF (rasm ko'rinishida) shaklida yuboradi
# ============================================================

import os
import sys
import json
import uuid
import asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import httpx

from config import BOT_TOKEN, WEBHOOK_URL, TEMPLATES, TEMP_DIR, load_allowed_users
from services.state_storage import storage
from services.pdf_builder import build_flattened_pdf

app = FastAPI()
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_message(chat_id: int, text: str, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=15)


async def send_document(chat_id: int, file_path: str, custom_filename: str, caption: str = "", reply_markup=None):
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            data = {"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"}
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)
            await client.post(
                f"{TELEGRAM_API}/sendDocument",
                data=data,
                files={"document": (custom_filename, f, "application/pdf")},
                timeout=60,
            )


def make_reply_keyboard(button_rows, one_time=True):
    if not button_rows:
        return {"remove_keyboard": True}
    keyboard = []
    for row in button_rows:
        keyboard.append([{"text": btn} for btn in row])
    return {
        "keyboard": keyboard,
        "resize_keyboard": True,
        "one_time_keyboard": one_time
    }


async def handle_start(chat_id: int, user_id: int):
    allowed = load_allowed_users()
    if allowed and user_id not in allowed:
        await send_message(
            chat_id,
            "⛔ Kechirasiz, siz bu botdan foydalana olmaysiz.\n"
            "Murojaat uchun admin bilan bog'laning."
        )
        return

    await storage.delete(user_id)

    menu_buttons = [[tpl["name"]] for tpl in TEMPLATES]
    kb = make_reply_keyboard(menu_buttons, one_time=True)

    await send_message(
        chat_id,
        "📋 <b>Qaysi hujjatni tayyorlashni xohlaysiz?</b>\n\n"
        "Quyidagi ro'yxatdan kerakli hujjatni tanlang 👇",
        reply_markup=kb
    )


async def start_document_dialog(chat_id: int, user_id: int, tpl_index: int):
    tpl = TEMPLATES[tpl_index]
    first_step = tpl["steps"][0]

    await storage.set(user_id, {
        "state": "answering",
        "tpl_index": tpl_index,
        "step": 0,
        "answers": {}
    })

    kb = make_reply_keyboard(first_step.get("buttons"))
    await send_message(
        chat_id,
        f"✅ <b>{tpl['name']}</b> tanlandi.\n\n"
        f"<b>(1/{len(tpl['steps'])})</b> {first_step['question']}",
        reply_markup=kb
    )


async def handle_user_input(chat_id: int, user_id: int, text: str):
    state_data = await storage.get(user_id)

    if not state_data or state_data.get("state") != "answering":
        for idx, tpl in enumerate(TEMPLATES):
            if text.strip() == tpl["name"].strip():
                await start_document_dialog(chat_id, user_id, idx)
                return

        await handle_start(chat_id, user_id)
        return

    tpl_index = state_data["tpl_index"]
    step      = state_data["step"]
    answers   = state_data["answers"]
    tpl       = TEMPLATES[tpl_index]
    current_step_info = tpl["steps"][step]

    answers[current_step_info["field"]] = text.strip()
    step += 1

    if step < len(tpl["steps"]):
        next_step_info = tpl["steps"][step]
        await storage.set(user_id, {**state_data, "step": step, "answers": answers})

        kb = make_reply_keyboard(next_step_info.get("buttons"))
        await send_message(
            chat_id,
            f"<b>({step + 1}/{len(tpl['steps'])})</b> {next_step_info['question']}",
            reply_markup=kb
        )
    else:
        await storage.delete(user_id)
        await _generate_and_send(chat_id, tpl, answers)


async def _generate_and_send(chat_id: int, tpl: dict, answers: dict):
    uid = uuid.uuid4().hex[:8]
    output_pdf = os.path.join(TEMP_DIR, f"doc_{uid}.pdf")

    wait_resp = await _send_and_get_id(chat_id, "⏳ Hujjat PDF shaklida tayyorlanmoqda...")

    try:
        # PDF ni yaratish va rasm shakliga o'tkazish (flattening)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, build_flattened_pdf, output_pdf, tpl["name"], answers
        )

        fio = answers.get("FIO", "Talaba").strip()
        custom_pdf_name = f"{fio} ma'lumotnoma.pdf"

        remove_kb = {"remove_keyboard": True}
        await send_document(
            chat_id,
            file_path=output_pdf,
            custom_filename=custom_pdf_name,
            caption=(
                f"✅ <b>{custom_pdf_name}</b> tayyorlandi!\n\n"
                f"📄 Hujjat PDF formatida (rasm shaklida) yuborildi.\n"
                f"Yangi hujjat yaratish uchun /start yuboring."
            ),
            reply_markup=remove_kb
        )

        if wait_resp:
            await _delete_message(chat_id, wait_resp)

    except Exception as e:
        if wait_resp:
            await _delete_message(chat_id, wait_resp)
        await send_message(
            chat_id,
            f"❌ Xatolik yuz berdi:\n<code>{e}</code>\n\nQayta boshlash: /start",
            reply_markup={"remove_keyboard": True}
        )
    finally:
        try:
            if os.path.exists(output_pdf):
                os.remove(output_pdf)
        except Exception:
            pass


async def _send_and_get_id(chat_id: int, text: str) -> int | None:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=10
        )
        data = r.json()
        return data.get("result", {}).get("message_id")


async def _delete_message(chat_id: int, message_id: int):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id},
            timeout=10
        )


@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = await request.json()
    except Exception:
        return Response(status_code=200)

    if "message" in update:
        msg     = update["message"]
        chat_id = msg["chat"]["id"]
        user_id = msg["from"]["id"]
        text    = msg.get("text", "")

        if text == "/start":
            await handle_start(chat_id, user_id)
        elif text == "/cancel":
            await storage.delete(user_id)
            await send_message(
                chat_id,
                "❌ Bekor qilindi.\n\nYangi hujjat yaratish uchun /start",
                reply_markup={"remove_keyboard": True}
            )
        elif text:
            await handle_user_input(chat_id, user_id, text)

    return Response(status_code=200)


@app.get("/")
async def set_webhook():
    if not WEBHOOK_URL or not BOT_TOKEN:
        return JSONResponse({"error": "BOT_TOKEN yoki WEBHOOK_HOST sozlanmagan"})

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{TELEGRAM_API}/setWebhook",
            json={"url": WEBHOOK_URL, "allowed_updates": ["message"]},
            timeout=15
        )
        result = r.json()

    return JSONResponse({
        "webhook_set": result.get("ok"),
        "webhook_url": WEBHOOK_URL,
        "description": result.get("description", ""),
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
