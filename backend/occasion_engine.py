# occasion_engine.py  — v3 — Fixed for real DB categories
# Key fixes:
#   1. Unicode arrow removed from print() -> no more cp1252 crash on Windows
#   2. OUTFIT_SLOTS now uses ACTUAL DB categories (Shirts, Tshirts, Jeans, etc.)
#   3. OCCASION_CATEGORIES updated to match real DB data
#   4. Broader category fallbacks so outfit set is never empty
#   5. Better cosine reranking with purpose-aligned queries
# ─────────────────────────────────────────────────────────────────────

import os
import pickle
import numpy as np
from flask import Blueprint, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from occasion_nlp import classify_occasion, OCCASION_LABELS, OCCASION_ICONS
from db import get_db, get_catalog_db

load_dotenv()

occasion_bp = Blueprint("occasion", __name__)
MODEL_DIR   = "models"

# ── Actual categories in the DB ───────────────────────────────────────
# Based on database_info: Shirts, Jeans, Watches, Track Pants, Tshirts,
#                         Casual Shoes, Sports Shoes, Trousers
# ─────────────────────────────────────────────────────────────────────

OCCASION_PURPOSE_QUERIES = {
    "job_interview": (
        "formal professional shirt trouser classic slim regular solid striped "
        "business corporate interview presentation oxford watch leather analog"
    ),
    "sports": (
        "sport athletic gym workout running track pants tshirt sports shoes "
        "breathable flexible dry fit performance active training digital watch"
    ),
    "wedding_guest": (
        "ethnic traditional wedding premium elegant shirt trouser watch "
        "casual shoes formal classic occasion special ceremony"
    ),
    "casual_outing": (
        "casual comfortable jeans tshirt casual shoes everyday hangout "
        "relaxed regular weekend friends printed polo simple watch"
    ),
    "date_night": (
        "stylish smart premium slim shirt jeans watch casual shoes "
        "elegant classy attractive minimalist dark special evening"
    ),
    "office": (
        "formal office business shirt trouser casual shoes watch "
        "professional daily corporate solid stripe classic"
    ),
    "festival": (
        "traditional ethnic festival premium shirt trouser classic "
        "casual shoes elegant watch celebration special"
    ),
    "beach": (
        "casual light summer tshirt track pants casual shoes simple "
        "comfortable relaxed breezy watch sport"
    ),
}

# Slot-specific purpose queries aligned with real DB categories
SLOT_PURPOSE_QUERIES = {
    "job_interview": {
        "shirt": "formal cotton shirt office business professional slim solid striped classic",
        "pant":  "formal trouser slim straight flat classic business dark office",
        "shoes": "casual shoes formal classic leather oxford office professional",
        "watch": "formal analog watch classic business leather metal professional",
    },
    "sports": {
        "shirt": "tshirt dry fit sport athletic gym running performance breathable",
        "pant":  "track pants sport flexible gym running athletic training",
        "shoes": "sports shoes running grip cushion training outdoor performance",
        "watch": "watch sport digital waterproof rubber active fitness",
    },
    "wedding_guest": {
        "shirt": "shirt ethnic traditional premium elegant classic occasion",
        "pant":  "trouser formal traditional classic straight elegant",
        "shoes": "casual shoes formal elegant classic premium leather",
        "watch": "watch premium classic elegant gold analog metal",
    },
    "casual_outing": {
        "shirt": "tshirt casual comfortable everyday printed polo light shirt",
        "pant":  "jeans casual slim regular comfortable stretch everyday",
        "shoes": "casual shoes comfortable everyday canvas street lightweight",
        "watch": "watch casual everyday simple sport colorful",
    },
    "date_night": {
        "shirt": "shirt slim stylish premium smart solid date elegant",
        "pant":  "jeans slim stylish dark premium skinny",
        "shoes": "casual shoes stylish premium clean elegant leather",
        "watch": "watch stylish premium elegant slim metal minimalist",
    },
    "office": {
        "shirt": "shirt formal office business cotton regular solid striped",
        "pant":  "trouser formal office slim classic flat front dark",
        "shoes": "casual shoes formal classic office professional",
        "watch": "watch formal classic business analog leather metal",
    },
    "festival": {
        "shirt": "shirt traditional premium elegant classic ethnic",
        "pant":  "trouser traditional classic festive elegant",
        "shoes": "casual shoes traditional classic premium elegant",
        "watch": "watch premium classic elegant analog metal festive",
    },
    "beach": {
        "shirt": "tshirt casual light summer breezy cotton relaxed",
        "pant":  "track pants casual light summer comfortable",
        "shoes": "casual shoes light comfortable slip canvas",
        "watch": "watch sport casual digital simple rubber",
    },
}

# ── Categories use REAL DB values ────────────────────────────────────
OCCASION_CATEGORIES = {
    "job_interview": {
        "primary":   ["Shirts", "Trousers"],
        "secondary": ["Watches", "Casual Shoes"],
    },
    "sports": {
        "primary":   ["Track Pants", "Sports Shoes", "Tshirts"],
        "secondary": ["Watches"],
    },
    "wedding_guest": {
        "primary":   ["Shirts", "Trousers"],
        "secondary": ["Watches", "Casual Shoes"],
    },
    "casual_outing": {
        "primary":   ["Jeans", "Tshirts", "Casual Shoes"],
        "secondary": ["Shirts", "Watches", "Track Pants"],
    },
    "date_night": {
        "primary":   ["Shirts", "Jeans", "Watches"],
        "secondary": ["Casual Shoes", "Trousers"],
    },
    "office": {
        "primary":   ["Shirts", "Trousers"],
        "secondary": ["Watches", "Casual Shoes"],
    },
    "festival": {
        "primary":   ["Shirts", "Trousers"],
        "secondary": ["Watches", "Casual Shoes"],
    },
    "beach": {
        "primary":   ["Tshirts", "Track Pants", "Casual Shoes"],
        "secondary": ["Watches"],
    },
}

# ── Outfit slots using REAL DB categories ────────────────────────────
OUTFIT_SLOTS = {
    "job_interview": {
        "shirt": ["Shirts"],
        "pant":  ["Trousers", "Jeans"],
        "shoes": ["Casual Shoes"],
        "watch": ["Watches"],
    },
    "sports": {
        "shirt": ["Tshirts", "Shirts"],
        "pant":  ["Track Pants", "Trousers"],
        "shoes": ["Sports Shoes", "Casual Shoes"],
        "watch": ["Watches"],
    },
    "wedding_guest": {
        "shirt": ["Shirts"],
        "pant":  ["Trousers", "Jeans"],
        "shoes": ["Casual Shoes"],
        "watch": ["Watches"],
    },
    "casual_outing": {
        "shirt": ["Tshirts", "Shirts"],
        "pant":  ["Jeans", "Track Pants", "Trousers"],
        "shoes": ["Casual Shoes", "Sports Shoes"],
        "watch": ["Watches"],
    },
    "date_night": {
        "shirt": ["Shirts", "Tshirts"],
        "pant":  ["Jeans", "Trousers"],
        "shoes": ["Casual Shoes"],
        "watch": ["Watches"],
    },
    "office": {
        "shirt": ["Shirts"],
        "pant":  ["Trousers", "Jeans"],
        "shoes": ["Casual Shoes"],
        "watch": ["Watches"],
    },
    "festival": {
        "shirt": ["Shirts", "Tshirts"],
        "pant":  ["Trousers", "Jeans"],
        "shoes": ["Casual Shoes"],
        "watch": ["Watches"],
    },
    "beach": {
        "shirt": ["Tshirts", "Shirts"],
        "pant":  ["Track Pants", "Jeans", "Trousers"],
        "shoes": ["Casual Shoes", "Sports Shoes"],
        "watch": ["Watches"],
    },
}

SLOT_LABELS = {"shirt": "Shirt / Top", "pant": "Bottom", "shoes": "Footwear", "watch": "Watch"}
SLOT_ICONS  = {"shirt": "👕", "pant": "👖", "shoes": "👟", "watch": "⌚"}

BUDGET_RANGES = {
    "budget":  (0,    800),
    "mid":     (0,   3000),
    "premium": (500, 8000),
    "luxury":  (2000, 999999),
}

CHATBOT_REPLIES = {
    "job_interview": "Great choice! For a job interview you want to look sharp and confident. Here are outfits that will make a strong first impression 💼",
    "sports":        "Let's get you geared up! Here are performance picks to power your workout 🏃",
    "wedding_guest": "Exciting! Here are smart outfits to help you look great at the function 🎊",
    "casual_outing": "Comfort meets style! Here are relaxed yet stylish picks for your day out ☀️",
    "date_night":    "Setting the right mood matters! Here are sharp picks for your evening 🌙",
    "office":        "Looking sharp at work pays off. Here are office-ready outfits for you 🏢",
    "festival":      "Festival vibes! Here are elegant picks to celebrate in style 🪔",
    "beach":         "Sun, sand, style! Here are breezy picks for your trip 🏖️",
}

LOW_CONF_REPLY = (
    "I am not sure which occasion you mean. Could you pick one below or tell me more? "
    "For example: 'job interview', 'gym session', 'wedding function', 'date night'..."
)


# ── Content model loader ──────────────────────────────────────────────
_content_model = None

def _load_content_model():
    global _content_model
    if _content_model is not None:
        return _content_model
    path = os.path.join(MODEL_DIR, "content_model.pkl")
    if not os.path.exists(path):
        print("[OccasionEngine] content_model.pkl not found — using SQL-only scoring")
        return None
    try:
        with open(path, "rb") as f:
            _content_model = pickle.load(f)
        print("[OccasionEngine] TF-IDF content model loaded")
        return _content_model
    except Exception as e:
        print(f"[OccasionEngine] Failed to load content model: {e}")
        return None


def _row_to_text(row: dict) -> str:
    parts = [
        str(row.get("name",        "")),
        str(row.get("category",    "")),
        str(row.get("category",    "")),  # repeat for weight
        str(row.get("brand",       "")),
        str(row.get("brand",       "")),  # repeat for weight
        str(row.get("description", "")),
    ]
    return " ".join(p for p in parts if p and p.strip() and p.lower() != "nan").lower()


def _norm(arr: np.ndarray) -> np.ndarray:
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-9:
        return np.zeros_like(arr, dtype=float)
    return (arr - mn) / (mx - mn)


def _cosine_rerank(rows: list, purpose_query: str,
                   primary_cats: list,
                   w_cosine=0.50, w_cat=0.20, w_rating=0.20, w_review=0.10) -> list:
    if not rows:
        return rows

    model = _load_content_model()
    n     = len(rows)

    ratings  = np.array([float(r.get("rating",  0) or 0) for r in rows])
    reviews  = np.log1p(np.array([float(r.get("reviews", 0) or 0) for r in rows]))
    r_norm   = _norm(ratings)
    rv_norm  = _norm(reviews)

    primary_set = {c.lower() for c in primary_cats}
    cat_score   = np.array([
        1.0 if str(r.get("category", "")).lower() in primary_set else 0.4
        for r in rows
    ])

    if model is not None:
        try:
            texts     = [_row_to_text(r) for r in rows]
            prod_vecs = model.vectorizer.transform(texts)
            query_vec = model.vectorizer.transform([purpose_query.lower()])
            sims      = cosine_similarity(query_vec, prod_vecs).flatten()
            cos_norm  = _norm(sims)
        except Exception as e:
            print(f"[OccasionEngine] cosine error: {e}")
            cos_norm = np.zeros(n)
    else:
        cos_norm = np.zeros(n)
        w_rating = w_rating + w_cosine * 0.6
        w_review = w_review + w_cosine * 0.4
        w_cosine = 0.0

    final = (w_cosine * cos_norm + w_cat * cat_score +
             w_rating * r_norm   + w_review * rv_norm)

    for i, row in enumerate(rows):
        row["cosine_score"]   = round(float(cos_norm[i]), 4) if model else 0.0
        row["occasion_score"] = round(float(final[i]),   4)
        row["match_pct"]      = int(round(float(cos_norm[i]) * 100)) if model else None

    rows.sort(key=lambda x: x["occasion_score"], reverse=True)
    return rows


# ── DB helpers ────────────────────────────────────────────────────────

def get_user_preferences(user_id):
    if not user_id:
        return {}
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT * FROM user_preferences WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()

        if not row:
            return {}
        row["preferred_categories_list"] = [
            c.strip().lower()
            for c in (row.get("preferred_categories") or "").split(",") if c.strip()
        ]
        row["preferred_brands_list"] = [
            b.strip().title()
            for b in (row.get("preferred_brands") or "").split(",") if b.strip()
        ]
        return row
    except Exception as e:
        print(f"[prefs error] {e}")
        return {}


def _fetch_candidates(categories: list, min_p: float, max_p: float,
                      brand_filter: str = "") -> list:
    """Fetch candidate products with multi-category fallback."""
    if not categories:
        return []
    conn = None
    try:
        conn = get_catalog_db()
        cur  = conn.cursor()
        cat_ph       = ",".join(["?"] * len(categories))
        brand_clause = "AND p.brand = ?" if brand_filter else ""
        query = f"""
            SELECT p.id, p.name, p.description, p.category,
                   p.price, p.rating, p.reviews, p.image_url, p.brand
            FROM products p
            WHERE p.category IN ({cat_ph})
              AND p.price BETWEEN ? AND ?
              AND p.stock > 0
              {brand_clause}
            ORDER BY p.rating DESC, p.reviews DESC
            LIMIT 200
        """
        params = (*categories, min_p, max_p, *([brand_filter] if brand_filter else []))
        cur.execute(query, params)
        rows = [dict(row) for row in cur.fetchall()]
        cur.close()

        for row in rows:
            row["price"]   = float(row["price"]  or 0)
            row["rating"]  = float(row["rating"] or 0)
            row["reviews"] = int(row["reviews"]  or 0)
        return rows
    except Exception as e:
        print(f"[fetch_candidates error] {e}")
        import traceback; traceback.print_exc()
        return []
    finally:
        if conn:
            try: conn.close()
            except: pass


def fetch_occasion_products(occasion_key: str, prefs: dict, refinements: dict) -> list:
    cfg       = OCCASION_CATEGORIES.get(occasion_key, {})
    primary   = cfg.get("primary",   [])
    secondary = cfg.get("secondary", [])
    all_cats  = list(dict.fromkeys(primary + secondary))

    budget_key   = (refinements.get("budget")
                    or (prefs.get("budget_range") if prefs else None)
                    or "mid")
    min_p, max_p = BUDGET_RANGES.get(budget_key, (0, 999999))
    brand_filter = refinements.get("brand", "")

    candidates = _fetch_candidates(all_cats, min_p, max_p, brand_filter)
    if not candidates:
        return []

    purpose_query = OCCASION_PURPOSE_QUERIES.get(occasion_key, occasion_key)
    ranked = _cosine_rerank(candidates, purpose_query, primary)

    if prefs:
        user_cats = prefs.get("preferred_categories_list", [])
        for p in ranked:
            cat_low = p["category"].lower()
            if any(uc in cat_low or cat_low in uc for uc in user_cats):
                p["occasion_score"] = round(p["occasion_score"] + 0.05, 4)
        ranked.sort(key=lambda x: x["occasion_score"], reverse=True)

    return ranked


def fetch_outfit_set(occasion_key: str, prefs: dict, refinements: dict) -> dict:
    slots        = OUTFIT_SLOTS.get(occasion_key, {})
    slot_queries = SLOT_PURPOSE_QUERIES.get(occasion_key, {})

    budget_key   = (refinements.get("budget")
                    or (prefs.get("budget_range") if prefs else None)
                    or "mid")
    min_p, max_p = BUDGET_RANGES.get(budget_key, (0, 999999))
    brand_filter = refinements.get("brand", "")

    outfit = {}
    for slot_name, cats in slots.items():
        # Try each category in priority order; widen budget if needed
        candidates = _fetch_candidates(cats, min_p, max_p, brand_filter)

        if not candidates:
            # Widen budget by 50% and try again
            candidates = _fetch_candidates(cats, 0, max_p * 1.5, brand_filter)

        if not candidates:
            print(f"[outfit] No candidates for slot={slot_name} cats={cats}")
            continue

        slot_q = slot_queries.get(slot_name, OCCASION_PURPOSE_QUERIES.get(occasion_key, ""))
        ranked = _cosine_rerank(candidates, slot_q, cats)
        best   = ranked[0] if ranked else None
        if best:
            best["slot"]       = slot_name
            best["slot_label"] = SLOT_LABELS[slot_name]
            best["slot_icon"]  = SLOT_ICONS[slot_name]
            outfit[slot_name]  = best

    return outfit


# ── API Routes ────────────────────────────────────────────────────────

@occasion_bp.route("/api/occasion/occasions", methods=["GET"])
def list_occasions():
    return jsonify([
        {"key": k, "label": OCCASION_LABELS[k], "icon": OCCASION_ICONS[k]}
        for k in OCCASION_CATEGORIES
    ])


@occasion_bp.route("/api/occasion/chat", methods=["POST"])
def occasion_chat():
    data        = request.json or {}
    user_id     = data.get("user_id")
    message     = (data.get("message") or "").strip()
    refinements = data.get("refinements") or {}

    if not message:
        return jsonify({"error": "message is required"}), 400

    nlp_result = classify_occasion(message)
    occasion   = nlp_result["occasion"]
    confidence = nlp_result["confidence"]

    # ASCII only in print to avoid Windows cp1252 crash
    print(f"[Occasion] msg='{message}' => {occasion} conf={confidence} method={nlp_result['method']}")

    if not occasion or confidence < 0.15:
        return jsonify({
            "type":         "clarify",
            "reply":        LOW_CONF_REPLY,
            "alternatives": nlp_result.get("alternatives", []),
            "occasions": [
                {"key": k, "label": OCCASION_LABELS[k], "icon": OCCASION_ICONS[k]}
                for k in OCCASION_CATEGORIES
            ],
        })

    prefs    = get_user_preferences(user_id)
    outfit   = fetch_outfit_set(occasion, prefs, refinements)
    products = fetch_occasion_products(occasion, prefs, refinements)

    if not products and not outfit:
        return jsonify({
            "type":     "no_results",
            "occasion": occasion,
            "label":    OCCASION_LABELS[occasion],
            "icon":     OCCASION_ICONS[occasion],
            "reply":    f"Hmm, I couldn't find matching products for {OCCASION_LABELS[occasion]} right now. Try adjusting your budget.",
        })

    return jsonify({
        "type":     "products",
        "occasion": occasion,
        "label":    OCCASION_LABELS[occasion],
        "icon":     OCCASION_ICONS[occasion],
        "reply":    CHATBOT_REPLIES[occasion],
        "outfit":   outfit,
        "products": products[:12],
        "total":    len(products),
        "nlp": {
            "confidence":   confidence,
            "method":       nlp_result["method"],
            "alternatives": nlp_result["alternatives"],
        },
    })