from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, AutoReply, SocialLink

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

async def get_all_users_count(session: AsyncSession) -> int:
    stmt = select(User)
    result = await session.execute(stmt)
    return len(list(result.scalars().all()))

async def get_all_users(session: AsyncSession) -> list[User]:
    stmt = select(User)
    result = await session.execute(stmt)
    return list(result.scalars().all())
