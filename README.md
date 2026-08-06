# 💰 Expense-Bot: Telegram Expense Manager Bot

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Telegram Bot API](https://img.shields.io/badge/telegram--bot--api-v21.0-blue)](https://python-telegram-bot.org/)
[![Google Sheets API](https://img.shields.io/badge/Google%20Sheets-API-green)](https://developers.google.com/sheets/api)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Expense-Bot** is a powerful, modern, and user-friendly Telegram Bot built with Python (`python-telegram-bot` v21) to seamlessly track personal & split expenses, generate spending analytics, and store data securely in **Google Sheets**.

---

## ✨ Features

- 👤 **Personal & 👥 Split Expense Tracking**: Easily log expenses with predefined categories or custom tags.
- ⚡ **Quick Add Command (`/add`)**: Log expenses in a single line (e.g. `/add 250 Food Lunch with team`).
- 🔄 **Interactive Flow (`ConversationHandler`)**: Multi-step button interface with step-by-step guidance and `/cancel` support.
- 📊 **Spending Analytics**:
  - Filter summary reports by **This Month 📅**, **Last Month 📆**, or **All Time 📊**.
  - Top spending categories breakdown & payment mode totals (Cash, Online, Card, UPI).
- 🗑️ **Transaction Management**: Delete mistaken transactions directly from the Telegram chat history.
- 📄 **CSV Data Export**: Instantly export your entire expense log to a CSV file.
- 💬 **Chat Interaction History**: Logs user commands and button actions to a dedicated `Chat_History` worksheet.
- ⚡ **Optimized Caching**: Thread-safe per-user TTL caching prevents hitting Google API rate limits.
- ☁️ **Deployment Ready**: Built-in Flask web server daemon for cloud platform health checks (Render, Railway, Heroku).

---

## 📁 Project Architecture

```
Expense-Bot/
├── main.py                     # Primary entry point & handler initialization
├── config.py                   # Environment configuration & logger setup
├── requirements.txt            # Python dependencies (google-auth, python-telegram-bot, Flask, etc.)
├── README.md                   # Documentation & setup guide
├── .gitignore                  # Git ignore file
├── services/
│   ├── sheets_service.py       # Google Sheets API handler (google-auth)
│   └── cache_service.py        # Isolated per-user TTL caching service
├── handlers/
│   ├── start.py                # /start, /help, /debug handlers
│   ├── expense_flow.py         # ConversationHandler for expense logging
│   ├── view_expenses.py        # Expense summary, date filters, delete & CSV export
│   ├── quick_add.py            # Quick one-line /add command
│   └── history.py              # Chat interaction history handler
└── utils/
    ├── formatters.py           # Emojis, currency formatting, & main menu keyboard
    └── web_server.py           # Flask health check web server for Render/Cloud
```

---

## 🛠️ Setup & Installation

### Prerequisites

1. **Python 3.9 or higher**
2. **Telegram Bot Token**:
   - Chat with [@BotFather](https://t.me/BotFather) on Telegram to create a new bot and copy the API Token.
3. **Google Cloud Service Account Credentials**:
   - Enable **Google Sheets API** and **Google Drive API** in your Google Cloud Console.
   - Create a Service Account and download the JSON key file.

---

### Step-by-step Setup

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:Chitransh-18/Expense-Bot.git
   cd Expense-Bot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:

   Set the required environment variables in your terminal or hosting service:

   - `BOT_TOKEN`: Your Telegram Bot API Token.
   - `GOOGLE_CREDENTIALS`: The raw contents of your Service Account JSON key file.
   - `SPREADSHEET_NAME` *(Optional)*: Name of the Google Spreadsheet (default: `ExpenseManager_Data`).
   - `OWNER_EMAIL` *(Optional)*: Your Google account email to auto-share newly created spreadsheets.
   - `PORT` *(Optional)*: Web server port for Render health check (default: `10000`).

   **PowerShell Example**:
   ```powershell
   $env:BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRstuVWXyz"
   $env:GOOGLE_CREDENTIALS='{"type": "service_account", "project_id": "...", ...}'
   $env:OWNER_EMAIL="your_email@gmail.com"
   ```

   **Linux / macOS Example**:
   ```bash
   export BOT_TOKEN="123456789:ABCdefGhIJKlmNoPQRstuVWXyz"
   export GOOGLE_CREDENTIALS='{"type": "service_account", "project_id": "...", ...}'
   export OWNER_EMAIL="your_email@gmail.com"
   ```

4. **Run the Bot**:
   ```bash
   python main.py
   ```

---

## 🤖 Bot Commands Reference

| Command | Description |
|---|---|
| `/start` | Opens the main menu with interactive buttons |
| `/add <amount> <category> [description]` | Quick one-line expense creation (e.g. `/add 250 Food Lunch`) |
| `/cancel` | Cancels any active expense entry flow |
| `/help` | Displays usage instructions and feature help |
| `/debug` | Checks Google Sheets connectivity and user record count |

---

## ☁️ Deployment Guide (Render / Cloud)

This bot is pre-configured for web hostings like **Render**:

1. Create a new **Web Service** on Render connected to your GitHub repository.
2. Set the **Build Command**: `pip install -r requirements.txt`
3. Set the **Start Command**: `python main.py`
4. Add Environment Variables (`BOT_TOKEN`, `GOOGLE_CREDENTIALS`, `OWNER_EMAIL`, `PORT`).
5. Render will automatically check the `/` health check route powered by Flask on port `10000` to keep the service active.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
