import os

SECRET_KEY = os.environ.get("SECRET_KEY", "expense_bot_super_secret_key_2026")
DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database.sqlite")
PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_ENV") == "development"
