import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import asyncio

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

logger = logging.getLogger(__name__)

if not SUPABASE_URL or not SUPABASE_KEY:
    logger.critical("❌ Отсутствуют SUPABASE_URL или SUPABASE_KEY в .env!")
else:
    logger.info("✅ Переменные окружения для Supabase загружены.")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.critical(f"❌ Ошибка подключения к Supabase: {e}", exc_info=True)
    raise e


def _fetch_new_tech_news_sync():
    """RPC: Получить новостей по тех работам"""
    res = supabase.rpc("fetch_and_update_tech_news").execute()
    return res.data


async def fetch_new_tech_news():
    try:
        return await asyncio.to_thread(_fetch_new_tech_news_sync)
    except Exception as e:
        logger.error(f"Ошибка в fetch_new_tech_news: {e}")
        return False