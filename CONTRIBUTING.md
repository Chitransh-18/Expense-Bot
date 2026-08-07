# Contributing to ExpenseTracker Pro 🚀

Thank you for your interest in contributing to **ExpenseTracker Pro**! We welcome bug reports, feature suggestions, UI enhancements, and Pull Requests from developers worldwide.

---

## 🛠️ Local Development Setup

1. **Fork & Clone the Repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/Expense-Bot.git
   cd Expense-Bot
   ```

2. **Create a Python Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy `.env.example` to `.env`**:
   ```bash
   cp .env.example .env
   ```

5. **Initialize Database & Launch Dev Server**:
   ```bash
   python database.py
   python app.py
   ```

6. **Open in Browser**:
   Navigate to `http://localhost:5000`

---

## 🌿 Branching Guidelines

- Create a feature branch off `main`:
  ```bash
  git checkout -b feature/your-feature-name
  ```
- Make sure code passes syntax compilation:
  ```bash
  python -m py_compile app.py database.py config.py services/email_service.py
  ```

---

## 📥 Submitting Pull Requests

1. Commit your changes with clear, descriptive commit messages.
2. Push your feature branch to your fork.
3. Open a Pull Request against the `main` branch of `Chitransh-18/Expense-Bot`.
4. Our automated GitHub Actions CI pipeline will run build checks. Once reviewed, your PR will be merged!

---

## 📜 Code of Conduct

Please adhere to standard open-source etiquette: be respectful, helpful, and collaborative.
