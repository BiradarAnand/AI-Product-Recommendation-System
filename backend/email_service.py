"""
email_service.py
─────────────────
Gmail SMTP with App Password.
Works locally + on Render (port 465 SSL is never blocked).

Setup:
    1. Go to https://myaccount.google.com/apppasswords
    2. Select app: Mail, device: Other → name it "RecoVibe"
    3. Copy the 16-character password (e.g. "abcd efgh ijkl mnop")
    4. Add to .env:
         GMAIL_USER=recovibe01@gmail.com
         GMAIL_APP_PASSWORD=abcdefghijklmnop
         MAIL_FROM_NAME=RecoVibe
         MAIL_FROM_EMAIL=recovibe01@gmail.com
"""
import os
import ssl
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER       = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASS   = os.getenv("GMAIL_APP_PASSWORD", "").replace(" ", "")
MAIL_FROM_NAME   = os.getenv("MAIL_FROM_NAME",  "RecoVibe")
MAIL_FROM_EMAIL  = os.getenv("MAIL_FROM_EMAIL", GMAIL_USER)


def send_otp_email(name: str, email: str, otp: str) -> bool:
    if not GMAIL_USER or not GMAIL_APP_PASS:
        print("[OTP Gmail] ERROR: GMAIL_USER or GMAIL_APP_PASSWORD not set in .env")
        print(f"[OTP Gmail] OTP for {email} (debug): {otp}")
        return False

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your OTP Code</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#f3f4f6;padding:48px 16px;">
    <tr>
      <td align="center">
        <table width="520" cellpadding="0" cellspacing="0" border="0"
               style="background:#ffffff;border-radius:16px;border:1px solid #e5e7eb;
                      box-shadow:0 4px 6px rgba(0,0,0,0.05);">

          <!-- Header -->
          <tr>
            <td style="background:#111111;padding:28px 36px;border-radius:16px 16px 0 0;">
              <p style="margin:0;font-size:26px;font-weight:900;color:#ffffff;
                         letter-spacing:-0.5px;font-family:Georgia,'Times New Roman',serif;">
                RecoVibe<span style="color:#F5C518;">.</span>
              </p>
              <p style="margin:6px 0 0;font-size:12px;color:#9ca3af;
                         letter-spacing:0.1em;text-transform:uppercase;">
                AI-Powered Fashion
              </p>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:40px 36px 32px;">
              <h1 style="margin:0 0 12px;font-size:22px;font-weight:700;color:#111827;">
                Verify your email
              </h1>
              <p style="margin:0 0 32px;font-size:15px;color:#6b7280;line-height:1.7;">
                Hi <strong style="color:#111827;">{name}</strong>,<br>
                Enter the code below to complete your
                <strong style="color:#111827;">RecoVibe</strong> account setup.
                This code expires in <strong style="color:#111827;">10 minutes</strong>.
              </p>

              <!-- OTP Block -->
              <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center"
                      style="background:#f9fafb;border:2px dashed #d1d5db;
                             border-radius:12px;padding:32px 24px;">
                    <p style="margin:0 0 8px;font-size:11px;font-weight:700;
                               color:#9ca3af;letter-spacing:0.2em;text-transform:uppercase;">
                      One-Time Password
                    </p>
                    <p style="margin:0;font-size:48px;font-weight:900;color:#111827;
                               letter-spacing:0.3em;
                               font-family:'Courier New',Courier,monospace;">
                      {otp}
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:28px 0 0;font-size:13px;color:#9ca3af;line-height:1.6;">
                If you didn't create a RecoVibe account, you can safely ignore this email.
                Never share this code with anyone — our team will never ask for it.
              </p>
            </td>
          </tr>

          <!-- Divider -->
          <tr>
            <td style="padding:0 36px;">
              <hr style="border:none;border-top:1px solid #f3f4f6;margin:0;">
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="padding:24px 36px;border-radius:0 0 16px 16px;">
              <p style="margin:0;font-size:12px;color:#d1d5db;
                         text-align:center;line-height:1.6;">
                &copy; 2026 RecoVibe &nbsp;&middot;&nbsp;
                AI-powered fashion recommendations
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    plain_text = (
        f"Hi {name},\n\n"
        f"Your RecoVibe verification code is:\n\n"
        f"    {otp}\n\n"
        f"This code expires in 10 minutes.\n"
        f"Do not share it with anyone.\n\n"
        f"If you didn't create a RecoVibe account, ignore this email.\n\n"
        f"— The RecoVibe Team"
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your RecoVibe verification code"
    msg["From"]    = formataddr((MAIL_FROM_NAME, MAIL_FROM_EMAIL))
    msg["To"]      = email
    msg["X-Mailer"] = "RecoVibe/1.0"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,  "html",  "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as server:
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            server.sendmail(MAIL_FROM_EMAIL, [email], msg.as_string())

        print(f"[OTP Gmail] Sent to {email} ✓")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[OTP Gmail] Authentication failed.")
        print("  → Make sure 2-Step Verification is ON for your Google account")
        print("  → Go to https://myaccount.google.com/apppasswords")
        print("  → Generate app password for 'Mail' and update GMAIL_APP_PASSWORD in .env")
        print(f"[OTP Gmail] OTP for {email} (debug): {otp}")
        return False

    except smtplib.SMTPRecipientsRefused:
        print(f"[OTP Gmail] Recipient refused: {email}")
        return False

    except smtplib.SMTPException as e:
        print(f"[OTP Gmail] SMTP error: {e}")
        print(f"[OTP Gmail] OTP for {email} (debug): {otp}")
        return False

    except Exception as e:
        print(f"[OTP Gmail] Unexpected error: {e}")
        print(f"[OTP Gmail] OTP for {email} (debug): {otp}")
        return False


def send_otp(name: str, email: str, otp: str) -> dict:
    success = send_otp_email(name, email, otp)
    if success:
        return {"email_sent": True,  "method": "gmail_smtp", "errors": []}
    else:
        return {"email_sent": False, "method": "failed",
                "errors": ["Gmail SMTP delivery failed — check server logs"]}


def test_connection() -> bool:
    print("Testing Gmail SMTP connection...")
    print(f"  User : {GMAIL_USER or '(not set)'}")
    print(f"  Pass : {'set' if GMAIL_APP_PASS else '(not set)'}")
    print(f"  From : {MAIL_FROM_NAME} <{MAIL_FROM_EMAIL}>")

    if not GMAIL_USER or not GMAIL_APP_PASS:
        print("  ERROR: GMAIL_USER or GMAIL_APP_PASSWORD not set in .env")
        return False

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=30) as server:
            server.ehlo()
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            print("  Connection OK ✓")
            return True

    except smtplib.SMTPAuthenticationError:
        print("  ERROR: Authentication failed")
        print("  → Enable 2-Step Verification on your Google account first")
        print("  → Then generate an App Password at https://myaccount.google.com/apppasswords")
        return False

    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    if test_connection():
        TEST_EMAIL = input("\nEnter email to send test OTP (or press Enter to skip): ").strip()
        if TEST_EMAIL:
            result = send_otp("Test User", TEST_EMAIL, "123456")
            print(f"\nResult: {result}")