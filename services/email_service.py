import os
import socket
import smtplib
import json
import urllib.request
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Force socket to resolve IPv4 addresses first
orig_getaddrinfo = socket.getaddrinfo
def getaddrinfo_ipv4_only(host, port, family=0, type=0, proto=0, flags=0):
    try:
        res = orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
        if res:
            return res
    except Exception:
        pass
    return orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = getaddrinfo_ipv4_only

def get_smtp_config():
    """Dynamically fetch current SMTP / API credentials from environment"""
    host = os.environ.get("SMTP_HOST", "smtp.gmail.com").strip().strip("'\"")
    port_str = os.environ.get("SMTP_PORT", "587").strip().strip("'\"")
    try:
        port = int(port_str)
    except ValueError:
        port = 587

    user = os.environ.get("SMTP_USER", "").strip().strip("'\"")
    password = os.environ.get("SMTP_PASS", "").strip().strip("'\"").replace(" ", "")
    sender = os.environ.get("SMTP_FROM", f"ExpenseTracker Pro <{user}>" if user else "ExpenseTracker Pro <noreply@expensetracker.app>").strip().strip("'\"")
    
    brevo_key = os.environ.get("BREVO_API_KEY", "").strip().strip("'\"")
    resend_key = os.environ.get("RESEND_API_KEY", "").strip().strip("'\"")
    
    # Auto-detect if user put Resend or Brevo key in SMTP_PASS
    if password.startswith("re_"):
        resend_key = password
    elif password.startswith("xkeysib-"):
        brevo_key = password

    return host, port, user, password, sender, brevo_key, resend_key

def is_smtp_configured() -> bool:
    """Check if SMTP credentials or Email API keys are configured"""
    host, port, user, password, sender, brevo_key, resend_key = get_smtp_config()
    return bool((host and user and password) or brevo_key or resend_key)

def send_via_brevo(api_key: str, sender_email: str, recipient_email: str, otp_code: str):
    """Send HTML OTP email via Brevo HTTPS API (Port 443 - Unblocked on Render)"""
    try:
        url = "https://api.brevo.com/v3/smtp/email"
        payload = {
            "sender": {"name": "ExpenseTracker Pro", "email": sender_email or "noreply@expensetracker.app"},
            "to": [{"email": recipient_email}],
            "subject": f"🔑 {otp_code} is your ExpenseTracker Pro Verification Code",
            "htmlContent": f"""
            <div style="font-family: sans-serif; background: #0f172a; color: #fff; padding: 30px; border-radius: 16px; text-align: center; max-width: 480px; margin: 0 auto;">
              <h2 style="color: #6366f1;">ExpenseTracker Pro</h2>
              <h3>Verification Code</h3>
              <div style="background: rgba(99,102,241,0.2); border: 1px dashed #6366f1; padding: 16px; font-size: 32px; font-weight: bold; color: #06b6d4; letter-spacing: 6px; margin: 20px 0;">{otp_code}</div>
              <p style="color: #94a3b8; font-size: 13px;">This code will expire in 10 minutes.</p>
            </div>
            """
        }
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                print(f"✅ OTP email sent via Brevo HTTPS API to {recipient_email}")
                return True, ""
    except Exception as e:
        print(f"⚠️ Brevo HTTPS API failed: {e}")
        return False, f"Brevo API error: {e}"
    return False, "Brevo API unknown error"

def send_via_resend(api_key: str, sender_email: str, recipient_email: str, otp_code: str):
    """Send HTML OTP email via Resend HTTPS API (Port 443 - Unblocked on Render)"""
    try:
        url = "https://api.resend.com/emails"
        payload = {
            "from": sender_email or "onboarding@resend.dev",
            "to": [recipient_email],
            "subject": f"🔑 {otp_code} is your ExpenseTracker Pro Verification Code",
            "html": f"""
            <div style="font-family: sans-serif; background: #0f172a; color: #fff; padding: 30px; border-radius: 16px; text-align: center; max-width: 480px; margin: 0 auto;">
              <h2 style="color: #6366f1;">ExpenseTracker Pro</h2>
              <h3>Verification Code</h3>
              <div style="background: rgba(99,102,241,0.2); border: 1px dashed #6366f1; padding: 16px; font-size: 32px; font-weight: bold; color: #06b6d4; letter-spacing: 6px; margin: 20px 0;">{otp_code}</div>
              <p style="color: #94a3b8; font-size: 13px;">This code will expire in 10 minutes.</p>
            </div>
            """
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status in (200, 201):
                print(f"✅ OTP email sent via Resend HTTPS API to {recipient_email}")
                return True, ""
    except Exception as e:
        print(f"⚠️ Resend HTTPS API failed: {e}")
        return False, f"Resend API error: {e}"
    return False, "Resend API unknown error"

def send_otp_email(recipient_email: str, otp_code: str):
    """
    Send formatted HTML OTP Verification Email via HTTPS API or SMTP fallback.
    Returns (success: bool, error_message: str) tuple.
    """
    host, port, user, password, sender, brevo_key, resend_key = get_smtp_config()

    if not is_smtp_configured():
        print(f"\n[DEV MODE] Email unconfigured. OTP for {recipient_email}: {otp_code}\n")
        return False, "Email service not configured"

    # Try Brevo HTTPS API if key present
    if brevo_key:
        ok, err = send_via_brevo(brevo_key, sender or user, recipient_email, otp_code)
        if ok: return True, ""

    # Try Resend HTTPS API if key present
    if resend_key:
        ok, err = send_via_resend(resend_key, sender or user, recipient_email, otp_code)
        if ok: return True, ""

    # Try SMTP Protocol
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

    last_error = ""
    ports_to_try = [port, 465, 587] if port not in (465, 587) else [port, 465 if port == 587 else 587]

    for p in ports_to_try:
        try:
            print(f"Attempting SMTP connection to {host}:{p} (IPv4)...")
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
