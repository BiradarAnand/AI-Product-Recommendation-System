"""
auth_routes.py — BULLETPROOF VERSION
✅ Resend SDK for email (works on Render)
✅ Synchronous send inside request (no threading — thread was dying silently)
✅ Full error logging so failures are always visible in Render logs
✅ Fallback: prints OTP to logs if email fails (for demo/testing)
"""

import os
import jwt
import bcrypt
import random
import mysql.connector
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
import traceback
from db import get_db


from dotenv import load_dotenv  # ← ADD THIS


load_dotenv()  # ← ADD THIS (right after imports, before anything else)

auth_bp          = Blueprint("auth", __name__)
JWT_SECRET       = os.getenv("JWT_SECRET", "your-jwt-secret")
JWT_EXPIRY_HOURS = 24

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
    Send OTP using Resend SDK.
    - Works on Render (HTTPS, not SMTP)
    - Synchronous so errors appear immediately in logs
    - Always prints OTP to logs as fallback for demos
    """
    print(f"[OTP] Attempting to send OTP to {email}")
    print(f"[OTP] FALLBACK (use this if email fails) — OTP for {email}: {otp}")

    api_key = os.getenv("RESEND_API_KEY", "").strip()

    if not api_key:
        print("[OTP] ❌ RESEND_API_KEY not set in environment variables!")
        print("[OTP]    → Go to Render Dashboard → Environment → Add RESEND_API_KEY")
        return False

    print(f"[OTP] API key found: {api_key[:8]}...")

    # ── Try Resend SDK first ──────────────────────────────────────
    try:
        import resend
        resend.api_key = api_key

        result = resend.Emails.send({
            "from":    "RecoVibe <onboarding@resend.dev>",
            "to":      [email],
            "subject": "Your OTP Code — RecoVibe",
            "html": f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;background:#f9fafb;padding:40px 0;">
<div style="max-width:480px;margin:auto;background:white;
            padding:32px;border:1px solid #e5e7eb;border-radius:12px;">
    <h2 style="color:#1f2937;margin-bottom:8px;">Your OTP Code</h2>
    <p style="color:#6b7280;">Hi {name}, use this code to verify your account:</p>
    <div style="font-size:40px;font-weight:bold;letter-spacing:14px;
                text-align:center;padding:24px;background:#f9fafb;
                border-radius:8px;color:#1f2937;margin:20px 0;">{otp}</div>
    <p style="color:#9ca3af;font-size:13px;">
        Expires in 10 minutes. Do not share with anyone.
    </p>
</div>
</body>
</html>"""
        })

        email_id = result.get("id") if isinstance(result, dict) else str(result)
        print(f"[OTP] ✅ Resend SDK SUCCESS — id={email_id}")
        return True

    except ImportError:
        print("[OTP] ❌ resend package not installed!")
        print("[OTP]    → Add 'resend' to requirements.txt and redeploy")

    except Exception as e:
        print(f"[OTP] ❌ Resend SDK failed: {type(e).__name__}: {e}")

    # ── Fallback: urllib (no extra packages) ──────────────────────
    print("[OTP] Trying urllib fallback...")
    try:
        import urllib.request
        import urllib.error
        import json

        payload = json.dumps({
            "from":    "RecoVibe <onboarding@resend.dev>",
            "to":      [email],
            "subject": "Your OTP Code — RecoVibe",
            "text":    f"Hi {name}, your OTP is: {otp}. Expires in 10 minutes.",
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization":  f"Bearer {api_key}",
                "Content-Type":   "application/json",
                "User-Agent":     "RecoVibe/1.0 Python",
                "Accept":         "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=20) as res:
            body = json.loads(res.read().decode())
        print(f"[OTP] ✅ urllib fallback SUCCESS — id={body.get('id')}")
        return True

    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"[OTP] ❌ urllib HTTP {e.code}: {err_body}")
    except Exception as e:
        print(f"[OTP] ❌ urllib failed: {type(e).__name__}: {e}")

    print(f"[OTP] ⚠️  All methods failed. OTP printed above for manual use.")
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
                    "INSERT INTO users (name, email, phone, password_hash, is_verified, role) "
                    "VALUES (%s,%s,%s,%s,0,%s)",
                    (name, email, phone, hashed, role)
                )
            except mysql.connector.errors.ProgrammingError:
                cur.execute(
                    "INSERT INTO users (name, email, phone, password_hash, is_verified) "
                    "VALUES (%s,%s,%s,%s,0)",
                    (name, email, phone, hashed)
                )
            conn.commit()
            user_id = cur.lastrowid
            print(f"[REGISTER] User created: ID {user_id}")

        otp         = str(random.randint(100000, 999999))
        otp_expires = datetime.utcnow() + timedelta(minutes=10)
        print(f"[REGISTER] OTP generated for {email}")

        try:
            cur.execute(
                "INSERT INTO otp_verification (user_id, otp_code, expires_at) "
                "VALUES (%s, %s, %s)",
                (user_id, otp, otp_expires)
            )
            conn.commit()
            print(f"[REGISTER] OTP stored in DB ✓")
        except mysql.connector.errors.ProgrammingError as e:
            print(f"[REGISTER] OTP table issue: {e}")
            try:
                cur.execute(
                    "INSERT INTO otp_verification (email, otp, otp_expiry) "
                    "VALUES (%s, %s, %s)",
                    (email, otp, otp_expires)
                )
                conn.commit()
            except Exception as e2:
                print(f"[REGISTER] OTP storage failed: {e2}")

        cur.close()

        # ✅ SYNCHRONOUS — so output always appears in logs
        email_sent = send_otp_email(name, email, otp)
        print(f"[REGISTER] Email sent: {email_sent}")

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
        if conn:
            try: conn.close()
            except: pass


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

        if not otp_row:
            try:
                cur.execute(
                    """SELECT id, otp AS otp_code, otp_expiry AS expires_at
                       FROM otp_verification WHERE email = %s
                       ORDER BY created_at DESC LIMIT 1""",
                    (user["email"],)
                )
                otp_row = cur.fetchone()
            except Exception as e:
                print(f"[VERIFY-OTP] Fallback query failed: {e}")

        if not otp_row:
            cur.close()
            return jsonify({"error": "No active OTP found. Please request a new one."}), 400

        if str(otp_input).strip() != str(otp_row["otp_code"]).strip():
            cur.close()
            return jsonify({"error": "Incorrect OTP. Please try again."}), 400

        if otp_row["expires_at"] and datetime.utcnow() > otp_row["expires_at"]:
            cur.close()
            return jsonify({"error": "OTP has expired. Please request a new one."}), 400

        try:
            cur.execute(
                "UPDATE otp_verification SET is_used = 1 WHERE id = %s",
                (otp_row["id"],)
            )
        except Exception:
            pass

        role = get_user_role(user["email"])
        try:
            cur.execute(
                "UPDATE users SET is_verified = 1, role = %s WHERE id = %s",
                (role, user_id)
            )
        except mysql.connector.errors.ProgrammingError:
            cur.execute(
                "UPDATE users SET is_verified = 1 WHERE id = %s", (user_id,)
            )

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
                "role":  role,
            },
        }), 200

    except Exception as e:
        print(f"[VERIFY-OTP] Error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Verification failed.", "detail": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


# ── POST /api/auth/login ──────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    err  = validate_fields(data, ["email", "password"])
    if err:
        return jsonify({"error": err}), 400

    email = data["email"].strip().lower()
    conn  = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        print(f"[LOGIN] Attempting: {email}")

        try:
            cur.execute(
                "SELECT id, name, email, password_hash, is_verified, role "
                "FROM users WHERE email = %s", (email,)
            )
        except mysql.connector.errors.ProgrammingError:
            cur.execute(
                "SELECT id, name, email, password_hash, is_verified "
                "FROM users WHERE email = %s", (email,)
            )

        user = cur.fetchone()
        cur.close()

        if not user or not bcrypt.checkpw(
            data["password"].encode(), user["password_hash"].encode()
        ):
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
                "role":  role,
            },
        }), 200

    except Exception as e:
        print(f"[LOGIN] Error: {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Login failed.", "detail": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


# ── POST /api/auth/resend-otp ─────────────────────────────────────
@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    data = request.get_json() or {}
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        if data.get("user_id"):
            cur.execute(
                "SELECT id, name, email FROM users WHERE id = %s",
                (int(data["user_id"]),)
            )
        elif data.get("email"):
            cur.execute(
                "SELECT id, name, email FROM users WHERE email = %s",
                (data["email"].strip().lower(),)
            )
        else:
            cur.close()
            return jsonify({"error": "'user_id' or 'email' is required."}), 400

        user = cur.fetchone()
        if not user:
            cur.close()
            return jsonify({"error": "User not found."}), 404

        otp         = str(random.randint(100000, 999999))
        otp_expires = datetime.utcnow() + timedelta(minutes=10)

        try:
            cur.execute(
                "INSERT INTO otp_verification (user_id, otp_code, expires_at) "
                "VALUES (%s, %s, %s)",
                (user["id"], otp, otp_expires)
            )
        except Exception:
            cur.execute(
                "INSERT INTO otp_verification (email, otp, otp_expiry) "
                "VALUES (%s, %s, %s)",
                (user["email"], otp, otp_expires)
            )

        conn.commit()
        cur.close()

        email_sent = send_otp_email(user["name"], user["email"], otp)
        print(f"[RESEND-OTP] Email sent: {email_sent}")

        return jsonify({
            "message":    "OTP resent.",
            "email_sent": email_sent,
        }), 200

    except Exception as e:
        print(f"[RESEND-OTP] Error: {e}")
        return jsonify({"error": "Resend failed.", "detail": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass