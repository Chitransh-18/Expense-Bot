# 💰 ExpenseTracker Pro: Installable Web App (PWA) & Split Expense Manager

[![Live Demo](https://img.shields.io/badge/Live%20App-expense--bot--1--jyl4.onrender.com-brightgreen.svg?style=for-the-badge&logo=render)](https://expense-bot-1-jyl4.onrender.com)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-blue.svg)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
[![Font](https://img.shields.io/badge/Typography-Plus%20Jakarta%20Sans-indigo.svg)](https://fonts.google.com/specimen/Plus+Jakarta+Sans)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask API](https://img.shields.io/badge/Flask-v3.0-green)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20Supabase-blue)](https://supabase.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**ExpenseTracker Pro** is a modern, installable Progressive Web Application (PWA) built for tracking personal spending, split expenses with friends (50% user share calculation), recurring monthly subscriptions (like YouTube Family Premium, Wi-Fi, Rent), unique Username authentication, real-time cross-device cloud syncing, and automated split reminders via WhatsApp.

🌐 **Live 24/7 Web App**: [https://expense-bot-1-jyl4.onrender.com](https://expense-bot-1-jyl4.onrender.com)

---

## ✨ Features & Architecture Highlights

- ☀️ **Vibrant & Warm Light UI**:
  - High-contrast, clean light design system built with **Plus Jakarta Sans** typography, crisp white floating cards, sunset coral accents (`#ff6b6b`, `#ff8e53`), and de-clustered spacing.
- 🔑 **Tabbed Auth & Unique Usernames**:
  - **[ 👤 Sign In ] Tab**: Instant 1-click sign-in using **Username (or Email)** + **Password**.
  - **[ ✨ Register ] Tab**: 1-form registration collecting Full Name, Unique Username, Email, and Password upfront with 6-digit OTP verification.
  - **Username Uniqueness Validation**: Real-time checking (e.g. *"Username 'chitransh' is taken! Try adding '_' or a number like chitransh_18"*).
- 🧮 **Accurate Split Expense Calculation**:
  - Automatically calculates net user share (**50% = ₹225** for an equal ₹450 bill) for dashboard analytics while preserving the total bill amount.
- 🔄 **Real-Time Cross-Device Cloud Sync**:
  - 12-second background sync & window focus triggers ensure any entry added on your phone instantly pops up on your laptop screen.
  - Live `🟢 Cloud Synced` status badge in the sidebar.
- 📱 **Installable Progressive Web App (PWA)**:
  - Add to Home Screen on iOS (Safari) and Android (Chrome) with interactive step-by-step installation guides.
  - Standalone app feel with network-first Service Worker asset caching (`sw.js`).
- 🗄️ **Supabase PostgreSQL & SQLite Auto-Switching**:
  - Built-in PostgreSQL support for 100% free cloud database hosting via **Supabase** (`DATABASE_URL`), ensuring zero data loss during server restarts.
- 📅 **Recurring Monthly Bills & Subscription Manager**:
  - Track monthly recurring bills like **YouTube Family Premium**, Wi-Fi, Rent, Netflix with due alerts (**Due Today 🚨**, **Overdue**, **Upcoming**).
  - One-click **"Mark Paid"** (auto-settles & logs expense) and **"📲 Remind Friend"** via WhatsApp.
- 📊 **Interactive Monthly Expenditure Reports**:
  - Statement period breakdown of total monthly spent, Personal vs Split ratio, top spending categories, and largest single transaction.
- 📄 **Data Export**:
  - One-click CSV export of your full transaction history.

---

## 📁 Project Architecture

```
Expense-Tracker-App/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions Automated CI Build & Syntax Check
├── app.py                      # Flask REST API backend, auth tabs & PWA route server
├── config.py                   # App configuration & JWT secret key
├── database.py                 # PostgreSQL (Supabase) / SQLite auto-initializer & migration runner
├── requirements.txt            # Python dependencies (Flask, Flask-CORS, PyJWT, Werkzeug, gunicorn, psycopg2-binary)
├── test_local.py               # Local API & Database integration test suite
├── Dockerfile                  # Container definition for web app
├── docker-compose.yml          # Multi-container orchestration (Web App + PostgreSQL)
├── Procfile                    # Production WSGI server command (gunicorn app:app)
├── render.yaml                 # 1-Click Render Cloud Deployment Blueprint (plan: free)
├── README.md                   # Documentation & setup guide
├── CONTRIBUTING.md             # Open-source contribution guidelines
├── SECURITY.md                 # Vulnerability reporting guidelines
├── LICENSE                     # MIT Open Source License
├── .env.example                # Environment variables template
├── services/
│   └── email_service.py        # Real SMTP & HTTPS Email OTP Dispatcher (Brevo / Resend / Gmail)
└── static/                     # PWA Frontend Assets
    ├── index.html              # Single Page App structure & Google Fonts (Plus Jakarta Sans)
    ├── manifest.json           # Web App Manifest for app installation
    ├── sw.js                   # Service Worker for offline asset caching
    ├── css/
    │   └── style.css           # Warm Light Theme CSS design system & Tabbed Auth styling
    └── js/
        ├── api.js              # Token management, fetch wrapper & non-JSON error parser
        ├── pwa.js              # Service Worker & PWA Install prompt handler
        ├── auth.js             # Tabbed Sign In / Register UI & Username validation
        ├── dashboard.js        # Overview stats, time greeting, & monthly report modal
        ├── expenses.js         # Log & view personal/split expenses (50% share badge)
        ├── recurring.js        # Recurring monthly bills manager (YouTube, Wi-Fi, Rent)
        ├── reminders.js        # Split reminder builder (WhatsApp & Native Share)
        └── app.js              # Client state router, auto-sync timer & mobile install guide
```

---

## 🛠️ Setup & Running Locally

### Prerequisites

- **Python 3.9 or higher** (or Docker Desktop)

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

4. **Run Automated Integration Tests**:
   ```bash
   python test_local.py
   ```

5. **Launch the Web Server**:
   ```bash
   python app.py
   ```

6. **Access the App**:
   Open your browser and navigate to: `http://localhost:5000`

---

## ☁️ 24/7 Live Deployment & Cloud Database Setup

### Live Demo URL
Access the live deployed application 24/7 at:  
👉 **[https://expense-bot-1-jyl4.onrender.com](https://expense-bot-1-jyl4.onrender.com)**

### Connecting Supabase Free Cloud PostgreSQL Database

To make user registrations and expense records permanent in the cloud:
1. Create a free project at **[supabase.com](https://supabase.com)**.
2. Copy your PostgreSQL connection string (`DATABASE_URL`):
   ```text
   postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres
   ```
3. Add **`DATABASE_URL`** under Render's **Environment** tab.

### Environment Variables for Real Email OTP Delivery

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | Supabase Cloud PostgreSQL Connection String | `postgresql://postgres:...@db.xxxx.supabase.co:5432/postgres` |
| `SMTP_PASS` | Brevo API Key (or Gmail App Password) | `xkeysib-...` |
| `SMTP_USER` | Registered Brevo / Gmail Email | `your_email@gmail.com` |
| `SMTP_HOST` | SMTP Host (default `smtp.gmail.com`) | `smtp.gmail.com` |
| `SMTP_PORT` | Port (465 SSL or 587 TLS) | `465` |

---

## 📱 How to Install on Your Mobile Device (PWA)

### Android (Google Chrome):
- Tap the **"📱 Install App"** button inside the sidebar, or open Chrome's top-right menu (⋮) ➔ select **"Add to Home screen"**.

### iPhone / iPad (Apple Safari):
- Open `https://expense-bot-1-jyl4.onrender.com` in Safari ➔ tap the **Share** button (⎋) ➔ select **"Add to Home Screen"** (`+`).

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for details on setting up local virtual environments, submitting Pull Requests, and reporting vulnerabilities.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
