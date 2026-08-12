from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from database.models import User, AutoReply, SocialLink, RepliedCustomer

async def get_or_create_user(session: AsyncSession, user_id: int, full_name: str = None) -> User:
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(user_id=user_id, full_name=full_name)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user

async def get_user_by_connection(session: AsyncSession, connection_id: str) -> User | None:
    stmt = select(User).where(User.connection_id == connection_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def update_user_connection(session: AsyncSession, user_id: int, connection_id: str):
    stmt = update(User).where(User.user_id == user_id).values(connection_id=connection_id)
    await session.execute(stmt)
    await session.commit()

async def get_user_auto_reply(session: AsyncSession, user_id: int) -> AutoReply | None:
    stmt = select(AutoReply).where(AutoReply.user_id == user_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def set_user_auto_reply(session: AsyncSession, user_id: int, greeting_text: str = None, media_file_id: str = None, media_type: str = "text"):
    stmt = select(AutoReply).where(AutoReply.user_id == user_id)
    result = await session.execute(stmt)
    auto_reply = result.scalar_one_or_none()

    if not auto_reply:
        auto_reply = AutoReply(user_id=user_id, greeting_text=greeting_text, media_file_id=media_file_id, media_type=media_type)
        session.add(auto_reply)
    else:
        auto_reply.greeting_text = greeting_text
        auto_reply.media_file_id = media_file_id
        auto_reply.media_type = media_type
    
    await session.commit()

async def get_user_social_links(session: AsyncSession, user_id: int) -> list[SocialLink]:
    stmt = select(SocialLink).where(SocialLink.user_id == user_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def add_social_link(session: AsyncSession, user_id: int, platform_type: str, title: str, url_or_number: str):
    link = SocialLink(user_id=user_id, platform_type=platform_type, title=title, url_or_number=url_or_number)
    session.add(link)
    await session.commit()

async def delete_social_link(session: AsyncSession, link_id: int):
    stmt = select(SocialLink).where(SocialLink.id == link_id)
    result = await session.execute(stmt)
    link = result.scalar_one_or_none()
    if link:
        await session.delete(link)
        await session.commit()

async def has_replied_to_customer(session: AsyncSession, owner_id: int, customer_id: int) -> bool:
    stmt = select(RepliedCustomer).where(
        RepliedCustomer.owner_id == owner_id,
        RepliedCustomer.customer_id == customer_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None

async def mark_replied_to_customer(session: AsyncSession, owner_id: int, customer_id: int) -> bool:
    """Mijozni 'javob berilganlar' ro'yxatiga qo'shadi.
    True qaytarsa - bu birinchi marta yozilgani va yozish muvaffaqiyatli bo'lgani,
    False qaytarsa - poyga holati (race condition) tufayli boshqa so'rov allaqachon
    belgilab ulgurgani (masalan mijoz tez-tez xabar yuborgan bo'lsa)."""
    session.add(RepliedCustomer(owner_id=owner_id, customer_id=customer_id))
    try:
        await session.commit()
        return True
    except IntegrityError:
        await session.rollback()
        return False

async def grant_premium(session: AsyncSession, user_id: int, days: int) -> User | None:
    """Foydalanuvchiga `days` kunlik premium beradi.
    Agar foydalanuvchida hali muddati tugamagan premium bo'lsa, muddatga
    qo'shib boradi (uzaytiradi), aks holda hozirgi vaqtdan boshlab hisoblaydi.
    Kelajakda to'lov tizimi (Click/Payme) integratsiya qilinganda ham
    shu funksiya webhook orqali chaqirilishi mumkin."""
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None

    now = datetime.utcnow()
    base = user.premium_expires_at if (user.premium_expires_at and user.premium_expires_at > now) else now
    user.premium_expires_at = base + timedelta(days=days)
    user.is_premium = True
    await session.commit()
    await session.refresh(user)
    return user

async def check_and_sync_premium(session: AsyncSession, user_id: int) -> User | None:
    """Foydalanuvchi profilini ochganda/chaqirilganda muddati tugagan
    premiumni darhol Freemiumga tushiradi."""
    stmt = select(User).where(User.user_id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        return None

    if user.is_premium and user.premium_expires_at and user.premium_expires_at <= datetime.utcnow():
        user.is_premium = False
        await session.commit()
        await session.refresh(user)
    return user

async def downgrade_expired_premiums(session: AsyncSession) -> int:
    """Fon rejimidagi (background) vazifa uchun: muddati tugagan barcha
    premiumlarni birdaniga Freemiumga tushiradi. Nechta foydalanuvchi
    tushirilganini qaytaradi."""
    stmt = select(User).where(User.is_premium == True, User.premium_expires_at <= datetime.utcnow())
    result = await session.execute(stmt)
    expired_users = list(result.scalars().all())

    for user in expired_users:
        user.is_premium = False

    if expired_users:
        await session.commit()
    return len(expired_users)

async def get_premium_users_count(session: AsyncSession) -> int:
    stmt = select(User).where(User.is_premium == True)
    result = await session.execute(stmt)
    return len(list(result.scalars().all()))

async def get_all_users_count(session: AsyncSession) -> int:
    stmt = select(User)
    result = await session.execute(stmt)
    return len(list(result.scalars().all()))

async def get_all_users(session: AsyncSession) -> list[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    return list(result.scalars().all())