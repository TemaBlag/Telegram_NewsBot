import os
import logging
from aiogram import Router
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from dotenv import load_dotenv

load_dotenv()

router = Router()
logger = logging.getLogger(__name__)

ADMIN_IDS = [int(admin_id.strip()) for admin_id in os.getenv("ADMIN_IDS").strip().split(',')]

if not ADMIN_IDS:
    logger.info("❌ Отсутствуют администраторы бота")
else:
    logger.info(f"✅ Администраторы бота: {ADMIN_IDS=}")


class AdminState(StatesGroup):
    waiting_for_broadcast_text = State()
    waiting_for_new_cat_name = State()
    waiting_for_new_cat_desc = State()
    edit_selecting_cat = State()
    edit_choosing_action = State()
    edit_input_name = State()
    edit_input_desc = State()


def is_admin(message: Message):
    return message.from_user.id in ADMIN_IDS


def get_admin_main_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Рассылка всем", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="➕ Добавить рассылку", callback_data="admin_add_category")],
        [InlineKeyboardButton(text="📝 Редактировать рассылку", callback_data="admin_edit_category")], 
        [InlineKeyboardButton(text="📋 Меню пользователя", callback_data="back_to_main")]
    ])
    return keyboard

def render_edit_category_list(categories):
    """Отрисовка списка категорий для выбора"""
    text = "<b>📝 Редактирование рассылок</b>\n\nВыберите рассылку из списка ниже:"
    
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=cat['category_name'], 
            callback_data=f"admin_edit_select_{cat['id']}"
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Отмена", callback_data="back_to_admin_main"))
    
    return text, builder.as_markup()

def render_edit_actions_menu(category_name):
    """Отрисовка меню действий для конкретной категории"""
    text = (
        f"⚙️ <b>Настройка рассылки:</b> {category_name}\n\n"
        "Выберите, какой параметр вы хотите изменить, или удалите рассылку целиком:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить название", callback_data="admin_edit_name")],
        [InlineKeyboardButton(text="📝 Изменить описание", callback_data="admin_edit_desc")],
        [InlineKeyboardButton(text="🗑 Удалить рассылку", callback_data="admin_edit_delete")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="admin_edit_category")]
    ])
    
    return text, keyboard
