from aiogram import Router, F, Bot
from aiogram.types import Message, BusinessConnection
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database.requests import update_user_connection, get_user_by_connection, get_user_auto_reply, get_user_social_links, get_or_create_user, has_replied_to_customer, mark_replied_to_customer
from keyboards.user_kb import build_business_links_kb

router = Router()

@router.business_connection()
async def handle_business_connection(connection: BusinessConnection, session: AsyncSession):
    user_id = connection.user_chat_id
    # Foydalanuvchi bazada mavjud emasligi mumkin (agar u botga /start bosmasdan
    # to'g'ridan-to'g'ri Telegram Business orqali ulagan bo'lsa). Shu sabab
    # avval qatorni yaratib olamiz, aks holda keyingi UPDATE hech narsaga
    # ta'sir qilmay, connection_id saqlanmay qolardi.
    full_name = connection.user.full_name if connection.user else None
    await get_or_create_user(session, user_id, full_name)

    if connection.is_enabled:
        logging.info(f"User {user_id} enabled business connection: {connection.id}")
        await update_user_connection(session, user_id, connection.id)
    else:
        logging.info(f"User {user_id} disabled business connection")
        await update_user_connection(session, user_id, None)

@router.business_message()
async def handle_business_message(message: Message, session: AsyncSession, bot: Bot):
    logging.info(f"Received business_message from {message.from_user.id} in chat {message.chat.id}")
    connection_id = message.business_connection_id
    if not connection_id:
        return
        
    owner = await get_user_by_connection(session, connection_id)
    if not owner:
        logging.warning(f"Owner not found for connection {connection_id}")
        return

    if message.from_user.id == owner.user_id:
        # Owner is typing, ignore
        return

    auto_reply = await get_user_auto_reply(session, owner.user_id)
    if not auto_reply:
        logging.info(f"Owner {owner.user_id} has no auto-reply set")
        return

    # Shu mijozga (message.from_user.id) shu owner nomidan avval javob
    # berilgan bo'lsa, qayta yubormaymiz - faqat birinchi murojaatga javob beramiz.
    already_replied = await has_replied_to_customer(session, owner.user_id, message.from_user.id)
    if already_replied:
        logging.info(f"Customer {message.from_user.id} already got the auto-reply for owner {owner.user_id}")
        return

    # Yozib qo'yishni xabar yuborishdan oldin qilamiz - shunda mijoz tez-tez
    # xabar yozib yuborsa ham (masalan bir necha xabarni ketma-ket), ikkinchi
    # marta yuborilib yubormaydi.
    is_first_time = await mark_replied_to_customer(session, owner.user_id, message.from_user.id)
    if not is_first_time:
        return

    social_links = await get_user_social_links(session, owner.user_id)
    
    # Telefon raqamlarni ajratib olamiz (ularni tugma qilib bo'lmaydi)
    phone_links = []
    button_links = []
    for link in social_links:
        url = link.url_or_number
        if not url.startswith("http") and not url.startswith("tg://") and any(c.isdigit() for c in url):
            phone_links.append(link)
        else:
            button_links.append(link)
            
    reply_markup = build_business_links_kb(button_links)

    text_to_send = auto_reply.greeting_text or ""
    if phone_links:
        text_to_send += "\n\n📞 <b>Aloqa uchun:</b>\n"
        for p in phone_links:
            text_to_send += f"• {p.title}: <code>{p.url_or_number}</code>\n"

    try:
        if auto_reply.media_type == "text":
            await bot.send_message(
                chat_id=message.chat.id, 
                text=text_to_send, 
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "photo":
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=auto_reply.media_file_id,
                caption=text_to_send,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "video":
            await bot.send_video(
                chat_id=message.chat.id,
                video=auto_reply.media_file_id,
                caption=text_to_send,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "video_note":
            await bot.send_video_note(
                chat_id=message.chat.id,
                video_note=auto_reply.media_file_id,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
            if text_to_send:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=text_to_send,
                    business_connection_id=connection_id
                )
        elif auto_reply.media_type == "voice":
            await bot.send_voice(
                chat_id=message.chat.id,
                voice=auto_reply.media_file_id,
                caption=text_to_send,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "document":
            await bot.send_document(
                chat_id=message.chat.id,
                document=auto_reply.media_file_id,
                caption=text_to_send,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
    except TelegramAPIError as e:
        logging.error(f"Error sending business message: {e}")