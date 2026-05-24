# test_gmail.py
# Run this file to check if your Gmail credentials work
# Command: python test_gmail.py

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# ── Put your credentials here OR load from .env ──────────────────
GMAIL_ADDRESS = os.getenv("GMAIL_ADDRESS") or "your_gmail@gmail.com"
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS") or "your_16_char_app_password"
TEST_SEND_TO   = GMAIL_ADDRESS  # sends test email to yourself


def test_gmail():
    print("=" * 50)
    print("Gmail SMTP Credentials Test")
    print("=" * 50)
    print(f"Gmail Address : {GMAIL_ADDRESS}")
    print(f"App Password  : {'*' * len(GMAIL_APP_PASS) if GMAIL_APP_PASS else 'NOT SET'}")
    print()

    # Step 1: Check if credentials are set
    if not GMAIL_ADDRESS or GMAIL_ADDRESS == "your_gmail@gmail.com":
        print("❌ GMAIL_ADDRESS is not set!")
        print("   Fix: Set GMAIL_ADDRESS=yourname@gmail.com in .env or Render")
        return False

    if not GMAIL_APP_PASS or GMAIL_APP_PASS == "your_16_char_app_password":
        print("❌ GMAIL_APP_PASS is not set!")
        print("   Fix: Generate App Password at:")
        print("   https://myaccount.google.com → Security → 2-Step Verification → App passwords")
        return False

    if len(GMAIL_APP_PASS.replace(" ", "")) != 16:
        print(f"⚠️  App Password length looks wrong: {len(GMAIL_APP_PASS.replace(' ', ''))} chars (should be 16)")
        print("   Make sure you copied the full 16-character App Password")

    # Step 2: Try connecting to Gmail SMTP
    print("Step 1: Connecting to smtp.gmail.com:587 ...")
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=10)
        server.ehlo()
        print("✅ Connected to Gmail SMTP server")
    except Exception as e:
        print(f"❌ Cannot connect to Gmail: {e}")
        print("   Check your internet connection or firewall")
        return False

    # Step 3: Try STARTTLS
    print("Step 2: Starting TLS encryption ...")
    try:
        server.starttls()
        print("✅ TLS started")
    except Exception as e:
        print(f"❌ TLS failed: {e}")
        server.quit()
        return False

    # Step 4: Try logging in
    print("Step 3: Logging in with credentials ...")
    try:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASS)
        print("✅ Login successful!")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Authentication failed!")
        print()
        print("   This means your App Password is WRONG. Here's how to fix it:")
        print()
        print("   1. Go to: https://myaccount.google.com")
        print("   2. Click 'Security' on the left")
        print("   3. Make sure '2-Step Verification' is ON")
        print("   4. Click '2-Step Verification'")
        print("   5. Scroll down → 'App passwords'")
        print("   6. Select app: 'Mail', device: 'Other' → type 'RecoVibe'")
        print("   7. Click 'Generate'")
        print("   8. Copy the 16-character password shown (e.g. abcd efgh ijkl mnop)")
        print("   9. Use THAT as GMAIL_APP_PASS (with or without spaces)")
        print()
        print("   ⚠️  Do NOT use your regular Gmail password!")
        print("   ⚠️  Do NOT use 2FA codes — use App Password only!")
        server.quit()
        return False
    except Exception as e:
        print(f"❌ Login error: {e}")
        server.quit()
        return False

    # Step 5: Send a test email
    print(f"Step 4: Sending test email to {TEST_SEND_TO} ...")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "✅ RecoVibe SMTP Test - Working!"
        msg["From"]    = GMAIL_ADDRESS
        msg["To"]      = TEST_SEND_TO

        html = """
        <div style="font-family:Arial,sans-serif;max-width:400px;padding:24px;
                    border:2px solid #22c55e;border-radius:12px;">
            <h2 style="color:#16a34a;">✅ Gmail SMTP is Working!</h2>
            <p>Your RecoVibe backend can send OTP emails successfully.</p>
            <p style="color:#6b7280;font-size:13px;">
                This is a test email from your test_gmail.py script.
            </p>
        </div>"""

        msg.attach(MIMEText("Gmail SMTP is working! RecoVibe can send OTP emails.", "plain"))
        msg.attach(MIMEText(html, "html"))

        server.sendmail(GMAIL_ADDRESS, TEST_SEND_TO, msg.as_string())
        server.quit()

        print(f"✅ Test email sent to {TEST_SEND_TO}!")
        print()
        print("=" * 50)
        print("🎉 ALL CHECKS PASSED — Gmail is working!")
        print("   Copy these to your Render environment variables:")
        print(f"   GMAIL_ADDRESS = {GMAIL_ADDRESS}")
        print(f"   GMAIL_APP_PASS = {GMAIL_APP_PASS}")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        server.quit()
        return False


if __name__ == "__main__":
    test_gmail()