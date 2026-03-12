from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# Database connection
db = mysql.connector.connect(
    host="127.0.0.1",
    user="root",
    password="Passwordmysql",
    database="ecomerce",
    port=3305
)

print("Database Connected Successfully")

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

if __name__ == "__main__":
    app.run(debug=True)