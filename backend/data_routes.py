"""
data_routes.py — FIXED for Filessio 5-connection limit
Every route has finally: conn.close() — guaranteed release
"""

import os
import jwt
from flask import Blueprint, request, jsonify
from functools import wraps
from db import get_db

data_bp    = Blueprint("data", __name__)
JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret")


def get_user_id():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    try:
        token   = auth.split(" ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload.get("user_id")
    except Exception:
        return None

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = get_user_id()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, user_id=user_id, **kwargs)
    return wrapper

def _notify():
    try:
        from auto_trainer import notify_new_interaction
        notify_new_interaction()
    except Exception:
        pass


# ── CART ──────────────────────────────────────────────────────────

@data_bp.route("/cart", methods=["GET"])
@require_auth
def get_cart(user_id: int):
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT c.id, c.product_id, c.quantity, c.price_at_add,
                   p.name, p.category, p.rating, p.image_url,
                   (c.quantity * c.price_at_add) AS item_total
            FROM cart c
            JOIN products p ON c.product_id = p.id
            WHERE c.user_id = %s
            ORDER BY c.added_at DESC
        """, (user_id,))
        items    = cur.fetchall()
        cur.close()
        subtotal = sum(float(i["item_total"]) for i in items) if items else 0
        discount = subtotal * 0.05
        total    = subtotal - discount
        return jsonify({
            "count": len(items), "items": items,
            "subtotal": round(subtotal, 2),
            "discount": round(discount, 2),
            "total":    round(total, 2),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/cart", methods=["POST"])
@require_auth
def add_to_cart(user_id: int):
    data       = request.get_json() or {}
    product_id = data.get("product_id")
    quantity   = int(data.get("quantity", 1))
    if not product_id or quantity < 1:
        return jsonify({"error": "Invalid product_id or quantity"}), 400
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        if not product:
            cur.close()
            return jsonify({"error": "Product not found"}), 404
        price = float(product["price"])
        cur.execute("""
            INSERT INTO cart (user_id, product_id, quantity, price_at_add)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + %s
        """, (user_id, product_id, quantity, price, quantity))
        conn.commit()
        cur.close()
        _notify()
        return jsonify({"message": "Added to cart", "product_id": product_id, "quantity": quantity}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/cart/<int:product_id>", methods=["PUT"])
@require_auth
def update_cart_item(product_id: int, user_id: int):
    data     = request.get_json() or {}
    quantity = int(data.get("quantity", 1))
    if quantity < 1:
        return jsonify({"error": "Quantity must be >= 1"}), 400
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "UPDATE cart SET quantity = %s WHERE user_id = %s AND product_id = %s",
            (quantity, user_id, product_id)
        )
        if cur.rowcount == 0:
            cur.close()
            return jsonify({"error": "Item not in cart"}), 404
        conn.commit()
        cur.close()
        return jsonify({"message": "Updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/cart/<int:product_id>", methods=["DELETE"])
@require_auth
def remove_from_cart(product_id: int, user_id: int):
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "DELETE FROM cart WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        )
        if cur.rowcount == 0:
            cur.close()
            return jsonify({"error": "Item not in cart"}), 404
        conn.commit()
        cur.close()
        return jsonify({"message": "Removed from cart"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


# ── WISHLIST ──────────────────────────────────────────────────────

@data_bp.route("/wishlist", methods=["GET"])
@require_auth
def get_wishlist(user_id: int):
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT w.id, w.product_id, w.added_at,
                   p.name, p.price, p.rating, p.category, p.image_url, p.reviews
            FROM wishlist w
            JOIN products p ON w.product_id = p.id
            WHERE w.user_id = %s
            ORDER BY w.added_at DESC
        """, (user_id,))
        items = cur.fetchall()
        cur.close()
        return jsonify({"count": len(items), "items": items})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/wishlist", methods=["POST"])
@require_auth
def add_to_wishlist(user_id: int):
    data       = request.get_json() or {}
    product_id = data.get("product_id")
    if not product_id:
        return jsonify({"error": "product_id is required"}), 400
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("SELECT id FROM products WHERE id = %s", (product_id,))
        if not cur.fetchone():
            cur.close()
            return jsonify({"error": "Product not found"}), 404
        cur.execute(
            "INSERT IGNORE INTO wishlist (user_id, product_id) VALUES (%s, %s)",
            (user_id, product_id)
        )
        conn.commit()
        cur.close()
        _notify()
        return jsonify({"message": "Added to wishlist", "product_id": product_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/wishlist/<int:product_id>", methods=["DELETE"])
@require_auth
def remove_from_wishlist(product_id: int, user_id: int):
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute(
            "DELETE FROM wishlist WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        )
        if cur.rowcount == 0:
            cur.close()
            return jsonify({"error": "Not in wishlist"}), 404
        conn.commit()
        cur.close()
        return jsonify({"message": "Removed from wishlist"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/wishlist/<int:product_id>/to-cart", methods=["POST"])
@require_auth
def move_wishlist_to_cart(product_id: int, user_id: int):
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("SELECT price FROM products WHERE id = %s", (product_id,))
        product = cur.fetchone()
        if not product:
            cur.close()
            return jsonify({"error": "Product not found"}), 404
        cur.execute("""
            INSERT INTO cart (user_id, product_id, quantity, price_at_add)
            VALUES (%s, %s, 1, %s)
            ON DUPLICATE KEY UPDATE quantity = quantity + 1
        """, (user_id, product_id, float(product["price"])))
        cur.execute(
            "DELETE FROM wishlist WHERE user_id = %s AND product_id = %s",
            (user_id, product_id)
        )
        conn.commit()
        cur.close()
        return jsonify({"message": "Moved to cart", "product_id": product_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


# ── SEARCH HISTORY ────────────────────────────────────────────────

@data_bp.route("/search-history", methods=["GET"])
@require_auth
def get_search_history(user_id: int):
    limit = int(request.args.get("limit", 10))
    conn  = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT DISTINCT search_query, MAX(searched_at) as last_searched
            FROM search_history
            WHERE user_id = %s
            GROUP BY search_query
            ORDER BY last_searched DESC
            LIMIT %s
        """, (user_id, limit))
        queries = cur.fetchall()
        cur.close()
        return jsonify({"count": len(queries), "queries": [q["search_query"] for q in queries]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/search-history", methods=["DELETE"])
@require_auth
def clear_search_history(user_id: int):
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("DELETE FROM search_history WHERE user_id = %s", (user_id,))
        conn.commit()
        cur.close()
        return jsonify({"message": "Search history cleared"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


# ── USER PREFERENCES ──────────────────────────────────────────────

@data_bp.route("/user-preferences", methods=["GET"])
@require_auth
def get_user_preferences(user_id: int):
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT gender, age_group, style, budget_range,
                   preferred_categories, preferred_brands, size_preference
            FROM user_preferences WHERE user_id = %s
        """, (user_id,))
        prefs = cur.fetchone()
        cur.close()
        if not prefs:
            return jsonify({"error": "Preferences not set"}), 404
        return jsonify(prefs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass


@data_bp.route("/user-preferences", methods=["POST"])
@require_auth
def set_user_preferences(user_id: int):
    data       = request.get_json() or {}
    gender     = data.get("gender", "unisex")
    age_group  = data.get("age_group", "young_adult")
    style      = data.get("style", "mixed")
    budget     = data.get("budget_range", "mid")
    categories = data.get("preferred_categories", "")
    brands     = data.get("preferred_brands", "")
    size       = data.get("size_preference", None)
    conn = None
    try:
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("""
            INSERT INTO user_preferences
            (user_id, gender, age_group, style, budget_range,
             preferred_categories, preferred_brands, size_preference)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                gender = %s, age_group = %s, style = %s, budget_range = %s,
                preferred_categories = %s, preferred_brands = %s, size_preference = %s
        """, (
            user_id, gender, age_group, style, budget, categories, brands, size,
            gender, age_group, style, budget, categories, brands, size
        ))
        conn.commit()
        cur.close()
        return jsonify({"message": "Preferences saved", "user_id": user_id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn:
            try: conn.close()
            except: pass