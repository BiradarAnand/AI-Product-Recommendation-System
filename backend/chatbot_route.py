"""
chat_routes.py — Simple keyword-based chatbot
Maps user intent to DB categories and returns real products
No SpaCy, no ML needed — pure keyword matching
"""

from flask import Blueprint, request, jsonify
from db import get_db

chat_bp = Blueprint("chat", __name__)

# ── Intent → Category mapping ──────────────────────────────────────────────
INTENT_MAP = {
    # Occasions
    "job interview":    ["Shirts", "Trousers", "Formal Shoes", "Blazers"],
    "interview":        ["Shirts", "Trousers", "Formal Shoes", "Blazers"],
    "office":           ["Shirts", "Trousers", "Formal Shoes", "Blazers"],
    "work":             ["Shirts", "Trousers", "Formal Shoes"],
    "formal":           ["Shirts", "Trousers", "Blazers", "Formal Shoes"],
    "wedding":          ["Blazers", "Shirts", "Trousers", "Ethnic Wear", "Kurtas"],
    "function":         ["Blazers", "Kurtas", "Ethnic Wear", "Shirts"],
    "festival":         ["Kurtas", "Ethnic Wear"],
    "ethnic":           ["Kurtas", "Ethnic Wear"],
    "traditional":      ["Kurtas", "Ethnic Wear"],
    "casual":           ["Tshirts", "Jeans", "Casual Shoes", "Shorts"],
    "outing":           ["Tshirts", "Jeans", "Casual Shoes", "Sneakers"],
    "weekend":          ["Tshirts", "Jeans", "Shorts", "Sneakers"],
    "date":             ["Shirts", "Jeans", "Casual Shoes", "Watches"],
    "date night":       ["Shirts", "Jeans", "Casual Shoes", "Watches"],
    "party":            ["Shirts", "Jeans", "Sneakers", "Watches"],
    "gym":              ["Tshirts", "Track Pants", "Sports Shoes", "Activewear"],
    "sports":           ["Sports Shoes", "Track Pants", "Tshirts", "Activewear"],
    "workout":          ["Track Pants", "Sports Shoes", "Tshirts", "Activewear"],
    "fitness":          ["Track Pants", "Sports Shoes", "Activewear"],
    "running":          ["Sports Shoes", "Track Pants", "Activewear"],
    "beach":            ["Shorts", "Tshirts", "Casual Shoes", "Caps", "Sunglasses"],
    "vacation":         ["Shorts", "Tshirts", "Casual Shoes", "Sunglasses"],
    "travel":           ["Tshirts", "Jeans", "Casual Shoes", "Caps"],
    "college":          ["Tshirts", "Jeans", "Sneakers", "Casual Shoes"],
    "campus":           ["Tshirts", "Jeans", "Sneakers"],

    # Product types
    "shirt":            ["Shirts"],
    "shirts":           ["Shirts"],
    "tshirt":           ["Tshirts"],
    "t-shirt":          ["Tshirts"],
    "tshirts":          ["Tshirts"],
    "jeans":            ["Jeans"],
    "denim":            ["Jeans"],
    "trouser":          ["Trousers"],
    "trousers":         ["Trousers"],
    "pant":             ["Trousers", "Jeans"],
    "pants":            ["Trousers", "Jeans"],
    "track":            ["Track Pants"],
    "trackpant":        ["Track Pants"],
    "track pants":      ["Track Pants"],
    "watch":            ["Watches"],
    "watches":          ["Watches"],
    "shoe":             ["Casual Shoes", "Sports Shoes", "Formal Shoes", "Sneakers"],
    "shoes":            ["Casual Shoes", "Sports Shoes", "Formal Shoes", "Sneakers"],
    "sneaker":          ["Sneakers", "Casual Shoes"],
    "sneakers":         ["Sneakers", "Casual Shoes"],
    "formal shoes":     ["Formal Shoes"],
    "casual shoes":     ["Casual Shoes"],
    "sports shoes":     ["Sports Shoes"],
    "hoodie":           ["Tshirts"],
    "blazer":           ["Blazers"],
    "blazers":          ["Blazers"],
    "kurta":            ["Kurtas"],
    "kurtas":           ["Kurtas"],
    "shorts":           ["Shorts"],
    "cap":              ["Caps"],
    "caps":             ["Caps"],
    "sunglass":         ["Sunglasses"],
    "sunglasses":       ["Sunglasses"],
    "activewear":       ["Activewear"],
}

OCCASIONS = [
    {"key": "job_interview", "label": "Job Interview",       "icon": "💼"},
    {"key": "sports",        "label": "Sports & Gym",        "icon": "🏃"},
    {"key": "wedding",       "label": "Wedding / Function",  "icon": "🎊"},
    {"key": "casual_outing", "label": "Casual Outing",       "icon": "☀️"},
    {"key": "date_night",    "label": "Date Night",          "icon": "🌙"},
    {"key": "office",        "label": "Office & Work",       "icon": "🏢"},
    {"key": "festival",      "label": "Festival",            "icon": "🪔"},
    {"key": "beach",         "label": "Beach & Vacation",    "icon": "🏖️"},
    {"key": "college",       "label": "College / Campus",    "icon": "🎓"},
]

OCCASION_KEY_MAP = {
    "job_interview":  "interview",
    "sports":         "sports",
    "wedding":        "wedding",
    "casual_outing":  "casual",
    "date_night":     "date night",
    "office":         "office",
    "festival":       "festival",
    "beach":          "beach",
    "college":        "college",
}


def get_products_by_categories(categories, limit=12, budget=None):
    """Fetch products from DB matching given categories."""
    if not categories:
        return []
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        placeholders = ",".join(["%s"] * len(categories))
        query = f"""
            SELECT id, name, brand, category, price, rating, image_url, stock
            FROM products
            WHERE category IN ({placeholders})
        """
        params = list(categories)

        # Budget filter
        if budget:
            budget_map = {
                "budget":  1000,
                "mid":     3000,
                "premium": 8000,
            }
            max_price = budget_map.get(budget)
            if max_price:
                query += " AND price <= %s"
                params.append(max_price)

        query += " ORDER BY rating DESC, RAND() LIMIT %s"
        params.append(limit)

        cur.execute(query, params)
        products = cur.fetchall()
        cur.close()
        conn.close()
        return products
    except Exception as e:
        print(f"[Chat] DB error: {e}")
        return []


def detect_intent(message):
    """Find matching categories from message."""
    msg = message.lower().strip()

    # Check multi-word phrases first (longer matches win)
    matched_categories = []
    matched_keys = sorted(INTENT_MAP.keys(), key=len, reverse=True)

    for key in matched_keys:
        if key in msg:
            for cat in INTENT_MAP[key]:
                if cat not in matched_categories:
                    matched_categories.append(cat)

    return matched_categories


def detect_budget(message):
    """Extract budget filter from message."""
    msg = message.lower()
    if any(x in msg for x in ["under 1000", "below 1000", "less than 1000", "₹1000", "budget"]):
        return "budget"
    if any(x in msg for x in ["under 3000", "below 3000", "less than 3000", "₹3000"]):
        return "mid"
    if any(x in msg for x in ["under 8000", "below 8000", "less than 8000", "₹8000", "premium"]):
        return "premium"
    return None


def format_products(products):
    """Format products for frontend."""
    result = []
    for p in products:
        img = p.get("image_url", "")
        if img and not img.startswith("http"):
            img = f"https://ai-product-recommendation-system-by60.onrender.com/{img}"
        result.append({
            "id":        p["id"],
            "name":      p["name"],
            "brand":     p.get("brand", ""),
            "category":  p.get("category", ""),
            "price":     float(p.get("price", 0)),
            "rating":    float(p.get("rating", 0)),
            "image_url": img,
            "stock":     p.get("stock", 0),
        })
    return result


# ── Routes ─────────────────────────────────────────────────────────────────

@chat_bp.route("/api/chat/occasions", methods=["GET"])
def get_occasions():
    return jsonify(OCCASIONS)


@chat_bp.route("/api/chat/unified", methods=["POST"])
def unified_chat():
    data    = request.get_json() or {}
    message = (data.get("message") or "").strip()
    refinements = data.get("refinements") or {}
    budget  = refinements.get("budget") or detect_budget(message)

    if not message:
        return jsonify({
            "reply":    "Hi! 👋 Ask me anything — try 'job interview', 'gym outfit', or 'watches under ₹3000'",
            "type":     "clarify",
            "products": [],
            "occasions": OCCASIONS,
        })

    # Detect categories from message
    categories = detect_intent(message)

    # No match found
    if not categories:
        return jsonify({
            "reply":    f"I couldn't find products for '{message}'. Try something like: job interview, casual outing, gym, wedding, jeans, watches 👇",
            "type":     "clarify",
            "products": [],
            "occasions": OCCASIONS,
        })

    # Fetch products
    products = get_products_by_categories(categories, limit=12, budget=budget)
    formatted = format_products(products)

    if not formatted:
        return jsonify({
            "reply":    f"No products found for that right now. Try a different style or occasion!",
            "type":     "clarify",
            "products": [],
            "occasions": OCCASIONS,
        })

 # Build reply message
    cat_names = ", ".join(categories[:3])
    budget_map = {"budget": 1000, "mid": 3000, "premium": 8000}
    budget_text = f" under ₹{budget_map.get(budget, '')}" if budget else ""
    reply = f"Here are {len(formatted)} picks for {message}{budget_text} — showing {cat_names} 🎯"

    return jsonify({
        "reply":    reply,
        "type":     "general",
        "products": formatted,
        "total":    len(formatted),
        "categories": categories,
    })


@chat_bp.route("/api/chat/search", methods=["GET"])
def chat_search():
    q      = request.args.get("q", "").strip()
    budget = request.args.get("budget")
    limit  = int(request.args.get("limit", 12))

    categories = detect_intent(q) if q else []

    if not categories:
        return jsonify({"results": [], "total": 0})

    products  = get_products_by_categories(categories, limit=limit, budget=budget)
    formatted = format_products(products)

    return jsonify({"results": formatted, "total": len(formatted), "categories": categories})