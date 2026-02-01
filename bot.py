import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from mailing.tech_news.tech_news import check_and_send_news
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
logger = logging.getLogger(__name__)

from handlers.user import router as user_router
from handlers.admin import router as admin_router

BOT_TOKEN = os.getenv("BOT_TOKEN")

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(admin_router)
    scheduler.add_job(
        check_and_send_news, 
        "cron", 
        hour='8-18', 
        minute=15, 
        args=[bot] 
    )
    scheduler.start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)
    logger.info("Start bot")
   

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("End bot")