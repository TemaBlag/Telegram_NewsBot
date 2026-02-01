import os
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
from cachetools import TTLCache, cached
import asyncio
from threading import Lock

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

cache = TTLCache(maxsize=100, ttl=3600 * 24) 
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

lock = Lock()

@cached(cache, lock=lock)
def _get_all_categories_sync():
    """RPC: Получение списка всех категорий для меню"""
    logger.info("📡 Запрос всех категорий через RPC...")
    response = supabase.rpc("get_all_categories").execute()
    return response.data

async def get_all_categories():
    """Асинхронная обертка"""
    try:
        return await asyncio.to_thread(_get_all_categories_sync)
    except Exception as e:
        logger.error(f"Ошибка в get_all_categories: {e}")
        return []

@cached(cache, lock=lock)
def _get_category_description_sync(cat_id):
    """RPC: Получаем текст описания"""
    logger.info(f"📡 Запрос описания ID={cat_id}...")
    response = supabase.rpc("get_category_description", {"p_cat_id": cat_id}).execute()
    return response.data
    
async def get_category_description(category_id: int):
    """Асинхронная обертка"""
    try:
        return await asyncio.to_thread(_get_category_description_sync, category_id)
    except Exception as e:
        logger.error(f"Ошибка в get_category_description: {e}")
    

def _get_user_subscriptions_sync(user_id):
    """RPC: Получаем список ID категорий"""
    response = supabase.rpc("get_user_subscriptions", {"p_user_id": user_id}).execute()
    return [item['category_id'] for item in response.data] if response.data else []
    
async def get_user_subscriptions(user_id: int):
    try:
        return await asyncio.to_thread(_get_user_subscriptions_sync, user_id)
    except Exception as e:
        logger.error(f"Ошибка в get_user_subscriptions: {e}")
        return []

def _update_user_subscriptions_sync(user_id, category_ids):
    """RPC: Удаляет старые и вставляет новые подписки одной транзакцией"""
    supabase.rpc("update_user_subscriptions", {
        "p_user_id": user_id, 
        "p_category_ids": category_ids
    }).execute()
    logger.info(f"✅ Подписки пользователя {user_id} обновлены через RPC")
    return True


async def update_user_subscriptions(user_id: int, category_ids: list):
    try:
        return await asyncio.to_thread(_update_user_subscriptions_sync, user_id, category_ids)
    except Exception as e:
        logger.error(f"Ошибка в update_user_subscriptions: {e}")
        return False


def _get_all_users_sync():
    """RPC: Получить список user_id пользователей"""
    response = supabase.rpc("get_all_users").execute()
    return response.data
    

async def get_all_users():
    try:
        return await asyncio.to_thread(_get_all_users_sync)
    except Exception as e:
        logger.error(f"Ошибка в get_all_users: {e}")
        return []


def _get_count_users_sync():
    """RPC: Получить количество пользователей"""
    response = supabase.rpc("get_unique_subscribers_count").execute()
    return response.data
    

async def get_count_users():
    try:
        return await asyncio.to_thread(_get_count_users_sync)
    except Exception as e:
        logger.error(f"Ошибка в get_count_users: {e}")
        return -1
    
def _get_categories_stats():
    """RPC: Статистика по категориям: category_name: count_users"""
    response = supabase.rpc("get_categories_stats").execute()
    return response.data
    

async def get_categories_stats():
    try:
        return await asyncio.to_thread(_get_categories_stats)
    except Exception as e:
        logger.error(f"Ошибка в get_categories_stats: {e}")
        return []


def _add_new_category_sync(name, desc):
    """RPC: Добавление новой категории в БД"""
    response = supabase.rpc("add_new_category", {
        "p_name": name,
        "p_description": desc
    }).execute()
    cache.clear() 
    return response.data 


async def add_new_category(name, desc):
    """Асинхронная обертка для админки"""
    try:
        new_id = await asyncio.to_thread(_add_new_category_sync, name, desc)
        logger.info(f"✅ В базу добавлена новая категория: {name} (ID: {new_id})")
        return new_id
    except Exception as e:
        logger.error(f"❌ Ошибка при добавлении категории в БД: {e}")
        return None
    

async def update_category_field(cat_id, field, value):
    def _sync():
        """RPC: Изменение названия/описания рассылки"""
        supabase.rpc("update_category_field", {
            "p_id": cat_id,
            "p_field": field,
            "p_value": value
        }).execute()
        cache.clear()
    await asyncio.to_thread(_sync)


async def delete_category(cat_id):
    def _sync():
        """RPC: Удаление рассылки"""
        supabase.rpc("delete_category", {"p_id": cat_id}).execute()
        cache.clear()
    await asyncio.to_thread(_sync)


def _get_category_subscribers_sync(category_id):
    """RPC: Получить список пользователей по калегории"""
    res = supabase.table("user_subscriptions")\
        .select("user_id")\
        .eq("category_id", category_id).execute()
    return [item['user_id'] for item in res.data]


async def get_category_subscribers(category_id):
    try:
        return await asyncio.to_thread(_get_category_subscribers_sync, category_id)
    except Exception as e:
        logger.error(f"Ошибка в get_category_subscribers: {e}")
        return False