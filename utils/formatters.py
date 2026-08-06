from telegram import InlineKeyboardButton

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

def get_payment_icon(payment_mode: str) -> str:
    """Return appropriate emoji icon for a given payment mode"""
    icons = {
        "Cash": "💵",
        "Online": "🌐",
        "Card": "💳",
        "Upi": "📱",
        "UPI": "📱"
    }
    return icons.get(payment_mode, "💰")

def format_currency(amount: float) -> str:
    """Format float amount into currency string"""
    return f"₹{amount:,.2f}"
