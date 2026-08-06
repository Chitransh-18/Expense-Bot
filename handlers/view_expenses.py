import io
import csv
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from services.sheets_service import sheets_service
from utils.formatters import get_main_menu_keyboard, get_payment_icon, format_currency
from config import logger

async def view_expenses_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View expense summaries with time filtering options"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    data = query.data
    filter_type = "all"
    if data.startswith("view_filter_"):
        filter_type = data.replace("view_filter_", "")

    try:
        user_expenses = await sheets_service.get_user_expenses_async(user.id, force_refresh=True)

        if not user_expenses:
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                "📊 *Your Expenses*\n\nNo expenses recorded yet!\n\nStart tracking by selecting an option below:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        # Apply date filter
        now = datetime.now()
        filtered_expenses = []
        filter_label = "All Time"

        if filter_type == "this_month":
            filter_label = "This Month"
            for exp in user_expenses:
                dt_str = exp.get("Date", "")
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d")
                    if dt.year == now.year and dt.month == now.month:
                        filtered_expenses.append(exp)
                except ValueError:
                    filtered_expenses.append(exp)
        elif filter_type == "last_month":
            filter_label = "Last Month"
            target_month = now.month - 1 if now.month > 1 else 12
            target_year = now.year if now.month > 1 else now.year - 1
            for exp in user_expenses:
                dt_str = exp.get("Date", "")
                try:
                    dt = datetime.strptime(dt_str, "%Y-%m-%d")
                    if dt.year == target_year and dt.month == target_month:
                        filtered_expenses.append(exp)
                except ValueError:
                    pass
        else:
            filtered_expenses = user_expenses

        total = sum(float(r.get('Amount', 0)) for r in filtered_expenses)
        personal_total = sum(float(r.get('Amount', 0)) for r in filtered_expenses if r.get('Expense Type') == 'Personal')
        split_total = sum(float(r.get('Amount', 0)) for r in filtered_expenses if r.get('Expense Type') == 'Split')

        categories = {}
        for exp in filtered_expenses:
            cat = exp.get('Category', 'Unknown')
            if cat:
                categories[cat] = categories.get(cat, 0) + float(exp.get('Amount', 0))

        top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        recent = filtered_expenses[-5:] if len(filtered_expenses) > 5 else filtered_expenses
        recent.reverse()

        message = f"📊 *Expense Summary* ({filter_label})\n\n"
        message += f"💰 Total Spent: {format_currency(total)}\n"
        message += f"👤 Personal: {format_currency(personal_total)}\n"
        message += f"👥 Split: {format_currency(split_total)}\n"
        message += f"📝 Transactions: {len(filtered_expenses)}\n\n"

        if top_categories:
            message += "*Top Categories:*\n"
            for cat, amt in top_categories:
                message += f"• {cat}: {format_currency(amt)}\n"
            message += "\n"

        if recent:
            message += "*Recent Transactions:*\n"
            for exp in recent:
                icon = get_payment_icon(exp.get('Payment Mode', ''))
                desc = f" - {exp.get('Description', '')}" if exp.get('Description') else ""
                message += f"{icon} {format_currency(float(exp.get('Amount', 0)))} - {exp.get('Category', 'Unknown')} ({exp.get('Date', '')}){desc}\n"

        keyboard = [
            [
                InlineKeyboardButton("This Month 📅", callback_data='view_filter_this_month'),
                InlineKeyboardButton("Last Month 📆", callback_data='view_filter_last_month'),
                InlineKeyboardButton("All Time 📊", callback_data='view_filter_all')
            ],
            [InlineKeyboardButton("Export CSV 📄", callback_data='export_csv')],
            [InlineKeyboardButton("« Main Menu", callback_data='back_to_main')]
        ]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in view_expenses: {e}", exc_info=True)
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(
            "⚠️ Having trouble loading your expenses right now. Please try again.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def transaction_history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View recent transaction history with delete actions"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    try:
        user_expenses = await sheets_service.get_user_expenses_async(user.id, force_refresh=True)
        history = user_expenses[-10:] if len(user_expenses) > 10 else user_expenses
        history.reverse()

        if not history:
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                "📜 *Transaction History*\n\nNo transactions recorded yet!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        message = "📜 *Transaction History* (Last 10)\n\n"
        keyboard = []

        for exp in history:
            txn_id = exp.get('Transaction ID', 'N/A')
            short_id = txn_id[-8:] if len(txn_id) > 8 else txn_id
            mode = exp.get('Payment Mode', 'N/A')
            icon = get_payment_icon(mode)
            desc = f"\n   Note: {exp.get('Description', '')}" if exp.get('Description') else ""
            split_info = ""
            if exp.get('Split With'):
                split_info = f"\n   Split with: {exp.get('Split With', '')}"

            message += (
                f"*{exp.get('Category', 'Unknown')}* - {format_currency(float(exp.get('Amount', 0)))} {icon}\n"
                f"   {exp.get('Expense Type', 'N/A')} | {mode} | {exp.get('Timestamp', 'N/A')}\n"
                f"   TXN: `{short_id}`{desc}{split_info}\n\n"
            )
            # Add delete button for this transaction
            keyboard.append([InlineKeyboardButton(f"🗑️ Delete {exp.get('Category')} ({short_id})", callback_data=f"del_txn_{txn_id}")])

        keyboard.append([InlineKeyboardButton("« Main Menu", callback_data='back_to_main')])
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in transaction_history: {e}", exc_info=True)
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text("⚠️ Having trouble loading transaction history.", reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_transaction_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deleting a transaction"""
    query = update.callback_query
    user = query.from_user
    await query.answer()

    txn_id = query.data.replace("del_txn_", "")
    success = await sheets_service.delete_expense_async(user.id, txn_id)

    keyboard = get_main_menu_keyboard()
    if success:
        await query.edit_message_text(f"✅ Transaction `{txn_id[-8:]}` successfully deleted!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await query.edit_message_text(f"❌ Failed to delete transaction `{txn_id[-8:]}`.", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def export_csv_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Export user transactions as CSV document"""
    query = update.callback_query
    user = query.from_user
    await query.answer("Generating CSV export...")

    try:
        user_expenses = await sheets_service.get_user_expenses_async(user.id)
        if not user_expenses:
            await query.message.reply_text("❌ No expenses to export.")
            return

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=user_expenses[0].keys())
        writer.writeheader()
        writer.writerows(user_expenses)

        csv_bytes = output.getvalue().encode('utf-8')
        output.close()

        buf = io.BytesIO(csv_bytes)
        buf.name = f"expenses_{user.id}_{datetime.now().strftime('%Y%m%d')}.csv"

        await context.bot.send_document(
            chat_id=query.message.chat_id,
            document=buf,
            caption="📄 Here is your full expense data export in CSV format."
        )
    except Exception as e:
        logger.error(f"CSV Export error: {e}", exc_info=True)
        await query.message.reply_text("❌ Failed to generate CSV export.")
