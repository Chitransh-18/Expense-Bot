import os
import sqlite3
from config import DATABASE_PATH

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_db():
    """Get database connection (PostgreSQL if DATABASE_URL set, otherwise SQLite)"""
    if DATABASE_URL:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    """Initialize database tables for PostgreSQL or SQLite"""
    conn = get_db()
    cursor = conn.cursor()

    is_postgres = bool(DATABASE_URL)
    auto_id_type = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    timestamp_type = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

    # Users Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS users (
            id {auto_id_type},
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            is_password_set INTEGER DEFAULT 0,
            created_at {timestamp_type}
        )
    ''')

    # OTP Codes Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS otp_codes (
            id {auto_id_type},
            email VARCHAR(255) NOT NULL,
            code VARCHAR(10) NOT NULL,
            expires_at {timestamp_type},
            created_at {timestamp_type}
        )
    ''')

    # Expenses Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS expenses (
            id {auto_id_type},
            user_id INTEGER NOT NULL,
            expense_type VARCHAR(50) NOT NULL,
            category VARCHAR(100) NOT NULL,
            amount REAL NOT NULL,
            total_bill_amount REAL,
            payment_mode VARCHAR(50) NOT NULL,
            description TEXT,
            date VARCHAR(20) NOT NULL,
            split_with TEXT,
            split_type VARCHAR(50),
            created_at {timestamp_type},
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Recurring Monthly Bills Table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS recurring_bills (
            id {auto_id_type},
            user_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            total_amount REAL NOT NULL,
            user_share REAL NOT NULL,
            paid_by VARCHAR(100) NOT NULL,
            due_day INTEGER NOT NULL,
            category VARCHAR(100) NOT NULL,
            last_settled_month VARCHAR(20),
            created_at {timestamp_type},
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Auto-migrations for existing databases
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_password_set INTEGER DEFAULT 0")
    except Exception:
        pass

    try:
        cursor.execute("ALTER TABLE expenses ADD COLUMN total_bill_amount REAL")
    except Exception:
        pass

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized successfully ({'PostgreSQL' if DATABASE_URL else 'SQLite'}).")
