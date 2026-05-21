from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_mail import Mail, Message
import random
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from auto_trainer import start_auto_trainer
from chatbot_route import chatbot_bp
from unified_chat_route import unified_chat_bp
from db import get_db  # ← single shared pool
load_dotenv()

# ── Blueprint imports ──────────────────────────────────────────────
from recommend_routes import recommend_bp, load_engine
from auth_routes import auth_bp          # ✅ imported ONCE (removed duplicate)
from data_routes import data_bp
from occasion_engine import occasion_bp

app = Flask(__name__)

# ✅ CORS called ONCE only (removed the bare CORS(app) call)

CORS(
    app,
    resources={r"/*": {"origins": [
        "http://localhost:5173",
        "https://ai-product-recommendation-system-phi.vercel.app",
        "https://ai-product-recommendation-sys-git-a014cc-biradaranands-projects.vercel.app",
        "https://ai-product-recommendation-system-py98jsht0.vercel.app"
    ]}},
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "https://ai-product-recommendation-system-phi.vercel.app"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# ── Register blueprints — each registered ONCE ───────────────────
# ✅ Removed the extra app.register_blueprint(auth_bp) without url_prefix
app.register_blueprint(auth_bp,        url_prefix="/api/auth")
app.register_blueprint(recommend_bp,   url_prefix="/api")
app.register_blueprint(data_bp,        url_prefix="/api")
app.register_blueprint(occasion_bp)
app.register_blueprint(chatbot_bp)
app.register_blueprint(unified_chat_bp)

# ── Load ML models at startup ─────────────────────────────────────
load_engine()
start_auto_trainer()

# ── Mail config ───────────────────────────────────────────────────
app.config['MAIL_SERVER']   = 'smtp.gmail.com'
app.config['MAIL_PORT']     = 587
app.config['MAIL_USE_TLS']  = True
app.config['MAIL_USERNAME'] = 'biradaranand025@gmail.com'
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
mail = Mail(app)

print("App started — using shared DB connection pool from db.py")


# ── OTP helper ────────────────────────────────────────────────────
def generate_otp():
    return str(random.randint(1000, 9999))


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
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    offset   = (page - 1) * per_page

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM products LIMIT %s OFFSET %s",
        (per_page, offset)
    )
    products = cursor.fetchall()
    cursor.close()
    conn.close()   # ← always close after use!
    return jsonify(products)


@app.route("/admin/add-product", methods=["POST"])
def add_product():
    data = request.json
    conn = get_db()
    try:
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
        return jsonify({"status": "success", "message": "Product added successfully"})
    finally:
        cursor.close()
        conn.close()


@app.route('/send-otp', methods=['POST'])
def send_otp():
    try:
        data    = request.get_json()
        email   = data.get('email', '')
        phone   = data.get('phone', '')
        channel = data.get('channel', 'email')

        otp    = generate_otp()
        expiry = datetime.now().astimezone() + timedelta(minutes=10)

        conn = get_db()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO otp_verification (email, otp, otp_expiry) VALUES (%s, %s, %s)",
                (email, otp, expiry)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()

        email_sent = False
        sms_sent   = False

        if channel in ('email', 'both') and email:
            try:
                msg = Message(
                    subject="Your OTP Code",
                    sender=app.config['MAIL_USERNAME'],
                    recipients=[email]
                )
                msg.body = f"Your OTP is: {otp}\n\nExpires in 10 minutes."
                msg.html = f"""
                <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;
                            padding:32px;border:1px solid #e5e7eb;border-radius:12px;">
                    <h2 style="color:#1f2937;">Your OTP Code</h2>
                    <div style="font-size:40px;font-weight:bold;letter-spacing:14px;
                                text-align:center;padding:24px;background:#f9fafb;
                                border-radius:8px;color:#1f2937;">{otp}</div>
                    <p style="color:#9ca3af;font-size:13px;margin-top:20px;">
                        Expires in 10 minutes. Do not share with anyone.
                    </p>
                </div>"""
                mail.send(msg)
                email_sent = True
                print(f"[OTP] Email sent to {email} — OTP: {otp}")
            except Exception as e:
                print(f"[OTP] Email failed: {e}")

        if channel in ('sms', 'both') and phone:
            try:
                from twilio.rest import Client as TwilioClient
                sid         = os.getenv("TWILIO_ACCOUNT_SID", "")
                token       = os.getenv("TWILIO_AUTH_TOKEN",  "")
                from_number = os.getenv("TWILIO_PHONE_NUMBER","")

                if not sid or not token or not from_number:
                    print("[OTP] Twilio credentials missing in .env")
                else:
                    if not phone.startswith("+"):
                        phone = "+91" + phone.lstrip("0")
                    client  = TwilioClient(sid, token)
                    message = client.messages.create(
                        body=f"Your OTP is: {otp}. Valid for 10 minutes. Do not share.",
                        from_=from_number,
                        to=phone
                    )
                    sms_sent = True
                    print(f"[OTP] SMS sent to {phone} — SID: {message.sid}")
            except Exception as e:
                print(f"[OTP] SMS failed: {e}")

        if not email_sent and not sms_sent:
            return jsonify({"message": "Failed to send OTP. Check server logs."}), 500

        return jsonify({
            "message":    "OTP sent successfully",
            "email_sent": email_sent,
            "sms_sent":   sms_sent,
        })

    except Exception as e:
        print(f"[OTP] Server error: {e}")
        return jsonify({"message": f"Server error: {str(e)}"}), 500


@app.route('/verify-otp', methods=['POST'])
def verify_otp():
    data     = request.get_json()
    email    = data.get('email')
    user_otp = data.get('otp')

    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT otp, otp_expiry FROM otp_verification
            WHERE email = %s ORDER BY created_at DESC LIMIT 1
        """, (email,))
        result = cursor.fetchone()

        if result:
            db_otp, expiry = result
            if str(db_otp) == str(user_otp) and datetime.utcnow() < expiry:
                cursor.execute(
                    "UPDATE otp_verification SET is_verified = TRUE WHERE email = %s",
                    (email,)
                )
                conn.commit()
                return jsonify({"message": "OTP verified ✅"})

        return jsonify({"message": "Invalid or expired OTP ❌"}), 400
    finally:
        cursor.close()
        conn.close()


# @app.route("/register", methods=["POST"])
# def register():
#     data     = request.get_json()
#     name     = data.get("name")
#     email    = data.get("email")
#     password = data.get("password")

#     if not name or not email or not password:
#         return jsonify({"message": "All fields required"}), 400

#     conn = get_db()
#     try:
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT is_verified FROM otp_verification
#             WHERE email = %s ORDER BY created_at DESC LIMIT 1
#         """, (email,))
#         result = cursor.fetchone()

#         if not result or not result[0]:
#             return jsonify({"message": "Please verify OTP first ❗"}), 400

#         cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
#         if cursor.fetchone():
#             return jsonify({"message": "User already exists"}), 400

#         cursor.execute(
#             "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
#             (name, email, password)
#         )
#         conn.commit()
#         return jsonify({"message": "Registered successfully ✅"})
#     finally:
#         cursor.close()
#         conn.close()


# ── Entry point ───────────────────────────────────────────────────
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)