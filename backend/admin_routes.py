"""
admin_routes.py
───────────────
Admin dashboard API endpoints.
GET /api/admin/stats — overview stats
GET /api/admin/users — user list
GET /api/admin/analytics — detailed analytics
POST/PUT/DELETE /api/admin/products — product CRUD

Register in app.py:
    from admin_routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
"""

import os
import jwt
from flask import Blueprint, request, jsonify
from functools import wraps
from db import get_db

admin_bp = Blueprint("admin", __name__)
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret")

# ── Admin auth check ──────────────────────────────────────────────
def require_admin(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            token   = auth.split(" ")[1]
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("user_id")
            email   = payload.get("email")
            
            # Check if user is admin
            conn = get_db()
            cur  = conn.cursor(dictionary=True)
            cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
            user = cur.fetchone()
            cur.close(); conn.close()
            
            if not user or user.get("role") != "admin":
                return jsonify({"error": "Admin access required"}), 403
            
            return f(*args, user_id=user_id, email=email, **kwargs)
        except Exception as e:
            return jsonify({"error": "Invalid token"}), 401
    return wrapper


# ─────────────────────────────────────────────────────────────────
# STATS ENDPOINT
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/stats", methods=["GET"])
@require_admin
def get_stats(user_id, email):
    """GET /api/admin/stats — Overview statistics."""
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        
        # Count tables
        cur.execute("SELECT COUNT(*) as count FROM users")
        total_users = cur.fetchone()["count"]
        
        cur.execute("SELECT COUNT(*) as count FROM products")
        total_products = cur.fetchone()["count"]
        
        cur.execute("SELECT COUNT(*) as count FROM search_history")
        total_searches = cur.fetchone()["count"]
        
        cur.execute("SELECT COUNT(*) as count FROM wishlist")
        total_wishlists = cur.fetchone()["count"]
        
        cur.execute("SELECT COUNT(DISTINCT user_id) as active FROM cart")
        active_carts = cur.fetchone()["active"]
        
        cur.close(); conn.close()
        
        return jsonify({
            "total_users":       total_users,
            "total_products":    total_products,
            "total_searches":    total_searches,
            "total_wishlists":   total_wishlists,
            "active_shopping":   active_carts,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# USERS ENDPOINT
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/users", methods=["GET"])
@require_admin
def get_users(user_id, email):
    """GET /api/admin/users — List all users."""
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, name, email, phone, role, is_verified, created_at
            FROM users
            ORDER BY created_at DESC
            LIMIT 100
        """)
        users = cur.fetchall()
        cur.close(); conn.close()
        
        return jsonify({"users": users, "count": len(users)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/users/<int:user_id>/block", methods=["PATCH"])
@require_admin
def block_user(user_id, email, **kwargs):
    """PATCH /api/admin/users/<id>/block — Block/unblock a user."""
    data = request.get_json() or {}
    blocked = bool(data.get("blocked", False))
    
    try:
        conn = get_db()
        cur  = conn.cursor()
        
        # Add blocked column if it doesn't exist (fallback)
        try:
            cur.execute("ALTER TABLE users ADD COLUMN blocked BOOLEAN DEFAULT 0")
            conn.commit()
        except:
            pass  # Column already exists
        
        cur.execute("UPDATE users SET blocked = %s WHERE id = %s", (blocked, user_id))
        conn.commit()
        cur.close(); conn.close()
        
        return jsonify({"message": f"User {'blocked' if blocked else 'unblocked'}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# PRODUCTS ENDPOINTS
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/products", methods=["GET"])
@require_admin
def get_products_admin(user_id, email):
    """GET /api/admin/products — List all products with details."""
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, name, brand, category, price, stock, rating, reviews, image_url
            FROM products
            ORDER BY id DESC
            LIMIT 500
        """)
        products = cur.fetchall()
        cur.close(); conn.close()
        
        return jsonify({"products": products, "count": len(products)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/products", methods=["POST"])
@require_admin
def add_product_admin(user_id, email):
    """POST /api/admin/products — Add new product."""
    data = request.get_json() or {}
    
    required = ["name", "brand", "category", "price"]
    if not all(data.get(k) for k in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO products
            (name, brand, category, price, stock, rating, description, image_url)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["name"],
            data["brand"],
            data["category"],
            float(data["price"]),
            int(data.get("stock", 10)),
            float(data.get("rating", 4.0)),
            data.get("description", ""),
            data.get("image_url", "https://via.placeholder.com/400x400.png")
        ))
        conn.commit()
        cur.close(); conn.close()
        
        return jsonify({"message": "Product added", "product_id": cur.lastrowid}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/products/<int:product_id>", methods=["PUT"])
@require_admin
def update_product_admin(product_id, user_id, email):
    """PUT /api/admin/products/<id> — Update product."""
    data = request.get_json() or {}
    
    try:
        conn = get_db()
        cur  = conn.cursor()
        
        # Build dynamic update query
        updates = []
        values = []
        for key in ["name", "brand", "category", "price", "stock", "rating", "description", "image_url"]:
            if key in data:
                updates.append(f"{key} = %s")
                values.append(data[key])
        
        if not updates:
            return jsonify({"error": "No fields to update"}), 400
        
        values.append(product_id)
        query = f"UPDATE products SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, values)
        conn.commit()
        cur.close(); conn.close()
        
        return jsonify({"message": "Product updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin_bp.route("/products/<int:product_id>", methods=["DELETE"])
@require_admin
def delete_product_admin(product_id, user_id, email):
    """DELETE /api/admin/products/<id> — Delete product."""
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM products WHERE id = %s", (product_id,))
        conn.commit()
        cur.close(); conn.close()
        
        return jsonify({"message": "Product deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─────────────────────────────────────────────────────────────────
# ANALYTICS ENDPOINT
# ─────────────────────────────────────────────────────────────────

@admin_bp.route("/analytics", methods=["GET"])
@require_admin
def get_analytics(user_id, email):
    """GET /api/admin/analytics — Detailed analytics."""
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        
        # Most searched
        cur.execute("""
            SELECT search_query, COUNT(*) as count
            FROM search_history
            GROUP BY search_query
            ORDER BY count DESC
            LIMIT 10
        """)
        most_searched = cur.fetchall()
        
        # Top categories
        cur.execute("""
            SELECT category, COUNT(*) as count
            FROM products
            GROUP BY category
            ORDER BY count DESC
        """)
        top_categories = cur.fetchall()
        
        # Top rated products
        cur.execute("""
            SELECT id, name, rating, reviews
            FROM products
            ORDER BY rating DESC, reviews DESC
            LIMIT 10
        """)
        top_products = cur.fetchall()
        
        cur.close(); conn.close()
        
        return jsonify({
            "most_searched":     most_searched,
            "top_categories":    top_categories,
            "top_rated_products": top_products,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500