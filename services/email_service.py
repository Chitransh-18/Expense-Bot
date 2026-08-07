import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def get_smtp_config():
    """Dynamically fetch current SMTP credentials from environment with robust string sanitization"""
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip().strip("'\"")
    port_str = os.environ.get("SMTP_PORT", "587").strip().strip("'\"")
    try:
        port = int(port_str)
    except ValueError:
        port = 587

    user = os.environ.get("SMTP_USER", "").strip().strip("'\"")
    password = os.environ.get("SMTP_PASS", "").strip().strip("'\"").replace(" ", "")
    sender = os.environ.get("SMTP_FROM", f"ExpenseTracker Pro <{user}>" if user else "ExpenseTracker Pro <noreply@expensetracker.app>").strip().strip("'\"")
    return host, port, user, password, sender

def is_smtp_configured() -> bool:
    """Check if SMTP credentials are configured"""
    host, port, user, password, sender = get_smtp_config()
    return bool(host and user and password)

def send_otp_email(recipient_email: str, otp_code: str):
    """
    Send formatted HTML OTP Verification Email via SMTP with automatic Port 587/465 fallback.
    Returns (success: bool, error_message: str) tuple.
    """
    host, port, user, password, sender = get_smtp_config()

    if not (host and user and password):
        print(f"\n[DEV MODE] SMTP not configured. OTP for {recipient_email}: {otp_code}\n")
        return False, "SMTP credentials not configured"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔑 {otp_code} is your ExpenseTracker Pro Verification Code"
    msg["From"] = sender
    msg["To"] = recipient_email

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #070a12; color: #f8fafc; margin: 0; padding: 20px; }}
        .card {{ background-color: #0f172a; border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 16px; max-width: 480px; margin: 0 auto; padding: 30px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }}
        .logo {{ font-size: 32px; margin-bottom: 10px; }}
        .title {{ font-size: 22px; font-weight: 700; color: #ffffff; margin-bottom: 8px; }}
        .subtitle {{ color: #94a3b8; font-size: 14px; margin-bottom: 24px; }}
        .otp-box {{ background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(6, 182, 212, 0.2)); border: 1px dashed #6366f1; border-radius: 12px; padding: 16px; font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #06b6d4; margin: 20px 0; }}
        .footer {{ color: #64748b; font-size: 12px; margin-top: 24px; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="logo">💰</div>
        <div class="title">Verification Code</div>
        <div class="subtitle">Use the OTP code below to complete your sign in to ExpenseTracker Pro.</div>
        <div class="otp-box">{otp_code}</div>
        <p style="color: #94a3b8; font-size: 13px;">This code will expire in <strong>10 minutes</strong>. If you did not request this, please ignore this email.</p>
        <div class="footer">
          ExpenseTracker Pro • Smart Installable Expense Manager & Reminders
        </div>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_body, "html"))

    # Try Primary Connection Method
    last_error = ""
    ports_to_try = [port, 465, 587] if port not in (465, 587) else [port, 465 if port == 587 else 587]

    for p in ports_to_try:
        try:
            print(f"Attempting SMTP connection to {host}:{p}...")
            if p == 465:
                server = smtplib.SMTP_SSL(host, p, timeout=8)
            else:
                server = smtplib.SMTP(host, p, timeout=8)
                server.starttls()

            server.login(user, password)
            server.sendmail(sender, [recipient_email], msg.as_string())
            server.quit()
            print(f"✅ OTP email sent successfully to {recipient_email} via port {p}")
            return True, ""
        except Exception as e:
            last_error = str(e)
            print(f"⚠️ SMTP connection on port {p} failed: {last_error}")

    return False, last_error
