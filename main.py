import asyncio
import logging
from core.loader import bot, dp
from database.db import init_db, AsyncSessionLocal
from middlewares.db_middleware import DbSessionMiddleware
from handlers import admin, user_setup, business

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

    logging.info("Bot is polling...")
    # await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped.")
