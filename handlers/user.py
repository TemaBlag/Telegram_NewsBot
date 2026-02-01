from aiogram.filters import Command
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

import database.supabase as db
from utils.user_utils import get_main_menu_content, render_subs_keyboard
from utils.user_utils import SubscriptionState


router = Router()


@router.message(Command("start"))
async def start_command(message: Message):
    text, reply_markup = get_main_menu_content()
    await message.answer(text, parse_mode="HTML", reply_markup=reply_markup)


@router.callback_query(F.data == "show_info")
async def show_newsletters_list(callback: CallbackQuery):
    categories = await db.get_all_categories()
    builder = InlineKeyboardBuilder()
    for item in categories:
        builder.button(
            text=f"{item['category_name']}", 
            callback_data=f"view_category_{item['id']}"
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="📋 Меню", callback_data="back_to_main"))
    await callback.message.edit_text(
        "ℹ️ <b>Каталог рассылок</b>\n\n"
        "Выберите категорию, чтобы прочитать подробности:",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("view_category_"))
async def show_category_details(callback: CallbackQuery):
    category_id = callback.data.split("_")[2]
    details = await db.get_category_description(category_id)
    if not details:
        await callback.answer("Описание этой категории отсутствует", show_alert=True)
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="show_info"),
         InlineKeyboardButton(text="📋 Меню", callback_data="back_to_main")]
    ])
    text = f"{details}\n\n"
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu(callback: CallbackQuery):
    text, reply_markup = get_main_menu_content()
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    await callback.answer()


@router.message(Command("help"))
async def help_command(message: Message):
    help_text = (
        "🆘 <b>Справка по боту</b>\n\n"
        "Я помогаю следить за актуальными рассылками новостей.\n\n"
        "<b>Доступные команды:</b>\n"
        "🔹 <b>/start</b> —  Главное меню\n"
        "🔹 <b>/help</b> — Показать это сообщение\n\n"
        "Используйте кнопки меню для навигации."
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Меню", callback_data="back_to_main")]
    ])
    await message.answer(help_text, parse_mode="HTML", reply_markup=keyboard)


@router.callback_query(F.data == "show_subs")
async def show_subscriptions_menu(callback: CallbackQuery, state: FSMContext):
    user_subs = await db.get_user_subscriptions(callback.from_user.id)
    
    await state.set_state(SubscriptionState.selecting)
    await state.update_data(subs=user_subs)
    
    await render_subs_keyboard(callback.message, user_subs)
    await callback.answer()


@router.callback_query(F.data.startswith("sub_toggle_"), SubscriptionState.selecting)
async def toggle_subscription_handler(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.split("_")[2])
    data = await state.get_data()
    current_subs = data.get("subs", [])
    
    if category_id in current_subs:
        current_subs.remove(category_id)
    else:
        current_subs.append(category_id)
    
    await state.update_data(subs=current_subs)
    
    await render_subs_keyboard(callback.message, current_subs)
    await callback.answer()


@router.callback_query(F.data == "subs_save", SubscriptionState.selecting)
async def save_subscriptions_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    final_subs = data.get("subs", [])
    
    await db.update_user_subscriptions(callback.from_user.id, final_subs)
    
    await state.clear()
    
    await callback.answer("✅ Настройки успешно сохранены!", show_alert=True)
    text, reply_markup = get_main_menu_content()
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)


@router.callback_query(F.data == "back_to_main")
async def back_to_main_menu_wrapper(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    
    text, reply_markup = get_main_menu_content()
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=reply_markup)
    await callback.answer()