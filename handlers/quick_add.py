from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.sheets_service import sheets_service
from utils.formatters import get_main_menu_keyboard, get_payment_icon, format_currency
from config import logger

async def quick_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Quickly add an expense via /add command
    Usage: /add <amount> <category> [description...]
    Example: /add 250 Food Lunch with team
    """
    user = update.effective_user
    if not update.message:
        return

    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "⚠️ *Quick Add Syntax:*\n`/add <amount> <category> [description...]` \n\n"
            "*Examples:*\n"
            "• `/add 250 Food Lunch` \n"
            "• `/add 1200 Travel Flight booking` \n"
            "• `/add 500 Bills Electricity`",
            parse_mode="Markdown"
        )
        return

    try:
        amount = float(args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0.")
            return

        category = args[1].title()
        description = " ".join(args[2:]) if len(args) > 2 else ""
        payment_mode = "UPI"

        transaction_id = await sheets_service.save_expense_async(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            expense_type="Personal",
            category=category,
            amount=amount,
            payment_mode=payment_mode,
            description=description
        )

        keyboard = get_main_menu_keyboard()
        if transaction_id:
            short_id = transaction_id[-8:]
            icon = get_payment_icon(payment_mode)
            await update.message.reply_text(
                f"⚡ *Quick Add Recorded!*\n\n"
                f"🏷️ Category: {category}\n"
                f"💰 Amount: {format_currency(amount)}\n"
                f"{icon} Payment: {payment_mode}\n"
                f"📝 Description: {description or 'None'}\n"
                f"🔖 Transaction ID: `{short_id}`",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to save expense. Please try again.")

    except ValueError:
        await update.message.reply_text("❌ Invalid amount format. Example: `/add 250 Food Lunch`", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error in quick_add_command: {e}", exc_info=True)
        await update.message.reply_text("❌ An error occurred while adding expense.")
