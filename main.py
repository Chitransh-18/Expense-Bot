import sys
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

from config import BOT_TOKEN, logger
from services.sheets_service import sheets_service
from utils.web_server import start_web_server_thread
from utils.formatters import get_main_menu_keyboard
from handlers.start import start_command, help_command, debug_command
from handlers.expense_flow import get_expense_conversation_handler
from handlers.view_expenses import (
    view_expenses_handler, transaction_history_handler,
    delete_transaction_handler, export_csv_handler
)
from handlers.history import chat_history_handler
from handlers.quick_add import quick_add_command

async def back_to_main_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for returning to main menu"""
    query = update.callback_query
    await query.answer()
    keyboard = get_main_menu_keyboard()
    await query.edit_message_text(
        "👋 Choose an option from the main menu below:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def main():
    """Main application launcher"""
    # Start web server thread for health checks (Render / cloud compatibility)
    start_web_server_thread()

    # Initialize Google Sheets
    logger.info("Initializing Google Sheets connection...")
    sheet_url = sheets_service.setup()
    if not sheet_url:
        logger.warning("Google Sheets credentials not supplied or failed initialization. Bot starting in offline mode.")

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is missing! Exiting...")
        sys.exit(1)

    # Build Application
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("debug", debug_command))
    app.add_handler(CommandHandler("add", quick_add_command))

    # Conversation handler for expense creation
    app.add_handler(get_expense_conversation_handler())

    # View & Analytics handlers
    app.add_handler(CallbackQueryHandler(view_expenses_handler, pattern="^(view_expenses|view_filter_)"))
    app.add_handler(CallbackQueryHandler(transaction_history_handler, pattern="^transaction_history$"))
    app.add_handler(CallbackQueryHandler(delete_transaction_handler, pattern="^del_txn_"))
    app.add_handler(CallbackQueryHandler(export_csv_handler, pattern="^export_csv$"))
    app.add_handler(CallbackQueryHandler(chat_history_handler, pattern="^chat_history$"))
    app.add_handler(CallbackQueryHandler(help_command, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(back_to_main_handler, pattern="^back_to_main$"))

    logger.info("ExpenseBot started and listening for updates...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

if __name__ == "__main__":
    main()
