from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Product
from extensions import db

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/add-product", methods=["POST"])
@jwt_required()
def add_product():
    data = request.get_json()

    new_product = Product(
        name=data["name"],
        description=data["description"],
        category=data["category"],
        price=data["price"],
        stock=data["stock"]
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({"message": "Product added successfully"})