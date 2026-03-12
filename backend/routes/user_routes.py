from flask import Blueprint, jsonify
from models.product_model import Product

user_bp = Blueprint("user", __name__)

@user_bp.route("/products", methods=["GET"])
def get_products():
    products = Product.query.all()
    return jsonify([
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "price": p.price
        } for p in products
    ])