"""
chatbot_route.py — Groq-powered chatbot with product recommendation
"""

import os
import json
import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from groq import Groq
from datetime import datetime
from db import get_db

chatbot_bp  = Blueprint("chatbot", __name__)
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# ── Product fetcher ───────────────────────────────────────────────────────────
def fetch_products(filters: dict, limit: int = 6) -> list:
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
    where_clause = " AND ".join(conditions)
    query = f"""
        SELECT id, name, description, category, price, stock, rating, reviews, image_url, brand
        FROM products WHERE {where_clause}
        ORDER BY rating DESC, reviews DESC LIMIT %s
    """
    params.append(limit)
    conn = None                                          # ✅ FIXED
    try:
        conn   = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        rows = cursor.fetchall()
        cursor.close()
        return rows
    except Exception as e:
        print(f"[fetch_products] error: {e}")
        return []
    finally:
        if conn:                                         # ✅ FIXED
            try: conn.close()
            except: pass
 
# ── Save chat to search history ───────────────────────────────────────────────

def save_search(user_id: int, query: str):
    if not user_id or not query:
        return
    conn = None                                          # ✅ FIXED
    try:
        conn   = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO search_history (user_id, search_query, searched_at) VALUES (%s, %s, %s)",
            (user_id, query, datetime.utcnow()),
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"[save_search] error: {e}")
    finally:
        if conn:                                         # ✅ FIXED
            try: conn.close()
            except: pass
 

# ── Filter extractor (Groq step 1) ────────────────────────────────────────────
def extract_filters(user_message: str, user_context: dict) -> dict:
    system_prompt = """You are a filter-extraction assistant for an e-commerce app.
Extract product search filters from the user message and return ONLY valid JSON.
Available categories: Shirts, Jeans, Watches, Track Pants, Tshirts, Casual Shoes, Sports Shoes, Trousers.

Return JSON with these optional keys (omit if not mentioned):
{
  "category": string,
  "brand": string,
  "keyword": string,
  "max_price": number,
  "min_price": number,
  "min_rating": number (1-5)
}

Examples:
- "show me blue jeans under 2000" → {"category":"Jeans","max_price":2000,"keyword":"blue"}
- "Nike sports shoes" → {"category":"Sports Shoes","brand":"Nike"}
- "casual shirt good rating" → {"category":"Shirts","min_rating":4}
"""
    context_hint = ""
    if user_context.get("recent_searches"):
        context_hint = f"\nUser recently searched: {', '.join(user_context['recent_searches'][:3])}"

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message + context_hint},
        ],
        temperature=0.1,
        max_tokens=300,
    )
    raw = re.sub(r"```json|```", "", response.choices[0].message.content.strip()).strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"keyword": user_message}


# ── Recommendation reply (Groq step 2) ────────────────────────────────────────
def generate_reply(user_message: str, products: list,
                   user_context: dict, chat_history: list) -> str:
    product_summary = "\n".join(
        f"- {p['name']} | {p['brand']} | ₹{p['price']} | ⭐{p['rating']} | Category: {p['category']}"
        for p in products
    )
    wish_hint = ""
    if user_context.get("wishlist_categories"):
        wish_hint = f"The user has shown interest in: {', '.join(set(user_context['wishlist_categories']))}."

    system_prompt = f"""You are a helpful and friendly shopping assistant for an Indian e-commerce store.
Your job is to recommend products and explain WHY they match the user's needs.
Keep responses concise (3-5 sentences max). Use ₹ for prices. Be warm and helpful.
{wish_hint}

Available products matching the query:
{product_summary if product_summary else "No exact matches found, suggest alternatives."}

Rules:
- Mention 2-3 top picks by name with a brief reason
- If no products found, ask clarifying questions
- Never make up products not in the list above
- If the user is asking a general question (not product search), just answer helpfully
"""
    messages = [{"role": "system", "content": system_prompt}]
    for turn in chat_history[-4:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user_message})

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()


# ── Main chat endpoint ────────────────────────────────────────────────────────
@chatbot_bp.route("/api/chat", methods=["POST"])
@jwt_required()
def chat():
    user_id      = get_jwt_identity()
    data         = request.get_json()
    user_message = data.get("message", "").strip()
    chat_history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    user_context = fetch_user_context(user_id)
    filters      = extract_filters(user_message, user_context)
    products     = fetch_products(filters, limit=6)

    if not products and filters.get("keyword"):
        products = fetch_products({"keyword": filters["keyword"]}, limit=6)

    reply = generate_reply(user_message, products, user_context, chat_history)
    save_search(user_id, user_message)

    return jsonify({"reply": reply, "products": products, "filters_used": filters})


# ── Guest chat ─────────────────────────────────────────────────────────────────
@chatbot_bp.route("/api/chat/guest", methods=["POST"])
def guest_chat():
    data         = request.get_json()
    user_message = data.get("message", "").strip()
    chat_history = data.get("history", [])

    if not user_message:
        return jsonify({"error": "Message is required"}), 400

    filters  = extract_filters(user_message, {})
    products = fetch_products(filters, limit=6)

    if not products and filters.get("keyword"):
        products = fetch_products({"keyword": filters["keyword"]}, limit=6)

    reply = generate_reply(user_message, products, {}, chat_history)
    return jsonify({"reply": reply, "products": products, "filters_used": filters})