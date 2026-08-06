import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ConversationHandler, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
from services.sheets_service import sheets_service
from utils.formatters import get_main_menu_keyboard, get_payment_icon
from config import logger

# States for ConversationHandler
(
    SELECT_TYPE,
    SELECT_CATEGORY,
    SELECT_SPLIT_TYPE,
    ENTER_SPLIT_NAMES,
    ENTER_AMOUNT,
    SELECT_PAYMENT_MODE,
    ENTER_DESCRIPTION
) = range(7)

async def cancel_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the active expense entry flow"""
    context.user_data.clear()
    keyboard = get_main_menu_keyboard()
    message = "❌ Expense entry cancelled."
    if update.message:
        await update.message.reply_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    elif update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def start_personal_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show categories for personal expense"""
    query = update.callback_query
    await query.answer()
    context.user_data['expense_type'] = "Personal"

    keyboard = [
        [InlineKeyboardButton("Travelling 🚖", callback_data='p_travelling')],
        [InlineKeyboardButton("Food 🍔", callback_data='p_food')],
        [InlineKeyboardButton("Shopping 🛍", callback_data='p_shopping')],
        [InlineKeyboardButton("Bills 💡", callback_data='p_bills')],
        [InlineKeyboardButton("Entertainment 🎬", callback_data='p_entertainment')],
        [InlineKeyboardButton("Health 🏥", callback_data='p_health')],
        [InlineKeyboardButton("Education 📚", callback_data='p_education')],
        [InlineKeyboardButton("Custom ✍️", callback_data='p_custom')],
        [InlineKeyboardButton("« Cancel", callback_data='cancel_flow')]
    ]
    await query.edit_message_text(
        "📌 Select a *Personal* expense category:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_CATEGORY

async def start_split_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show categories for split expense"""
    query = update.callback_query
    await query.answer()
    context.user_data['expense_type'] = "Split"

    keyboard = [
        [InlineKeyboardButton("Outing 🎉", callback_data='s_outing')],
        [InlineKeyboardButton("Food 🍕", callback_data='s_food')],
        [InlineKeyboardButton("Travelling 🚆", callback_data='s_travelling')],
        [InlineKeyboardButton("Group Activity 🎮", callback_data='s_activity')],
        [InlineKeyboardButton("Party 🎊", callback_data='s_party')],
        [InlineKeyboardButton("Custom ✍️", callback_data='s_custom')],
        [InlineKeyboardButton("« Cancel", callback_data='cancel_flow')]
    ]
    await query.edit_message_text(
        "📌 Select a *Split* expense category:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return SELECT_CATEGORY

async def handle_category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection callback"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'cancel_flow':
        return await cancel_flow(update, context)

    # Extract category name
    if data.startswith('p_'):
        category = data[2:].replace('_', ' ').title()
        context.user_data['category'] = category
        await query.edit_message_text(
            f"✅ Category: *{category}* (Personal)\n\n💵 Enter the amount (₹):",
            parse_mode="Markdown"
        )
        return ENTER_AMOUNT

    elif data.startswith('s_'):
        category = data[2:].replace('_', ' ').title()
        context.user_data['category'] = category
        keyboard = [
            [InlineKeyboardButton("Equal Split ⚖️", callback_data='split_equal')],
            [InlineKeyboardButton("Custom Split ✍️", callback_data='split_custom_type')],
            [InlineKeyboardButton("« Cancel", callback_data='cancel_flow')]
        ]
        await query.edit_message_text(
            f"✅ Category: *{category}* (Split)\n\nHow do you want to split?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return SELECT_SPLIT_TYPE

    return SELECT_CATEGORY

async def handle_split_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle choice of Equal or Custom split"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'cancel_flow':
        return await cancel_flow(update, context)

    if data == 'split_equal':
        context.user_data['split_type'] = 'Equal'
    else:
        context.user_data['split_type'] = 'Custom'

    await query.edit_message_text(
        f"✅ Split Type: *{context.user_data['split_type']}*\n\n"
        f"👥 Enter names of people to split with:\n"
        f"(Separate multiple names with commas)\n\n"
        f"Example: Amrit, Daksh, Dhruv",
        parse_mode="Markdown"
    )
    return ENTER_SPLIT_NAMES

async def handle_split_names_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text input for names of people to split with"""
    if not update.message:
        return ENTER_SPLIT_NAMES
    text = update.message.text.strip()
    names = [n.strip() for n in text.split(',') if n.strip()]

    if not names:
        await update.message.reply_text("❌ Please enter at least one name.")
        return ENTER_SPLIT_NAMES

    context.user_data['split_with'] = names
    await update.message.reply_text(
        f"✅ Splitting with: *{', '.join(names)}*\n\n"
        f"💵 Enter the *total* amount (₹):",
        parse_mode="Markdown"
    )
    return ENTER_AMOUNT

async def handle_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle text input for amount"""
    if not update.message:
        return ENTER_AMOUNT
    text = update.message.text.strip()
    try:
        amount = float(text)
        if amount <= 0:
            await update.message.reply_text("❌ Amount must be greater than 0")
            return ENTER_AMOUNT

        context.user_data['amount'] = amount
        keyboard = [
            [InlineKeyboardButton("Cash 💵", callback_data='pay_Cash')],
            [InlineKeyboardButton("Online/Net Banking 🌐", callback_data='pay_Online')],
            [InlineKeyboardButton("Card 💳", callback_data='pay_Card')],
            [InlineKeyboardButton("UPI 📱", callback_data='pay_UPI')],
            [InlineKeyboardButton("« Cancel", callback_data='cancel_flow')]
        ]
        await update.message.reply_text(
            f"💵 Amount: ₹{amount:,.2f}\n\n💳 Select payment mode:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return SELECT_PAYMENT_MODE
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number (e.g. 150 or 250.50)")
        return ENTER_AMOUNT

async def handle_payment_mode_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle choice of payment mode"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == 'cancel_flow':
        return await cancel_flow(update, context)

    payment_mode = data.replace('pay_', '')
    context.user_data['payment_mode'] = payment_mode
    icon = get_payment_icon(payment_mode)

    keyboard = [[InlineKeyboardButton("Skip Description ⏭️", callback_data='skip_desc')]]
    await query.edit_message_text(
        f"💵 Amount: ₹{context.user_data['amount']:,.2f}\n"
        f"{icon} Payment: {payment_mode}\n\n"
        f"📝 Add a description (optional) or click Skip:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ENTER_DESCRIPTION

async def handle_description_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save expense with user-entered description or skip"""
    user = update.effective_user
    description = ""

    if update.callback_query and update.callback_query.data == 'skip_desc':
        await update.callback_query.answer()
    elif update.message:
        description = update.message.text.strip()

    transaction_id = await sheets_service.save_expense_async(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        expense_type=context.user_data.get('expense_type', 'Personal'),
        category=context.user_data.get('category', 'General'),
        amount=context.user_data.get('amount', 0.0),
        payment_mode=context.user_data.get('payment_mode', 'Cash'),
        description=description,
        split_with=context.user_data.get('split_with'),
        split_type=context.user_data.get('split_type')
    )

    keyboard = get_main_menu_keyboard()
    if transaction_id:
        short_id = transaction_id[-8:]
        icon = get_payment_icon(context.user_data.get('payment_mode', 'Cash'))
        split_info = ""
        if context.user_data.get('split_with'):
            split_info = f"\n👥 Split with: {', '.join(context.user_data['split_with'])}"

        msg_text = (
            f"🎉 *Transaction Recorded!*\n\n"
            f"🏷️ Category: {context.user_data.get('category')}\n"
            f"💰 Amount: ₹{context.user_data.get('amount'):,.2f}\n"
            f"{icon} Payment: {context.user_data.get('payment_mode')}\n"
            f"📝 Description: {description or 'None'}\n"
            f"🔖 Transaction ID: `{short_id}`{split_info}"
        )
    else:
        msg_text = "❌ Failed to save transaction to Google Sheets. Please check configuration."

    if update.callback_query:
        await update.callback_query.edit_message_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif update.message:
        await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    context.user_data.clear()
    return ConversationHandler.END

def get_expense_conversation_handler():
    """Create and return ConversationHandler for expense creation"""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_personal_category, pattern='^personal$'),
            CallbackQueryHandler(start_split_category, pattern='^split$')
        ],
        states={
            SELECT_CATEGORY: [CallbackQueryHandler(handle_category_selected)],
            SELECT_SPLIT_TYPE: [CallbackQueryHandler(handle_split_type_selected)],
            ENTER_SPLIT_NAMES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_split_names_entered)],
            ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_amount_entered)],
            SELECT_PAYMENT_MODE: [CallbackQueryHandler(handle_payment_mode_selected)],
            ENTER_DESCRIPTION: [
                CallbackQueryHandler(handle_description_entered, pattern='^skip_desc$'),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description_entered)
            ]
        },
        fallbacks=[
            CommandHandler('cancel', cancel_flow),
            CallbackQueryHandler(cancel_flow, pattern='^cancel_flow$')
        ],
        per_message=False
    )
