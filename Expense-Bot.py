import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio
from functools import lru_cache

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment variable
TOKEN = os.environ.get("BOT_TOKEN")

# Google Sheets setup
SPREADSHEET_NAME = "ExpenseManager_Data"
worksheet_expenses = None
worksheet_history = None
gc = None

# Cache for reducing API calls
expense_cache = []
history_cache = []
cache_timeout = 300  # 5 minutes


def setup_google_sheets():
    """Initialize Google Sheets connection with service account"""
    global worksheet_expenses, worksheet_history, gc
    try:
        # Use service account credentials
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        # Get credentials from environment variable (JSON string)
        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if not creds_json:
            logger.error("GOOGLE_CREDENTIALS not found in environment")
            return None

        import json
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

        gc = gspread.authorize(creds)

        # Open or create spreadsheet
        try:
            spreadsheet = gc.open(SPREADSHEET_NAME)
        except gspread.SpreadsheetNotFound:
            spreadsheet = gc.create(SPREADSHEET_NAME)
            # Share with your email
            spreadsheet.share(os.environ.get("OWNER_EMAIL"), perm_type='user', role='writer')
            logger.info(f"Created new spreadsheet: {SPREADSHEET_NAME}")

        # Setup Expenses worksheet
        try:
            worksheet_expenses = spreadsheet.worksheet("Expenses")
        except gspread.WorksheetNotFound:
            worksheet_expenses = spreadsheet.add_worksheet("Expenses", rows=1000, cols=13)
            worksheet_expenses.append_row([
                "Transaction ID", "Timestamp", "User ID", "Username", "First Name",
                "Expense Type", "Category", "Amount", "Payment Mode", "Description", "Date", "Status", "Notes"
            ])
            logger.info("Created Expenses worksheet")

        # Setup Chat History worksheet
        try:
            worksheet_history = spreadsheet.worksheet("Chat_History")
        except gspread.WorksheetNotFound:
            worksheet_history = spreadsheet.add_worksheet("Chat_History", rows=5000, cols=10)
            worksheet_history.append_row([
                "Timestamp", "User ID", "Username", "First Name",
                "Action Type", "Action Details", "Message Text", "Button Clicked", "Chat ID", "Message ID"
            ])
            logger.info("Created Chat History worksheet")

        logger.info(f"Connected to Google Sheets: {spreadsheet.url}")
        return spreadsheet.url

    except Exception as e:
        logger.error(f"Error setting up Google Sheets: {e}")
        return None


async def log_chat_history_async(user_id, username, first_name, action_type, action_details, message_text="",
                                 button_clicked="", chat_id="", message_id=""):
    """Log interactions asynchronously"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp, str(user_id), username or "N/A", first_name or "N/A",
            action_type, action_details, message_text[:200] if message_text else "",
            button_clicked, str(chat_id), str(message_id)
        ]

        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, worksheet_history.append_row, row)
        return True
    except Exception as e:
        logger.error(f"Error logging chat history: {e}")
        return False


async def save_expense_async(user_id, username, first_name, expense_type, category, amount, payment_mode,
                             description=""):
    """Save expense asynchronously"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        transaction_id = f"TXN{user_id}_{int(datetime.now().timestamp())}"

        row = [
            transaction_id, timestamp, str(user_id), username or "N/A", first_name or "N/A",
            expense_type, category, float(amount), payment_mode, description, date, "Completed", ""
        ]

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, worksheet_expenses.append_row, row)

        # Clear cache
        global expense_cache
        expense_cache = []

        # Log to chat history
        await log_chat_history_async(
            user_id, username, first_name, "Expense Added",
            f"{expense_type} - {category} - ₹{amount} - {payment_mode}", description
        )

        return transaction_id
    except Exception as e:
        logger.error(f"Error saving expense: {e}")
        return None


async def get_user_history_async(user_id, limit=10):
    """Get user's transaction history with caching"""
    global expense_cache
    try:
        if not expense_cache:
            loop = asyncio.get_event_loop()
            expense_cache = await loop.run_in_executor(None, worksheet_expenses.get_all_records)

        user_expenses = [r for r in expense_cache if str(r['User ID']) == str(user_id)]
        user_expenses.reverse()
        return user_expenses[:limit]
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return []


async def get_user_chat_log_async(user_id, limit=20):
    """Get user's chat interaction history with caching"""
    global history_cache
    try:
        if not history_cache:
            loop = asyncio.get_event_loop()
            history_cache = await loop.run_in_executor(None, worksheet_history.get_all_records)

        user_history = [r for r in history_cache if str(r['User ID']) == str(user_id)]
        user_history.reverse()
        return user_history[:limit]
    except Exception as e:
        logger.error(f"Error fetching chat log: {e}")
        return []


# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    asyncio.create_task(log_chat_history_async(
        user.id, user.username, user.first_name, "Command", "/start",
        update.message.text, chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    ))

    keyboard = [
        [InlineKeyboardButton("Personal 💰", callback_data='personal')],
        [InlineKeyboardButton("Split 👥", callback_data='split')],
        [InlineKeyboardButton("View My Expenses 📊", callback_data='view_expenses')],
        [InlineKeyboardButton("Transaction History 📜", callback_data='transaction_history')],
        [InlineKeyboardButton("Chat History 💬", callback_data='chat_history')],
        [InlineKeyboardButton("Help ℹ️", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Hi *{user.first_name}*! I'm *ExpenseManager Bot*.\n\n"
        f"Track your expenses with full history:\n"
        f"• Personal & Split expenses\n"
        f"• Complete transaction history\n"
        f"• Full chat interaction log\n"
        f"• Spending analytics\n\n"
        f"Choose an option below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


# Button handler (keeping core logic, replacing sync calls with async)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    asyncio.create_task(log_chat_history_async(
        user.id, user.username, user.first_name, "Button Click", query.data,
        button_clicked=query.data, chat_id=query.message.chat_id,
        message_id=query.message.message_id
    ))

    if query.data == "personal":
        keyboard = [
            [InlineKeyboardButton("Travelling 🚖", callback_data='personal_travel')],
            [InlineKeyboardButton("Food 🍔", callback_data='personal_food')],
            [InlineKeyboardButton("Shopping 🛍", callback_data='personal_shopping')],
            [InlineKeyboardButton("Bills 💡", callback_data='personal_bills')],
            [InlineKeyboardButton("Entertainment 🎬", callback_data='personal_entertainment')],
            [InlineKeyboardButton("Health 🏥", callback_data='personal_health')],
            [InlineKeyboardButton("Education 📚", callback_data='personal_education')],
            [InlineKeyboardButton("Custom ✍️", callback_data='personal_custom')],
            [InlineKeyboardButton("« Back", callback_data='back_to_main')]
        ]
        await query.edit_message_text(
            "📌 Select a *Personal* expense category:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "split":
        keyboard = [
            [InlineKeyboardButton("Outing 🎉", callback_data='split_outing')],
            [InlineKeyboardButton("Food 🍕", callback_data='split_food')],
            [InlineKeyboardButton("Travelling 🚆", callback_data='split_travel')],
            [InlineKeyboardButton("Group Activity 🎮", callback_data='split_activity')],
            [InlineKeyboardButton("Party 🎊", callback_data='split_party')],
            [InlineKeyboardButton("Custom ✍️", callback_data='split_custom')],
            [InlineKeyboardButton("« Back", callback_data='back_to_main')]
        ]
        await query.edit_message_text(
            "📌 Select a *Split* expense category:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif query.data == "view_expenses":
        user_id = user.id
        try:
            loop = asyncio.get_event_loop()
            all_records = await loop.run_in_executor(None, worksheet_expenses.get_all_records)
            user_expenses = [r for r in all_records if str(r['User ID']) == str(user_id)]

            if not user_expenses:
                keyboard = [[InlineKeyboardButton("« Back to Main", callback_data='back_to_main')]]
                await query.edit_message_text(
                    "📊 *Your Expenses*\n\nNo expenses recorded yet!",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return

            # Calculate totals
            total = sum(float(r['Amount']) for r in user_expenses)
            personal_total = sum(float(r['Amount']) for r in user_expenses if r['Expense Type'] == 'Personal')
            split_total = sum(float(r['Amount']) for r in user_expenses if r['Expense Type'] == 'Split')

            # Payment mode breakdown
            cash_total = sum(float(r['Amount']) for r in user_expenses if r.get('Payment Mode') == 'Cash')
            online_total = sum(float(r['Amount']) for r in user_expenses if r.get('Payment Mode') == 'Online')
            card_total = sum(float(r['Amount']) for r in user_expenses if r.get('Payment Mode') == 'Card')
            upi_total = sum(float(r['Amount']) for r in user_expenses if r.get('Payment Mode') == 'Upi')

            # Category breakdown
            categories = {}
            for exp in user_expenses:
                cat = exp['Category']
                categories[cat] = categories.get(cat, 0) + float(exp['Amount'])

            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]

            # Get last 5 expenses
            recent = user_expenses[-5:]
            recent.reverse()

            message = f"📊 *Your Expense Summary*\n\n"
            message += f"💰 Total Spent: ₹{total:,.2f}\n"
            message += f"👤 Personal: ₹{personal_total:,.2f}\n"
            message += f"👥 Split: ₹{split_total:,.2f}\n"
            message += f"📝 Total Transactions: {len(user_expenses)}\n\n"

            message += f"*Payment Modes:*\n"
            if cash_total > 0:
                message += f"💵 Cash: ₹{cash_total:,.2f}\n"
            if online_total > 0:
                message += f"🌐 Online: ₹{online_total:,.2f}\n"
            if card_total > 0:
                message += f"💳 Card: ₹{card_total:,.2f}\n"
            if upi_total > 0:
                message += f"📱 UPI: ₹{upi_total:,.2f}\n"

            message += f"\n*Top Categories:*\n"
            for cat, amt in top_categories:
                message += f"• {cat}: ₹{amt:,.2f}\n"

            message += f"\n*Recent Transactions:*\n"
            for exp in recent:
                payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(exp.get('Payment Mode'), "💰")
                desc = f" - {exp['Description']}" if exp['Description'] else ""
                message += f"{payment_icon} ₹{exp['Amount']} - {exp['Category']} ({exp['Date']}){desc}\n"

            keyboard = [
                [InlineKeyboardButton("Full History 📜", callback_data='transaction_history')],
                [InlineKeyboardButton("« Back to Main", callback_data='back_to_main')]
            ]
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in view_expenses: {e}")
            await query.edit_message_text(f"❌ Error fetching expenses. Please try again.")

    elif query.data == "transaction_history":
        history = await get_user_history_async(user.id, limit=15)

        if not history:
            keyboard = [[InlineKeyboardButton("« Back to Main", callback_data='back_to_main')]]
            await query.edit_message_text(
                "📜 *Transaction History*\n\nNo transactions yet!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        message = f"📜 *Transaction History* (Last 15)\n\n"
        for exp in history:
            txn_id = exp.get('Transaction ID', 'N/A')
            short_id = txn_id[-8:] if len(txn_id) > 8 else txn_id
            payment_mode = exp.get('Payment Mode', 'N/A')
            payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(payment_mode, "💰")
            desc = f"\n   Note: {exp['Description']}" if exp.get('Description') else ""
            message += (
                f"*{exp['Category']}* - ₹{exp['Amount']} {payment_icon}\n"
                f"   {exp['Expense Type']} | {payment_mode} | {exp['Timestamp']}\n"
                f"   TXN: `{short_id}`{desc}\n\n"
            )

        keyboard = [[InlineKeyboardButton("« Back to Main", callback_data='back_to_main')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "chat_history":
        chat_log = await get_user_chat_log_async(user.id, limit=15)

        if not chat_log:
            keyboard = [[InlineKeyboardButton("« Back to Main", callback_data='back_to_main')]]
            await query.edit_message_text(
                "💬 *Chat History*\n\nNo interactions logged yet!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

        message = f"💬 *Your Chat History* (Last 15 interactions)\n\n"
        for log in chat_log:
            action_icon = {"Command": "🔵", "Button Click": "🟢"}.get(log['Action Type'], "🟡")
            message += f"{action_icon} *{log['Action Type']}*: {log['Action Details']}\n   {log['Timestamp']}\n\n"

        keyboard = [[InlineKeyboardButton("« Back to Main", callback_data='back_to_main')]]
        await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "help":
        help_text = (
            "ℹ️ *How to use ExpenseManager Bot*\n\n"
            "*Adding Expenses:*\n"
            "1. Choose Personal or Split\n"
            "2. Select a category\n"
            "3. Enter the amount\n"
            "4. Select payment mode\n"
            "5. Optionally add description\n\n"
            "*Viewing Data:*\n"
            "• 📊 View Expenses - Summary & analytics\n"
            "• 📜 Transaction History - All transactions\n"
            "• 💬 Chat History - Your interaction log\n\n"
            "All data is securely stored in Google Sheets."
        )
        keyboard = [[InlineKeyboardButton("« Back to Main", callback_data='back_to_main')]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "back_to_main":
        keyboard = [
            [InlineKeyboardButton("Personal 💰", callback_data='personal')],
            [InlineKeyboardButton("Split 👥", callback_data='split')],
            [InlineKeyboardButton("View My Expenses 📊", callback_data='view_expenses')],
            [InlineKeyboardButton("Transaction History 📜", callback_data='transaction_history')],
            [InlineKeyboardButton("Chat History 💬", callback_data='chat_history')],
            [InlineKeyboardButton("Help ℹ️", callback_data='help')]
        ]
        await query.edit_message_text("Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        # Category selection
        expense_type = "Personal" if query.data.startswith('personal') else "Split"
        category = query.data.replace('personal_', '').replace('split_', '').replace('_', ' ').title()

        context.user_data['expense_type'] = expense_type
        context.user_data['category'] = category
        context.user_data['awaiting'] = 'amount'

        asyncio.create_task(log_chat_history_async(
            user.id, user.username, user.first_name,
            "Category Selected", f"{expense_type} - {category}"
        ))

        await query.edit_message_text(
            f"✅ Category: *{category}* ({expense_type})\n\n💵 Enter the amount (₹):",
            parse_mode="Markdown"
        )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    asyncio.create_task(log_chat_history_async(
        user.id, user.username, user.first_name, "Message Sent", "User input",
        text, chat_id=update.effective_chat.id, message_id=update.message.message_id
    ))

    if context.user_data.get('awaiting') == 'amount':
        try:
            amount = float(text)
            context.user_data['amount'] = amount
            context.user_data['awaiting'] = 'payment_mode'

            asyncio.create_task(log_chat_history_async(
                user.id, user.username, user.first_name, "Amount Entered", f"₹{amount}"
            ))

            keyboard = [
                [InlineKeyboardButton("Cash 💵", callback_data='payment_cash')],
                [InlineKeyboardButton("Online/Net Banking 🌐", callback_data='payment_online')],
                [InlineKeyboardButton("Card 💳", callback_data='payment_card')],
                [InlineKeyboardButton("UPI 📱", callback_data='payment_upi')]
            ]
            await update.message.reply_text(
                f"💵 Amount: ₹{amount}\n\n💳 Select payment mode:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except ValueError:
            await update.message.reply_text("❌ Please enter a valid number")

    elif context.user_data.get('awaiting') == 'description':
        description = text

        transaction_id = await save_expense_async(
            user_id=user.id, username=user.username, first_name=user.first_name,
            expense_type=context.user_data['expense_type'],
            category=context.user_data['category'],
            amount=context.user_data['amount'],
            payment_mode=context.user_data['payment_mode'],
            description=description
        )

        if transaction_id:
            short_id = transaction_id[-8:]
            payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(context.user_data['payment_mode'],
                                                                                     "💰")
            await update.message.reply_text(
                f"✅ *Expense Saved!*\n\n"
                f"🏷️ Category: {context.user_data['category']}\n"
                f"💰 Amount: ₹{context.user_data['amount']}\n"
                f"{payment_icon} Payment: {context.user_data['payment_mode']}\n"
                f"📝 Description: {description}\n"
                f"🔖 Transaction ID: `{short_id}`\n\n"
                f"Use /start to add more!",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Failed to save. Try again.")

        context.user_data.clear()
    else:
        await update.message.reply_text("Please use /start to begin.")


async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    await query.answer()

    if query.data.startswith('payment_'):
        payment_mode = query.data.replace('payment_', '').title()
        context.user_data['payment_mode'] = payment_mode
        context.user_data['awaiting'] = 'description'

        asyncio.create_task(log_chat_history_async(
            user.id, user.username, user.first_name, "Payment Mode Selected", payment_mode
        ))

        payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(payment_mode, "💰")
        keyboard = [[InlineKeyboardButton("Skip Description ⏭️", callback_data='skip_description')]]
        await query.edit_message_text(
            f"💵 Amount: ₹{context.user_data['amount']}\n"
            f"{payment_icon} Payment: {payment_mode}\n\n"
            f"📝 Add description (optional) or skip:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == 'skip_description':
        transaction_id = await save_expense_async(
            user_id=user.id, username=user.username, first_name=user.first_name,
            expense_type=context.user_data['expense_type'],
            category=context.user_data['category'],
            amount=context.user_data['amount'],
            payment_mode=context.user_data['payment_mode'],
            description=""
        )

        if transaction_id:
            short_id = transaction_id[-8:]
            payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(context.user_data['payment_mode'],
                                                                                     "💰")
            await query.edit_message_text(
                f"✅ *Expense Saved!*\n\n"
                f"🏷️ Category: {context.user_data['category']}\n"
                f"💰 Amount: ₹{context.user_data['amount']}\n"
                f"{payment_icon} Payment: {context.user_data['payment_mode']}\n"
                f"🔖 Transaction ID: `{short_id}`\n\n"
                f"Use /start to add more!",
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text("❌ Failed to save. Try again.")

        context.user_data.clear()


def main():
    logger.info("Setting up Google Sheets...")
    sheet_url = setup_google_sheets()
    if not sheet_url:
        logger.error("Failed to setup Google Sheets!")
        return

    if not TOKEN:
        logger.error("BOT_TOKEN not found in environment!")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(payment_handler, pattern='^(payment_|skip_description)'))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()