from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
from flask_jwt_extended import JWTManager   # ✅ FIXED: added JWTManager import
import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from auto_trainer import start_auto_trainer
from chatbot_route import chatbot_bp
from unified_chat_route import unified_chat_bp
from db import get_db
load_dotenv()

# ── Blueprint imports ──────────────────────────────────────────────
from recommend_routes import recommend_bp, load_engine
from auth_routes import auth_bp
from data_routes import data_bp
from occasion_engine import occasion_bp
from admin_routes import admin_bp


app = Flask(__name__)

# ✅ FIXED: JWT secret key must be set BEFORE JWTManager(app)
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET", "your-jwt-secret")
jwt = JWTManager(app)   # ✅ FIXED: initialize JWTManager properly

import re

# ✅ Dynamic CORS Configuration to support localhost and any Vercel deployments
cors_origins_patterns = [
    r"^https?://localhost(:\d+)?$",
    r"^https?://.*\.vercel\.app$"
]
env_frontend = os.environ.get("FRONTEND_URL")
if env_frontend:
    cors_origins_patterns.append(f"^{re.escape(env_frontend.rstrip('/'))}$")

cors_origins_compiled = [re.compile(p) for p in cors_origins_patterns]

CORS(
    app,
    resources={r"/*": {"origins": cors_origins_compiled}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if origin:
        is_allowed = False
        for pattern in cors_origins_compiled:
            if pattern.match(origin):
                is_allowed = True
                break
        if is_allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


# ── Register blueprints ───────────────────────────────────────────
app.register_blueprint(auth_bp,        url_prefix="/api/auth")
app.register_blueprint(recommend_bp,   url_prefix="/api")
app.register_blueprint(data_bp,        url_prefix="/api")
app.register_blueprint(occasion_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(unified_chat_bp)
app.register_blueprint(admin_bp,       url_prefix="/api/admin")


# ── Load ML models at startup ─────────────────────────────────────
load_engine()
start_auto_trainer()

# ── Mail config ───────────────────────────────────────────────────
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = os.environ.get('GMAIL_ADDRESS', 'biradaranand025@gmail.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') or os.environ.get('GMAIL_APP_PASS')
mail = Mail(app)

print("App started — using shared DB connection pool from db.py")


# ── OTP helper ────────────────────────────────────────────────────
def generate_otp():
    return str(random.randint(100000, 999999))


# ─────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def home():
    return "Backend is Running Successfully!"

@app.route("/health")
def health():
    return {"status": "ok"}

@app.route('/images/<path:filename>')
def get_image(filename):
    return send_from_directory('images', filename)

@app.route("/products")
def get_products():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
        cursor.close()
        return jsonify(products)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

@app.route("/test-db")
def test_db():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM products")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return {"status": "TiDB connected ✓", "products": count}
    except Exception as e:
        return {"error": str(e)}, 500
    
@app.route("/products/<int:product_id>")
def get_product_by_id(product_id):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
        product = cursor.fetchone()
        cursor.close()
        if not product:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(product)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


@app.route("/admin/add-product", methods=["POST"])
def add_product():
    conn = None
    data = request.json
    try:
        conn = get_db()
        cursor = conn.cursor()
        query = """
        INSERT INTO products
        (name, description, category, brand, price, stock, rating, reviews, image_url, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """
        cursor.execute(query, (
            data["name"], data["description"], data["category"],
            data["brand"], data["price"],  data["stock"],
            data["rating"], data["reviews"], data["image_url"]
        ))
        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Product added successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass


# ── Entry point ───────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)