from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import config
from core.loader import bot
from database.requests import get_all_users_count, get_all_users, get_premium_users_count, grant_premium
from keyboards.admin_kb import get_admin_main_kb, get_cancel_kb
from states.admin_states import AdminBroadcast, AdminPremium
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
    premium_count = await get_premium_users_count(session)
    await call.message.edit_text(
        f"📊 Umumiy foydalanuvchilar soni: {count}\n👑 Faol premium foydalanuvchilar: {premium_count}",
        reply_markup=get_admin_main_kb()
    )

@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (yoki bekor qiling):", reply_markup=get_cancel_kb())
    await state.set_state(AdminBroadcast.waiting_for_message)

@router.callback_query(F.data == "admin_cancel")
async def cancel_admin_flow(call: CallbackQuery, state: FSMContext):
    # Broadcast, premium yoki boshqa istalgan admin FSM oqimini bekor qiladi.
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    await call.message.edit_text("Bekor qilindi.", reply_markup=get_admin_main_kb())

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
async def admin_premium(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await call.message.edit_text(
        "👑 <b>Premium berish</b>\n\n"
        "Premium beriladigan foydalanuvchining Telegram ID raqamini yuboring.\n"
        "<i>(Foydalanuvchi ID'sini bilish uchun u avval botga /start bosgan bo'lishi kerak)</i>",
        reply_markup=get_cancel_kb()
    )
    await state.set_state(AdminPremium.waiting_for_user_id)

@router.message(AdminPremium.waiting_for_user_id)
async def admin_premium_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    raw = (message.text or "").strip()
    if not raw.isdigit():
        return await message.answer("❗️ Iltimos, faqat raqamlardan iborat Telegram ID yuboring.", reply_markup=get_cancel_kb())

    await state.update_data(target_user_id=int(raw))
    await message.answer("Necha kunlik premium berilsin? (masalan: 30)", reply_markup=get_cancel_kb())
    await state.set_state(AdminPremium.waiting_for_days)

@router.message(AdminPremium.waiting_for_days)
async def admin_premium_days(message: Message, state: FSMContext, session: AsyncSession):
    if not is_admin(message.from_user.id):
        return
    raw = (message.text or "").strip()
    if not raw.isdigit() or int(raw) <= 0:
        return await message.answer("❗️ Iltimos, musbat butun son kiriting (masalan: 30).", reply_markup=get_cancel_kb())

    data = await state.get_data()
    target_user_id = data["target_user_id"]
    days = int(raw)
    await state.clear()

    user = await grant_premium(session, target_user_id, days)
    if not user:
        return await message.answer(
            f"❌ <code>{target_user_id}</code> ID'li foydalanuvchi topilmadi.\n"
            "U botga hech bo'lmaganda bir marta /start bosgan bo'lishi kerak.",
            reply_markup=get_admin_main_kb()
        )

    expiry_str = user.premium_expires_at.strftime("%Y-%m-%d %H:%M")
    await message.answer(
        f"✅ Premium berildi!\n\n"
        f"Foydalanuvchi: <code>{target_user_id}</code>\n"
        f"Amal qilish muddati: <b>{expiry_str}</b> gacha",
        reply_markup=get_admin_main_kb()
    )

    try:
        await bot.send_message(
            target_user_id,
            f"🎉 Tabriklaymiz! Sizga <b>{days} kunlik Premium</b> tarif faollashtirildi.\n"
            f"Amal qilish muddati: <b>{expiry_str}</b> gacha."
        )
    except Exception:
        # Foydalanuvchi botni bloklagan yoki boshqa sabab bo'lishi mumkin - buni admin oqimini to'xtatmaymiz.
        pass