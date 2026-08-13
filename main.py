# ============================================================
#  main.py — Botni ishga tushirish
# ============================================================

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from handlers.start import router as start_router
from handlers.dialog import dialog_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if BOT_TOKEN == "BU_YERGA_TOKEN_YOZING":
        logger.error(
            "BOT_TOKEN o'rnatilmagan!\n"
            "1) .env faylini yarating va BOT_TOKEN=... yozing\n"
            "   YOKI\n"
            "2) config.py dagi BOT_TOKEN ni to'g'ridan to'g'ri yozing"
        )
        return

    bot = Bot(token=BOT_TOKEN)
    dp  = Dispatcher(storage=MemoryStorage())

    # Routerlarni qo'shamiz (dialog_router avval — FSM uchun)
    dp.include_router(dialog_router)
    dp.include_router(start_router)

    logger.info("Bot ishga tushdi ✅")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
