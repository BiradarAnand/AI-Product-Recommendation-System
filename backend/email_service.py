"""
email_service.py
─────────────────
Brevo (formerly Sendinblue) SMTP email service.
No domain verification required — works immediately on free plan.

Free plan: 300 emails/day, no credit card needed.

Setup:
    1. Sign up at brevo.com
    2. Go to: Top-right menu → SMTP & API → SMTP tab
    3. Copy your Login and Password (SMTP key)
    4. Add to .env:
         BREVO_SMTP_HOST=smtp-relay.brevo.com
         BREVO_SMTP_PORT=587
         BREVO_SMTP_LOGIN=your_brevo_account@email.com
         BREVO_SMTP_PASSWORD=xsmtpsib-xxxxxxxxxxxxxxxxxxxx
         MAIL_FROM_NAME=RecoVibe
         MAIL_FROM_EMAIL=your_brevo_account@email.com
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from dotenv import load_dotenv
import ssl
load_dotenv()

# ── Brevo SMTP config ─────────────────────────────────────────────
SMTP_HOST      = os.getenv("BREVO_SMTP_HOST",     "smtp-relay.brevo.com")
SMTP_PORT      = int(os.getenv("BREVO_SMTP_PORT", 587))
SMTP_LOGIN     = os.getenv("BREVO_SMTP_LOGIN",    "")   # your Brevo account email
SMTP_PASSWORD  = os.getenv("BREVO_SMTP_PASSWORD", "")   # SMTP key from Brevo dashboard
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME",  "recovibe")
MAIL_FROM_EMAIL= os.getenv("MAIL_FROM_EMAIL", SMTP_LOGIN)

context = ssl.create_default_context()

def send_otp_email(name: str, email: str, otp: str) -> bool:
    """
    Send OTP verification email via Brevo SMTP.

    Args:
        name  : recipient's display name
        email : recipient's email address
        otp   : 6-digit OTP string

    Returns:
        True if sent successfully, False on failure.
        Never raises — registration always succeeds even if email fails.
    """
    if not SMTP_LOGIN or not SMTP_PASSWORD:
        print("[OTP Brevo] ERROR: BREVO_SMTP_LOGIN or BREVO_SMTP_PASSWORD not set in .env")
        print(f"[OTP Brevo] OTP for {email} (debug only): {otp}")
        return False

    # ── HTML email body ───────────────────────────────────────────
    html_body = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your OTP Code</title>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;
             font-family:Arial,Helvetica,sans-serif;">

  <table width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background-color:#f3f4f6;padding:48px 16px;">
    <tr>
      <td align="center">

        <!-- Card -->
        <table width="520" cellpadding="0" cellspacing="0" border="0"
               style="background:#ffffff;border-radius:16px;
                      border:1px solid #e5e7eb;
                      box-shadow:0 4px 6px rgba(0,0,0,0.05);">

          <!-- ── Header ───────────────────────────── -->
          <tr>
            <td style="background:#111111;padding:28px 36px;
                        border-radius:16px 16px 0 0;">
              <p style="margin:0;font-size:26px;font-weight:900;
                         color:#ffffff;letter-spacing:-0.5px;
                         font-family:Georgia,'Times New Roman',serif;">
                RecoVibe<span style="color:#F5C518;">.</span>
              </p>
              <p style="margin:6px 0 0;font-size:12px;color:#9ca3af;
                         letter-spacing:0.1em;text-transform:uppercase;">
                AI-Powered Fashion
              </p>
            </td>
          </tr>

          <!-- ── Body ─────────────────────────────── -->
          <tr>
            <td style="padding:40px 36px 32px;">

              <h1 style="margin:0 0 12px;font-size:22px;font-weight:700;
                          color:#111827;">
                Verify your email
              </h1>

              <p style="margin:0 0 32px;font-size:15px;color:#6b7280;
                         line-height:1.7;">
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
                               color:#9ca3af;letter-spacing:0.2em;
                               text-transform:uppercase;">
                      One-Time Password
                    </p>
                    <p style="margin:0;font-size:48px;font-weight:900;
                               color:#111827;letter-spacing:0.3em;
                               font-family:'Courier New',Courier,monospace;">
                      {otp}
                    </p>
                  </td>
                </tr>
              </table>

              <p style="margin:28px 0 0;font-size:13px;color:#9ca3af;
                         line-height:1.6;">
                If you didn't create a RecoVibe account, you can safely
                ignore this email. Never share this code with anyone —
                our team will never ask for it.
              </p>

            </td>
          </tr>

          <!-- ── Divider ───────────────────────────── -->
          <tr>
            <td style="padding:0 36px;">
              <hr style="border:none;border-top:1px solid #f3f4f6;margin:0;">
            </td>
          </tr>

          <!-- ── Footer ───────────────────────────── -->
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
        <!-- /Card -->

      </td>
    </tr>
  </table>

</body>
</html>"""

    # ── Plain text fallback ───────────────────────────────────────
    plain_text = (
        f"Hi {name},\n\n"
        f"Your RecoVibe verification code is:\n\n"
        f"    {otp}\n\n"
        f"This code expires in 10 minutes.\n"
        f"Do not share it with anyone.\n\n"
        f"If you didn't create a RecoVibe account, ignore this email.\n\n"
        f"— The RecoVibe Team"
    )

    # ── Build MIME message ────────────────────────────────────────
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Your RecoVibe verification code"
    msg["From"]    = formataddr((MAIL_FROM_NAME, MAIL_FROM_EMAIL))
    msg["To"]      = email
    msg["X-Mailer"] = "RecoVibe/1.0"

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_body,  "html",  "utf-8"))

    # ── Send via Brevo SMTP (STARTTLS on port 587) ────────────────
    try:
       with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context, timeout=20) as server:
            server.ehlo()
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            server.sendmail(MAIL_FROM_EMAIL, [email], msg.as_string())

            print(f"[OTP Brevo] Sent to {email} ✓")
            return True

    except smtplib.SMTPAuthenticationError:
        print(
            "[OTP Brevo] Authentication failed.\n"
            "  → Check BREVO_SMTP_LOGIN (your Brevo account email)\n"
            "  → Check BREVO_SMTP_PASSWORD (SMTP key from Brevo dashboard,\n"
            "    NOT your account password — it starts with 'xsmtpsib-')"
        )
        print(f"[OTP Brevo] OTP for {email} (debug only): {otp}")
        return False

    except smtplib.SMTPRecipientsRefused:
        print(f"[OTP Brevo] Recipient refused: {email}")
        return False

    except smtplib.SMTPException as e:
        print(f"[OTP Brevo] SMTP error: {e}")
        print(f"[OTP Brevo] OTP for {email} (debug only): {otp}")
        return False

    except Exception as e:
        print(f"[OTP Brevo] Unexpected error: {e}")
        print(f"[OTP Brevo] OTP for {email} (debug only): {otp}")
        return False


def send_otp(name: str, email: str, otp: str) -> dict:
    """
    Main entry point called by auth_routes.py.

    Returns:
        {
            "email_sent": bool,
            "method":     "brevo_smtp" | "failed",
            "errors":     list[str]
        }
    """
    success = send_otp_email(name, email, otp)

    if success:
        return {"email_sent": True,  "method": "brevo_smtp", "errors": []}
    else:
        return {"email_sent": False, "method": "failed",
                "errors": ["Brevo SMTP delivery failed — check Flask terminal"]}


# ── Quick connection test ─────────────────────────────────────────
def test_connection() -> bool:
    """
    Run this to verify your Brevo credentials before deploying.
    Usage:  python email_service.py
    """
    print(f"Testing Brevo SMTP connection...")
    print(f"  Host : {SMTP_HOST}:{SMTP_PORT}")
    print(f"  Login: {SMTP_LOGIN or '(not set)'}")

    if not SMTP_LOGIN or not SMTP_PASSWORD:
        print("  ERROR: credentials not set in .env")
        return False

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, 465, context=context, timeout=20) as server:
            server.ehlo()
            server.login(SMTP_LOGIN, SMTP_PASSWORD)
            print("  Connection OK ✓")
            return True
    except smtplib.SMTPAuthenticationError:
        print("  ERROR: Authentication failed — wrong login or SMTP key")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


if __name__ == "__main__":
    # Test connection first
    if test_connection():
        # Optionally send a real test email — change the address below
        TEST_EMAIL = input("\nEnter email to send test OTP (or press Enter to skip): ").strip()
        if TEST_EMAIL:
            result = send_otp("Test User", TEST_EMAIL, "123456")
            print(f"\nResult: {result}")