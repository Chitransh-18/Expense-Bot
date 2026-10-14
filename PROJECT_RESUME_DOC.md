# 📄 ExpenseTracker Pro - Engineering Documentation & Resume Portfolio Guide

This comprehensive document is crafted specifically for updating your **Resume**, **LinkedIn Project Section**, and preparing for **Technical Software Engineering Interviews**.

---

## 📌 1. Project Overview & Elevator Pitch

- **Project Name**: ExpenseTracker Pro
- **Role**: Full-Stack AI Engineer / Lead Developer
- **Type**: Production-Grade Progressive Web Application (PWA) & Micro-SaaS
- **Live URL**: [https://expense-bot-1-jyl4.onrender.com](https://expense-bot-1-jyl4.onrender.com)
- **GitHub Repository**: [https://github.com/Chitransh-18/Expense-Bot](https://github.com/Chitransh-18/Expense-Bot)

### 💡 Elevator Pitch (30-Second Interview Summary)
> *"ExpenseTracker Pro is a full-stack, mobile-first financial management platform featuring a custom NLP entity extraction engine that parses conversational expense messages in English, Hindi, and Hinglish. It automates 50% split-bill calculations, recurring subscription tracking with WhatsApp reminders, and real-time cross-device synchronization, backed by a resilient PostgreSQL database with automated GitHub Actions keep-alive workflows."*

---

## 🎯 2. Ready-to-Paste Resume Bullet Points (Google XYZ / STAR Format)

Choose the version that best matches the role you are applying for:

### Option A: Full-Stack Software Engineer (Recommended)
- **Architected and deployed a full-stack Progressive Web Application (PWA)** in Python/Flask and vanilla JavaScript, supporting 1-tap mobile installation and offline caching for personal finance tracking.
- **Engineered an Indian-first NLP Entity Extraction engine** parsing English, Hindi, and Hinglish conversational inputs (e.g., *"Daksh ke saath dinner 540 aadha aadha UPI se"*) in **<10ms** with zero external API dependencies and optional Gemini LLM fallback.
- **Implemented a real-time cross-device data synchronization pipeline** with window-focus triggers and 12s polling, ensuring instant ledger updates between mobile and desktop clients.
- **Automated recurring subscription tracking and split bill management**, computing exact 50% user liability with one-click automated WhatsApp debt-settlement reminders.
- **Designed a resilient dual-database persistence layer** auto-migrating between SQLite and cloud Supabase PostgreSQL with transaction-safe DDL migrations and a 24/7 GitHub Actions cron keep-alive bot.

### Option B: Backend & Cloud / DevOps Focused
- **Developed scalable REST APIs in Flask/Python** with JWT authentication, Werkzeug salted password hashing, and custom row-serialization parsers handling concurrent requests.
- **Integrated cloud-managed Supabase PostgreSQL** with isolated transaction blocks and error rollbacks, preventing DDL transaction abortions during dynamic schema migrations.
- **Constructed automated CI/CD and cron orchestration using GitHub Actions**, triggering synthetic keep-alive heartbeats every 3 days to prevent cloud database hibernation.
- **Dockerized the entire service architecture** with Docker Compose, orchestrating web and PostgreSQL containers for reproducible local and cloud deployments.
- **Built an automated integration test suite** achieving 100% pass rates across auth, unique username validation, split calculation logic, and multilingual NLP parsers.

### Option C: AI & Product Engineer Focused
- **Built an AI Natural Language Quick-Add system** leveraging custom regex tokenizers and semantic keyword classifiers to extract amount, category, split parties, and payment methods from colloquial speech and text.
- **Integrated the Web Speech API** enabling speech-to-text voice expense recording with Indian English/Hinglish language models (`en-IN`).
- **Executed a 17-point UX/accessibility overhaul** eliminating horizontal scroll, adding mobile bottom navigation, empty-state illustrations, dynamic route titles, and toast alert systems.

---

## 🛠️ 3. Complete Technical Stack Breakdown

| Layer | Technologies & Tools | Key Role in Project |
|---|---|---|
| **Frontend** | Vanilla JavaScript (ES6+), HTML5, CSS3 | Zero-dependency high-performance SPA, sub-second load times |
| **Typography & Theme** | Plus Jakarta Sans, Glassmorphism, CSS Variables | Warm light fintech design system, custom responsive layouts |
| **Mobile / PWA** | Service Workers (`sw.js`), Web App Manifest, Cache API | Full offline asset caching, standalone home-screen app |
| **Voice / Speech** | Web Speech API (`SpeechRecognition`) | Native voice-to-text expense dictation in Indian accents |
| **Backend API** | Python 3.11, Flask, Gunicorn | Lightweight, high-throughput WSGI RESTful microservices |
| **Authentication** | PyJWT (JSON Web Tokens), Werkzeug, OTP Verification | Stateless Bearer token auth, email OTP verification, unique usernames |
| **Database** | Supabase Managed PostgreSQL & SQLite3 | Dual-engine database adapter with auto-detection via `DATABASE_URL` |
| **Natural Language** | Custom Rule-Based NLP + Google Gemini Flash API | Sub-10ms multilingual entity parser with LLM fallback |
| **DevOps & Cloud** | Docker, Docker Compose, Render Cloud PaaS | Containerized microservice deployment with health monitoring |
| **Automation & CI** | GitHub Actions (`cron: '0 0 */3 * *'`) | Automated build validation and 24/7 database keep-alive bot |
| **Third-Party APIs** | WhatsApp URI Scheme, Brevo / Gmail SMTP | Deep-linked messaging and automated transactional email dispatch |

---

## 🧠 4. Core System Design & Architecture Highlights

### 1. Multilingual Hybrid NLP Pipeline (`services/nlp_parser.py`)
```
[User Input: "Daksh ke saath dinner 540 aadha aadha UPI se"]
                    │
                    ▼
     ┌─────────────────────────────┐
     │  Has GEMINI_API_KEY set?    │
     └──────────────┬──────────────┘
            YES ───►│◄─── NO
             │             │
             ▼             ▼
      [Gemini Flash]   [Instant Core NLP Engine]
             │             ├── Amount Extractor (₹, Rs, rupaye, numeric)
             │             ├── Category Classifier (Food, Travel, Bills, etc.)
             │             ├── Split Detector (ke saath, aadha, with, divide)
             │             ├── Payment Mode Parser (UPI, GPay, Cash, Card)
             │             └── Date Normalizer (kal = yesterday, aaj = today)
             │             │
             └──────┬──────┘
                    ▼
    [Structured Expense Object (JSON)]
    {
      "amount": 270.0,
      "total_bill_amount": 540.0,
      "category": "Food & Dining",
      "expense_type": "Split",
      "split_with": "Daksh",
      "payment_mode": "UPI",
      "date": "2026-10-14",
      "description": "Daksh ke saath dinner"
    }
```

### 2. Zero-Downtime Database Architecture (`database.py`)
- **Dual Engine Abstraction**: Seamlessly connects to **PostgreSQL** in production (via Supabase `DATABASE_URL`) or local **SQLite** when running offline.
- **Transaction Isolation Fix**: In PostgreSQL (`psycopg2`), failed statements abort the entire transaction block. We isolated every `CREATE TABLE` and migration statement with individual commits and explicit `conn.rollback()` error boundaries.
- **Unified Dictionary Serializer (`to_dict`)**: Uniformly maps SQLite `sqlite3.Row` objects, PostgreSQL `RealDictCursor` dictionaries, and raw tuples into standard Python dictionaries.

### 3. 24/7 Cloud Keep-Alive Cron Automation
- **The Problem**: Free-tier cloud PostgreSQL databases (like Supabase) enter sleep/hibernation mode after 7 consecutive days of inactivity.
- **The Solution**: Created a GitHub Actions cron bot running every 3 days (`0 0 */3 * *`). It sends an authenticated HTTP request to `GET /api/ping`, which executes a live `SELECT 1` query on PostgreSQL, permanently resetting the sleep timer at zero infrastructure cost.

---

## 💬 5. Technical Interview Q&A (Prepare for Interviews)

### Q1: Why did you build a custom NLP engine instead of relying solely on an LLM like OpenAI or Gemini?
> **Answer**: *"Relying purely on third-party LLMs introduces network latency (1.5–3 seconds per query), token billing costs, rate limits, and potential downtime. For expense tracking, users want instant feedback. I built a deterministic, zero-latency (<10ms) rule-based NLP pipeline covering English, Hindi, and Hinglish colloquial vocabulary. I then added an optional Gemini adapter so if complex conversational logs occur, the app can leverage the LLM, but defaults to the local engine for 100% availability and ₹0 operating cost."*

### Q2: How did you solve the database pausing issue on Supabase?
> **Answer**: *"Supabase free tier automatically pauses projects after 7 days of inactivity. Instead of manually logging into a console or paying for an upgrade, I engineered a synthetic keep-alive bot using GitHub Actions scheduled workflows (`cron: '0 0 */3 * *'`). Every 3 days, GitHub's free runners trigger an endpoint on the Flask app that runs a lightweight `SELECT 1` query against the PostgreSQL instance, keeping the connection pool alive and resetting the inactivity clock."*

### Q3: How does the application handle split expenses and debt reconciliation?
> **Answer**: *"When a user logs a split expense (e.g. ₹600 with Daksh), the system tracks both the total bill (₹600) and the user's personal liability (₹300). This prevents dashboard spending analytics from being artificially inflated. For reconciliation, the app integrates with the WhatsApp URI scheme and the Web Share API, automatically generating pre-filled debt settlement reminders with recipient name and exact balance owed."*

---

## 📊 6. Key Metrics & Quantifiable Impact

- **⚡ Latency**: Natural language parsing executes in **<10ms** locally.
- **💰 Cost**: **$0.00/month** total hosting cost (Flask on Render Free Tier + Supabase PostgreSQL + GitHub Actions).
- **🧪 Test Coverage**: **100% passing automated test suite** (`test_local.py`) covering auth, unique usernames, OTP verification, split arithmetic, and multilingual parsing.
- **📱 PWA Standards**: Meets 100% of Progressive Web App installability criteria (Service Worker cache-first architecture, web app manifest, maskable icons).

---

## 👨‍💻 7. Author Information

- **Developer**: Chitransh Saxena
- **Email**: [chitranshsaxena85@gmail.com](mailto:chitranshsaxena85@gmail.com)
- **GitHub**: [@Chitransh-18](https://github.com/Chitransh-18)
- **LinkedIn**: [Chitransh Saxena](https://linkedin.com/in/)
