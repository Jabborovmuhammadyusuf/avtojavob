from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import config
from database.models import Base

engine = create_async_engine(config.db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        # Create tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)

        # create_all yangi jadvallarni yaratadi, lekin ALLAQACHON mavjud
        # jadvalga (masalan bot_users) yangi ustun qo'shmaydi. Shu sabab
        # eski o'rnatishlarda yangi ustunlarni qo'lda qo'shib qo'yamiz.
        # "IF NOT EXISTS" tufayli bu har safar ishga tushirilsa ham xavfsiz.
        await conn.execute(text(
            "ALTER TABLE bot_users ADD COLUMN IF NOT EXISTS trial_used BOOLEAN NOT NULL DEFAULT FALSE"
        ))