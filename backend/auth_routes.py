"""
auth_routes.py
──────────────
Flask Blueprint — full auth with OTP using otp_verification table.

Register in app.py:
    from auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
"""

import os
import jwt
import bcrypt
import mysql.connector
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from otp_service import generate_otp, otp_expiry, is_otp_valid, send_otp

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
# auth_bp          = Blueprint("auth", __name__)
JWT_SECRET       = os.getenv("JWT_SECRET", "your-jwt-secret")
JWT_EXPIRY_HOURS = 24

DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "your_db_name"),
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def make_jwt(user_id: int, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email":   email,
        "exp":     datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def validate_fields(data: dict, required: list):
    for field in required:
        if not data.get(field, "").strip():
            return f"'{field}' is required."
    return None

def create_otp_record(cur, user_id: int, channel: str) -> str:
    """Insert a fresh OTP row into otp_verification, return the OTP code."""
    otp     = generate_otp()
    expires = otp_expiry()
    cur.execute(
        "INSERT INTO otp_verification (user_id, otp_code, channel, expires_at) VALUES (%s, %s, %s, %s)",
        (user_id, otp, channel, expires)
    )
    return otp


# POST /api/auth/register
@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Body: { name, email, password, phone (optional), otp_channel: "email"|"sms"|"both" }
    Creates unverified user, inserts OTP row, sends OTP.
    """
    data    = request.get_json() or {}
    channel = data.get("otp_channel", "email")

    err = validate_fields(data, ["name", "email", "password"])
    if err:
        return jsonify({"error": err}), 400

    if channel in ("sms", "both") and not data.get("phone", "").strip():
        return jsonify({"error": "Phone number is required for SMS OTP."}), 400

    if len(data["password"]) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    name  = data["name"].strip()
    email = data["email"].strip().lower()
    phone = data.get("phone", "").strip() or None

    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, is_verified FROM users WHERE email = %s", (email,))
        existing = cur.fetchone()

        if existing:
            if existing["is_verified"]:
                return jsonify({"error": "An account with this email already exists."}), 409
            user_id = existing["id"]
        else:
            hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()
            cur.execute(
                "INSERT INTO users (name, email, phone, password_hash, is_verified) VALUES (%s,%s,%s,%s,0)",
                (name, email, phone, hashed)
            )
            user_id = cur.lastrowid

        otp    = create_otp_record(cur, user_id, channel)
        conn.commit()

        result = send_otp(name, email, phone, otp, channel)
        if not result["email_sent"] and not result["sms_sent"]:
            return jsonify({"error": "Failed to send OTP.", "detail": result["errors"]}), 500

        return jsonify({
            "message":    "OTP sent. Please verify your account.",
            "user_id":    user_id,
            "email_sent": result["email_sent"],
            "sms_sent":   result["sms_sent"],
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({"error": "Email already registered."}), 409
    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Registration failed.", "detail": str(e)}), 500
    finally:
        cur.close(); conn.close()


# POST /api/auth/verify-otp
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    """
    Body: { user_id, otp }
    Validates from otp_verification table.
    Marks OTP as used + user as verified. Returns JWT.
    """
    data = request.get_json() or {}
    if not data.get("user_id") or not data.get("otp", "").strip():
        return jsonify({"error": "'user_id' and 'otp' are required."}), 400

    user_id   = int(data["user_id"])
    otp_input = data["otp"].strip()

    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, name, email, is_verified FROM users WHERE id = %s", (user_id,))
        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found."}), 404
        if user["is_verified"]:
            return jsonify({"error": "Account already verified. Please log in."}), 400

        # Get latest unused OTP for this user
        cur.execute(
            """SELECT id, otp_code, expires_at FROM otp_verification
               WHERE user_id = %s AND is_used = 0
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,)
        )
        otp_row = cur.fetchone()
        if not otp_row:
            return jsonify({"error": "No active OTP found. Please request a new one."}), 400

        valid, err = is_otp_valid(otp_input, otp_row["otp_code"], otp_row["expires_at"])
        if not valid:
            return jsonify({"error": err}), 400

        # Mark OTP used + verify user in one transaction
        cur.execute("UPDATE otp_verification SET is_used = 1 WHERE id = %s", (otp_row["id"],))
        cur.execute("UPDATE users SET is_verified = 1 WHERE id = %s", (user_id,))
        conn.commit()

        token = make_jwt(user["id"], user["email"])
        return jsonify({
            "message": "Account verified successfully.",
            "token":   token,
            "user":    {"id": user["id"], "name": user["name"], "email": user["email"]},
        }), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Verification failed.", "detail": str(e)}), 500
    finally:
        cur.close(); conn.close()


# POST /api/auth/resend-otp
@auth_bp.route("/resend-otp", methods=["POST"])
def resend_otp():
    """
    Body: { user_id }  OR  { email }
    Creates a fresh OTP row and resends using last channel.
    """
    data = request.get_json() or {}
    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    try:
        if data.get("user_id"):
            cur.execute("SELECT id, name, email, phone FROM users WHERE id = %s", (int(data["user_id"]),))
        elif data.get("email"):
            cur.execute("SELECT id, name, email, phone FROM users WHERE email = %s", (data["email"].strip().lower(),))
        else:
            return jsonify({"error": "'user_id' or 'email' is required."}), 400

        user = cur.fetchone()
        if not user:
            return jsonify({"error": "User not found."}), 404

        # Reuse last channel
        cur.execute(
            "SELECT channel FROM otp_verification WHERE user_id = %s ORDER BY created_at DESC LIMIT 1",
            (user["id"],)
        )
        last    = cur.fetchone()
        channel = last["channel"] if last else "email"

        otp = create_otp_record(cur, user["id"], channel)
        conn.commit()

        result = send_otp(user["name"], user["email"], user["phone"], otp, channel)
        return jsonify({"message": "OTP resent.", "email_sent": result["email_sent"], "sms_sent": result["sms_sent"]}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": "Resend failed.", "detail": str(e)}), 500
    finally:
        cur.close(); conn.close()


# POST /api/auth/login
@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Body: { email, password }
    Only verified users can log in.
    """
    data = request.get_json() or {}
    err  = validate_fields(data, ["email", "password"])
    if err:
        return jsonify({"error": err}), 400

    email = data["email"].strip().lower()

    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, name, email, password_hash, is_verified FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        if not user or not bcrypt.checkpw(data["password"].encode(), user["password_hash"].encode()):
            return jsonify({"error": "Invalid email or password."}), 401

        if not user["is_verified"]:
            return jsonify({
                "error":   "Account not verified. Please check your email or SMS for the OTP.",
                "user_id": user["id"],
                "action":  "verify_otp",
            }), 403

        token = make_jwt(user["id"], user["email"])
        return jsonify({
            "message": "Login successful.",
            "token":   token,
            "user":    {"id": user["id"], "name": user["name"], "email": user["email"]},
        }), 200

    except Exception as e:
        return jsonify({"error": "Login failed.", "detail": str(e)}), 500
    finally:
        cur.close(); conn.close()