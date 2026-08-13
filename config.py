# ============================================================
#  config.py — DOCX Shablonni tahrirlash sozlamalari
# ============================================================

import os
import json
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
WEBHOOK_HOST: str = os.getenv("WEBHOOK_HOST", "")
WEBHOOK_PATH: str = "/webhook"
WEBHOOK_URL:  str = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
REDIS_URL: str = os.getenv("REDIS_URL", "")

def load_allowed_users() -> set[int]:
    raw = os.getenv("ALLOWED_USERS", "[]")
    try:
        users = json.loads(raw)
        return {int(u) for u in users}
    except Exception:
        return set()

BASE_DIR = os.path.dirname(__file__)

# ── Shablonlar konfiguratsiyasi ─────────────────────────────────────────────
TEMPLATES = [
    {
        "id": "malumotnoma",
        "name": "🎓 O'qishga qabul ma'lumotnomasi",
        "file": os.path.join(BASE_DIR, "templates", "malumotnoma.docx"),
        "questions": [
            "👤 Talabaning F.I.O ni kiriting (masalan: Napasov Ozodbek Zafar o’g’li):",
            "📚 Yo'nalish nomini kiriting (masalan: Hamshiralik ishi):",
            "📅 O'quv yilini kiriting (masalan: 2026/2027):",
            "📆 Berilgan sanani kiriting (masalan: 12.07.2026 y.):",
        ],
        "fields": ["FIO", "YONALISH", "OQUV_YILI", "SANA"],
    }
]

TEMP_DIR = "/tmp" if os.path.exists("/tmp") else os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
