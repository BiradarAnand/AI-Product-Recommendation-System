# """
# otp_service.py
# ──────────────
# OTP generation + Email (Gmail) + SMS
# - Indian numbers: Fast2SMS (free, no verification needed)
# - International: Twilio
# """

# import os
# import random
# import smtplib
# from datetime import datetime, timedelta
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart


# def generate_otp() -> str:
#     return str(random.randint(100000, 999999))


# def otp_expiry() -> datetime:
#     return datetime.utcnow() + timedelta(minutes=10)


# def is_otp_valid(user_input: str, stored_otp: str, expires_at) -> tuple:
#     if str(user_input).strip() != str(stored_otp).strip():
#         return False, "Incorrect OTP. Please try again."
#     if datetime.utcnow() > expires_at:
#         return False, "OTP has expired. Please request a new one."
#     return True, ""


# # ── EMAIL ─────────────────────────────────────────────────────────

# def send_otp_email(name: str, email: str, otp: str) -> bool:
#     gmail_address = os.getenv("GMAIL_ADDRESS", "biradaranand025@gmail.com")
#     gmail_pass    = os.getenv("GMAIL_APP_PASS",  "vmwv hqel teiw lncf")

#     if not gmail_address or not gmail_pass:
#         print("[OTP Email] GMAIL credentials missing in .env")
#         return False

#     try:
#         msg            = MIMEMultipart("alternative")
#         msg["Subject"] = "Your OTP Code"
#         msg["From"]    = gmail_address
#         msg["To"]      = email

#         plain = f"Hi {name},\n\nYour OTP is: {otp}\n\nExpires in 10 minutes."
#         html  = f"""
#         <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
#                     padding:32px;border:1px solid #e5e7eb;border-radius:12px;">
#             <h2 style="color:#1f2937;">Your OTP Code</h2>
#             <p style="color:#6b7280;">Hi {name}, use this code to verify your account:</p>
#             <div style="font-size:40px;font-weight:bold;letter-spacing:14px;
#                         text-align:center;padding:24px;background:#f9fafb;
#                         border-radius:8px;color:#1f2937;">{otp}</div>
#             <p style="color:#9ca3af;font-size:13px;margin-top:20px;">
#                 Expires in 10 minutes. Do not share with anyone.
#             </p>
#         </div>"""

#         msg.attach(MIMEText(plain, "plain"))
#         msg.attach(MIMEText(html,  "html"))
        
#         with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
#             server.ehlo()
#             server.starttls()
#             server.login(gmail_address, gmail_pass)
#             server.sendmail(gmail_address, email, msg.as_string())

#         print(f"[OTP Email] Sent to {email}")
#         return True

#     except Exception as e:
#         print(f"[OTP Email] Failed: {e}")
#         return False


# # ── SMS — routes Indian → Fast2SMS, International → Twilio ────────

# def send_otp_sms(phone: str, otp: str) -> bool:
#     phone = phone.strip().replace(" ", "").replace("-", "")

#     # Indian number → Fast2SMS (free, works for ALL Indian numbers)
#     if not phone.startswith("+") or phone.startswith("+91"):
#         return _send_fast2sms(phone, otp)
#     else:
#         # International → Twilio
#         return _send_twilio(phone, otp)


# def _send_fast2sms(phone: str, otp: str) -> bool:
#     """
#     Fast2SMS — free Indian SMS service.
#     Works for ALL Indian numbers without verification.
#     Get free API key at: fast2sms.com -> Dev API
#     Add to .env: FAST2SMS_API_KEY=your_key
#     """
#     import urllib.request
#     import json

#     api_key = os.getenv("FAST2SMS_API_KEY", "")
#     if not api_key:
#         print("[OTP SMS] FAST2SMS_API_KEY not set in .env")
#         print("          Get free key at fast2sms.com -> Dev API")
#         return False

#     # Fast2SMS needs 10-digit number only
#     number = phone.replace("+91", "").replace("+", "").lstrip("0")
#     if len(number) != 10:
#         print(f"[OTP SMS] Invalid Indian number format: {phone}")
#         return False

#     try:
#         payload = json.dumps({
#             "route":             "otp",
#             "variables_values":  otp,
#             "numbers":           number,
#         }).encode("utf-8")

#         req = urllib.request.Request(
#             "https://www.fast2sms.com/dev/bulkV2",
#             data=payload,
#             headers={
#                 "authorization": api_key,
#                 "Content-Type":  "application/json",
#             },
#             method="POST"
#         )

#         with urllib.request.urlopen(req, timeout=10) as res:
#             response = json.loads(res.read().decode())

#         if response.get("return") is True:
#             print(f"[OTP SMS Fast2SMS] Sent to +91{number} ✓")
#             return True
#         else:
#             print(f"[OTP SMS Fast2SMS] Failed: {response.get('message', 'Unknown')}")
#             return False

#     except Exception as e:
#         print(f"[OTP SMS Fast2SMS] Error: {e}")
#         return False


# def _send_twilio(phone: str, otp: str) -> bool:
#     """Twilio — for international numbers."""
#     account_sid = os.getenv("TWILIO_ACCOUNT_SID",  "")
#     auth_token  = os.getenv("TWILIO_AUTH_TOKEN",   "")
#     from_number = os.getenv("TWILIO_PHONE_NUMBER", "")

#     if not account_sid or not auth_token or not from_number:
#         print("[OTP SMS Twilio] Missing credentials in .env")
#         return False

#     try:
#         from twilio.rest import Client
#         client  = Client(account_sid, auth_token)
#         message = client.messages.create(
#             body=f"Your OTP is: {otp}. Valid for 10 minutes.",
#             from_=from_number,
#             to=phone
#         )
#         print(f"[OTP SMS Twilio] Sent to {phone} — SID: {message.sid}")
#         return True
#     except Exception as e:
#         print(f"[OTP SMS Twilio] Failed: {e}")
#         return False


# # ── MAIN ──────────────────────────────────────────────────────────

# def send_otp(name: str, email: str, phone: str, otp: str, channel: str) -> dict:
#     email_sent = False
#     sms_sent   = False
#     errors     = []

#     if channel in ("email", "both"):
#         email_sent = send_otp_email(name, email, otp)
#         if not email_sent:
#             errors.append("Email delivery failed")

#     if channel in ("sms", "both"):
#         if phone:
#             sms_sent = send_otp_sms(phone, otp)
#             if not sms_sent:
#                 errors.append("SMS delivery failed — check Flask terminal")
#         else:
#             errors.append("Phone number required for SMS")

#     return {"email_sent": email_sent, "sms_sent": sms_sent, "errors": errors}

"""
otp_service.py
──────────────
OTP generation + Email (Gmail SMTP only)

Required .env variables:
    GMAIL_ADDRESS   — your Gmail address
    GMAIL_APP_PASS  — 16-char Gmail App Password (NOT your account password)
                      Generate at: myaccount.google.com -> Security -> App passwords
"""

import os
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# ── OTP CORE ──────────────────────────────────────────────────────

def generate_otp() -> str:
    return str(random.randint(100000, 999999))


def otp_expiry() -> datetime:
    return datetime.utcnow() + timedelta(minutes=10)


def is_otp_valid(user_input: str, stored_otp: str, expires_at: datetime) -> tuple:
    if str(user_input).strip() != str(stored_otp).strip():
        return False, "Incorrect OTP. Please try again."
    if datetime.utcnow() > expires_at:
        return False, "OTP has expired. Please request a new one."
    return True, ""


# ── EMAIL ─────────────────────────────────────────────────────────

def send_otp_email(name: str, email: str, otp: str) -> bool:
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_pass    = os.getenv("GMAIL_APP_PASS")

    if not gmail_address or not gmail_pass:
        print("[OTP Email] ERROR: GMAIL_ADDRESS or GMAIL_APP_PASS not set in .env")
        return False

    try:
        msg            = MIMEMultipart("alternative")
        msg["Subject"] = "Your OTP Code"
        msg["From"]    = gmail_address
        msg["To"]      = email

        plain = (
            f"Hi {name},\n\n"
            f"Your OTP is: {otp}\n\n"
            f"It expires in 10 minutes. Do not share it with anyone."
        )
        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                    padding:32px;border:1px solid #e5e7eb;border-radius:12px;">
            <h2 style="color:#1f2937;">Your OTP Code</h2>
            <p style="color:#6b7280;">Hi {name}, use this code to verify your account:</p>
            <div style="font-size:40px;font-weight:bold;letter-spacing:14px;
                        text-align:center;padding:24px;background:#f9fafb;
                        border-radius:8px;color:#1f2937;">{otp}</div>
            <p style="color:#9ca3af;font-size:13px;margin-top:20px;">
                Expires in 10 minutes. Do not share with anyone.
            </p>
        </div>"""

        msg.attach(MIMEText(plain, "plain"))
        msg.attach(MIMEText(html,  "html"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_address, gmail_pass)
            server.sendmail(gmail_address, email, msg.as_string())

        print(f"[OTP Email] Sent to {email} ✓")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[OTP Email] Authentication failed — check GMAIL_ADDRESS and GMAIL_APP_PASS in .env")
        return False
    except smtplib.SMTPException as e:
        print(f"[OTP Email] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[OTP Email] Unexpected error: {e}")
        return False


# ── MAIN ENTRY POINT ──────────────────────────────────────────────

def send_otp(name: str, email: str, otp: str) -> dict:
    """
    Send OTP via email.

    Returns:
        {
            "email_sent": bool,
            "errors":     list[str]
        }
    """
    errors = []

    email_sent = send_otp_email(name, email, otp)
    if not email_sent:
        errors.append("Email delivery failed — check Flask terminal for details")

    return {
        "email_sent": email_sent,
        "errors":     errors,
    }