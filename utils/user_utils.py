from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import database.supabase as db
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.state import State, StatesGroup


class SubscriptionState(StatesGroup):
    selecting = State()


def get_main_menu_content():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Мои подписки", callback_data="show_subs")],
        [InlineKeyboardButton(text="ℹ️ Подробнее о рассылках", callback_data="show_info")]
    ])
    text = (
        "Здесь вы можете получить информацию о существующих рассылках, "
        "подписаться на интересующие Вас темы и получать самые свежие новости!\n\n"
        "👇 <b>Выберите действие в меню:</b>"
    )
    return text, keyboard


async def render_subs_keyboard(message, current_selection):
    all_categories = await db.get_all_categories()
    builder = InlineKeyboardBuilder()
    
    for cat in all_categories:
        cat_id = cat['id']
        cat_name = cat['category_name']
        
        is_selected = cat_id in current_selection
        icon = "✅" if is_selected else "⬜"
        
        builder.button(
            text=f"{icon} {cat_name}", 
            callback_data=f"sub_toggle_{cat_id}"
        )
        
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🆗 Сохранить", callback_data="subs_save"),
        InlineKeyboardButton(text="📋 Меню", callback_data="back_to_main")
    )

    try:
        await message.edit_text(
            "🔔 <b>Ваши подписки на рассылки</b>\n\n"
            "Настройте список и нажмите «Сохранить».\n"
            "✅ — выбрано (будет сохранено)\n"
            "⬜ — не выбрано",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    except Exception:
        pass