# 📄 Telegram Hujjat Generator Bot

Foydalanuvchi dialog orqali ma'lumot kiritadi → Bot `.docx` shablonni to'ldiradi → Pechat/imzoni PDF ustiga qo'yadi → Tayyor PDFni yuboradi.

---

## ⚡ Ishga tushirish (1-marta sozlash)

### 1. Bot token
[@BotFather](https://t.me/BotFather) dan token oling va `.env` fayliga yozing:
```
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 2. Ruxsat etilgan foydalanuvchilar
`allowed_users.txt` ga Telegram user_id larini qo'shing (har birini alohida qatorga):
```
123456789
987654321
```
> Telegram ID ni bilmasangiz: [@userinfobot](https://t.me/userinfobot) ga `/start` yuboring

### 3. Shablon fayllar
`templates/` papkasiga qo'ying:
- `shablon1.docx` — birinchi shablon
- `shablon2.docx` — ikkinchi shablon
- `stamps/pechat.png` — pechat rasmi (PNG, shaffof fon)
- `stamps/imzo.png` — imzo rasmi (PNG, shaffof fon)

### 4. Shablonni sozlash
`.docx` faylingiz ichida o'zgaruvchi joylarni `{{FIELD_NOMI}}` bilan belgilang:
```
F.I.O: {{FIO}}
Passport: {{PASSPORT}}
Sana: {{TUGILGAN_SANA}}
```
Keyin `config.py` da mos `fields` va `questions` ni yangilang.

### 5. LibreOffice o'rnatish
PDF konversiya uchun kerak:
- **Windows**: https://www.libreoffice.org/download/download/
- **Linux**: `sudo apt install libreoffice`

### 6. Botni ishga tushirish
```bash
python main.py
```

---

## 🗂 Fayl tuzilmasi

```
docbot/
├── main.py                  ← Botni ishga tushirish
├── config.py                ← Sozlamalar va shablon konfiguratsiyasi
├── .env                     ← Bot token (maxfiy!)
├── allowed_users.txt        ← Ruxsat etilgan user_id lar
├── requirements.txt
├── handlers/
│   ├── start.py             ← /start, shablon tanlash
│   └── dialog.py            ← Savol-javob zanjiri, PDF yaratish
├── services/
│   ├── docx_filler.py       ← Shablonni to'ldirish
│   └── pdf_maker.py         ← PDF konversiya + pechat/imzo
├── templates/
│   ├── shablon1.docx        ← O'zingiz qo'ying
│   ├── shablon2.docx        ← O'zingiz qo'ying
│   └── stamps/
│       ├── pechat.png       ← O'zingiz qo'ying
│       └── imzo.png         ← O'zingiz qo'ying
└── temp/                    ← Vaqtinchalik fayllar (avtomatik)
```

---

## ⚙️ Yangi shablon qo'shish

`config.py` dagi `TEMPLATES` ro'yxatiga qo'shing:

```python
{
    "name": "📄 Yangi hujjat",
    "file": "yangi_shablon.docx",
    "questions": [
        "👤 F.I.O:",
        "📅 Sana:",
    ],
    "fields": ["FIO", "SANA"],
    "stamp": {
        "pechat": {"x_mm": 30, "y_mm": 240, "w_mm": 40, "h_mm": 40},
        "imzo":   {"x_mm": 100, "y_mm": 248, "w_mm": 50, "h_mm": 15},
    },
},
```

> **x_mm / y_mm** — sahifaning chap-yuqori burchagidan mm da masofa  
> Joylashuvni to'g'rilash uchun qiymatlarni biroz o'zgartirib sinab ko'ring

---

## 🔒 Xavfsizlik

- Bot faqat `allowed_users.txt` dagi ID larga javob beradi
- `.env` faylini hech kimga ko'rsatmang
- Vaqtinchalik fayllar (`temp/`) yuborilgandan so'ng avtomatik o'chiriladi
