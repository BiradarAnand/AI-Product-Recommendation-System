# unified_chat_route.py
# ─────────────────────────────────────────────────────────────────────
#  Single endpoint that handles BOTH:
#    • Occasion-based queries  → occasion_engine + Groq reply
#    • General product queries → Groq filter extract + MySQL + Groq reply
#
#  POST /api/chat/unified
#  Request  : { message, history, refinements, user_id (optional) }
#  Response : { type, reply, products, outfit, occasion, filters_used, nlp }
# ─────────────────────────────────────────────────────────────────────

import os
import json
import re
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
import mysql.connector
from groq import Groq
from dotenv import load_dotenv

# ── import your existing occasion modules ─────────────────────────────
from occasion_nlp    import classify_occasion, OCCASION_LABELS, OCCASION_ICONS
from occasion_engine import (
    fetch_outfit_set,
    fetch_occasion_products,
    get_user_preferences,
    CHATBOT_REPLIES,
)

load_dotenv()

unified_chat_bp = Blueprint("unified_chat", __name__)

# ── Clients / config ──────────────────────────────────────────────────
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "127.0.0.1"),
    "port":     int(os.getenv("DB_PORT", 3305)),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", "Passwordmysql"),
    "database": os.getenv("DB_NAME",     "myecomerce"),
}

OCCASION_CONFIDENCE_THRESHOLD = 0.15   # tune this if needed


# ═════════════════════════════════════════════════════════════════════
#  DB HELPERS
# ═════════════════════════════════════════════════════════════════════

def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def fetch_user_context(user_id: int) -> dict:
    """Pull last 10 searches + wishlist categories/brands for personalisation."""
    if not user_id:
        return {}
    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)

        cur.execute(
            "SELECT search_query FROM search_history "
            "WHERE user_id = %s ORDER BY searched_at DESC LIMIT 10",
            (user_id,),
        )
        searches = [r["search_query"] for r in cur.fetchall()]

        cur.execute(
            "SELECT DISTINCT p.category, p.brand "
            "FROM wishlist w JOIN products p ON w.product_id = p.id "
            "WHERE w.user_id = %s LIMIT 10",
            (user_id,),
        )
        wish = cur.fetchall()
        db.close()

        return {
            "recent_searches":      searches,
            "wishlist_categories":  list({i["category"] for i in wish}),
            "wishlist_brands":      list({i["brand"]    for i in wish}),
        }
    except Exception as e:
        print(f"[unified] fetch_user_context error: {e}")
        return {}


def save_search(user_id, query: str):
    if not user_id or not query:
        return
    try:
        db  = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO search_history (user_id, search_query, searched_at) "
            "VALUES (%s, %s, %s)",
            (user_id, query, datetime.utcnow()),
        )
        db.commit()
        db.close()
    except Exception as e:
        print(f"[unified] save_search error: {e}")


# ═════════════════════════════════════════════════════════════════════
#  GENERAL PATH — helpers
# ═════════════════════════════════════════════════════════════════════

def extract_filters(message: str, user_context: dict) -> dict:
    """
    Groq llama3-8b: parse message into structured filter JSON.
    Fast model used here — filter extraction doesn't need quality reasoning.
    """
    context_hint = ""
    if user_context.get("recent_searches"):
        context_hint = (
            f"\nUser recently searched: "
            f"{', '.join(user_context['recent_searches'][:3])}"
        )

    system = """You are a filter-extraction assistant for an e-commerce app.
Extract product search filters from the user message and return ONLY valid JSON.

Available categories:
Track Pants, Sports Shoes, Tshirts, Casual Shoes, Watches, Shirts,
Jeans, Trousers, Blazers, Formal Shoes, Sneakers, Kurtas, Ethnic Wear,
Activewear, Shorts, Caps, Sunglasses

Return JSON with these optional keys (omit keys that are not mentioned):
{
  "category":   string,
  "brand":      string,
  "keyword":    string,
  "max_price":  number,
  "min_price":  number,
  "min_rating": number (1-5)
}

Examples:
"blue jeans under 2000"       → {"category":"Jeans","max_price":2000,"keyword":"blue"}
"Nike sports shoes"           → {"category":"Sports Shoes","brand":"Nike"}
"good rated casual shirt"     → {"category":"Shirts","min_rating":4}
"watches between 500 and 3000"→ {"min_price":500,"max_price":3000,"category":"Watches"}
"""

    resp = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system",  "content": system},
            {"role": "user",    "content": message + context_hint},
        ],
        temperature=0.1,
        max_tokens=300,
    )
    raw = resp.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"keyword": message}


def fetch_general_products(filters: dict, limit: int = 6) -> list:
    """Build dynamic SQL from extracted filters and return ranked products."""
    conditions = ["stock > 0"]
    params     = []

    if filters.get("category"):
        conditions.append("LOWER(category) LIKE %s")
        params.append(f"%{filters['category'].lower()}%")
    if filters.get("brand"):
        conditions.append("LOWER(brand) LIKE %s")
        params.append(f"%{filters['brand'].lower()}%")
    if filters.get("max_price"):
        conditions.append("price <= %s")
        params.append(filters["max_price"])
    if filters.get("min_price"):
        conditions.append("price >= %s")
        params.append(filters["min_price"])
    if filters.get("min_rating"):
        conditions.append("rating >= %s")
        params.append(filters["min_rating"])
    if filters.get("keyword"):
        conditions.append(
            "(LOWER(name) LIKE %s OR LOWER(description) LIKE %s OR LOWER(brand) LIKE %s)"
        )
        kw = f"%{filters['keyword'].lower()}%"
        params.extend([kw, kw, kw])

    where = " AND ".join(conditions)
    sql   = f"""
        SELECT id, name, description, category, price, stock,
               rating, reviews, image_url, brand
        FROM products
        WHERE {where}
        ORDER BY rating DESC, reviews DESC
        LIMIT %s
    """
    params.append(limit)

    try:
        db  = get_db()
        cur = db.cursor(dictionary=True)
        cur.execute(sql, params)
        rows = cur.fetchall()
        db.close()
        for r in rows:
            r["price"]   = float(r["price"]  or 0)
            r["rating"]  = float(r["rating"] or 0)
            r["reviews"] = int(r["reviews"]  or 0)
        return rows
    except Exception as e:
        print(f"[unified] fetch_general_products error: {e}")
        import traceback; traceback.print_exc()
        return []

def generate_general_reply(
    message: str,
    products: list,
    user_context: dict,
    chat_history: list,
) -> str:
    """Groq llama3-70b: write a friendly reply for the general product path."""
    product_summary = "\n".join(
        f"- {p['name']} | {p['brand']} | ₹{p['price']} "
        f"| ⭐{p['rating']} | {p['category']}"
        for p in products
    ) or "No exact matches found."

    wish_hint = ""
    if user_context.get("wishlist_categories"):
        wish_hint = (
            f"The user has previously saved items from: "
            f"{', '.join(set(user_context['wishlist_categories']))}. "
            "Mention this only if relevant."
        )

    system = f"""You are a helpful and friendly shopping assistant for an Indian e-commerce store.
Recommend products and explain briefly why they match the user's needs.
Keep responses to 2-4 sentences. Use ₹ for prices. Be warm and helpful.
{wish_hint}

Matching products:
{product_summary}

Rules:
- Mention 2-3 top picks by name with a short reason
- If no products found, ask a clarifying question
- Never invent products not in the list above
- If the user asks a general question (not product search), just answer helpfully
"""
    messages = [{"role": "system", "content": system}]
    for turn in chat_history[-4:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=400,
    )
    return resp.choices[0].message.content.strip()


# ═════════════════════════════════════════════════════════════════════
#  OCCASION PATH — helper
# ═════════════════════════════════════════════════════════════════════

def generate_occasion_reply(
    message: str,
    occasion_key: str,
    occasion_label: str,
    outfit: dict,
    products: list,
    user_context: dict,
    chat_history: list,
) -> str:
    """
    Groq llama3-70b: write a personalised occasion reply.
    Replaces the old hardcoded CHATBOT_REPLIES dict.
    """
    outfit_summary = "\n".join(
        f"- {slot.upper()}: {item['name']} | {item['brand']} | ₹{item['price']} "
        f"| match {item.get('match_pct', '?')}%"
        for slot, item in outfit.items()
    ) if outfit else "No outfit set found."

    top_products = "\n".join(
        f"- {p['name']} | {p['brand']} | ₹{p['price']} | ⭐{p['rating']}"
        for p in products[:5]
    ) or "No additional products found."

    wish_hint = ""
    if user_context.get("wishlist_categories"):
        wish_hint = (
            f"User has saved interest in: "
            f"{', '.join(set(user_context['wishlist_categories']))}."
        )

    system = f"""You are a warm, friendly fashion assistant for an Indian e-commerce app.
The user needs an outfit for: {occasion_label}
{wish_hint}

Curated 4-piece outfit:
{outfit_summary}

More matching products:
{top_products}

Write 2-3 sentences explaining:
1. Why this outfit works for {occasion_label}
2. One specific highlight from the curated set (mention item name + price)
Keep it conversational, encouraging, and specific. Use ₹ for prices.
"""
    messages = [{"role": "system", "content": system}]
    for turn in chat_history[-4:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": message})

    resp = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=400,
    )
    return resp.choices[0].message.content.strip()


# ═════════════════════════════════════════════════════════════════════
#  MAIN ENDPOINT
# ═════════════════════════════════════════════════════════════════════

@unified_chat_bp.route("/api/chat/unified", methods=["POST"])
def unified_chat():
    """
    Request JSON:
    {
      "message":     string   (required),
      "history":     list     (optional, last N turns),
      "refinements": dict     (optional, e.g. {"budget":"mid","brand":"Nike"}),
      "user_id":     int      (optional, passed from frontend for guest mode)
    }

    Response JSON:
    {
      "type":         "occasion" | "general" | "clarify",
      "reply":        string,
      "products":     list,
      "outfit":       dict   (occasion only),
      "occasion":     string (occasion only),
      "occasion_label": string (occasion only),
      "occasion_icon":  string (occasion only),
      "filters_used": dict   (general only),
      "nlp": {
        "confidence":   float,
        "method":       string,
        "alternatives": list
      }
    }
    """
    # ── 1. Parse request ──────────────────────────────────────────────
    data        = request.get_json() or {}
    message     = (data.get("message") or "").strip()
    history     = data.get("history")     or []
    refinements = data.get("refinements") or {}

    if not message:
        return jsonify({"error": "message is required"}), 400

    # ── 2. Resolve user_id (JWT optional — guest fallback) ────────────
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
    except Exception:
        pass
    # also accept explicit user_id from frontend (guest sessions)
    if not user_id:
        user_id = data.get("user_id")

    # ── 3. Fetch user context from MySQL ─────────────────────────────
    user_context = fetch_user_context(user_id)
    prefs        = get_user_preferences(user_id) if user_id else {}

    # ── 4. NLP: classify occasion ─────────────────────────────────────
    nlp_result = classify_occasion(message)
    occasion   = nlp_result["occasion"]
    confidence = nlp_result["confidence"]
    nlp_meta   = {
        "confidence":   confidence,
        "method":       nlp_result["method"],
        "alternatives": nlp_result.get("alternatives", []),
    }

    print(
        f"[unified] msg='{message}' "
        f"occasion={occasion} conf={confidence} method={nlp_result['method']}"
    )

    # ── 5. CLARIFY — confidence too low, no keyword matched ───────────
    if not occasion or confidence < OCCASION_CONFIDENCE_THRESHOLD:

        # try general Groq path first before giving up
        try:
            filters  = extract_filters(message, user_context)
            products = fetch_general_products(filters, limit=6)

            # if products found → treat as general query
            if products:
                reply = generate_general_reply(message, products, user_context, history)
                save_search(user_id, message)
                return jsonify({
                    "type":         "general",
                    "reply":        reply,
                    "products":     products,
                    "outfit":       {},
                    "filters_used": filters,
                    "nlp":          nlp_meta,
                })
        except Exception as e:
            print(f"[unified] general path error: {e}")

        # no products found either → ask user to clarify
        from occasion_nlp import OCCASION_LABELS, OCCASION_ICONS
        from occasion_engine import OCCASION_CATEGORIES
        save_search(user_id, message)
        return jsonify({
            "type":  "clarify",
            "reply": (
                "I'm not sure what you're looking for 🤔 "
                "Could you pick an occasion below or describe what you need? "
                "E.g. 'job interview', 'gym session', 'wedding', 'date night'..."
            ),
            "occasions": [
                {"key": k, "label": OCCASION_LABELS[k], "icon": OCCASION_ICONS[k]}
                for k in OCCASION_CATEGORIES
            ],
            "products": [],
            "outfit":   {},
            "nlp":      nlp_meta,
        })

    # ── 6. OCCASION PATH ──────────────────────────────────────────────
    try:
        outfit   = fetch_outfit_set(occasion, prefs, refinements)
        products = fetch_occasion_products(occasion, prefs, refinements)
        top12    = products[:12]

        if not outfit and not top12:
            return jsonify({
                "type":     "no_results",
                "occasion": occasion,
                "reply": (
                    f"Hmm, I couldn't find products for "
                    f"{OCCASION_LABELS.get(occasion, occasion)} right now. "
                    "Try adjusting your budget filter."
                ),
                "products": [],
                "outfit":   {},
                "nlp":      nlp_meta,
            })

        reply = generate_occasion_reply(
            message, occasion,
            OCCASION_LABELS.get(occasion, occasion),
            outfit, top12, user_context, history,
        )

        save_search(user_id, message)

        return jsonify({
            "type":           "occasion",
            "occasion":       occasion,
            "occasion_label": OCCASION_LABELS.get(occasion, occasion),
            "occasion_icon":  OCCASION_ICONS.get(occasion, "🛍️"),
            "reply":          reply,
            "products":       top12,
            "outfit":         outfit,
            "filters_used":   {},
            "nlp":            nlp_meta,
        })

    except Exception as e:
        print(f"[unified] occasion path error: {e}")
        import traceback; traceback.print_exc()
        return jsonify({"error": f"Occasion engine error: {str(e)}"}), 500


# ═════════════════════════════════════════════════════════════════════
#  OCCASIONS LIST  (used by frontend chip buttons on load)
# ═════════════════════════════════════════════════════════════════════

@unified_chat_bp.route("/api/chat/occasions", methods=["GET"])
def list_occasions():
    """Returns all occasion options for the frontend chip buttons."""
    from occasion_nlp    import OCCASION_LABELS, OCCASION_ICONS
    from occasion_engine import OCCASION_CATEGORIES
    return jsonify([
        {"key": k, "label": OCCASION_LABELS[k], "icon": OCCASION_ICONS[k]}
        for k in OCCASION_CATEGORIES
    ])