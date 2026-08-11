from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from core.config import config
from database.models import Base

engine = create_async_engine(config.db_url, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        # Create tables if they do not exist
        await conn.run_sync(Base.metadata.create_all)
