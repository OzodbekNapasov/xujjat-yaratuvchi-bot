# ============================================================
#  api/webhook.py — Vercel Serverless Entry Point
#  Telegram webhook xabarlarini qabul qiladi va qayta ishlaydi
# ============================================================

import os
import sys
import json
import uuid
import asyncio

# Loyiha root ni path ga qo'shamiz
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

import httpx
from config import BOT_TOKEN, WEBHOOK_URL, TEMPLATES, TEMP_DIR, load_allowed_users
from services.state_storage import storage
from services.pdf_builder import build_pdf

app = FastAPI()

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"


# ── Telegram API yordamchi funksiyalari ───────────────────────────────────────

async def send_message(chat_id: int, text: str, reply_markup=None, parse_mode="HTML"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=15)


async def send_document(chat_id: int, file_path: str, caption: str = ""):
    async with httpx.AsyncClient() as client:
        with open(file_path, "rb") as f:
            await client.post(
                f"{TELEGRAM_API}/sendDocument",
                data={"chat_id": str(chat_id), "caption": caption, "parse_mode": "HTML"},
                files={"document": (os.path.basename(file_path), f, "application/pdf")},
                timeout=60,
            )


async def answer_callback(callback_query_id: str, text: str = ""):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id, "text": text},
            timeout=10,
        )


async def edit_message_reply_markup(chat_id: int, message_id: int):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{TELEGRAM_API}/editMessageReplyMarkup",
            json={"chat_id": chat_id, "message_id": message_id, "reply_markup": "{}"},
            timeout=10,
        )


# ── Shablon tanlash menyusi ───────────────────────────────────────────────────

def _build_template_keyboard():
    buttons = [
        [{"text": tpl["name"], "callback_data": f"tpl:{i}"}]
        for i, tpl in enumerate(TEMPLATES)
    ]
    return {"inline_keyboard": buttons}


# ── /start ────────────────────────────────────────────────────────────────────

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
    await send_message(
        chat_id,
        "📋 <b>Xush kelibsiz!</b>\n\n"
        "Qaysi hujjatni tayyorlashni xohlaysiz?\n"
        "Quyidagi ro'yxatdan birini tanlang 👇",
        reply_markup=_build_template_keyboard()
    )


# ── Shablon tanlanganda ───────────────────────────────────────────────────────

async def handle_template_select(chat_id: int, user_id: int, tpl_index: int,
                                  message_id: int, callback_id: str):
    allowed = load_allowed_users()
    if allowed and user_id not in allowed:
        await answer_callback(callback_id, "⛔ Ruxsat yo'q")
        return

    tpl = TEMPLATES[tpl_index]
    await storage.set(user_id, {
        "state": "answering",
        "tpl_index": tpl_index,
        "step": 0,
        "answers": {}
    })

    await answer_callback(callback_id)
    await edit_message_reply_markup(chat_id, message_id)
    await send_message(
        chat_id,
        f"✅ <b>{tpl['name']}</b> tanlandi.\n\n"
        f"Savollarga navbat bilan javob bering.\n"
        f"Bekor qilish: /cancel\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"<b>(1/{len(tpl['questions'])})</b> {tpl['questions'][0]}"
    )


# ── Foydalanuvchi javobini qayta ishlash ─────────────────────────────────────

async def handle_answer(chat_id: int, user_id: int, text: str):
    state_data = await storage.get(user_id)
    if not state_data or state_data.get("state") != "answering":
        await send_message(chat_id, "❓ Hujjat tayyorlash uchun /start buyrug'ini yuboring.")
        return

    tpl_index = state_data["tpl_index"]
    step      = state_data["step"]
    answers   = state_data["answers"]
    tpl       = TEMPLATES[tpl_index]

    # Javobni saqlaymiz
    answers[tpl["fields"][step]] = text.strip()
    step += 1

    if step < len(tpl["questions"]):
        await storage.set(user_id, {**state_data, "step": step, "answers": answers})
        await send_message(
            chat_id,
            f"<b>({step + 1}/{len(tpl['questions'])})</b> {tpl['questions'][step]}"
        )
    else:
        # Barcha savollar tugadi
        await storage.delete(user_id)
        await _generate_and_send(chat_id, tpl, answers)


# ── PDF yaratish va yuborish ──────────────────────────────────────────────────

async def _generate_and_send(chat_id: int, tpl: dict, answers: dict):
    uid       = uuid.uuid4().hex[:8]
    pdf_path  = os.path.join(TEMP_DIR, f"doc_{uid}.pdf")

    wait_resp = await _send_and_get_id(chat_id, "⏳ Hujjat tayyorlanmoqda...")

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, build_pdf, pdf_path, tpl["name"], answers, tpl.get("stamp", {})
        )

        fio = answers.get("FIO", "hujjat")
        await send_document(
            chat_id, pdf_path,
            caption=(
                f"✅ <b>{tpl['name']}</b> tayyor!\n"
                f"Yangi hujjat uchun /start"
            )
        )

        # "tayyorlanmoqda" xabarini o'chiramiz
        if wait_resp:
            await _delete_message(chat_id, wait_resp)

    except Exception as e:
        if wait_resp:
            await _delete_message(chat_id, wait_resp)
        await send_message(
            chat_id,
            f"❌ Xatolik:\n<code>{e}</code>\n\nQayta urinib ko'ring yoki /start"
        )
    finally:
        try:
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
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


# ── Webhook endpoint ──────────────────────────────────────────────────────────

@app.post("/webhook")
async def webhook(request: Request):
    try:
        update = await request.json()
    except Exception:
        return Response(status_code=200)

    # Callback query (tugma bosildi)
    if "callback_query" in update:
        cq       = update["callback_query"]
        user_id  = cq["from"]["id"]
        chat_id  = cq["message"]["chat"]["id"]
        msg_id   = cq["message"]["message_id"]
        cq_id    = cq["id"]
        data     = cq.get("data", "")

        if data.startswith("tpl:"):
            tpl_index = int(data.split(":")[1])
            await handle_template_select(chat_id, user_id, tpl_index, msg_id, cq_id)
        else:
            await answer_callback(cq_id)
        return Response(status_code=200)

    # Oddiy xabar
    if "message" in update:
        msg     = update["message"]
        chat_id = msg["chat"]["id"]
        user_id = msg["from"]["id"]
        text    = msg.get("text", "")

        if text == "/start":
            await handle_start(chat_id, user_id)
        elif text == "/cancel":
            await storage.delete(user_id)
            await send_message(chat_id, "❌ Bekor qilindi.\n\nYangi hujjat uchun /start")
        elif text:
            await handle_answer(chat_id, user_id, text)

    return Response(status_code=200)


# ── Webhook o'rnatish endpointi ───────────────────────────────────────────────

@app.get("/")
async def set_webhook():
    """
    Brauzerda https://your-app.vercel.app/ ni ochsangiz,
    webhook avtomatik o'rnatiladi.
    """
    if not WEBHOOK_URL or not BOT_TOKEN:
        return JSONResponse({"error": "BOT_TOKEN yoki WEBHOOK_HOST sozlanmagan"})

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{TELEGRAM_API}/setWebhook",
            json={"url": WEBHOOK_URL, "allowed_updates": ["message", "callback_query"]},
            timeout=15
        )
        result = r.json()

    return JSONResponse({
        "webhook_set": result.get("ok"),
        "webhook_url": WEBHOOK_URL,
        "description": result.get("description", ""),
    })


# ── Lokal ishga tushirish (test uchun) ────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
