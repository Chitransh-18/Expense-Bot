# 💰 ExpenseTracker Pro: Downloadable Web App (PWA) with OTP Auth & Bill Manager

[![PWA Ready](https://img.shields.io/badge/PWA-Installable-blue.svg)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask API](https://img.shields.io/badge/Flask-v3.0-green)](https://flask.palletsprojects.com/)
[![Docker Supported](https://img.shields.io/badge/Docker-PostgreSQL-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**ExpenseTracker Pro** is a modern, installable Progressive Web Application (PWA) built for tracking personal spending, split expenses with friends, recurring monthly subscriptions (like YouTube Family Premium paid by Daksh on the 3rd of every month, Wi-Fi, Rent), 6-digit OTP verified authentication, and automated split reminders via WhatsApp or native share.

---

## ✨ Features

- 📱 **Installable Progressive Web App (PWA)**:
  - Add to Home Screen on iOS, Android, Windows, and macOS.
  - Native standalone app feel with offline asset caching (`sw.js` Service Worker).
- 🔑 **6-Digit OTP Verified Authentication**:
  - Secure sign in and registration via 6-digit verification code.
  - Real HTML Email OTP sending via SMTP (Gmail, SendGrid, Amazon SES) with automatic fallback to local Dev Mode.
- 🌅 **Time-Aware Personalized Greetings**:
  - Dynamic local-time greeting on your dashboard: *Good morning 🌅*, *Good afternoon ☀️*, *Good evening 🌇*, *Good night 🌙*.
- 📅 **Recurring Monthly Bills & Subscription Manager**:
  - Track monthly recurring bills like **YouTube Family Premium** (paid by Daksh on the **3rd of every month**), Wi-Fi, Rent, Netflix.
  - Automatic due alerts (**Due Today 🚨**, **Overdue**, **Upcoming**).
  - One-click **"Mark Paid"** (auto-settles & logs expense) and **"📲 Remind Daksh"** via WhatsApp.
- 📊 **Interactive Monthly Expenditure Reports**:
  - Breakdown of total monthly spent, Personal vs Split ratio, top spending categories, and largest single transaction of the month.
- 💰 **Personal & Split Expense Logging**:
  - Log expenses with category tags, payment modes (UPI, Cash, Online, Card), and custom split member details.
- 🔔 **Split Reminder Generator**:
  - Send formatted reminder messages to friends via **WhatsApp Share**, **Native Share Drawer**, or Copy text.
- ✨ **Fintech Glassmorphic UI**:
  - Multi-layered dark glass cards with ambient glowing mesh gradients, status badges, and mobile-responsive navigation.
- 📄 **Data Export**:
  - One-click CSV export of your full transaction history.

---

## 📁 Project Architecture

```
Expense-Tracker-App/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions Automated CI Build & Syntax Check
├── app.py                      # Flask REST API backend & static file server
├── config.py                   # App configuration & JWT secret key
├── database.py                 # SQLite / PostgreSQL auto-initializer
├── requirements.txt            # Python dependencies (Flask, Flask-CORS, PyJWT, Werkzeug, gunicorn)
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
│   └── email_service.py        # Real SMTP HTML Email OTP Dispatcher
└── static/                     # PWA Frontend Assets
    ├── index.html              # Single Page App structure & meta tags
    ├── manifest.json           # Web App Manifest for app installation
    ├── sw.js                   # Service Worker for offline asset caching
    ├── css/
    │   └── style.css           # Glassmorphism CSS design system & OTP styling
    └── js/
        ├── api.js              # Token management & fetch wrapper
        ├── pwa.js              # Service Worker & PWA Install prompt handler
        ├── auth.js             # 6-Digit OTP Sign in UI & auto-advance inputs
        ├── dashboard.js        # Overview stats, time greeting, & monthly report modal
        ├── expenses.js         # Log & view personal/split expenses
        ├── recurring.js        # Recurring monthly bills manager (YouTube, Wi-Fi, Rent)
        ├── reminders.js        # Split reminder builder (WhatsApp & Native Share)
        └── app.js              # Client state router & tab switcher
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

4. **Launch the Server**:
   ```bash
   python app.py
   ```

5. **Access the App**:
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

---

## 🐳 Running with Docker Compose (PostgreSQL)

To run the full stack with a dedicated **PostgreSQL** database container:

```bash
docker-compose up --build
```

Access the app in your browser at `http://localhost:5000`.

---

## ☁️ 24/7 Cloud Deployment Guide

### Deploy on Render.com (100% Free - No Credit Card Required)

1. Sign up on [dashboard.render.com](https://dashboard.render.com/).
2. Click **New +** ➔ Select **Web Service**.
3. Connect your repository `Chitransh-18/Expense-Bot`.
4. Select **Free ($0/mo)** instance type.
5. Click **Create Web Service**! Render will deploy your live 24/7 HTTPS URL.

---

## 📱 How to Install on Your Device (PWA)

### Android / Chrome:
- Click the **"📱 Install App"** button inside the top bar, or open browser menu (⋮) ➔ **"Add to Home screen"**.

### iPhone / iOS Safari:
- Open your live site in Safari ➔ tap the **Share** button ➔ select **"Add to Home Screen"**.

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for details on setting up local virtual environments, submitting Pull Requests, and reporting vulnerabilities.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
