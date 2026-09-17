"""
auth_routes.py — JWT Token-Based Authentication (No OTP)
✅ Register → immediate login, no OTP needed
✅ Login → returns JWT token
✅ JWT used for all protected routes
"""

import os
import jwt
import bcrypt
import traceback
import mysql.connector

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from db import get_db
from dotenv import load_dotenv

load_dotenv()

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

        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing = cur.fetchone()

        if existing:
            cur.close()
            return jsonify({"error": "An account with this email already exists."}), 409

        print(f"[REGISTER] Creating user: {name}")
        hashed = bcrypt.hashpw(data["password"].encode(), bcrypt.gensalt()).decode()

        try:
            cur.execute(
                "INSERT INTO users (name, email, phone, password_hash, role) "
                "VALUES (%s,%s,%s,%s,%s)",
                (name, email, phone, hashed, role)
            )
        except mysql.connector.errors.ProgrammingError:
            # Fallback if 'role' column doesn't exist yet
            cur.execute(
                "INSERT INTO users (name, email, phone, password_hash) "
                "VALUES (%s,%s,%s,%s)",
                (name, email, phone, hashed)
            )

        conn.commit()
        user_id = cur.lastrowid
        print(f"[REGISTER] User created: ID {user_id}")

        # Issue JWT immediately — no OTP step
        token = make_jwt(user_id, email, role)
        cur.close()

        return jsonify({
            "message": "Registration successful.",
            "token":   token,
            "user": {
                "id":    user_id,
                "name":  name,
                "email": email,
                "role":  role,
            },
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
                "SELECT id, name, email, password_hash, role "
                "FROM users WHERE email = %s", (email,)
            )
        except mysql.connector.errors.ProgrammingError:
            cur.execute(
                "SELECT id, name, email, password_hash "
                "FROM users WHERE email = %s", (email,)
            )

        user = cur.fetchone()
        cur.close()

        if not user or not bcrypt.checkpw(
            data["password"].encode(), user["password_hash"].encode()
        ):
            return jsonify({"error": "Invalid email or password."}), 401

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