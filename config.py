# ============================================================
#  config.py — Shablonlar va tugmalar sozlamalari
# ============================================================

import os
import json
from datetime import datetime
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_FILE = os.path.join(BASE_DIR, "templates", "malumotnoma.docx")
if not os.path.exists(TEMPLATE_FILE):
    alt_path = os.path.join(os.getcwd(), "templates", "malumotnoma.docx")
    if os.path.exists(alt_path):
        TEMPLATE_FILE = alt_path

today_str = datetime.now().strftime("%d.%m.%Y y.")

# Shablonlar ro'yxati (Kelajakda 2, 3-hujjatlarni ham osongina qo'shishingiz mumkin)
TEMPLATES = [
    {
        "id": "qabul_1_kurs",
        "name": "🎓 1-kursga qabul ma'lumotnomasi",
        "file": TEMPLATE_FILE,
        "steps": [
            {
                "field": "FIO",
                "question": "👤 Talabaning F.I.O ni kiriting:\n<i>(Masalan: Napasov Ozodbek Zafar o’g’li)</i>",
                "buttons": None
            },
            {
                "field": "YONALISH",
                "question": "📚 Yo'nalishni tanlang yoki kiriting:",
                "buttons": [
                    ["Hamshiralik ishi"],
                    ["Feldsherlik ishi"],
                    ["Farmatsiya ishi"]
                ]
            },
            {
                "field": "OQUV_YILI",
                "question": "📅 O'quv yilini tanlang yoki kiriting:",
                "buttons": [
                    ["2026/2027", "2025/2026"]
                ]
            },
            {
                "field": "SANA",
                "question": "📆 Berilgan sanani tanlang yoki qo'lda kiriting:",
                "buttons": [
                    [today_str]
                ]
            }
        ]
    }
]

TEMP_DIR = "/tmp" if os.path.exists("/tmp") else os.path.join(BASE_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)
