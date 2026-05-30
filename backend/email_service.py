"""
email_service.py — RecoVibe OTP Email
═══════════════════════════════════════════════════════════════════
Strategy (Render-compatible, two-layer):

  Layer 1 — Nodemailer (Node.js subprocess)
      Calls  mailer/send_otp.js  via  node  command.
      Node.js is pre-installed on Render's Python environments.
      Passes payload as JSON through stdin, checks exit code.

  Layer 2 — Python smtplib (Gmail SMTP, always available)
      Falls back automatically if the Node.js call fails for any
      reason (Node not in PATH, auth error, network glitch, etc.).

  Layer 3 — Console fallback (never blocks registration)
      Prints OTP to logs so developers can still test.

Required .env variables:
    GMAIL_USER          — e.g.  recovibe3@gmail.com
    GMAIL_APP_PASSWORD  — 16-char Gmail App Password
                          Generate: myaccount.google.com → Security → App passwords
    MAIL_FROM_NAME      — Display name  (default: RecoVibe)
"""

import os
import json
import subprocess
import smtplib
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

GMAIL_USER     = os.getenv("GMAIL_USER") or os.getenv("GMAIL_ADDRESS", "")
GMAIL_PASS     = os.getenv("GMAIL_APP_PASSWORD") or os.getenv("GMAIL_APP_PASS", "")
FROM_NAME      = os.getenv("MAIL_FROM_NAME", "RecoVibe")

# Path to the Node.js script — relative to backend/ working dir (Render root)
_MAILER_SCRIPT = os.path.join(os.path.dirname(__file__), "mailer", "send_otp.js")


# ══════════════════════════════════════════════════════════════════
#  LAYER 1 — Nodemailer (Node.js subprocess)
# ══════════════════════════════════════════════════════════════════

def _send_via_nodemailer(name: str, email: str, otp: str) -> bool:
    """
    Invoke  mailer/send_otp.js  as a child process.
    Passes credentials through the inherited environment so they
    never appear in the command line (no shell-injection risk).
    Returns True on exit-code 0, False otherwise.
    """
    script = _MAILER_SCRIPT
    if not os.path.isfile(script):
        print(f"[Nodemailer] ⚠  Script not found: {script}")
        return False

    payload = json.dumps({"name": name, "email": email, "otp": otp})

    # Inherit the current process environment (Flask already loaded .env)
    env = os.environ.copy()

    try:
        result = subprocess.run(
            ["node", script],
            input=payload,
            capture_output=True,
            text=True,
            timeout=20,          # generous — Gmail SMTP can be slow
            env=env,
        )

        # Always surface Node.js logs in Flask/Gunicorn output
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip())

        if result.returncode == 0:
            print(f"[email_service] [OK] Nodemailer success -> {email}")
            return True

        print(f"[email_service] [FAIL] Nodemailer exited {result.returncode}")
        return False

    except FileNotFoundError:
        print("[email_service] [WARN] 'node' not found in PATH - skipping Nodemailer layer")
        return False
    except subprocess.TimeoutExpired:
        print("[email_service] [WARN] Nodemailer timed out after 20 s")
        return False
    except Exception as exc:
        print(f"[email_service] [WARN] Nodemailer subprocess error: {exc}")
        return False


# ══════════════════════════════════════════════════════════════════
#  LAYER 2 — Python smtplib (Gmail SMTP — always available on Render)
# ══════════════════════════════════════════════════════════════════

def _build_html(name: str, otp: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>Verify your RecoVibe account</title>
</head>
<body style="margin:0;padding:0;background:#0f0f0f;
             font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#0f0f0f;padding:48px 16px;">
    <tr><td align="center">
      <table width="520" cellpadding="0" cellspacing="0" border="0"
             style="background:#1a1a1a;border-radius:20px;
                    border:1px solid #2a2a2a;">

        <!-- Header -->
        <tr>
          <td style="background:#111;padding:32px 40px;
                     border-radius:20px 20px 0 0;
                     border-bottom:2px solid #F5C518;">
            <p style="margin:0;font-size:26px;font-weight:900;color:#fff;
                       font-family:Georgia,serif;">
              RecoVibe<span style="color:#F5C518;">.</span>
            </p>
            <p style="margin:4px 0 0;font-size:11px;color:#6b7280;
                       letter-spacing:0.15em;text-transform:uppercase;">
              AI-Powered Fashion
            </p>
          </td>
        </tr>

        <!-- Body -->
        <tr>
          <td style="padding:40px 40px 32px;">
            <h1 style="margin:0 0 8px;font-size:22px;color:#f9fafb;">
              Verify your email
            </h1>
            <p style="margin:0 0 32px;font-size:15px;color:#9ca3af;
                       line-height:1.7;">
              Hi <strong style="color:#f3f4f6;">{name}</strong>,<br>
              Enter the code below to activate your
              <strong style="color:#F5C518;">RecoVibe</strong> account.
              Expires in <strong style="color:#f3f4f6;">10 minutes</strong>.
            </p>

            <!-- OTP -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td align="center"
                    style="background:#111;border:2px solid #F5C518;
                           border-radius:16px;padding:36px 24px;">
                  <p style="margin:0 0 12px;font-size:11px;font-weight:700;
                             color:#6b7280;letter-spacing:0.2em;
                             text-transform:uppercase;">
                    One-Time Password
                  </p>
                  <p style="margin:0;font-size:52px;font-weight:900;
                             color:#F5C518;letter-spacing:0.4em;
                             font-family:'Courier New',monospace;">
                    {otp}
                  </p>
                  <p style="margin:12px 0 0;font-size:12px;color:#4b5563;">
                    Valid for 10 minutes only
                  </p>
                </td>
              </tr>
            </table>

            <!-- Security note -->
            <table width="100%" cellpadding="0" cellspacing="0" border="0"
                   style="margin-top:24px;">
              <tr>
                <td style="background:#1f1f1f;border-radius:12px;
                           padding:16px 20px;border-left:3px solid #F5C518;">
                  <p style="margin:0;font-size:13px;color:#6b7280;
                             line-height:1.6;">
                    🔒 <strong style="color:#9ca3af;">Security tip:</strong>
                    Never share this code. RecoVibe will never ask for your
                    OTP via phone or chat.
                  </p>
                </td>
              </tr>
            </table>

            <p style="margin:28px 0 0;font-size:13px;color:#4b5563;
                       line-height:1.6;">
              Didn't create a RecoVibe account? You can safely ignore this email.
            </p>
          </td>
        </tr>

        <!-- Footer -->
        <tr>
          <td style="padding:0 40px;">
            <hr style="border:none;border-top:1px solid #2a2a2a;margin:0;">
          </td>
        </tr>
        <tr>
          <td style="padding:24px 40px;border-radius:0 0 20px 20px;">
            <p style="margin:0;font-size:12px;color:#374151;text-align:center;">
              &copy; 2026 RecoVibe &nbsp;&middot;&nbsp;
              AI-powered fashion recommendations
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _send_via_python_smtp(name: str, email: str, otp: str) -> bool:
    """
    Pure Python Gmail SMTP fallback.
    Uses smtplib — zero extra dependencies, 100 % Render-compatible.
    """
    if not GMAIL_USER or not GMAIL_PASS:
        print("[email_service] [FAIL] GMAIL_USER / GMAIL_APP_PASSWORD not set - cannot send email")
        return False

    try:
        msg             = MIMEMultipart("alternative")
        msg["Subject"]  = f"{otp} is your RecoVibe verification code"
        msg["From"]     = f"{FROM_NAME} <{GMAIL_USER}>"
        msg["To"]       = email

        plain = (
            f"Hi {name},\n\n"
            f"Your RecoVibe verification code is:\n\n"
            f"    {otp}\n\n"
            f"This code expires in 10 minutes.\n"
            f"Do not share it with anyone.\n\n"
            f"If you didn't create a RecoVibe account, ignore this email.\n\n"
            f"— The RecoVibe Team"
        )

        msg.attach(MIMEText(plain,              "plain"))
        msg.attach(MIMEText(_build_html(name, otp), "html"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(GMAIL_USER, GMAIL_PASS)
            server.sendmail(GMAIL_USER, email, msg.as_string())

        print(f"[email_service] [OK] Python SMTP success -> {email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print(
            "[email_service] [FAIL] SMTP auth failed - check GMAIL_USER + GMAIL_APP_PASSWORD\n"
            "                   Generate at: myaccount.google.com -> Security -> App passwords"
        )
        return False
    except smtplib.SMTPException as exc:
        print(f"[email_service] [FAIL] SMTP error: {exc}")
        return False
    except Exception as exc:
        print(f"[email_service] [FAIL] Unexpected SMTP error: {exc}")
        traceback.print_exc()
        return False


# ══════════════════════════════════════════════════════════════════
#  PUBLIC API — called by auth_routes.py (signature unchanged)
# ══════════════════════════════════════════════════════════════════

def send_otp_email(name: str, email: str, otp: str) -> bool:
    """
    Try Nodemailer first, fall back to Python SMTP.
    Returns True if the email was delivered by either method.
    """
    print(f"[email_service] Sending OTP to {email} ...")

    # Layer 1 — Nodemailer
    if _send_via_nodemailer(name, email, otp):
        return True

    # Layer 2 — Python smtplib
    print("[email_service] Falling back to Python SMTP ...")
    if _send_via_python_smtp(name, email, otp):
        return True

    # Layer 3 — Console (never blocks registration)
    print(f"[email_service] [WARN] ALL delivery methods failed.")
    print(f"[email_service] [DEBUG] OTP for {email}: {otp}")
    return False


def send_otp(name: str, email: str, otp: str) -> dict:
    """
    Entry point called by auth_routes.py — signature unchanged from
    the previous Mailjet version so no changes are needed in auth_routes.
    """
    success = send_otp_email(name, email, otp)
    method  = "nodemailer/smtp" if success else "failed"
    errors  = [] if success else ["All email delivery layers failed - check server logs"]

    return {
        "email_sent": success,
        "method":     method,
        "errors":     errors,
    }


def test_connection() -> bool:
    """Quick credential check — run  python email_service.py  to verify."""
    print("=== RecoVibe Email Service ===")
    print(f"  GMAIL_USER         : {GMAIL_USER or '(not set)'}")
    print(f"  GMAIL_APP_PASSWORD : {'[OK] set' if GMAIL_PASS else '(not set)'}")
    print(f"  FROM_NAME          : {FROM_NAME}")
    print(f"  Nodemailer script  : {_MAILER_SCRIPT}")
    print(f"  Script exists      : {os.path.isfile(_MAILER_SCRIPT)}")
    return bool(GMAIL_USER and GMAIL_PASS)


if __name__ == "__main__":
    if test_connection():
        test_email = input("\nEnter email to send test OTP (Enter to skip): ").strip()
        if test_email:
            result = send_otp("Test User", test_email, "857341")
            print(f"\nResult: {result}")
    else:
        print("\n[FAIL] Credentials not configured - set GMAIL_USER and GMAIL_APP_PASSWORD in .env")