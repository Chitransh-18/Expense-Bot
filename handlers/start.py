import asyncio
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from utils.formatters import get_main_menu_keyboard
from services.sheets_service import sheets_service
from config import logger

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command"""
    user = update.effective_user
    if not update.message:
        return

    asyncio.create_task(sheets_service.log_chat_history_async(
        user.id, user.username, user.first_name, "Command", "/start",
        update.message.text, chat_id=str(update.effective_chat.id),
        message_id=str(update.message.message_id)
    ))

    keyboard = get_main_menu_keyboard()
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Hi *{user.first_name}*! I'm *ExpenseManager Bot*.\n\n"
        f"Track your expenses with full history:\n"
        f"• Personal & Split expenses\n"
        f"• Complete transaction history\n"
        f"• Monthly & categorical analytics\n"
        f"• Quick entry via `/add <amount> <category>`\n"
        f"• CSV exports & transaction deletion\n\n"
        f"Choose an option below or type /help for details:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /help command"""
    help_text = (
        "ℹ️ *How to use ExpenseManager Bot*\n\n"
        "*Adding Expenses:*\n"
        "1. Click *Personal 💰* or *Split 👥*\n"
        "2. Select a category\n"
        "3. Enter amount & payment mode\n"
        "4. Or use Quick Add: `/add 250 Food Lunch`\n\n"
        "*Managing Expenses:*\n"
        "• 📊 *View My Expenses* - Analytics & summaries\n"
        "• 📜 *Transaction History* - Delete or inspect past expenses\n"
        "• 📄 *Export CSV* - Download expenses spreadsheet\n\n"
        "*Commands:*\n"
        "• `/start` - Main menu\n"
        "• `/add <amt> <cat> [desc]` - Quick add\n"
        "• `/cancel` - Abort active entry flow\n"
        "• `/debug` - Check Google Sheets connectivity\n"
    )
    keyboard = get_main_menu_keyboard()
    if update.message:
        await update.message.reply_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check Google Sheets data"""
    user = update.effective_user
    if not update.message:
        return
    try:
        user_records = await sheets_service.get_user_expenses_async(user.id, force_refresh=True)
        message = f"🔍 *Debug Info*\n\n"
        message += f"Your User ID: `{user.id}`\n"
        message += f"Your Username: {user.username or 'None'}\n"
        message += f"Your Name: {user.first_name}\n\n"
        message += f"Your records count: {len(user_records)}\n\n"

        if user_records:
            latest = user_records[-1]
            message += f"*Your Latest Record:*\n"
            message += f"Category: {latest.get('Category', 'N/A')}\n"
            message += f"Amount: ₹{latest.get('Amount', 0)}\n"
            message += f"Date: {latest.get('Date', 'N/A')}\n"
        else:
            message += "⚠️ No records found for your User ID\n"

        await update.message.reply_text(message, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Debug command error: {e}", exc_info=True)
        await update.message.reply_text(f"Debug Error: {str(e)}")
