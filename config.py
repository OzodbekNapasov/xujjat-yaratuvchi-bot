# ============================================================
#  config.py — Sozlamalar (Vercel webhook versiyasi)
# ============================================================

import os
import json
from dotenv import load_dotenv

load_dotenv()

# ── Bot token ─────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── Webhook URL (Vercel domain) ───────────────────────────────────────────────
# Vercel deploy qilgandan so'ng avtomatik beriladi, masalan:
# https://docbot-xyz.vercel.app
WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")   # https://your-app.vercel.app
WEBHOOK_PATH: str = "/webhook"
WEBHOOK_URL:  str = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# ── Redis (Vercel KV) — FSM holati saqlash ────────────────────────────────────
# Vercel KV → Settings → Create Database → KV Store
# U yerdan REDIS_URL ni olib, Vercel Environment Variables ga qo'shing
REDIS_URL: str = os.getenv("REDIS_URL", "")

# ── Ruxsat etilgan foydalanuvchilar ───────────────────────────────────────────
# Vercel da fayl tizimi yo'q, shuning uchun JSON string sifatida env var da saqlang:
# ALLOWED_USERS=["123456789","987654321"]
def load_allowed_users() -> set[int]:
    raw = os.getenv("ALLOWED_USERS", "[]")
    try:
        users = json.loads(raw)
        return {int(u) for u in users}
    except Exception:
        return set()

# ── Shablon konfiguratsiyasi ──────────────────────────────────────────────────
# Har bir shablon uchun:
#   name      — foydalanuvchiga ko'rsatiladigan nom
#   questions — navbat bilan beriladigan savollar
#   fields    — PDF da to'ldiriladigan maydonlar (savollar bilan bir tartibda)
#   stamp     — pechat/imzo joylashuvi (mm da, A4 sahifada)
#
# A4: 210mm x 297mm

TEMPLATES = [
    {
        "name": "📄 Ma'lumotnoma №1",
        "questions": [
            "👤 F.I.O ni kiriting (To'liq ismi sharifi):",
            "🪪 Passport seriya va raqamini kiriting:",
            "📅 Tug'ilgan sanangizni kiriting (KK.OO.YYYY):",
            "🏠 Yashash manzilingizni kiriting:",
            "📞 Telefon raqamingizni kiriting:",
        ],
        "fields": ["FIO", "PASSPORT", "TUGILGAN_SANA", "MANZIL", "TELEFON"],
        "stamp": {
            "pechat": {"x_mm": 30,  "y_mm": 240, "w_mm": 40, "h_mm": 40},
            "imzo":   {"x_mm": 100, "y_mm": 252, "w_mm": 50, "h_mm": 15},
        },
    },
    {
        "name": "📄 Ma'lumotnoma №2",
        "questions": [
            "👤 F.I.O ni kiriting:",
            "🏢 Tashkilot nomini kiriting:",
            "📅 Sana (KK.OO.YYYY):",
            "💬 Murojaat mazmunini kiriting:",
        ],
        "fields": ["FIO", "TASHKILOT", "SANA", "MAZMUN"],
        "stamp": {
            "pechat": {"x_mm": 25,  "y_mm": 250, "w_mm": 40, "h_mm": 40},
            "imzo":   {"x_mm": 100, "y_mm": 262, "w_mm": 50, "h_mm": 15},
        },
    },
]

# ── Fayl yo'llari ─────────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(__file__)
PECHAT_FILE = os.path.join(BASE_DIR, "templates", "stamps", "pechat.png")
IMZO_FILE   = os.path.join(BASE_DIR, "templates", "stamps", "imzo.png")
FONT_FILE   = os.path.join(BASE_DIR, "templates", "fonts", "FreeSans.ttf")

# Vercel da /tmp papkasi mavjud (512 MB)
TEMP_DIR = "/tmp" if os.path.exists("/tmp") else os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
