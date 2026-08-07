import os
import io
import csv
import jwt
import random
import sqlite3
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from config import SECRET_KEY, PORT, DEBUG
from database import init_db, get_db

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# Initialize Database on startup
init_db()

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
            cursor.execute("SELECT id, email, full_name FROM users WHERE id = ?", (data["user_id"],))
            current_user = cursor.fetchone()
            conn.close()
            if not current_user:
                return jsonify({"error": "User not found"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(dict(current_user), *args, **kwargs)
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

# --- OTP Verified Authentication API Routes ---

@app.route("/api/auth/send-otp", methods=["POST"])
def send_otp():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()

    if not email:
        return jsonify({"error": "Email address is required"}), 400

    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    expires_at = (datetime.utcnow() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.cursor()
    
    # Delete old OTPs for this email
    cursor.execute("DELETE FROM otp_codes WHERE email = ?", (email,))
    
    # Insert new OTP
    cursor.execute(
        "INSERT INTO otp_codes (email, code, expires_at) VALUES (?, ?, ?)",
        (email, otp_code, expires_at)
    )
    conn.commit()
    conn.close()

    print(f"\n==========================================")
    print(f"🔑 OTP Code for {email}: {otp_code}")
    print(f"==========================================\n")

    return jsonify({
        "message": f"OTP Verification Code sent to {email}",
        "email": email,
        "otp_debug": otp_code  # Returned for easy local testing/auto-fill
    })

@app.route("/api/auth/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    otp_code = data.get("otp_code", "").strip()
    full_name = data.get("full_name", "").strip()

    if not email or not otp_code:
        return jsonify({"error": "Email and OTP code are required"}), 400

    conn = get_db()
    cursor = conn.cursor()

    # Check OTP validity
    cursor.execute("SELECT * FROM otp_codes WHERE email = ? AND code = ?", (email, otp_code))
    otp_record = cursor.fetchone()

    if not otp_record:
        conn.close()
        return jsonify({"error": "Invalid or expired OTP code"}), 400

    # Delete used OTP
    cursor.execute("DELETE FROM otp_codes WHERE email = ?", (email,))

    # Find or Create User
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()

    if not user:
        name = full_name if full_name else email.split("@")[0].title()
        default_pwd_hash = generate_password_hash(f"pwd_{otp_code}_{email}")
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
            (email, default_pwd_hash, name)
        )
        user_id = cursor.lastrowid
        conn.commit()
        user = {"id": user_id, "email": email, "full_name": name}
    else:
        user = dict(user)

    conn.close()

    # Generate JWT Token
    token = jwt.encode(
        {"user_id": user["id"], "exp": datetime.utcnow() + timedelta(days=30)},
        SECRET_KEY,
        algorithm="HS256"
    )

    return jsonify({
        "message": "OTP Verification successful!",
        "token": token,
        "user": {"id": user["id"], "email": user["email"], "full_name": user["full_name"]}
    })

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
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
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
    amount = float(data.get("amount", 0))
    payment_mode = data.get("payment_mode", "UPI")
    description = data.get("description", "")
    date_str = data.get("date") or datetime.now().strftime("%Y-%m-%d")
    split_with = data.get("split_with", "")
    split_type = data.get("split_type", "Equal")

    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (user_id, expense_type, category, amount, payment_mode, description, date, split_with, split_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_user["id"], expense_type, category, amount, payment_mode, description, date_str, split_with, split_type))
    expense_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Expense recorded successfully",
        "expense": {
            "id": expense_id,
            "expense_type": expense_type,
            "category": category,
            "amount": amount,
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
    cursor.execute("DELETE FROM expenses WHERE id = ? AND user_id = ?", (expense_id, current_user["id"]))
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
    cursor.execute("SELECT * FROM recurring_bills WHERE user_id = ? ORDER BY due_day ASC", (current_user["id"],))
    rows = [dict(r) for r in cursor.fetchall()]
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
    cursor.execute('''
        INSERT INTO recurring_bills (user_id, title, total_amount, user_share, paid_by, due_day, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (current_user["id"], title, total_amount, user_share, paid_by, due_day, category))
    bill_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({"message": "Recurring bill added successfully", "id": bill_id}), 201

@app.route("/api/recurring/<int:bill_id>/settle", methods=["POST"])
@token_required
def settle_recurring_bill(current_user, bill_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recurring_bills WHERE id = ? AND user_id = ?", (bill_id, current_user["id"]))
    bill = cursor.fetchone()

    if not bill:
        conn.close()
        return jsonify({"error": "Recurring bill not found"}), 404

    now = datetime.now()
    current_month_str = now.strftime("%Y-%m")
    today_str = now.strftime("%Y-%m-%d")

    cursor.execute("UPDATE recurring_bills SET last_settled_month = ? WHERE id = ?", (current_month_str, bill_id))

    desc = f"Monthly Bill: {bill['title']} (Paid by {bill['paid_by']})"
    cursor.execute('''
        INSERT INTO expenses (user_id, expense_type, category, amount, payment_mode, description, date, split_with, split_type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_user["id"], "Split" if bill["paid_by"] != "Self" else "Personal", bill["category"], bill["user_share"], "Online", desc, today_str, bill["paid_by"] if bill["paid_by"] != "Self" else "", "Equal"))

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
    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (current_user["id"],))
    expenses = [dict(r) for r in cursor.fetchall()]
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
    cursor.execute("SELECT id, expense_type, category, amount, payment_mode, description, date, split_with, split_type, created_at FROM expenses WHERE user_id = ? ORDER BY date DESC", (current_user["id"],))
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Expense Type", "Category", "Amount (INR)", "Payment Mode", "Description", "Date", "Split With", "Split Type", "Logged At"])

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
