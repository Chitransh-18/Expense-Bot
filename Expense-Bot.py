from flask import Flask
import threading
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import asyncio

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
cache_last_updated = None


def setup_google_sheets():
    """Initialize Google Sheets connection with service account"""
    global worksheet_expenses, worksheet_history, gc
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/drive']

        creds_json = os.environ.get("GOOGLE_CREDENTIALS")
        if not creds_json:
            logger.error("GOOGLE_CREDENTIALS not found in environment")
            return None

        import json
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

        gc = gspread.authorize(creds)

        try:
            spreadsheet = gc.open(SPREADSHEET_NAME)
            logger.info(f"Successfully opened existing spreadsheet: {SPREADSHEET_NAME}")
        except gspread.SpreadsheetNotFound:
            spreadsheet = gc.create(SPREADSHEET_NAME)
            owner_email = os.environ.get("OWNER_EMAIL")
            if owner_email:
                spreadsheet.share(owner_email, perm_type='user', role='writer')
            logger.info(f"Created new spreadsheet: {SPREADSHEET_NAME}")

        try:
            worksheet_expenses = spreadsheet.worksheet("Expenses")
        except gspread.WorksheetNotFound:
            worksheet_expenses = spreadsheet.add_worksheet("Expenses", rows=1000, cols=16)
            worksheet_expenses.append_row([
                "Transaction ID", "Timestamp", "User ID", "Username", "First Name",
                "Expense Type", "Category", "Amount", "Payment Mode", "Description", "Date", "Status", "Notes", 
                "Split With", "Split Type", "Split Details"
            ])
            logger.info("Created Expenses worksheet")

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

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, worksheet_history.append_row, row)
        return True
    except Exception as e:
        logger.error(f"Error logging chat history: {e}")
        return False


async def save_expense_async(user_id, username, first_name, expense_type, category, amount, payment_mode,
                             description="", split_with=None, split_type=None, split_details=None):
    """Save expense asynchronously"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
        transaction_id = f"TXN{user_id}_{int(datetime.now().timestamp())}"
        
        split_with_str = ", ".join(split_with) if split_with else ""
        split_details_str = str(split_details) if split_details else ""
        
        row = [
            transaction_id, timestamp, str(user_id), username or "N/A", first_name or "N/A",
            expense_type, category, float(amount), payment_mode, description, date, "Completed", "", 
            split_with_str, split_type or "", split_details_str
        ]

        logger.info(f"Attempting to save expense for user {user_id}: {transaction_id}")
        logger.info(f"Row data: User ID={user_id}, Category={category}, Amount={amount}")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, worksheet_expenses.append_row, row)
        logger.info(f"✓ Expense saved successfully to Google Sheets: {transaction_id}")

        # Clear cache and force next fetch to refresh
        global expense_cache, cache_last_updated
        expense_cache = []
        cache_last_updated = None
        logger.info("✓ Cache cleared after saving expense")

        # Wait a moment for Google Sheets to propagate the change
        await asyncio.sleep(0.5)

        await log_chat_history_async(
            user_id, username, first_name, "Expense Added",
            f"{expense_type} - {category} - ₹{amount} - {payment_mode}", description
        )

        return transaction_id
    except Exception as e:
        logger.error(f"✗ Error saving expense: {e}", exc_info=True)
        return None


async def get_user_expenses_async(user_id, force_refresh=False):
    """Get user's all expenses with caching"""
    global expense_cache, cache_last_updated
    try:
        # Refresh cache if empty, forced, or older than 5 minutes
        now = datetime.now()
        should_refresh = (
            force_refresh or 
            not expense_cache or 
            not cache_last_updated or 
            (now - cache_last_updated).seconds > 300
        )
        
        if should_refresh:
            loop = asyncio.get_event_loop()
            
            # Retry mechanism for API calls
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    expense_cache = await loop.run_in_executor(None, worksheet_expenses.get_all_records)
                    cache_last_updated = now
                    logger.info(f"Cache refreshed successfully. Total records: {len(expense_cache)}")
                    break
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # Wait 1 second before retry
                    else:
                        raise

        # Debug logging
        logger.info(f"Searching for expenses with User ID: {user_id}")
        logger.info(f"Total records in cache: {len(expense_cache)}")
        
        # Check what User IDs exist in the sheet
        if expense_cache:
            unique_user_ids = set(str(r.get('User ID', '')) for r in expense_cache)
            logger.info(f"Unique User IDs in sheet: {unique_user_ids}")

        user_expenses = [r for r in expense_cache if str(r.get('User ID', '')) == str(user_id)]
        logger.info(f"Found {len(user_expenses)} expenses for user {user_id}")
        
        # Debug: Show first record if exists
        if user_expenses:
            logger.info(f"First expense record: {user_expenses[0]}")
        
        return user_expenses
    except Exception as e:
        logger.error(f"Error fetching expenses: {e}", exc_info=True)
        return []


async def get_user_chat_log_async(user_id, limit=20):
    """Get user's chat interaction history"""
    global history_cache
    try:
        if not history_cache:
            loop = asyncio.get_event_loop()
            history_cache = await loop.run_in_executor(None, worksheet_history.get_all_records)

        user_history = [r for r in history_cache if str(r.get('User ID', '')) == str(user_id)]
        user_history.reverse()
        return user_history[:limit]
    except Exception as e:
        logger.error(f"Error fetching chat log: {e}")
        return []


def get_main_menu_keyboard():
    """Return the main menu keyboard"""
    return [
        [InlineKeyboardButton("Personal 💰", callback_data='personal')],
        [InlineKeyboardButton("Split 👥", callback_data='split')],
        [InlineKeyboardButton("View My Expenses 📊", callback_data='view_expenses')],
        [InlineKeyboardButton("Transaction History 📜", callback_data='transaction_history')],
        [InlineKeyboardButton("Chat History 💬", callback_data='chat_history')],
        [InlineKeyboardButton("Help ℹ️", callback_data='help')]
    ]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    asyncio.create_task(log_chat_history_async(
        user.id, user.username, user.first_name, "Command", "/start",
        update.message.text, chat_id=update.effective_chat.id,
        message_id=update.message.message_id
    ))

    keyboard = get_main_menu_keyboard()
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


async def debug_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Debug command to check Google Sheets data"""
    user = update.effective_user
    
    try:
        # Force fresh fetch
        loop = asyncio.get_event_loop()
        all_records = await loop.run_in_executor(None, worksheet_expenses.get_all_records)
        
        total_records = len(all_records)
        user_records = [r for r in all_records if str(r.get('User ID', '')) == str(user.id)]
        
        message = f"🔍 *Debug Info*\n\n"
        message += f"Your User ID: `{user.id}`\n"
        message += f"Your Username: {user.username or 'None'}\n"
        message += f"Your Name: {user.first_name}\n\n"
        message += f"Total records in sheet: {total_records}\n"
        message += f"Your records: {len(user_records)}\n\n"
        
        if user_records:
            message += f"*Your Latest Record:*\n"
            latest = user_records[-1]
            message += f"Category: {latest.get('Category', 'N/A')}\n"
            message += f"Amount: ₹{latest.get('Amount', 0)}\n"
            message += f"Date: {latest.get('Date', 'N/A')}\n"
        else:
            message += "⚠️ No records found for your User ID\n\n"
            # Show sample of User IDs in sheet
            if all_records:
                sample_ids = [str(r.get('User ID', 'N/A')) for r in all_records[:5]]
                message += f"Sample User IDs in sheet:\n"
                for uid in sample_ids:
                    message += f"• `{uid}`\n"
        
        await update.message.reply_text(message, parse_mode="Markdown")
        
    except Exception as e:
        logger.error(f"Debug command error: {e}", exc_info=True)
        await update.message.reply_text(f"Debug Error: {str(e)}")


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

    elif query.data == "split_equal":
        context.user_data['split_type'] = 'Equal'
        context.user_data['awaiting'] = 'names'
        
        asyncio.create_task(log_chat_history_async(
            user.id, user.username, user.first_name,
            "Split Type Selected", "Equal Split"
        ))
        
        await query.edit_message_text(
            f"✅ Split Type: *Equal*\n\n"
            f"👥 Enter names of people to split with:\n"
            f"(Separate multiple names with commas)\n\n"
            f"Example: Amrit, Daksh, Dhruv",
            parse_mode="Markdown"
        )

    elif query.data == "split_custom_type":
        context.user_data['split_type'] = 'Custom'
        context.user_data['awaiting'] = 'names'
        
        asyncio.create_task(log_chat_history_async(
            user.id, user.username, user.first_name,
            "Split Type Selected", "Custom Split"
        ))
        
        await query.edit_message_text(
            f"✅ Split Type: *Custom*\n\n"
            f"👥 Enter names of people to split with:\n"
            f"(Separate multiple names with commas)\n\n"
            f"Example: Amrit, Daksh, Dhruv",
            parse_mode="Markdown"
        )

    elif query.data == "view_expenses":
        user_id = user.id
        try:
            # Force refresh cache to get latest data
            user_expenses = await get_user_expenses_async(user_id, force_refresh=True)

            if not user_expenses:
                keyboard = get_main_menu_keyboard()
                await query.edit_message_text(
                    "📊 *Your Expenses*\n\nNo expenses recorded yet!\n\nStart tracking by selecting an option below:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return

            total = sum(float(r.get('Amount', 0)) for r in user_expenses)
            personal_total = sum(float(r.get('Amount', 0)) for r in user_expenses if r.get('Expense Type') == 'Personal')
            split_total = sum(float(r.get('Amount', 0)) for r in user_expenses if r.get('Expense Type') == 'Split')

            cash_total = sum(float(r.get('Amount', 0)) for r in user_expenses if r.get('Payment Mode') == 'Cash')
            online_total = sum(float(r.get('Amount', 0)) for r in user_expenses if r.get('Payment Mode') == 'Online')
            card_total = sum(float(r.get('Amount', 0)) for r in user_expenses if r.get('Payment Mode') == 'Card')
            upi_total = sum(float(r.get('Amount', 0)) for r in user_expenses if r.get('Payment Mode') == 'Upi')

            categories = {}
            for exp in user_expenses:
                cat = exp.get('Category', 'Unknown')
                if cat:
                    categories[cat] = categories.get(cat, 0) + float(exp.get('Amount', 0))

            top_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
            recent = user_expenses[-5:] if len(user_expenses) > 5 else user_expenses
            recent.reverse()

            message = f"📊 *Your Expense Summary*\n\n"
            message += f"💰 Total Spent: ₹{total:,.2f}\n"
            message += f"👤 Personal: ₹{personal_total:,.2f}\n"
            message += f"👥 Split: ₹{split_total:,.2f}\n"
            message += f"📝 Total Transactions: {len(user_expenses)}\n\n"

            if cash_total > 0 or online_total > 0 or card_total > 0 or upi_total > 0:
                message += f"*Payment Modes:*\n"
                if cash_total > 0:
                    message += f"💵 Cash: ₹{cash_total:,.2f}\n"
                if online_total > 0:
                    message += f"🌐 Online: ₹{online_total:,.2f}\n"
                if card_total > 0:
                    message += f"💳 Card: ₹{card_total:,.2f}\n"
                if upi_total > 0:
                    message += f"📱 UPI: ₹{upi_total:,.2f}\n"
                message += "\n"

            if top_categories:
                message += f"*Top Categories:*\n"
                for cat, amt in top_categories:
                    message += f"• {cat}: ₹{amt:,.2f}\n"
                message += "\n"

            message += f"*Recent Transactions:*\n"
            for exp in recent:
                payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(
                    exp.get('Payment Mode', ''), "💰")
                desc = f" - {exp.get('Description', '')}" if exp.get('Description') else ""
                amount_val = exp.get('Amount', 0)
                category_val = exp.get('Category', 'Unknown')
                date_val = exp.get('Date', '')
                message += f"{payment_icon} ₹{amount_val} - {category_val} ({date_val}){desc}\n"

            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard),
                                          parse_mode="Markdown")

        except Exception as e:
            logger.error(f"Error in view_expenses: {e}", exc_info=True)
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                f"📊 *Your Expenses*\n\n"
                f"⚠️ Having trouble loading your expenses right now.\n\n"
                f"This might be due to:\n"
                f"• Temporary connection issue\n"
                f"• Google Sheets sync delay\n\n"
                f"Please try again in a moment, or check Transaction History.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    elif query.data == "transaction_history":
        try:
            # Force refresh to get latest data
            user_expenses = await get_user_expenses_async(user.id, force_refresh=True)
            history = user_expenses[-15:] if len(user_expenses) > 15 else user_expenses
            history.reverse()

            if not history:
                keyboard = get_main_menu_keyboard()
                await query.edit_message_text(
                    "📜 *Transaction History*\n\nNo transactions yet!\n\nStart tracking by selecting an option below:",
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
                desc = f"\n   Note: {exp.get('Description', '')}" if exp.get('Description') else ""
                split_info = ""
                if exp.get('Split With'):
                    split_info = f"\n   Split: {exp.get('Split Type', 'N/A')} with {exp.get('Split With', '')}"
                message += (
                    f"*{exp.get('Category', 'Unknown')}* - ₹{exp.get('Amount', 0)} {payment_icon}\n"
                    f"   {exp.get('Expense Type', 'N/A')} | {payment_mode} | {exp.get('Timestamp', 'N/A')}\n"
                    f"   TXN: `{short_id}`{desc}{split_info}\n\n"
                )

            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error in transaction_history: {e}", exc_info=True)
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                f"📜 *Transaction History*\n\n"
                f"⚠️ Having trouble loading your transaction history right now.\n\n"
                f"Please try again in a moment.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )

    elif query.data == "chat_history":
        try:
            chat_log = await get_user_chat_log_async(user.id, limit=15)

            if not chat_log:
                keyboard = get_main_menu_keyboard()
                await query.edit_message_text(
                    "💬 *Chat History*\n\nNo interactions logged yet!",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return

            message = f"💬 *Your Chat History* (Last 15 interactions)\n\n"
            for log in chat_log:
                action_icon = {"Command": "🔵", "Button Click": "🟢"}.get(log.get('Action Type'), "🟡")
                message += f"{action_icon} *{log.get('Action Type', 'Unknown')}*: {log.get('Action Details', 'N/A')}\n   {log.get('Timestamp', 'N/A')}\n\n"

            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        
        except Exception as e:
            logger.error(f"Error in chat_history: {e}")
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                f"❌ Error fetching chat history. Please try again.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    elif query.data == "help":
        help_text = (
            "ℹ️ *How to use ExpenseManager Bot*\n\n"
            "*Adding Expenses:*\n"
            "1. Choose Personal or Split\n"
            "2. Select a category\n"
            "3. For Split: Choose split type & enter names\n"
            "4. Enter the amount\n"
            "5. Select payment mode\n"
            "6. Optionally add description\n\n"
            "*Split Options:*\n"
            "• Equal - Split amount equally\n"
            "• Custom - Specify individual amounts\n\n"
            "*Viewing Data:*\n"
            "• 📊 View Expenses - Summary & analytics\n"
            "• 📜 Transaction History - All transactions\n"
            "• 💬 Chat History - Your interaction log\n\n"
            "All data is securely stored in Google Sheets."
        )
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif query.data == "back_to_main":
        keyboard = get_main_menu_keyboard()
        await query.edit_message_text("Choose an option:", reply_markup=InlineKeyboardMarkup(keyboard))

    else:
        # Category selection
        if query.data.startswith('personal_'):
            expense_type = "Personal"
            category = query.data.replace('personal_', '').replace('_', ' ').title()
            
            context.user_data['expense_type'] = expense_type
            context.user_data['category'] = category
            context.user_data['awaiting'] = 'amount'
            
            asyncio.create_task(log_chat_history_async(
                user.id, user.username, user.first_name,
                "Category Selected", f"{expense_type} - {category}"
            ))
            
            await query.edit_message_text(
                f"✅ Category: *{category}* (Personal)\n\n💵 Enter the amount (₹):",
                parse_mode="Markdown"
            )
        
        elif query.data.startswith('split_'):
            expense_type = "Split"
            category = query.data.replace('split_', '').replace('_', ' ').title()
            
            context.user_data['expense_type'] = expense_type
            context.user_data['category'] = category
            
            asyncio.create_task(log_chat_history_async(
                user.id, user.username, user.first_name,
                "Category Selected", f"{expense_type} - {category}"
            ))
            
            # Ask for split type
            keyboard = [
                [InlineKeyboardButton("Equal Split ⚖️", callback_data='split_equal')],
                [InlineKeyboardButton("Custom Split ✍️", callback_data='split_custom_type')],
                [InlineKeyboardButton("« Back", callback_data='split')]
            ]
            await query.edit_message_text(
                f"✅ Category: *{category}* (Split)\n\n"
                f"How do you want to split?",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    asyncio.create_task(log_chat_history_async(
        user.id, user.username, user.first_name, "Message Sent", "User input",
        text, chat_id=update.effective_chat.id, message_id=update.message.message_id
    ))

    if context.user_data.get('awaiting') == 'names':
        names_text = text
        names_list = [name.strip() for name in names_text.split(',') if name.strip()]
        
        if not names_list:
            await update.message.reply_text("❌ Please enter at least one name.")
            return
        
        context.user_data['split_with'] = names_list
        context.user_data['awaiting'] = 'amount'

        asyncio.create_task(log_chat_history_async(
            user.id, user.username, user.first_name, "Split Names Entered", ", ".join(names_list)
        ))

        await update.message.reply_text(
            f"✅ Splitting with: *{', '.join(names_list)}*\n\n"
            f"💵 Enter the *total* amount (₹):",
            parse_mode="Markdown"
        )

    elif context.user_data.get('awaiting') == 'amount':
        try:
            amount = float(text)
            if amount <= 0:
                await update.message.reply_text("❌ Amount must be greater than 0")
                return
            
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
            description=description,
            split_with=context.user_data.get('split_with'),
            split_type=context.user_data.get('split_type')
        )

        if transaction_id:
            short_id = transaction_id[-8:]
            payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(
                context.user_data['payment_mode'], "💰")
            
            split_info = ""
            if context.user_data.get('split_with'):
                split_info = f"\n👥 Split with: {', '.join(context.user_data['split_with'])}"
            
            # Success message with main menu
            keyboard = get_main_menu_keyboard()
            await update.message.reply_text(
                f"🎉 *Congratulations!*\n\n"
                f"✅ *Transaction Successfully Recorded!*\n\n"
                f"🏷️ Category: {context.user_data['category']}\n"
                f"💰 Amount: ₹{context.user_data['amount']}\n"
                f"{payment_icon} Payment: {context.user_data['payment_mode']}\n"
                f"📝 Description: {description}\n"
                f"🔖 Transaction ID: `{short_id}`{split_info}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            keyboard = get_main_menu_keyboard()
            await update.message.reply_text(
                "❌ Failed to save. Try again.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

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
            description="",
            split_with=context.user_data.get('split_with'),
            split_type=context.user_data.get('split_type')
        )

        if transaction_id:
            short_id = transaction_id[-8:]
            payment_icon = {"Cash": "💵", "Online": "🌐", "Card": "💳", "Upi": "📱"}.get(
                context.user_data['payment_mode'], "💰")
            
            split_info = ""
            if context.user_data.get('split_with'):
                split_info = f"\n👥 Split with: {', '.join(context.user_data['split_with'])}"
            
            # Success message with main menu
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                f"🎉 *Congratulations!*\n\n"
                f"✅ *Transaction Successfully Recorded!*\n\n"
                f"🏷️ Category: {context.user_data['category']}\n"
                f"💰 Amount: ₹{context.user_data['amount']}\n"
                f"{payment_icon} Payment: {context.user_data['payment_mode']}\n"
                f"🔖 Transaction ID: `{short_id}`{split_info}",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
        else:
            keyboard = get_main_menu_keyboard()
            await query.edit_message_text(
                "❌ Failed to save. Try again.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

        context.user_data.clear()


# --- Web Server for Render Health Checks ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run_web_server():
    # Get the port from the environment variable Render sets
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
# -----------------------------------------

def main():
    # Start the web server in a separate thread
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()

    # Setup Google Sheets
    logger.info("Setting up Google Sheets...")
    sheet_url = setup_google_sheets()
    if not sheet_url:
        logger.error("Failed to setup Google Sheets!")
        return

    if not TOKEN:
        logger.error("BOT_TOKEN not found in environment!")
        return

    # Build the application
    telegram_app = Application.builder().token(TOKEN).build()

    # Add handlers
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("debug", debug_command))  # Debug command
    telegram_app.add_handler(CallbackQueryHandler(payment_handler, pattern='^(payment_|skip_description)'))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    logger.info("Bot is running...")
    
    # Run the bot with proper error handling
    telegram_app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
