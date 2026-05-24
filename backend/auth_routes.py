"""
auth_routes.py — FIXED VERSION
────────────────────────────────
✅ Includes role in JWT token
✅ Proper connection cleanup with finally blocks
✅ Robust OTP sending with fallback (no crash if SMTP fails)
✅ Better error messages
✅ Graceful fallbacks for missing columns
"""

import os
import jwt
import bcrypt
import mysql.connector
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
import traceback

from db import get_db

auth_bp          = Blueprint("auth", __name__)
JWT_SECRET       = os.getenv("JWT_SECRET", "your-jwt-secret")
JWT_EXPIRY_HOURS = 24

# Admin emails
ADMIN_EMAILS = [
    "arunchityala18@gmail.com",
    "biradaranandof@gmail.com",
]


def make_jwt(user_id: int, email: str, role: str = "user") -> str:
    payload = {
        "user_id": user_id,
        "email":   email,
        "role":    role,
        "exp":     datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def validate_fields(data: dict, required: list):
    for field in required:
        if not data.get(field, "").strip():
            return f"'{field}' is required."
    return None


def get_user_role(email: str) -> str:
    return "admin" if email.lower() in [e.lower() for e in ADMIN_EMAILS] else "user"


def send_otp_email(name: str, email: str, otp: str) -> bool:
    """
    ✅ FIXED: Tries Flask-Mail first, falls back to raw SMTP.
    Returns True if sent, False if failed (does NOT crash registration).
    """
    gmail_address = os.getenv("GMAIL_ADDRESS")
    gmail_pass    = os.getenv("GMAIL_APP_PASS") or os.getenv("MAIL_PASSWORD")

    if not gmail_address or not gmail_pass:
        print(f"[OTP] WARNING: Gmail credentials not set. OTP for {email} is: {otp}")
        return False

    html_body = f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                padding:32px;border:1px solid #e5e7eb;border-radius:12px;">
        <h2 style="color:#1f2937;">Your OTP Code</h2>
        <p>Hi {name}, use this code to verify your account:</p>
        <div style="font-size:40px;font-weight:bold;letter-spacing:14px;
                    text-align:center;padding:24px;background:#f9fafb;
                    border-radius:8px;color:#1f2937;">{otp}</div>
        <p style="color:#9ca3af;font-size:13px;margin-top:20px;">
            Expires in 10 minutes. Do not share with anyone.
        </p>
    </div>"""

    # ── Try Flask-Mail first ──────────────────────────────────────
    try:
        from flask_mail import Message, Mail
        from flask import current_app
        mail = Mail(current_app)
        msg = Message(
            subject="Your OTP Code — RecoVibe",
            sender=gmail_address,
            recipients=[email]
        )
        msg.html = html_body
        mail.send(msg)
        print(f"[OTP Flask-Mail] Sent to {email} ✓")
        return True
    except Exception as e:
        print(f"[OTP Flask-Mail] Failed ({e}), trying SMTP fallback...")

    # ── Fallback: raw SMTP ────────────────────────────────────────
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your OTP Code — RecoVibe"
        msg["From"]    = gmail_address
        msg["To"]      = email
        msg.attach(MIMEText(f"Your OTP is: {otp}. Expires in 10 minutes.", "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(gmail_address, gmail_pass)
            server.sendmail(gmail_address, email, msg.as_string())

        print(f"[OTP SMTP] Sent to {email} ✓")
        return True
    except smtplib.SMTPAuthenticationError:
        print(f"[OTP SMTP] Auth failed. Check GMAIL_ADDRESS and GMAIL_APP_PASS env vars.")
        print(f"[OTP SMTP] Use App Password (not account password): myaccount.google.com -> Security -> App passwords")
        return False
    except Exception as e:
        print(f"[OTP SMTP] Failed: {e}")
        print(f"[OTP] OTP for {email} (for debugging only): {otp}")
        return False


# ── POST /api/auth/register ───────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    print(f"[REGISTER] Starting for {data.get('email')}")

    err = validate_fields(data, ["name", "email", "password"])
    if err:
        return jsonify({"error": err}), 400

    if len(data["password"]) < 4:
        return jsonify({"error": "Password must be at least 4 characters."}), 400

    name  = data["name"].strip()
    email = data["email"].strip().lower()
    phone = data.get("phone", "").strip() or None
    role  = get_user_role(email)

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        # Check if already verified
        cur.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
        existing = cur.fetchone()

        if existing and existing["is_verified"]:
            cur.close()
            return jsonify({"error": "An account with this email already exists."}), 409

        user_id = existing["id"] if existing else None

        if not existing:
            print(f"[REGISTER] Creating user: {name}")
            hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

            try:
                cur.execute(
                    "INSERT INTO users (name, email, phone, password_hash, is_verified, role) VALUES (%s,%s,%s,%s,0,%s)",
                    (name, email, phone, hashed, role)
                )
            except mysql.connector.errors.ProgrammingError:
                # role column might not exist yet
                cur.execute(
                    "INSERT INTO users (name, email, phone, password_hash, is_verified) VALUES (%s,%s,%s,%s,0)",
                    (name, email, phone, hashed)
                )

            conn.commit()
            user_id = cur.lastrowid
            print(f"[REGISTER] User created: ID {user_id}")

        # Generate OTP
        import random
        otp = str(random.randint(100000, 999999))
        print(f"[REGISTER] OTP generated for {email}")

        # Store OTP
        otp_expires = datetime.utcnow() + timedelta(minutes=10)
        try:
            cur.execute(
                "INSERT INTO otp_verification (user_id, otp_code, expires_at) VALUES (%s, %s, %s)",
                (user_id, otp, otp_expires)
            )
            conn.commit()
            print(f"[REGISTER] OTP stored in DB ✓")
        except mysql.connector.errors.ProgrammingError as e:
            print(f"[REGISTER] OTP table issue: {e}")
            # ✅ Try alternate column names if schema is different
            try:
                cur.execute(
                    "INSERT INTO otp_verification (email, otp, otp_expiry) VALUES (%s, %s, %s)",
                    (email, otp, otp_expires)
                )
                conn.commit()
            except Exception as e2:
                print(f"[REGISTER] OTP storage failed both ways: {e2}")

        cur.close()

        # Send OTP email (non-blocking — registration succeeds even if email fails)
        email_sent = send_otp_email(name, email, otp)

        return jsonify({
            "message":    "OTP sent. Please verify your account.",
            "user_id":    user_id,
            "email_sent": email_sent,
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already registered."}), 409
    except Exception as e:
        print(f"[REGISTER] Error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Registration failed.", "detail": str(e)}), 500
    finally:
        # ✅ FIXED: connection ALWAYS closed
        if conn:
            try:
                conn.close()
            except:
                pass


# ── POST /api/auth/verify-otp ─────────────────────────────────────
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json() or {}

    if not data.get("user_id") or not data.get("otp", "").strip():
        return jsonify({"error": "'user_id' and 'otp' are required."}), 400

    user_id   = int(data["user_id"])
    otp_input = data["otp"].strip()

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        print(f"[VERIFY-OTP] Verifying for user {user_id}")

        cur.execute(
            "SELECT id, name, email, is_verified FROM users WHERE id = %s",
            (user_id,)
        )
        user = cur.fetchone()

        if not user:
            cur.close()
            return jsonify({"error": "User not found."}), 404
        if user["is_verified"]:
            cur.close()
            return jsonify({"error": "Account already verified. Please log in."}), 400

        # ✅ Try new schema first (user_id, otp_code, expires_at)
        otp_row = None
        try:
            cur.execute(
                """SELECT id, otp_code, expires_at FROM otp_verification
                   WHERE user_id = %s AND (is_used = 0 OR is_used IS NULL)
                   ORDER BY created_at DESC LIMIT 1""",
                (user_id,)
            )
            otp_row = cur.fetchone()
        except Exception:
            pass

        # ✅ Fallback to old schema (email, otp, otp_expiry)
        if not otp_row:
            try:
                cur.execute(
                    """SELECT id, otp AS otp_code, otp_expiry AS expires_at
                       FROM otp_verification
                       WHERE email = %s
                       ORDER BY created_at DESC LIMIT 1""",
                    (user["email"],)
                )
                otp_row = cur.fetchone()
            except Exception as e:
                print(f"[VERIFY-OTP] Fallback OTP query failed: {e}")

        if not otp_row:
            cur.close()
            return jsonify({"error": "No active OTP found. Please request a new one."}), 400

        if str(otp_input).strip() != str(otp_row["otp_code"]).strip():
            cur.close()
            return jsonify({"error": "Incorrect OTP. Please try again."}), 400

        if otp_row["expires_at"] and datetime.utcnow() > otp_row["expires_at"]:
            cur.close()
            return jsonify({"error": "OTP has expired. Please request a new one."}), 400

        # Mark OTP used
        try:
            cur.execute(
                "UPDATE otp_verification SET is_used = 1 WHERE id = %s",
                (otp_row["id"],)
            )
        except Exception:
            pass

        # Mark user verified
        role = get_user_role(user["email"])
        try:
            cur.execute(
                "UPDATE users SET is_verified = 1, role = %s WHERE id = %s",
                (role, user_id)
            )
        except mysql.connector.errors.ProgrammingError:
            cur.execute("UPDATE users SET is_verified = 1 WHERE id = %s", (user_id,))

        conn.commit()
        cur.close()
        print(f"[VERIFY-OTP] User {user_id} verified ✓")

        token = make_jwt(user["id"], user["email"], role)

        return jsonify({
            "message": "Account verified successfully.",
            "token":   token,
            "user": {
                "id":    user["id"],
                "name":  user["name"],
                "email": user["email"],
                "role":  role
            },
        }), 200

    except Exception as e:
        print(f"[VERIFY-OTP] Error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Verification failed.", "detail": str(e)}), 500
    finally:
        # ✅ FIXED: connection ALWAYS closed
        if conn:
            try:
                conn.close()
            except:
                pass


# ── POST /api/auth/login ──────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    err  = validate_fields(data, ["email", "password"])
    if err:
        return jsonify({"error": err}), 400

    email = data["email"].strip().lower()

    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        print(f"[LOGIN] Attempting: {email}")

        try:
            cur.execute(
                "SELECT id, name, email, password_hash, is_verified, role FROM users WHERE email = %s",
                (email,)
            )
        except mysql.connector.errors.ProgrammingError:
            cur.execute(
                "SELECT id, name, email, password_hash, is_verified FROM users WHERE email = %s",
                (email,)
            )

        user = cur.fetchone()
        cur.close()

        if not user or not bcrypt.checkpw(data["password"].encode(), user["password_hash"].encode()):
            return jsonify({"error": "Invalid email or password."}), 401

        if not user["is_verified"]:
            return jsonify({
                "error":   "Account not verified. Please check your email for the OTP.",
                "user_id": user["id"],
                "action":  "verify_otp",
            }), 403

        role  = user.get("role") or get_user_role(email)
        token = make_jwt(user["id"], user["email"], role)

        print(f"[LOGIN] Success: {email} (role: {role})")

        return jsonify({
            "message": "Login successful.",
            "token":   token,
            "user": {
                "id":    user["id"],
                "name":  user["name"],
                "email": user["email"],
                "role":  role
            },
        }), 200

    except Exception as e:
        print(f"[LOGIN] Error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Login failed.", "detail": str(e)}), 500
    finally:
        # ✅ FIXED: connection ALWAYS closed
        if conn:
            try:
                conn.close()
            except:
                pass


# ── POST /api/auth/resend-otp ────────────────────────────────────
@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json() or {}
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        if data.get("user_id"):
            cur.execute("SELECT id, name, email FROM users WHERE id = %s", (int(data["user_id"]),))
        elif data.get("email"):
            cur.execute("SELECT id, name, email FROM users WHERE email = %s", (data["email"].strip().lower(),))
        else:
            cur.close()
            return jsonify({"error": "'user_id' or 'email' is required."}), 400

        user = cur.fetchone()
        if not user:
            cur.close()
            return jsonify({"error": "User not found."}), 404

        import random
        otp = str(random.randint(100000, 999999))
        otp_expires = datetime.utcnow() + timedelta(minutes=10)

        try:
            cur.execute(
                "INSERT INTO otp_verification (user_id, otp_code, expires_at) VALUES (%s, %s, %s)",
                (user["id"], otp, otp_expires)
            )
        except Exception:
            cur.execute(
                "INSERT INTO otp_verification (email, otp, otp_expiry) VALUES (%s, %s, %s)",
                (user["email"], otp, otp_expires)
            )

        conn.commit()
        cur.close()

        email_sent = send_otp_email(user["name"], user["email"], otp)

        return jsonify({
            "message":    "OTP resent.",
            "email_sent": email_sent,
        }), 200

    except Exception as e:
        print(f"[RESEND-OTP] Error: {e}")
        return jsonify({"error": "Resend failed.", "detail": str(e)}), 500
    finally:
        # ✅ FIXED: connection ALWAYS closed
        if conn:
            try:
                conn.close()
            except:
                pass