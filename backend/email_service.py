"""
email_service.py — MailerSend HTTP API
Works on Render (HTTPS port 443, never blocked)
Free: 3000 emails/month, no domain needed (use trial domain)
"""
import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

MAILERSEND_API_KEY = os.getenv("MAILERSEND_API_KEY", "")
MAIL_FROM_NAME     = os.getenv("MAIL_FROM_NAME",  "RecoVibe")
MAIL_FROM_EMAIL    = os.getenv("MAIL_FROM_EMAIL", "")


def send_otp_email(name: str, email: str, otp: str) -> bool:
    if not MAILERSEND_API_KEY:
        print("[OTP] ERROR: MAILERSEND_API_KEY not set")
        print(f"[OTP] OTP for {email} (debug): {otp}")
        return False

    if not MAIL_FROM_EMAIL:
        print("[OTP] ERROR: MAIL_FROM_EMAIL not set")
        print(f"[OTP] OTP for {email} (debug): {otp}")
        return False

    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Your OTP</title></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:48px 16px;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0"
             style="background:#fff;border-radius:16px;border:1px solid #e5e7eb;">
        <tr>
          <td style="background:#111;padding:28px 36px;border-radius:16px 16px 0 0;">
            <p style="margin:0;font-size:26px;font-weight:900;color:#fff;font-family:Georgia,serif;">
              RecoVibe<span style="color:#F5C518;">.</span>
            </p>
            <p style="margin:6px 0 0;font-size:12px;color:#9ca3af;letter-spacing:.1em;text-transform:uppercase;">
              AI-Powered Fashion
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:40px 36px 32px;">
            <h1 style="margin:0 0 12px;font-size:22px;font-weight:700;color:#111827;">
              Verify your email
            </h1>
            <p style="margin:0 0 32px;font-size:15px;color:#6b7280;line-height:1.7;">
              Hi <strong style="color:#111827;">{name}</strong>,<br>
              Enter the code below to complete your
              <strong style="color:#111827;">RecoVibe</strong> account setup.
              Expires in <strong style="color:#111827;">10 minutes</strong>.
            </p>
            <table width="100%" cellpadding="0" cellspacing="0">
              <tr>
                <td align="center"
                    style="background:#f9fafb;border:2px dashed #d1d5db;
                           border-radius:12px;padding:32px 24px;">
                  <p style="margin:0 0 8px;font-size:11px;font-weight:700;
                             color:#9ca3af;letter-spacing:.2em;text-transform:uppercase;">
                    One-Time Password
                  </p>
                  <p style="margin:0;font-size:48px;font-weight:900;color:#111827;
                             letter-spacing:.3em;font-family:'Courier New',monospace;">
                    {otp}
                  </p>
                </td>
              </tr>
            </table>
            <p style="margin:28px 0 0;font-size:13px;color:#9ca3af;line-height:1.6;">
              If you didn't create a RecoVibe account, ignore this email.
              Never share this code with anyone.
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:0 36px;">
            <hr style="border:none;border-top:1px solid #f3f4f6;margin:0;">
          </td>
        </tr>
        <tr>
          <td style="padding:24px 36px;border-radius:0 0 16px 16px;">
            <p style="margin:0;font-size:12px;color:#d1d5db;text-align:center;">
              &copy; 2026 RecoVibe &middot; AI-powered fashion recommendations
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    plain_text = (
        f"Hi {name},\n\n"
        f"Your RecoVibe verification code is: {otp}\n\n"
        f"Expires in 10 minutes. Do not share it.\n\n"
        f"— The RecoVibe Team"
    )

    payload = json.dumps({
        "from": {
            "email": MAIL_FROM_EMAIL,
            "name":  MAIL_FROM_NAME,
        },
        "to": [{"email": email, "name": name}],
        "subject": "Your RecoVibe verification code",
        "html": html_body,
        "text": plain_text,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.mailersend.com/v1/email",
        data=payload,
        headers={
            "Authorization": f"Bearer {MAILERSEND_API_KEY}",
            "Content-Type":  "application/json",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            status = res.getcode()
        print(f"[OTP MailerSend] Sent to {email} ✓  status={status}")
        return True

    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"[OTP MailerSend] HTTP {e.code}: {err}")
        print(f"[OTP MailerSend] OTP for {email} (debug): {otp}")
        return False

    except Exception as e:
        print(f"[OTP MailerSend] Error: {e}")
        print(f"[OTP MailerSend] OTP for {email} (debug): {otp}")
        return False


def send_otp(name: str, email: str, otp: str) -> dict:
    success = send_otp_email(name, email, otp)
    if success:
        return {"email_sent": True,  "method": "mailersend", "errors": []}
    else:
        return {"email_sent": False, "method": "failed",
                "errors": ["MailerSend delivery failed — check logs"]}


def test_connection() -> bool:
    print("Testing MailerSend API...")
    print(f"  API key : {'set ✓' if MAILERSEND_API_KEY else 'NOT SET ✗'}")
    print(f"  From    : {MAIL_FROM_NAME} <{MAIL_FROM_EMAIL}>")

    if not MAILERSEND_API_KEY:
        print("\n  ERROR: MAILERSEND_API_KEY not set in .env")
        return False

    req = urllib.request.Request(
        "https://api.mailersend.com/v1/domains",
        headers={
            "Authorization": f"Bearer {MAILERSEND_API_KEY}",
            "Content-Type":  "application/json",
            "User-Agent": "Mozilla/5.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            body = json.loads(r.read().decode())
        domains = [d.get("name") for d in body.get("data", [])]
        print(f"\n  Connection OK ✓")
        print(f"  Available domains: {domains}")
        print(f"\n  Use one of these as MAIL_FROM_EMAIL domain!")
        return True
    except urllib.error.HTTPError as e:
        print(f"\n  HTTP {e.code}: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"\n  ERROR: {e}")
        return False


if __name__ == "__main__":
    if test_connection():
        TEST_EMAIL = input("\nEnter email to send test OTP (or press Enter to skip): ").strip()
        if TEST_EMAIL:
            result = send_otp("Test User", TEST_EMAIL, "123456")
            print(f"\nResult: {result}")