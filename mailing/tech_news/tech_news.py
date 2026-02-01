import supabase
import asyncio
import logging
import html
from aiogram import Bot
import database.supabase as db
from aiogram.types import LinkPreviewOptions
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

from .supabase_tech_news import fetch_new_tech_news

logger = logging.getLogger(__name__)

    
async def check_and_send_news(bot: Bot):
    category_id: int = 1
    logger.info("🕵️‍♂️ Проверка наличия новых новостей по техническим работам...")
    new_news_list = await fetch_new_tech_news()
    if not new_news_list:
        logger.info("📭 Новых новостей пока нет.")
        return
    messages_to_send = []
    current_message = ""
    for news in new_news_list:
        title = html.escape(news.get('title', 'Без заголовка'))
        summary = html.escape(news.get('summary', ''))
        url = news.get('url', '#')
        news_item = (
            f"📌 <a href='{url}'><b>{title}</b></a>\n"
            f"{summary}\n\n"
        )
        if len(current_message) + len(news_item) > 4000:
            messages_to_send.append(current_message.strip())
            current_message = news_item
        else:
            current_message += news_item
    if current_message:
        messages_to_send.append(current_message.strip())
    subscribers = await db.get_category_subscribers(category_id)
    if not subscribers:
        logger.info("👥 Подписчиков на данную категорию нет.")
        return
    sent_count = 0
    for user_id in subscribers:
        try:
            for part in messages_to_send:
                await bot.send_message(
                    chat_id=user_id, 
                    text=part,
                    parse_mode="HTML", 
                    link_preview_options=LinkPreviewOptions(is_disabled=True)
                )
                await asyncio.sleep(0.2) 
            
            sent_count += 1
            await asyncio.sleep(0.2) 
        except TelegramForbiddenError:
            logger.warning(f"Пользователь {user_id} заблокировал бота.")
        except TelegramRetryAfter as e:
            logger.warning(f"Flood limit! Ждем {e.retry_after} сек.")
            await asyncio.sleep(e.retry_after)
        except Exception as e:
            logger.error(f"Ошибка отправки пользователю {user_id}: {e}")
    logger.info(f"✅ Рассылка завершена. Сообщения получили {sent_count} из {len(subscribers)}. "
                f"Всего новостей было: {len(new_news_list)}, частей сообщения: {len(messages_to_send)}")