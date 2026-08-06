from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.sheets_service import sheets_service
from utils.formatters import get_main_menu_keyboard
from config import logger

async def chat_history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View user chat interaction log"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    try:
        chat_log = await sheets_service.get_user_chat_log_async(user.id, limit=15)

        if not chat_log:
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                "💬 *Chat History*\n\nNo interactions logged yet!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        message = "💬 *Your Chat History* (Last 15 interactions)\n\n"
        for log in chat_log:
            action_icon = {"Command": "🔵", "Button Click": "🟢"}.get(log.get('Action Type'), "🟡")
            message += (
                f"{action_icon} *{log.get('Action Type', 'Unknown')}*: {log.get('Action Details', 'N/A')}\n"
                f"   {log.get('Timestamp', 'N/A')}\n\n"
            )

        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in chat_history: {e}")
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "❌ Error fetching chat history. Please try again.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
