import os
import io
import csv
import jwt
import random
import re
import sqlite3
import smtplib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from config import SECRET_KEY, PORT, DEBUG
from database import init_db, get_db, execute_sql, to_dict
from services.email_service import send_otp_email, is_smtp_configured, get_smtp_config

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Initialize Database on startup
init_db()

# --- Global Error Handler to return JSON instead of HTML on exceptions ---
@app.errorhandler(Exception)
def handle_exception(e):
    print(f"❌ Global API Exception: {e}")
    if "does not exist" in str(e).lower() or "no such table" in str(e).lower():
        try:
            init_db()
        except Exception:
            pass
    return jsonify({"error": f"Server Error: {str(e)}"}), 500

# --- Auth Helper Decorator ---
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header:
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            else:
                token = auth_header

        if not token:
            return jsonify({"error": "Authorization token is missing"}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            conn = get_db()
            cursor = conn.cursor()
            try:
                execute_sql(cursor, conn, "SELECT id, username, email, full_name, is_password_set FROM users WHERE id = ?", (data["user_id"],))
                user_row = cursor.fetchone()
            except Exception as e:
                if "does not exist" in str(e).lower() or "no such table" in str(e).lower():
                    conn.close()
                    init_db()
                    conn = get_db()
                    cursor = conn.cursor()
                    execute_sql(cursor, conn, "SELECT id, username, email, full_name, is_password_set FROM users WHERE id = ?", (data["user_id"],))
                    user_row = cursor.fetchone()
                else:
                    raise e
            conn.close()
            current_user = to_dict(user_row)
            if not current_user:
                return jsonify({"error": "User not found"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(current_user, *args, **kwargs)
    return decorated

# --- Static PWA Routes ---
@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/<path:path>")
def static_files(path):
    if path.startswith("api/"):
        return jsonify({"error": "API route not found"}), 404
    return send_from_directory("static", path)

# --- Authentication API Routes ---

@app.route("/api/auth/check-username", methods=["POST"])
def check_username():
    data = request.get_json() or {}
    raw_username = data.get("username", "").strip()
    username = re.sub(r'[^a-zA-Z0-9_]', '', raw_username).lower()

    if not username:
        return jsonify({"available": False, "error": "Username must contain letters, numbers, or '_'"}), 400

    conn = get_db()
    cursor = conn.cursor()
    execute_sql(cursor, conn, "SELECT id FROM users WHERE LOWER(username) = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    if row:
        suggestion1 = f"{username}_1"
        suggestion2 = f"{username}_18"
        return jsonify({
            "available": False,
            "username": username,
            "message": f"Username '{raw_username}' is already taken. Try adding '_' or a number.",
            "suggestions": [suggestion1, suggestion2]
        })

    return jsonify({"available": True, "username": username})

@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    identifier = data.get("username_or_email", "").strip().lower()
    password = data.get("password", "").strip()

    if not identifier or not password:
        return jsonify({"error": "Username/Email and Password are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    execute_sql(cursor, conn, "SELECT * FROM users WHERE LOWER(username) = ? OR LOWER(email) = ?", (identifier, identifier))
    user_row = cursor.fetchone()
    conn.close()

    user = to_dict(user_row)
    if not user:
        return jsonify({"error": "No account found with this username or email"}), 400

    if not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Incorrect password. Please try again."}), 400

    # Generate JWT Token
    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.utcnow() + timedelta(days=30)},
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Signed in successfully!",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user.get("username") or user["email"].split("@")[0],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    })

@app.route("/api/auth/register-send-otp", methods=["POST"])
def register_send_otp():
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    raw_username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not full_name or not email or not password or not raw_username:
        return jsonify({"error": "All fields (Full Name, Username, Email, Password) are required"}), 400

    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters long"}), 400

    username = re.sub(r'[^a-zA-Z0-9_]', '', raw_username).lower()
    if not username:
        return jsonify({"error": "Username can only contain letters, numbers, and '_'"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # 1. Check Username Uniqueness
    execute_sql(cursor, conn, "SELECT id FROM users WHERE LOWER(username) = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return jsonify({
            "error": f"Username '{raw_username}' already exists! Try adding '_' or a number (e.g. {username}_18 or {username}_1)"
        }), 400

    # 2. Check Email Uniqueness
    execute_sql(cursor, conn, "SELECT id FROM users WHERE LOWER(email) = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({
            "error": f"An account with email '{email}' already exists. Please click 'Sign In'."
        }), 400

    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    # Store OTP in DB
    execute_sql(cursor, conn, "DELETE FROM otp_codes WHERE email = ?", (email,))
    execute_sql(cursor, conn, 
        "INSERT INTO otp_codes (email, code, expires_at) VALUES (?, ?, ?)",
        (email, otp_code, expires_at)
    )
    conn.commit()
    conn.close()

    # Dispatch Email OTP
    sent_via_email, error_msg = send_otp_email(email, otp_code)

    res_data = {
        "message": f"Verification OTP code sent to {email}",
        "email": email,
        "username": username,
        "full_name": full_name,
        "email_sent": sent_via_email
    }

    if not sent_via_email:
        if is_smtp_configured():
            res_data["dev_notice"] = f"SMTP Delivery Notice: {error_msg}. Demo OTP: {otp_code}"
        else:
            res_data["dev_notice"] = f"SMTP Email unconfigured. Demo OTP: {otp_code}"
        res_data["otp_debug"] = otp_code

    return jsonify(res_data)

@app.route("/api/auth/register-verify-otp", methods=["POST"])
def register_verify_otp():
    data = request.get_json() or {}
    full_name = data.get("full_name", "").strip()
    raw_username = data.get("username", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()
    otp_code = data.get("otp_code", "").strip()

    if not email or not otp_code or not password:
        return jsonify({"error": "Email, Password, and OTP code are required"}), 400

    username = re.sub(r'[^a-zA-Z0-9_]', '', raw_username).lower() if raw_username else email.split("@")[0].lower()

    conn = get_db()
    cursor = conn.cursor()

    # Check OTP validity
    execute_sql(cursor, conn, "SELECT * FROM otp_codes WHERE email = ? AND code = ?", (email, otp_code))
    otp_record = cursor.fetchone()

    if not otp_record:
        conn.close()
        return jsonify({"error": "Invalid or expired OTP code"}), 400

    # Delete used OTP
    execute_sql(cursor, conn, "DELETE FROM otp_codes WHERE email = ?", (email,))

    pwd_hash = generate_password_hash(password)

    # Check existing user
    execute_sql(cursor, conn, "SELECT * FROM users WHERE email = ?", (email,))
    existing_user = to_dict(cursor.fetchone())

    if not existing_user:
        execute_sql(cursor, conn, 
            "INSERT INTO users (username, email, password_hash, full_name, is_password_set) VALUES (?, ?, ?, ?, 1)",
            (username, email, pwd_hash, full_name)
        )
        execute_sql(cursor, conn, "SELECT id FROM users WHERE email = ?", (email,))
        row = to_dict(cursor.fetchone())
        user_id = row["id"] if row else 1
        conn.commit()
        user_dict = {"id": user_id, "username": username, "email": email, "full_name": full_name}
    else:
        user_dict = dict(existing_user)
        execute_sql(cursor, conn, 
            "UPDATE users SET username = ?, password_hash = ?, is_password_set = 1, full_name = ? WHERE id = ?",
            (username, pwd_hash, full_name, user_dict["id"])
        )
        conn.commit()
        user_dict["username"] = username
        user_dict["full_name"] = full_name

    conn.close()

    # Generate JWT Token
    token = jwt.encode(
        {"user_id": user_dict["id"], "exp": datetime.utcnow() + timedelta(days=30)},
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "Account created and signed in successfully!",
        "token": token,
        "user": {
            "id": user_dict["id"],
            "username": user_dict["username"],
            "email": user_dict["email"],
            "full_name": user_dict["full_name"]
        }
    })

# Backward compatibility routes
@app.route("/api/auth/check-user", methods=["POST"])
def check_user():
    return login()

@app.route("/api/auth/login-password", methods=["POST"])
def login_password():
    return login()

@app.route("/api/auth/send-otp", methods=["POST"])
def send_otp():
    return register_send_otp()

@app.route("/api/auth/verify-otp-set-password", methods=["POST"])
def verify_otp_set_password():
    return register_verify_otp()

@app.route("/api/auth/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    return jsonify({"user": current_user})

# --- Expenses API Routes ---
@app.route("/api/expenses", methods=["GET"])
@token_required
def get_expenses(current_user):
    category = request.args.get("category")
    filter_type = request.args.get("filter", "all")

    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT * FROM expenses WHERE user_id = ?"
    params = [current_user["id"]]

    if category:
        query += " AND category = ?"
        params.append(category)

    query += " ORDER BY date DESC, id DESC"
    
    try:
        execute_sql(cursor, conn, query, params)
        rows = [to_dict(r) for r in cursor.fetchall()]
    except Exception as e:
        if "does not exist" in str(e).lower() or "no such table" in str(e).lower():
            conn.close()
            init_db()
            conn = get_db()
            cursor = conn.cursor()
            execute_sql(cursor, conn, query, params)
            rows = [to_dict(r) for r in cursor.fetchall()]
        else:
            raise e

    conn.close()

    now = datetime.now()
    if filter_type == "this_month":
        rows = [r for r in rows if r["date"].startswith(now.strftime("%Y-%m"))]
    elif filter_type == "last_month":
        last_m = now.month - 1 if now.month > 1 else 12
        last_y = now.year if now.month > 1 else now.year - 1
        prefix = f"{last_y:04d}-{last_m:02d}"
        rows = [r for r in rows if r["date"].startswith(prefix)]

    return jsonify({"expenses": rows})

@app.route("/api/expenses", methods=["POST"])
@token_required
def add_expense(current_user):
    data = request.get_json() or {}
    expense_type = data.get("expense_type", "Personal")
    category = data.get("category", "General")
    raw_amount = float(data.get("amount", 0))
    payment_mode = data.get("payment_mode", "UPI")
    description = data.get("description", "")
    date_str = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    split_with = data.get("split_with", "")
    split_type = data.get("split_type", "Equal")

    if raw_amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    total_bill_amount = raw_amount

    # Calculate user share vs total bill for Split Expenses
    if expense_type == "Split":
        if split_type == "Equal":
            num_people = len([p for p in split_with.split(",") if p.strip()]) + 1 if split_with else 2
            user_amount = total_bill_amount / float(num_people)
        elif split_type == "Percentage":
            user_percent = float(data.get("user_share_percent", 50))
            user_amount = total_bill_amount * (user_percent / 100.0)
        else:
            user_amount = total_bill_amount / 2.0
    else:
        user_amount = total_bill_amount

    conn = get_db()
    cursor = conn.cursor()

    try:
        try:
            execute_sql(cursor, conn, '''
                INSERT INTO expenses (user_id, expense_type, category, amount, total_bill_amount, payment_mode, description, date, split_with, split_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_user["id"], expense_type, category, user_amount, total_bill_amount, payment_mode, description, date_str, split_with, split_type))
        except Exception:
            execute_sql(cursor, conn, '''
                INSERT INTO expenses (user_id, expense_type, category, amount, payment_mode, description, date, split_with, split_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_user["id"], expense_type, category, user_amount, payment_mode, description, date_str, split_with, split_type))
        conn.commit()
    except Exception as e:
        if "does not exist" in str(e).lower() or "no such table" in str(e).lower():
            conn.close()
            init_db()
            conn = get_db()
            cursor = conn.cursor()
            execute_sql(cursor, conn, '''
                INSERT INTO expenses (user_id, expense_type, category, amount, total_bill_amount, payment_mode, description, date, split_with, split_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (current_user["id"], expense_type, category, user_amount, total_bill_amount, payment_mode, description, date_str, split_with, split_type))
            conn.commit()
        else:
            raise e

    execute_sql(cursor, conn, "SELECT id FROM expenses WHERE user_id = ? ORDER BY id DESC LIMIT 1", (current_user["id"],))
    row = to_dict(cursor.fetchone())
    expense_id = row["id"] if row else 1
    conn.close()

    return jsonify({
        "message": "Expense recorded successfully",
        "expense": {
            "id": expense_id,
            "expense_type": expense_type,
            "category": category,
            "amount": user_amount,
            "total_bill_amount": total_bill_amount,
            "payment_mode": payment_mode,
            "description": description,
            "date": date_str,
            "split_with": split_with,
            "split_type": split_type
        }
    }), 201

@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
@token_required
def delete_expense(current_user, expense_id):
    conn = get_db()
    cursor = conn.cursor()
    execute_sql(cursor, conn, "DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, current_user["id"]))
    affected = cursor.rowcount
    conn.commit()
    conn.close()

    if affected == 0:
        return jsonify({"error": "Expense not found"}), 404
    return jsonify({"message": "Expense deleted successfully"})

# --- Recurring Monthly Bills API Routes ---
@app.route("/api/recurring", methods=["GET"])
@token_required
def get_recurring_bills(current_user):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_sql(cursor, conn, "SELECT * FROM recurring_bills WHERE user_id = ? ORDER BY due_day ASC", (current_user["id"],))
        rows = [to_dict(r) for r in cursor.fetchall()]
    except Exception as e:
        if "does not exist" in str(e).lower() or "no such table" in str(e).lower():
            conn.close()
            init_db()
            conn = get_db()
            cursor = conn.cursor()
            execute_sql(cursor, conn, "SELECT * FROM recurring_bills WHERE user_id = ? ORDER BY due_day ASC", (current_user["id"],))
            rows = [to_dict(r) for r in cursor.fetchall()]
        else:
            raise e

    conn.close()

    now = datetime.now()
    current_month_str = now.strftime("%Y-%m")
    current_day = now.day

    bills_processed = []
    for bill in rows:
        due_day = bill["due_day"]
        last_settled = bill["last_settled_month"]
        is_settled_this_month = (last_settled == current_month_str)

        if is_settled_this_month:
            status = "Settled"
            status_text = f"Paid for {now.strftime('%B')}"
        elif current_day == due_day:
            status = "Due Today"
            status_text = f"Due TODAY ({due_day}th of {now.strftime('%B')})!"
        elif current_day > due_day:
            status = "Overdue"
            status_text = f"Overdue since {due_day}th of {now.strftime('%B')}"
        elif (due_day - current_day) <= 5:
            status = "Upcoming"
            days_left = due_day - current_day
            status_text = f"Due in {days_left} day{'s' if days_left > 1 else ''} ({due_day}th)"
        else:
            status = "Normal"
            status_text = f"Due on {due_day}th of every month"

        bill_data = dict(bill)
        bill_data["status"] = status
        bill_data["status_text"] = status_text
        bill_data["is_settled_this_month"] = is_settled_this_month
        bills_processed.append(bill_data)

    return jsonify({"recurring_bills": bills_processed})

@app.route("/api/recurring", methods=["POST"])
@token_required
def add_recurring_bill(current_user):
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    total_amount = float(data.get("total_amount", 0))
    user_share = float(data.get("user_share", 0))
    paid_by = data.get("paid_by", "Self").strip()
    due_day = int(data.get("due_day", 1))
    category = data.get("category", "Subscriptions").strip()

    if not title or total_amount <= 0 or user_share <= 0:
        return jsonify({"error": "Title, total amount, and your share are required"}), 400

    if not (1 <= due_day <= 31):
        return jsonify({"error": "Due day must be between 1 and 31"}), 400

    conn = get_db()
    cursor = conn.cursor()
    execute_sql(cursor, conn, '''
        INSERT INTO recurring_bills (user_id, title, total_amount, user_share, paid_by, due_day, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (current_user["id"], title, total_amount, user_share, paid_by, due_day, category))
    execute_sql(cursor, conn, "SELECT id FROM recurring_bills WHERE user_id = ? ORDER BY id DESC LIMIT 1", (current_user["id"],))
    row = to_dict(cursor.fetchone())
    bill_id = row["id"] if row else 1
    conn.commit()
    conn.close()

    return jsonify({"message": "Recurring bill added successfully", "id": bill_id}), 201

@app.route("/api/recurring/<int:bill_id>/settle", methods=["POST"])
@token_required
def settle_recurring_bill(current_user, bill_id):
    conn = get_db()
    cursor = conn.cursor()
    execute_sql(cursor, conn, "SELECT * FROM recurring_bills WHERE id = ? AND user_id = ?", (bill_id, current_user["id"]))
    bill_row = cursor.fetchone()

    if not bill_row:
        conn.close()
        return jsonify({"error": "Recurring bill not found"}), 404

    bill = to_dict(bill_row)
    now = datetime.now()
    current_month_str = now.strftime("%Y-%m")
    today_str = now.strftime("%Y-%m-%d")

    execute_sql(cursor, conn, "UPDATE recurring_bills SET last_settled_month = ? WHERE id = ?", (current_month_str, bill_id))

    desc = f"Monthly Bill: {bill['title']} (Paid by {bill['paid_by']})"
    user_share_amt = bill['user_share']
    total_bill_amt = bill['total_amount']

    try:
        execute_sql(cursor, conn, '''
            INSERT INTO expenses (user_id, expense_type, category, amount, total_bill_amount, payment_mode, description, date, split_with, split_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user["id"], "Split" if bill["paid_by"] != "Self" else "Personal", bill["category"], user_share_amt, total_bill_amt, "Online", desc, today_str, bill["paid_by"] if bill["paid_by"] != "Self" else "", "Equal"))
    except Exception:
        execute_sql(cursor, conn, '''
            INSERT INTO expenses (user_id, expense_type, category, amount, payment_mode, description, date, split_with, split_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (current_user["id"], "Split" if bill["paid_by"] != "Self" else "Personal", bill["category"], user_share_amt, "Online", desc, today_str, bill["paid_by"] if bill["paid_by"] != "Self" else "", "Equal"))

    conn.commit()
    conn.close()

    return jsonify({
        "message": f"Bill '{bill['title']}' settled for {now.strftime('%B %Y')}!",
        "settled_month": current_month_str
    })

# --- Analytics API Routes ---
@app.route("/api/analytics", methods=["GET"])
@token_required
def get_analytics(current_user):
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        execute_sql(cursor, conn, "SELECT * FROM expenses WHERE user_id = ?", (current_user["id"],))
        expenses = [to_dict(r) for r in cursor.fetchall()]
    except Exception as e:
        if "does not exist" in str(e).lower() or "no such table" in str(e).lower():
            conn.close()
            init_db()
            conn = get_db()
            cursor = conn.cursor()
            execute_sql(cursor, conn, "SELECT * FROM expenses WHERE user_id = ?", (current_user["id"],))
            expenses = [to_dict(r) for r in cursor.fetchall()]
        else:
            raise e

    conn.close()

    total_spent = sum(e["amount"] for e in expenses)
    personal_spent = sum(e["amount"] for e in expenses if e["expense_type"] == "Personal")
    split_spent = sum(e["amount"] for e in expenses if e["expense_type"] == "Split")

    categories = {}
    for e in expenses:
        cat = e["category"]
        categories[cat] = categories.get(cat, 0) + e["amount"]

    payment_modes = {}
    for e in expenses:
        mode = e["payment_mode"]
        payment_modes[mode] = payment_modes.get(mode, 0) + e["amount"]

    return jsonify({
        "total_spent": total_spent,
        "personal_spent": personal_spent,
        "split_spent": split_spent,
        "categories": categories,
        "payment_modes": payment_modes,
        "total_count": len(expenses)
    })

# --- CSV Export API Route ---
@app.route("/api/export/csv", methods=["GET"])
@token_required
def export_csv(current_user):
    conn = get_db()
    cursor = conn.cursor()
    execute_sql(cursor, conn, "SELECT id, expense_type, category, amount, payment_mode, description, date, split_with, split_type, created_at FROM expenses WHERE user_id = ? ORDER BY date DESC", (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Expense Type", "Category", "User Share Amount (INR)", "Payment Mode", "Description", "Date", "Split With", "Split Type", "Logged At"])

    for row in rows:
        writer.writerow(list(row))

    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=expenses_{current_user['id']}_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
