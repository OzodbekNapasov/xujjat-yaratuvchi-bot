# ============================================================
#  config.py — Qarshi Tibbiyot Texnikumi Sozlamalari
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

# ── Shablonlar konfiguratsiyasi ─────────────────────────────────────────────
TEMPLATES = [
    {
        "id": "qabul_malumotnoma",
        "name": "🎓 O'qishga qabul ma'lumotnomasi",
        "questions": [
            "👤 Talabaning F.I.O ni kiriting (masalan: Napasov Ozodbek Zafar o’g’li):",
            "📚 Yo'nalish nomini kiriting (masalan: Hamshiralik ishi):",
            "📅 O'quv yilini kiriting (masalan: 2026/2027):",
            "📆 Berilgan sanani kiriting (masalan: 12.07.2026 y.):",
        ],
        "fields": ["FIO", "YONALISH", "OQUV_YILI", "SANA"],
        "stamp": {
            "pechat": {"x_mm": 130, "y_mm": 220, "w_mm": 45, "h_mm": 45},
            "imzo":   {"x_mm": 140, "y_mm": 235, "w_mm": 45, "h_mm": 20},
        },
    }
]

BASE_DIR    = os.path.dirname(__file__)
LOGO_FILE   = os.path.join(BASE_DIR, "templates", "stamps", "logo.png")
PECHAT_FILE = os.path.join(BASE_DIR, "templates", "stamps", "pechat.png")
IMZO_FILE   = os.path.join(BASE_DIR, "templates", "stamps", "imzo.png")
FONT_FILE   = os.path.join(BASE_DIR, "templates", "fonts", "FreeSans.ttf")

TEMP_DIR = "/tmp" if os.path.exists("/tmp") else os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
