# 💰 ExpenseTracker Pro: AI Natural Language Expense Tracker & Split Manager

[![Live Demo](https://img.shields.io/badge/Live%20App-expense--bot--1--jyl4.onrender.com-brightgreen.svg?style=for-the-badge&logo=render)](https://expense-bot-1-jyl4.onrender.com)
[![PWA Ready](https://img.shields.io/badge/PWA-Installable-blue.svg)](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)
[![Font](https://img.shields.io/badge/Typography-Plus%20Jakarta%20Sans-indigo.svg)](https://fonts.google.com/specimen/Plus+Jakarta+Sans)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Flask API](https://img.shields.io/badge/Flask-v3.0-green)](https://flask.palletsprojects.com/)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20%7C%20Supabase-blue)](https://supabase.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**ExpenseTracker Pro** is a modern, installable Progressive Web Application (PWA) built for tracking personal spending, split expenses with friends (50% user share calculation), recurring monthly subscriptions (like YouTube Family Premium, Wi-Fi, Rent), unique Username authentication, real-time cross-device cloud syncing, and conversational **AI Natural Language text and voice expense logging in English, Hindi, and Hinglish**.

🌐 **Live 24/7 Web App**: [https://expense-bot-1-jyl4.onrender.com](https://expense-bot-1-jyl4.onrender.com)

---

## ⚡ Natural Language AI Expense Logger (The Core USP)

Log expenses by simply typing or speaking conversational sentences in **English, Hindi, or Hinglish**. The intelligent parsing engine automatically extracts Amount, Category, Payment Mode, Split names, Split ratio, Net user share, and Date:

| Natural Language Input | Extracted Category | Extracted Amount & Split | Payment & Date |
|---|---|---|---|
| *"Dinner 540 with Daksh split via UPI"* | Food & Dining | ₹270 your share (₹540 total bill, split with Daksh) | UPI • Today |
| *"Daksh ke saath dinner 600 aadha aadha UPI se"* | Food & Dining | ₹300 your share (₹600 total bill, split with Daksh) | UPI • Today |
| *"Uber cab 250 cash kal"* | Travel & Cab | ₹250 personal | Cash • Yesterday |
| *"Bijli ka bill 1500 online bhara"* | Bills & Utilities | ₹1,500 personal | Online • Today |
| *"Rohit aur Aman ke saath dinner 900 split kiya"* | Food & Dining | ₹300 your share (₹900 total bill, split 3-ways) | UPI • Today |
| *"Chai nashta 60 cash"* | Food & Dining | ₹60 personal | Cash • Today |

### 🎙️ Speech-to-Text Voice Input
Tap the microphone button 🎙️ next to the AI Quick Bar to speak your expense using the browser's Web Speech API (`en-IN` recognition).

### 🤖 Hybrid Architecture (Fast Offline NLP + Optional Gemini LLM)
- **Zero-Latency Core NLP Engine (Default)**: Custom linguistic parser in `services/nlp_parser.py` that responds in **<10ms**, costs **₹0**, has no rate limits, and requires zero external API dependencies.
- **Optional Gemini LLM Adapter**: If you configure `GEMINI_API_KEY` in Render environment variables, the engine can optionally invoke Google's Gemini Flash for complex multi-sentence logs.

---

## 📋 17-Point Production Polish Checklist

All 17 items from the production audit checklist are implemented and verified:

- [x] **1. Remove horizontal scroll**: Strict `overflow-x: hidden` across root elements and responsive container wrapping.
- [x] **2. Add meta descriptions**: Full SEO metadata, keywords, author, and OpenGraph/Twitter social cards in `index.html`.
- [x] **3. Add a favicon**: Inline vector SVG favicon with PNG fallback and `apple-touch-icon`.
- [x] **4. Fix page titles**: Primary descriptive title + dynamic page titles per route (`Dashboard`, `Expenses`, `Bills`).
- [x] **5. Compress images**: Lightweight CSS gradients, vector SVG icons, Google Fonts preconnect, and zero heavy raster images.
- [x] **6. Clickable email**: Clickable `mailto:chitranshsaxena85@gmail.com` link in sidebar, footer, and Help modal.
- [x] **7. Fix broken links**: Audited all navigation anchors (`#dashboard`, `#expenses`, `#recurring`, `#support`, CSV export).
- [x] **8. Add mobile menu**: Sleek **Mobile Bottom Navigation Bar** and top brand header for screens $\le 768\text{px}$.
- [x] **9. Remove placeholder text**: Cleaned all inputs with realistic bilingual financial examples.
- [x] **10. Test on a mobile device / Optimize**: Touch targets $\ge 48\text{px}$, responsive font sizing, and iOS safe-area insets (`env(safe-area-inset-bottom)`).
- [x] **11. Have an empty state page**: Illustrated empty state cards with emoji artwork and CTA buttons when 0 expenses or 0 bills exist.
- [x] **12. Fix mobile overflow**: Set card widths to `100%`, flex wrapping, and smooth horizontal table scrolling.
- [x] **13. Add error messages**: Replaced browser `alert()` with an animated **Toast Notification System** (`toast-error`).
- [x] **14. Add success messages**: Smooth green toast alerts (`toast-success`) for expense logged, bill settled, and quick-add.
- [x] **15. Add 404 page**: Flask `@app.errorhandler(404)` + frontend client fallback card with "Return to Dashboard" action.
- [x] **16. Clickable phone number**: Clickable WhatsApp (`https://wa.me/...`) and direct phone (`tel:...`) links in Support modal.
- [x] **17. Natural language text message feature**: English, Hindi & Hinglish NLP parser + Quick Add Magic Bar.

---

## 💓 24/7 Supabase Database Keep-Alive Bot

To prevent Supabase's free tier from pausing after 7 days of inactivity:
- **GitHub Actions Scheduled Cron Bot (`.github/workflows/keep_alive.yml`)**: Runs automatically **every 3 days at 00:00 UTC** (`0 0 */3 * *`).
- **Endpoint**: Pings `GET /api/ping` on your live app, executing `SELECT 1` on Supabase PostgreSQL.
- **In-App Keep-Alive**: 24-hour background thread inside Flask that runs a daily database keep-alive query.

---

## 📁 Project Architecture

```
Expense-Tracker-App/
├── .github/
│   └── workflows/
│       ├── ci.yml              # GitHub Actions Automated CI Build & Syntax Check
│       └── keep_alive.yml       # 24/7 Automated Supabase Keep-Alive Cron Bot (Every 3 Days)
├── app.py                      # Flask REST API backend, auth tabs, NLP routes & 404 handler
├── config.py                   # App configuration & JWT secret key
├── database.py                 # PostgreSQL (Supabase) / SQLite auto-initializer & migration runner
├── requirements.txt            # Python dependencies (Flask, Flask-CORS, PyJWT, Werkzeug, gunicorn, psycopg2-binary)
├── test_local.py               # Local API, NLP, & Database integration test suite
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
│   ├── email_service.py        # Real SMTP & HTTPS Email OTP Dispatcher (Brevo / Resend / Gmail)
│   └── nlp_parser.py           # Multi-lingual English + Hindi/Hinglish NLP Parser (+ optional Gemini adapter)
└── static/                     # PWA Frontend Assets
    ├── index.html              # SPA structure, Meta SEO, Favicon, Toast & Mobile Navbars
    ├── manifest.json           # Web App Manifest for app installation
    ├── sw.js                   # Service Worker for offline asset caching
    ├── css/
    │   └── style.css           # Warm Light Theme CSS design system, Toast & Mobile Nav styling
    └── js/
        ├── api.js              # Token management, fetch wrapper & non-JSON error parser
        ├── pwa.js              # Service Worker & PWA Install prompt handler
        ├── auth.js             # Tabbed Sign In / Register UI & Username validation
        ├── dashboard.js        # AI Magic Quick-Add Bar, Voice Input, Stats, & Monthly Reports
        ├── expenses.js         # AI Quick-Add Bar, 50% Share calculations, & Table View
        ├── recurring.js        # Recurring monthly bills manager (YouTube, Wi-Fi, Rent)
        ├── reminders.js        # Split reminder builder (WhatsApp & Native Share)
        └── app.js              # Client state router, Toast manager, dynamic titles & Support modal
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

### Environment Variables

| Variable | Description | Example |
| --- | --- | --- |
| `DATABASE_URL` | Supabase Cloud PostgreSQL Connection String | `postgresql://postgres:...@db.xxxx.supabase.co:5432/postgres` |
| `GEMINI_API_KEY` | Optional Google Gemini API key for advanced conversational logs | `AIzaSy...` |
| `SMTP_PASS` | Brevo API Key (or Gmail App Password) | `xkeysib-...` |
| `SMTP_USER` | Registered Brevo / Gmail Email | `your_email@gmail.com` |
| `SMTP_HOST` | SMTP Host (default `smtp.gmail.com`) | `smtp.gmail.com` |
| `SMTP_PORT` | Port (465 SSL or 587 TLS) | `465` |

---

## 📱 How to Install on Your Mobile Device (PWA)

### Android (Google Chrome):
- Tap the **"📱 Install App"** button inside the menu, or open Chrome's top-right menu (⋮) ➔ select **"Add to Home screen"**.

### iPhone / iPad (Apple Safari):
- Open `https://expense-bot-1-jyl4.onrender.com` in Safari ➔ tap the **Share** button (⎋) ➔ select **"Add to Home Screen"** (`+`).

---

## 🤝 Contributing

Contributions are welcome! Please check out [CONTRIBUTING.md](CONTRIBUTING.md) for details on setting up local virtual environments, submitting Pull Requests, and reporting vulnerabilities.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.
