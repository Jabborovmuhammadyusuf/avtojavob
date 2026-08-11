from aiogram import Router, F, Bot
from aiogram.types import Message, BusinessConnection
from aiogram.exceptions import TelegramAPIError
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database.requests import update_user_connection, get_user_by_connection, get_user_auto_reply, get_user_social_links
from keyboards.user_kb import build_business_links_kb

router = Router()

@router.business_connection()
async def handle_business_connection(connection: BusinessConnection, session: AsyncSession):
    user_id = connection.user_chat_id
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
        
    social_links = await get_user_social_links(session, owner.user_id)
    reply_markup = build_business_links_kb(social_links)
    
    try:
        if auto_reply.media_type == "text":
            await bot.send_message(
                chat_id=message.chat.id, 
                text=auto_reply.greeting_text, 
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "photo":
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=auto_reply.media_file_id,
                caption=auto_reply.greeting_text,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "video":
            await bot.send_video(
                chat_id=message.chat.id,
                video=auto_reply.media_file_id,
                caption=auto_reply.greeting_text,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "video_note":
            # Video note da caption va reply_markup qo'llab-quvvatlanmasligi mumkin, lekin yuborib ko'ramiz
            await bot.send_video_note(
                chat_id=message.chat.id,
                video_note=auto_reply.media_file_id,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
            # Agar text ham bo'lsa
            if auto_reply.greeting_text:
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=auto_reply.greeting_text,
                    business_connection_id=connection_id
                )
        elif auto_reply.media_type == "voice":
            await bot.send_voice(
                chat_id=message.chat.id,
                voice=auto_reply.media_file_id,
                caption=auto_reply.greeting_text,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
        elif auto_reply.media_type == "document":
            await bot.send_document(
                chat_id=message.chat.id,
                document=auto_reply.media_file_id,
                caption=auto_reply.greeting_text,
                reply_markup=reply_markup,
                business_connection_id=connection_id
            )
    except TelegramAPIError as e:
        logging.error(f"Error sending business message: {e}")
