from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import config
from core.loader import bot
from database.requests import get_all_users_count, get_all_users
from keyboards.admin_kb import get_admin_main_kb, get_cancel_kb
from states.admin_states import AdminBroadcast
from services.broadcaster import broadcast

router = Router()

# Middleware orqali faqat adminlar kirishini ta'minlash ham mumkin, 
# lekin bu yerda oddiy filter ishlatamiz.
def is_admin(user_id: int) -> bool:
    return user_id in config.admin_ids_list

@router.message(Command("admin"))
async def admin_start(message: Message):
    if not is_admin(message.from_user.id):
        return
    await message.answer("👑 Super Admin paneliga xush kelibsiz!", reply_markup=get_admin_main_kb())

@router.callback_query(F.data == "admin_stats")
async def show_stats(call: CallbackQuery, session: AsyncSession):
    if not is_admin(call.from_user.id):
        return
    count = await get_all_users_count(session)
    await call.message.edit_text(f"📊 Umumiy foydalanuvchilar soni: {count}\nFaol business ulanishlar tekshirilmoqda...", reply_markup=get_admin_main_kb())

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (yoki bekor qiling):", reply_markup=get_cancel_kb())
    await state.set_state(AdminBroadcast.waiting_for_message)

@router.callback_query(F.data == "admin_cancel", AdminBroadcast.waiting_for_message)
async def cancel_broadcast(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Brodcast bekor qilindi.", reply_markup=get_admin_main_kb())

@router.message(AdminBroadcast.waiting_for_message)
async def process_broadcast(message: Message, state: FSMContext, session: AsyncSession):
    await state.clear()
    users = await get_all_users(session)
    user_ids = [u.user_id for u in users]
    
    msg = await message.answer(f"Ommaviy xabar yuborish boshlandi. Jami: {len(user_ids)} ta foydalanuvchi.")
    
    # Text orqali jo'natamiz. Media fayllarni copy_message qilib jo'natish qismi murakkabroq bo'lishi mumkin.
    count = await broadcast(bot, user_ids, message.html_text)
    
    await msg.reply(f"Xabar yuborish yakunlandi.\nMuvaffaqiyatli: {count} ta")

@router.callback_query(F.data == "admin_premium")
async def admin_premium(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    await call.answer("Premium funksiyasi hali ishlab chiqilmoqda.", show_alert=True)
