# ============================================================
#  handlers/start.py  (to'liq, dialog.py bilan integratsiya)
# ============================================================

from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import TEMPLATES, load_allowed_users
from handlers.dialog import begin_dialog

router = Router()


def _is_allowed(user_id: int) -> bool:
    return user_id in load_allowed_users()


# ── /start ───────────────────────────────────────────────────────────────────
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    if not _is_allowed(message.from_user.id):
        await message.answer(
            "⛔ Kechirasiz, siz bu botdan foydalana olmaysiz.\n"
            "Murojaat uchun admin bilan bog'laning."
        )
        return

    await state.clear()
    await _show_menu(message)


# ── /cancel ──────────────────────────────────────────────────────────────────
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.\n\nYangi hujjat uchun /start")


# ── Shablon tanlash menyusi ───────────────────────────────────────────────────
async def _show_menu(message: Message):
    builder = InlineKeyboardBuilder()
    for i, tpl in enumerate(TEMPLATES):
        builder.button(text=tpl["name"], callback_data=f"tpl:{i}")
    builder.adjust(1)

    await message.answer(
        "📋 <b>Xush kelibsiz!</b>\n\n"
        "Qaysi hujjatni tayyorlashni xohlaysiz?\n"
        "Quyidagi ro'yxatdan birini tanlang 👇",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


# ── Shablon tanlanganda ───────────────────────────────────────────────────────
@router.callback_query(F.data.startswith("tpl:"))
async def on_template_selected(call: CallbackQuery, state: FSMContext):
    if not _is_allowed(call.from_user.id):
        await call.answer("⛔ Ruxsat yo'q", show_alert=True)
        return

    tpl_index = int(call.data.split(":")[1])
    await call.message.edit_reply_markup(reply_markup=None)
    await call.answer()
    await begin_dialog(call.message, state, tpl_index)


# ── Noma'lum xabarlar ─────────────────────────────────────────────────────────
@router.message()
async def unknown_message(message: Message, state: FSMContext):
    if not _is_allowed(message.from_user.id):
        return
    current = await state.get_state()
    if current is None:
        await message.answer(
            "❓ Hujjat tayyorlash uchun /start buyrug'ini yuboring."
        )
