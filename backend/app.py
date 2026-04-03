from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from flask import Flask, request, jsonify, send_from_directory
import smtplib
from email.mime.text import MIMEText
app = Flask(__name__)
CORS(app)

# Database connection
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Passwordmysql",
    database="myecomerce",
    port=3305
)

import random

def generate_otp():
    return str(random.randint(1000, 9999))  # 4-digit OTP


print("Database Connected Successfully")
@app.route('/images/<path:filename>')
def get_image(filename):
    return send_from_directory('images', filename)
# Home Route
@app.route("/")
def home():
    return "Backend is Running Successfully!"

# Get all products
@app.route("/products", methods=["GET"])
def get_products():
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    return jsonify(products)

# Add product (Admin)
@app.route("/admin/add-product", methods=["POST"])
def add_product():
    data = request.json

    cursor = db.cursor()

    query = """
    INSERT INTO products
    (name, description, category, brand, price, stock, rating, reviews, image_url, created_at)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """

    cursor.execute(query, (
        data["name"],
        data["description"],
        data["category"],
        data["brand"],
        data["price"],
        data["stock"],
        data["rating"],
        data["reviews"],
        data["image_url"]
    ))

    db.commit()

    return jsonify({
        "status": "success",
        "message": "Product added successfully"
    })
    
def send_email_otp(receiver_email, otp):
    sender_email = "your_email@gmail.com"
    sender_password = "your_app_password"  # NOT normal password

    subject = "Your OTP Code"
    body = f"Your OTP is {otp}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        print("OTP sent to email ✅")
    except Exception as e:
        print("Error sending email:", e)
    

@app.route("/send-otp", methods=["POST"])
def send_otp():
    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"message": "Email required"}), 400

    otp = generate_otp()

    cursor = db.cursor()

    # delete old OTP
    cursor.execute("DELETE FROM otp_verification WHERE email=%s", (email,))

    # insert new OTP
    cursor.execute(
        "INSERT INTO otp_verification (email, otp) VALUES (%s, %s)",
        (email, otp)
    )
    db.commit()

    # 🔷 ADD THIS LINE HERE 👇
    send_email_otp(email, otp)

    print("OTP:", otp)  # optional (for debug)

    return jsonify({"message": "OTP sent to your email"})

@app.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")

    cursor = db.cursor()

    cursor.execute(
        "SELECT * FROM otp_verification WHERE email=%s AND otp=%s ORDER BY id DESC LIMIT 1",
        (email, otp)
    )

    result = cursor.fetchone()

    if result:
        cursor.execute("DELETE FROM otp_verification WHERE email=%s", (email,))
        db.commit()
        return jsonify({"message": "OTP verified"})
    else:
        return jsonify({"message": "Invalid OTP"}), 400


# 🔷 MOVE IT HERE (OUTSIDE)
@app.route("/register", methods=["POST"])
def register():
    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if not name or not email or not password:
        return jsonify({"message": "All fields required"}), 400

    cursor = db.cursor()

    # Check OTP (must be deleted after verification)
    cursor.execute("SELECT * FROM otp_verification WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"message": "Please verify OTP first"}), 400

    # Check existing user
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    if cursor.fetchone():
        return jsonify({"message": "User already exists"}), 400

    # Insert user
    cursor.execute(
        "INSERT INTO users (name, email, password, is_verified) VALUES (%s, %s, %s, %s)",
        (name, email, password, True)
    )
    db.commit()

    return jsonify({"message": "Registered successfully ✅"})

if __name__ == "__main__":
    app.run(debug=True)