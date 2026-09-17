"""
tools/product_search.py

Controlled product retrieval layer. Agents never query the database or
an external API directly — they call these two functions, which return
plain dicts in a normalized schema, each tagged with a "source".

Fixes applied (2024-09):
  - search_internal now uses sqlite3.Row properly (no dictionary=True)
  - Category intent map added to translate chatbot categories → real DB values
  - search_external BuyWhere: removed deliver_to=IN (causes 500), added country_code fallback
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Ensure backend/ is on the path so `db` can always be imported,
# whether this file is run directly or imported from agents/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from db import get_catalog_db

BUYWHERE_URL     = "https://api.buywhere.ai/v1/products/search"
BUYWHERE_API_KEY = os.getenv("BUYWHERE_API_KEY")
BUYWHERE_COUNTRY = os.getenv("BUYWHERE_COUNTRY")


# ── Catalog category/sub_category mapping ──────────────────────────────────
# The SQLite catalog uses:
#   category     → "men's clothing" | "sports & fitness" | "women's shoes" | ...
#   sub_category → "Jeans" | "T-shirts & Polos" | "Shoes" | "All Sports..." | ...
#
# Chatbot intents use friendly names like "Shirts", "Jeans", "Sneakers".
# This map translates intent → (category_filter, sub_category_filter).
# Both filters are applied as LIKE patterns. None means "skip that filter".

INTENT_TO_CATALOG = {
    # Tops / Shirts
    "Shirts":       ("men's clothing", None),
    "Tshirts":      ("men's clothing", "T-shirts"),
    "Blazers":      ("men's clothing", None),
    "Kurtas":       ("men's clothing", None),
    "Ethnic Wear":  ("men's clothing", None),
    "Activewear":   ("sports & fitness", None),
    # Bottoms
    "Jeans":        ("men's clothing", "Jeans"),
    "Trousers":     ("men's clothing", None),
    "Track Pants":  ("sports & fitness", None),
    "Shorts":       ("sports & fitness", None),
    # Footwear
    "Casual Shoes": ("women's shoes",   None),
    "Formal Shoes": ("women's shoes",   None),
    "Sports Shoes": ("sports & fitness","All Sports"),
    "Sneakers":     ("women's shoes",   None),
    # Accessories
    "Watches":      ("stores",          None),
    "Caps":         ("sports & fitness",None),
    "Sunglasses":   ("stores",          None),
}

# Fallback: broad keyword search against name/description when no mapping found
def _category_conditions(intent_categories: list) -> tuple:
    """Return (conditions_list, params_list) for the intent categories."""
    if not intent_categories:
        return [], []

    conditions, params = [], []
    mapped_clauses = []

    for cat in intent_categories:
        mapping = INTENT_TO_CATALOG.get(cat)
        if mapping:
            db_cat, db_sub = mapping
            if db_sub:
                mapped_clauses.append(
                    "(LOWER(category) LIKE %s AND LOWER(sub_category) LIKE %s)"
                )
                params.extend([f"%{db_cat.lower()}%", f"%{db_sub.lower()}%"])
            else:
                mapped_clauses.append("LOWER(category) LIKE %s")
                params.append(f"%{db_cat.lower()}%")
        else:
            # Fallback: keyword search on name
            mapped_clauses.append(
                "(LOWER(name) LIKE %s OR LOWER(sub_category) LIKE %s)"
            )
            kw = f"%{cat.lower()}%"
            params.extend([kw, kw])

    if mapped_clauses:
        conditions.append("(" + " OR ".join(mapped_clauses) + ")")

    return conditions, params


def search_internal(filters: dict, limit: int = 6) -> list:
    """Query the internal `products` table (SQLite catalog) using only
    parameterized filters built here.

    Accepts filters dict with keys:
      category   – chatbot intent category name (e.g. "Jeans", "Sports Shoes")
      categories – list of chatbot intent categories
      brand      – brand name substring
      keyword    – free-text keyword matched against name/description/brand
      max_price  – upper price bound
      min_price  – lower price bound
      min_rating – minimum star rating (1–5)
    """
    # SQLite uses ? placeholders, not %s
    conditions = ["(stock IS NULL OR stock > 0)"]
    params = []

    # ── Category / intent mapping ───────────────────────────────────────────
    intent_cats = []
    if filters.get("categories"):
        intent_cats = filters["categories"]
    elif filters.get("category"):
        intent_cats = [filters["category"]]

    if intent_cats:
        cat_conditions, cat_params = _category_conditions(intent_cats)
        if cat_conditions:
            # Convert %s → ? for SQLite
            for cond in cat_conditions:
                conditions.append(cond.replace("%s", "?"))
            params.extend(cat_params)

    # ── Brand ───────────────────────────────────────────────────────────────
    if filters.get("brand"):
        conditions.append("LOWER(brand) LIKE ?")
        params.append(f"%{filters['brand'].lower()}%")

    # ── Price bounds ────────────────────────────────────────────────────────
    if filters.get("max_price"):
        conditions.append("price <= ?")
        params.append(filters["max_price"])
    if filters.get("min_price"):
        conditions.append("price >= ?")
        params.append(filters["min_price"])

    # ── Rating ──────────────────────────────────────────────────────────────
    if filters.get("min_rating"):
        conditions.append("rating >= ?")
        params.append(filters["min_rating"])

    # ── Keyword (free text) ──────────────────────────────────────────────────
    if filters.get("keyword"):
        conditions.append(
            "(LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(brand) LIKE ?)"
        )
        kw = f"%{filters['keyword'].lower()}%"
        params.extend([kw, kw, kw])

    where = " AND ".join(conditions)
    sql = f"""
        SELECT id, name, description, category, sub_category, price, stock,
               rating, reviews, image_url, brand
        FROM products
        WHERE {where}
        ORDER BY rating DESC, reviews DESC
        LIMIT ?
    """
    params.append(limit)

    try:
        conn = get_catalog_db()   # returns SQLite conn with row_factory = sqlite3.Row
        cur  = conn.cursor()
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        result = []
        for r in rows:
            row = dict(r)   # sqlite3.Row → plain dict
            row["price"]    = float(row.get("price")   or 0)
            row["rating"]   = float(row.get("rating")  or 0)
            row["reviews"]  = int(row.get("reviews")   or 0)
            row["source"]   = "internal"
            # normalise category display
            row["category"] = row.get("sub_category") or row.get("category") or ""
            result.append(row)
        return result
    except Exception as e:
        print(f"[product_search] search_internal error: {e}")
        import traceback; traceback.print_exc()
        return []


def search_external(query: str, limit: int = 6) -> list:
    """Fallback search via BuyWhere's product catalog API. Only call this
    when search_internal() returns nothing.

    Results are tagged source='external' and MUST be presented as
    suggestions outside our catalog — never as in-stock items.
    """
    if not query:
        return []

    try:
        headers = {}
        if BUYWHERE_API_KEY:
            headers["Authorization"] = f"Bearer {BUYWHERE_API_KEY}"

        params = {
            "q": query,
            "limit": limit,
        }
        if BUYWHERE_COUNTRY:
            params["country_code"] = BUYWHERE_COUNTRY

        resp = requests.get(
            BUYWHERE_URL,
            params=params,
            headers=headers,
            timeout=6,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        items = data.get("data") or data.get("results") or data.get("products") or []
        for item in items[:limit]:
            results.append({
                "id":          None,
                "name":        item.get("title") or item.get("name"),
                "description": item.get("domain") or item.get("description") or "",
                "category":    item.get("category") or None,
                "price":       item.get("price"),
                "currency":    item.get("currency", "INR"),
                "stock":       None,
                "rating":      item.get("rating") or item.get("stars"),
                "reviews":     item.get("reviews") or item.get("review_count"),
                "image_url":   item.get("image") or item.get("image_url"),
                "brand":       item.get("brand") or item.get("source") or item.get("domain"),
                "product_url": item.get("url") or item.get("link"),
                "source":      "external",
            })
        return results
    except Exception as e:
        print(f"[product_search] search_external error: {e}")
        return []