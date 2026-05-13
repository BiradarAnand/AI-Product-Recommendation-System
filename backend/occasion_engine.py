# occasion_engine.py  — v2 — Content-Based TF-IDF Cosine Similarity

import os
import pickle
import numpy as np
from flask import Blueprint, request, jsonify
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv
from occasion_nlp import classify_occasion, OCCASION_LABELS, OCCASION_ICONS
from db import get_db

load_dotenv()

occasion_bp = Blueprint("occasion", __name__)

MODEL_DIR = "models"

# ── Rich purpose queries ──────────────────────────────────────────────
OCCASION_PURPOSE_QUERIES = {
    "job_interview": (
        "formal professional office business shirt trouser blazer formal shoes "
        "leather oxford classic cotton slim fit regular fit corporate executive "
        "interview meeting boardroom client presentation polished attire suit "
        "professional look solid color formal pants classic watch analog leather strap"
    ),
    "sports": (
        "sport athletic gym workout running training exercise fitness dry fit "
        "track pants sports shoes sneakers activewear shorts athletic cap "
        "flexible breathable grip cushion running outdoor physical performance "
        "jogging trekking cycling badminton cricket waterproof sport watch rubber"
    ),
    "wedding_guest": (
        "ethnic traditional wedding kurta sherwani embroidered premium elegant "
        "festive cotton traditional wear sangeet baraat function ceremony ethnic shoes "
        "mojari jutti gold analog watch metal strap classic premium elegant "
        "traditional outfit marriage reception formal classic trouser churidar"
    ),
    "casual_outing": (
        "casual comfortable everyday relaxed jeans tshirt sneakers casual shoes "
        "regular fit slim lightweight everyday wear college hangout friends outing "
        "weekend mall shopping casual shorts cap sunglasses street style printed polo "
        "canvas everyday round dial silicon casual watch colorful"
    ),
    "date_night": (
        "stylish smart elegant premium slim fit shirt jeans watch sneakers casual shoes "
        "date night dinner romantic classy attractive minimalist dark skinny tapered "
        "leather shoes elegant slim metal watch stylish premium look solid printed "
        "clean minimalist dress to impress special evening"
    ),
    "office": (
        "office work professional formal business casual shirt trouser formal shoes "
        "analog watch leather strap workplace daily wear corporate attire cotton "
        "formal shirt slim fit office trousers flat front business oxford derby "
        "steel watch solid striped regular business look professional daily"
    ),
    "festival": (
        "ethnic traditional festival diwali eid puja navratri festive kurta "
        "ethnic wear embroidered cotton premium elegant gold analog watch metal strap "
        "festive shoes traditional leather ethnic mojari celebration outfit "
        "churidar dhoti classic premium elegant festive season cultural"
    ),
    "beach": (
        "casual beach summer vacation light comfortable breezy shorts tshirt linen "
        "cotton casual shoes sneakers slip on sandals cap sunglasses waterproof "
        "sport digital rubber strap watch lightweight summer outfit relaxed "
        "vacation travel holiday tropical breezy comfortable everyday summer casual"
    ),
}

SLOT_PURPOSE_QUERIES = {
    "job_interview": {
        "shirt": "formal cotton shirt office business professional slim regular solid striped classic",
        "pant":  "formal trouser office classic slim straight flat front business professional dark",
        "shoes": "formal leather shoes oxford derby classic office business professional polished",
        "watch": "formal analog watch leather strap classic business professional metal dial steel",
    },
    "sports": {
        "shirt": "dry fit sport athletic gym running performance activewear tshirt breathable flexible",
        "pant":  "track pants sport flexible gym running athletic training shorts outdoor performance",
        "shoes": "sports shoes running grip cushion athletic training outdoor performance durable",
        "watch": "sport digital waterproof fitness stopwatch rubber strap outdoor active",
    },
    "wedding_guest": {
        "shirt": "kurta ethnic traditional premium elegant festive embroidered cotton wedding",
        "pant":  "formal traditional trouser churidar ethnic classic straight palazzo",
        "shoes": "formal leather premium ethnic mojari jutti traditional classic wedding",
        "watch": "premium classic elegant gold analog metal strap watch formal wedding",
    },
    "casual_outing": {
        "shirt": "casual comfortable everyday regular printed polo tshirt shirt light",
        "pant":  "casual slim regular comfortable stretch skinny jeans shorts everyday",
        "shoes": "casual comfortable everyday canvas street lightweight sneakers slip",
        "watch": "casual sport everyday colorful silicon round dial simple watch",
    },
    "date_night": {
        "shirt": "slim stylish premium smart printed solid shirt date elegant",
        "pant":  "slim stylish dark premium skinny tapered jeans trouser",
        "shoes": "stylish premium clean elegant leather minimalist shoes sneaker",
        "watch": "stylish premium elegant slim metal minimalist watch",
    },
    "office": {
        "shirt": "formal office business cotton regular solid striped shirt classic",
        "pant":  "formal office slim classic flat front pleated trouser dark",
        "shoes": "formal leather oxford derby office classic business shoes",
        "watch": "formal classic business analog leather strap steel watch",
    },
    "festival": {
        "shirt": "ethnic traditional festive premium embroidered cotton kurta",
        "pant":  "traditional ethnic churidar dhoti classic festive trouser",
        "shoes": "ethnic traditional premium mojari leather festive shoes",
        "watch": "premium gold classic elegant analog metal watch festive",
    },
    "beach": {
        "shirt": "casual light summer breezy linen cotton relaxed tshirt shirt",
        "pant":  "casual light summer beach comfortable shorts swim cargo",
        "shoes": "casual light comfortable slip on sandals canvas sneakers",
        "watch": "sport waterproof casual digital rubber strap colorful summer",
    },
}

OCCASION_CATEGORIES = {
    "job_interview": {
        "primary":   ["Shirts", "Trousers", "Formal Shoes"],
        "secondary": ["Blazers", "Watches"],
    },
    "sports": {
        "primary":   ["Track Pants", "Sports Shoes", "Activewear"],
        "secondary": ["Tshirts", "Shorts", "Caps"],
    },
    "wedding_guest": {
        "primary":   ["Kurtas", "Ethnic Wear", "Shirts"],
        "secondary": ["Trousers", "Watches", "Formal Shoes"],
    },
    "casual_outing": {
        "primary":   ["Jeans", "Tshirts", "Sneakers"],
        "secondary": ["Casual Shoes", "Shirts", "Shorts", "Caps", "Sunglasses"],
    },
    "date_night": {
        "primary":   ["Shirts", "Jeans", "Watches"],
        "secondary": ["Sneakers", "Casual Shoes", "Trousers", "Sunglasses"],
    },
    "office": {
        "primary":   ["Shirts", "Trousers", "Formal Shoes"],
        "secondary": ["Watches", "Blazers", "Casual Shoes"],
    },
    "festival": {
        "primary":   ["Kurtas", "Ethnic Wear", "Shirts"],
        "secondary": ["Trousers", "Watches", "Casual Shoes"],
    },
    "beach": {
        "primary":   ["Shorts", "Tshirts", "Sneakers"],
        "secondary": ["Casual Shoes", "Caps", "Sunglasses"],
    },
}

OUTFIT_SLOTS = {
    "job_interview": {
        "shirt": ["Shirts"],
        "pant":  ["Trousers"],
        "shoes": ["Formal Shoes"],
        "watch": ["Watches"],
    },
    "sports": {
        "shirt": ["Tshirts", "Activewear"],
        "pant":  ["Track Pants", "Shorts"],
        "shoes": ["Sports Shoes"],
        "watch": ["Watches"],
    },
    "wedding_guest": {
        "shirt": ["Kurtas", "Shirts"],
        "pant":  ["Trousers", "Ethnic Wear"],
        "shoes": ["Formal Shoes", "Casual Shoes"],
        "watch": ["Watches"],
    },
    "casual_outing": {
        "shirt": ["Tshirts", "Shirts"],
        "pant":  ["Jeans", "Shorts"],
        "shoes": ["Sneakers", "Casual Shoes"],
        "watch": ["Watches"],
    },
    "date_night": {
        "shirt": ["Shirts"],
        "pant":  ["Jeans", "Trousers"],
        "shoes": ["Sneakers", "Casual Shoes", "Formal Shoes"],
        "watch": ["Watches"],
    },
    "office": {
        "shirt": ["Shirts"],
        "pant":  ["Trousers"],
        "shoes": ["Formal Shoes"],
        "watch": ["Watches"],
    },
    "festival": {
        "shirt": ["Kurtas", "Ethnic Wear"],
        "pant":  ["Trousers", "Ethnic Wear"],
        "shoes": ["Formal Shoes", "Casual Shoes"],
        "watch": ["Watches"],
    },
    "beach": {
        "shirt": ["Tshirts", "Shirts"],
        "pant":  ["Shorts"],
        "shoes": ["Casual Shoes", "Sneakers"],
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
    "job_interview": "Great choice! For a job interview you want to look sharp and confident. Here are outfits that'll make a strong first impression 💼",
    "sports":        "Let's get you geared up! Here are performance picks to power your workout 🏃",
    "wedding_guest": "Exciting! Here are smart outfits to help you look great at the function 🎊",
    "casual_outing": "Comfort meets style! Here are relaxed yet stylish picks for your day out ☀️",
    "date_night":    "Setting the right mood matters! Here are sharp picks for your evening 🌙",
    "office":        "Looking sharp at work pays off. Here are office-ready outfits for you 🏢",
    "festival":      "Festival vibes! Here are elegant picks to celebrate in style 🪔",
    "beach":         "Sun, sand, style! Here are breezy picks for your trip 🏖️",
}

LOW_CONF_REPLY = (
    "I'm not sure which occasion you mean 🤔 Could you pick one below — "
    "or tell me more? E.g. 'job interview', 'gym session', 'wedding function', 'date night'..."
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
        print("[OccasionEngine] TF-IDF content model loaded ✓")
        return _content_model
    except Exception as e:
        print(f"[OccasionEngine] Failed to load content model: {e}")
        return None


def _row_to_text(row: dict) -> str:
    name        = str(row.get("name", ""))
    category    = str(row.get("category", ""))
    brand       = str(row.get("brand", ""))
    description = str(row.get("description", ""))
    parts = [name, category, category, brand, brand, description]
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

    ratings  = np.array([float(r.get("rating", 0) or 0)  for r in rows])
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
        cos_norm  = np.zeros(n)
        w_rating  = w_rating + w_cosine * 0.6
        w_review  = w_review + w_cosine * 0.4
        w_cosine  = 0.0

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
    if not categories:
        return []
    try:
        conn = get_db()
        cur  = conn.cursor(dictionary=True)
        try:
            cat_ph       = ",".join(["%s"] * len(categories))
            brand_clause = "AND p.brand = %s" if brand_filter else ""
            query = f"""
                SELECT p.id, p.name, p.description, p.category,
                       p.price, p.rating, p.reviews, p.image_url, p.brand
                FROM products p
                WHERE p.category IN ({cat_ph})
                  AND p.price BETWEEN %s AND %s
                  AND p.stock > 0
                  {brand_clause}
                ORDER BY p.rating DESC, p.reviews DESC
                LIMIT 200
            """
            params = (*categories, min_p, max_p, *([brand_filter] if brand_filter else []))
            cur.execute(query, params)
            rows = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        for row in rows:
            row["price"]   = float(row["price"]  or 0)
            row["rating"]  = float(row["rating"] or 0)
            row["reviews"] = int(row["reviews"]  or 0)
        return rows
    except Exception as e:
        print(f"[fetch_candidates error] {e}")
        import traceback; traceback.print_exc()
        return []


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
        candidates = _fetch_candidates(cats, min_p, max_p, brand_filter)
        if not candidates:
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

    print(f"[Occasion] msg='{message}' -> {occasion} conf={confidence} method={nlp_result['method']}")

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