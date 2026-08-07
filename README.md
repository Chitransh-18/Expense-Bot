# 💰 ExpenseTracker Pro: Downloadable Web App (PWA) with Split Reminders & Recurring Bill Manager

[![PWA Ready](https://img.shields.io/badge/PWA-Installable-blue.svg)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask API](https://img.shields.io/badge/Flask-v3.0-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**ExpenseTracker Pro** is a modern, installable Progressive Web Application (PWA) designed for tracking personal spending, split expenses, recurring monthly subscriptions (like YouTube Family Premium paid by Daksh every 3rd of the month, Wi-Fi, Rent), and sending instant split reminders via WhatsApp or native device sharing.

---

## ✨ Key Features

- 📱 **Downloadable & Installable (PWA)**:
  - Add to Home Screen on iOS, Android, Windows, and macOS.
  - Native standalone app feel with offline asset caching (`sw.js` Service Worker).
- 🔒 **User Authentication**:
  - Secure signup, sign-in, and password hashing (`werkzeug.security`) with 30-day persistent sessions.
- 📅 **Recurring Monthly Bills & Subscription Manager**:
  - Track recurring monthly bills like **YouTube Family Premium** (paid by Daksh on the **3rd of every month**), Wi-Fi, Rent, Netflix.
  - Automatic due status alerts (**Due Today 🚨**, **Overdue**, **Upcoming**).
  - One-click **"Mark Paid"** and **"📲 Remind Daksh"** via WhatsApp.
- 💰 **Personal & Split Expense Logging**:
  - Log expenses with category tags, payment mode (UPI, Cash, Online, Card), and custom split member details.
- 🔔 **Split Reminder Generator**:
  - Send formatted reminder messages to friends via **WhatsApp Share**, **Native Share Drawer**, or Copy text.
- 📊 **Rich Glassmorphic Dashboard**:
  - Modern dark-mode design system with gradient accents, spending breakdown progress bars, and stats cards.
- 📄 **Data Export**:
  - One-click CSV export of your entire transaction history.

---

## 📁 Project Architecture

```
Expense-Tracker-App/
├── app.py                      # Flask REST API backend & static file server
├── config.py                   # App configuration & JWT secret key
├── database.py                 # SQLite database schema & connection helper
├── requirements.txt            # Python dependencies (Flask, Flask-CORS, PyJWT, Werkzeug)
├── README.md                   # Documentation & setup guide
├── database.sqlite             # Local SQLite database (created automatically)
└── static/                     # PWA Frontend Assets
    ├── index.html              # Single Page App structure & meta tags
    ├── manifest.json           # Web App Manifest for app installation
    ├── sw.js                   # Service Worker for offline asset caching
    ├── css/
    │   └── style.css           # Glassmorphism CSS design system
    └── js/
        ├── api.js              # Token management & fetch wrapper
        ├── pwa.js              # Service Worker & PWA Install prompt handler
        ├── auth.js             # Sign up & Sign in UI logic
        ├── dashboard.js        # Overview stats, top categories, & urgent bill alerts
        ├── expenses.js         # Log & view personal/split expenses
        ├── recurring.js        # Recurring monthly bills manager (YouTube, Wi-Fi, Rent)
        ├── reminders.js        # Split reminder builder (WhatsApp & Native Share)
        └── app.js              # Client state router & tab switcher
```

---

## 🛠️ Setup & Running Locally

### Prerequisites

- **Python 3.9 or higher**

### Step-by-step Execution

1. **Clone the Repository**:
   ```bash
   git clone git@github.com:Chitransh-18/Expense-Bot.git
   cd Expense-Bot
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize Database**:
   ```bash
   python database.py
   ```

4. **Launch the Web Application Server**:
   ```bash
   python app.py
   ```

5. **Access the App**:
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

---

## 📲 How to Install on Your Device (PWA)

### On Android / Chrome:
- Click the **"📱 Install App"** button on the top bar or sidebar, or open browser menu (⋮) -> select **"Add to Home screen"**.

### On iPhone / iOS Safari:
- Open `http://<your-host>:5000` in Safari -> tap the **Share** button -> select **"Add to Home Screen"**.

### On Desktop (Chrome / Edge / Brave):
- Click the **Install** icon in the browser address bar or click **"📱 Install App"** inside the dashboard.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
