import asyncio
import logging
from core.loader import bot, dp
from database.db import init_db, AsyncSessionLocal
from database.requests import downgrade_expired_premiums
from middlewares.db_middleware import DbSessionMiddleware
from handlers import admin, user_setup, business

PREMIUM_CHECK_INTERVAL_HOURS = 1

async def premium_expiry_watcher():
    """Fon rejimida muntazam ishlaydi: muddati tugagan premium
    foydalanuvchilarni avtomatik ravishda Freemiumga tushiradi."""
    while True:
        try:
            async with AsyncSessionLocal() as session:
                downgraded = await downgrade_expired_premiums(session)
                if downgraded:
                    logging.info(f"Premium muddati tugagan {downgraded} ta foydalanuvchi Freemiumga tushirildi.")
        except Exception as e:
            logging.error(f"Premium expiry watcher xatoligi: {e}")
        await asyncio.sleep(PREMIUM_CHECK_INTERVAL_HOURS * 3600)

async def main():
    logging.info("Starting database initialization...")
    await init_db()
    logging.info("Database initialized.")

    # Middlewares
    dp.update.middleware(DbSessionMiddleware(AsyncSessionLocal))

    # Routers
    dp.include_router(admin.router)
    dp.include_router(user_setup.router)
    dp.include_router(business.router)

    # Fon vazifasi: premium muddatlarini avtomatik tekshirish
    asyncio.create_task(premium_expiry_watcher())

    logging.info("Bot is polling...")
    # await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")