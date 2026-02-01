import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramForbiddenError, TelegramRetryAfter

import database.supabase as db
from utils.admin_utils import (is_admin, get_admin_main_keyboard,
                               AdminState,render_edit_actions_menu,
                               render_edit_category_list)


router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("admin"), is_admin)
async def admin_main_menu(message: Message):
    await message.answer(
        "🛠 <b>Панель администратора</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_main_keyboard()
    )


@router.callback_query(F.data == "admin_stats", is_admin)
async def admin_stats(callback: CallbackQuery):
    await callback.answer("📊 Сбор статистики...")
    all_user_count = await db.get_count_users() 
    categories_data = await db.get_categories_stats()
    if categories_data:
        categories_text = "\n".join(
            [f"  ├ {item['name']}: <b>{item['count']}</b>" for item in categories_data]
        )
    else:
        categories_text = "  <i>Рассылки еще не созданы</i>"
    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👤 Всего пользователей: <b>{all_user_count}</b>\n\n"
        "📂 <b>Количество подписчиков по рассылкам:</b>\n"
        f"{categories_text}\n\n"
    )
    try:
        await callback.message.edit_text(
            text, 
            parse_mode="HTML", 
            reply_markup=get_admin_main_keyboard()
        )
    except Exception as e:
        pass

@router.callback_query(F.data == "admin_broadcast", is_admin)
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.waiting_for_broadcast_text)
    await callback.message.answer("Введите текст сообщения для рассылки всем пользователям:")
    await callback.answer()


@router.message(AdminState.waiting_for_broadcast_text, is_admin)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    users = await db.get_all_users()
    count = 0
    blocked = 0
    logger.info(f"🚀 Рассылка запущена для {len(users)} пользователей...")
    status_msg = await message.answer(f"🚀 Рассылка запущена для {len(users)} пользователей...")
    for user in users:
        try:
            await message.copy_to(chat_id=user['user_id'])
            count += 1
            await asyncio.sleep(0.05) 
        except TelegramForbiddenError:
            blocked += 1
        except TelegramRetryAfter as e:
            await asyncio.sleep(e.retry_after)
            await message.copy_to(chat_id=user['user_id'])
            count += 1
        except Exception as e:
            logger.error(f"Ошибка при отправке {user['user_id']}: {e}")
    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📥 Доставлено: {count}\n",
        parse_mode="HTML",
    )

@router.callback_query(F.data == "back_to_admin_main", is_admin)
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "🛠 <b>Панель администратора</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_main_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_category", is_admin)
async def add_category_step1(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.waiting_for_new_cat_name)
    await callback.message.answer("Введите название новой рассылки:", parse_mode="HTML")
    await callback.answer()


@router.message(AdminState.waiting_for_new_cat_name, is_admin)
async def add_category_step2(message: Message, state: FSMContext):
    await state.update_data(cat_name=message.text)
    await state.set_state(AdminState.waiting_for_new_cat_desc)
    await message.answer("Теперь введите описание этой категории:")


@router.message(AdminState.waiting_for_new_cat_desc, is_admin)
async def add_category_final(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    cat_name = data['cat_name']
    cat_desc = message.html_text if message.html_text else message.text
    
    new_cat = await db.add_new_category(cat_name, cat_desc)
    await state.clear()
    logger.info(f"✅ Категория '{cat_name}' создана!")
    await message.answer(f"✅ Категория '{cat_name}' создана!", reply_markup=get_admin_main_keyboard())


@router.callback_query(F.data == "admin_edit_category", is_admin)
async def edit_category_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    categories = await db.get_all_categories()
    if not categories:
        await callback.answer("Список рассылок пуст!", show_alert=True)
        return
    text, reply_markup = render_edit_category_list(categories)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_edit_select_"), is_admin)
async def edit_category_actions(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[3])
    categories = await db.get_all_categories()
    category = next((c for c in categories if c['id'] == cat_id), None)
    cat_name = category['category_name'] if category else f"ID {cat_id}"
    await state.update_data(edit_cat_id=cat_id, edit_cat_name=cat_name)
    text, reply_markup = render_edit_actions_menu(cat_name)
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    await callback.answer()


@router.callback_query(F.data == "admin_edit_delete", is_admin)
async def edit_category_delete_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("edit_cat_id")
    cat_name = data.get("edit_cat_name", "Без названия")
    admin_info = f"@{callback.from_user.username}" if callback.from_user.username else f"ID: {callback.from_user.id}"
    await db.delete_category(cat_id)
    logger.info(f"🗑 Админ {admin_info} удалил рассылку: '{cat_name}' (ID: {cat_id})")
    await state.clear()
    await callback.answer(f"✅ Рассылка '{cat_name}' успешно удалена", show_alert=True)
    await callback.message.edit_text(
        "🛠 <b>Панель администратора</b>\n\nВыберите действие:",
        parse_mode="HTML",
        reply_markup=get_admin_main_keyboard()
    )


@router.callback_query(F.data == "admin_edit_name", is_admin)
async def edit_name_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.edit_input_name)
    await callback.message.answer("Введите новое НАЗВАНИЕ для рассылки:")
    await callback.answer()


@router.callback_query(F.data == "admin_edit_desc", is_admin)
async def edit_desc_prompt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.edit_input_desc)
    await callback.message.answer("Введите новое ОПИСАНИЕ (поддерживается встроенное форматирование Telegram):")
    await callback.answer()


@router.message(AdminState.edit_input_name, is_admin)
async def edit_name_save(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("edit_cat_id")
    old_name = data.get("edit_cat_name", "Неизвестно")
    new_name = message.text
    admin_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    await db.update_category_field(cat_id, "name", message.text)
    logger.info(f"✏️ Админ {admin_info} изменил название рассылки ID {cat_id}: '{old_name}' -> '{new_name}'")
    await state.clear()
    await message.answer(f"✅ Название обновлено на: {message.text}", reply_markup=get_admin_main_keyboard())


@router.message(AdminState.edit_input_desc, is_admin)
async def edit_desc_save(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("edit_cat_id")
    cat_name = data.get("edit_cat_name", "Неизвестно")
    admin_info = f"@{message.from_user.username}" if message.from_user.username else f"ID: {message.from_user.id}"
    new_desc = message.html_text if message.html_text else message.text
    await db.update_category_field(cat_id, "description", new_desc)
    logger.info(f"📝 Админ {admin_info} обновил описание рассылки: '{cat_name}' (ID: {cat_id})")
    await state.clear()
    await message.answer("✅ Описание успешно обновлено!", reply_markup=get_admin_main_keyboard())
