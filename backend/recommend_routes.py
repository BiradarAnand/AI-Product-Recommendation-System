"""
recommend_routes.py
────────────────────
Flask Blueprint — plug this into your existing Flask app.

In your main app.py:
    from recommend_routes import recommend_bp, load_engine
    app.register_blueprint(recommend_bp, url_prefix="/api")
    load_engine()          # call once at startup
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import os
from dotenv import load_dotenv

load_dotenv()

from recommendation_engine import HybridRecommendationEngine
from db import get_db   # ✅ single shared pool

recommend_bp = Blueprint("recommend", __name__)
_engine: HybridRecommendationEngine | None = None

JWT_SECRET = os.getenv("JWT_SECRET", "your-jwt-secret")


# ─────────────────────────────────────────────
# ENGINE LOADER  (call at app startup)
# ─────────────────────────────────────────────
def load_engine():
    global _engine
    _engine = HybridRecommendationEngine()
    try:
        _engine.load()
        print("[API] Recommendation engine loaded.")
    except FileNotFoundError:
        print("[API] WARNING: No trained models found. Run train_models.py first.")
        _engine = None


def get_engine() -> HybridRecommendationEngine:
    if _engine is None:
        raise RuntimeError("Recommendation engine not loaded. Run train_models.py first.")
    return _engine


# ─────────────────────────────────────────────
# AUTH HELPER
# ─────────────────────────────────────────────
def optional_user_id() -> int | None:
    """Extract user_id from JWT if present; return None for anonymous requests."""
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
    """Decorator — reject request if no valid JWT."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = optional_user_id()
        if not user_id:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, user_id=user_id, **kwargs)
    return wrapper


# ─────────────────────────────────────────────
# SEARCH HISTORY LOGGER
# ─────────────────────────────────────────────
def _log_search(user_id: int | None, query: str):
    """Persist search query to search_history table (best-effort)."""
    if not user_id or not query:
        return
    try:
        conn = get_db()          # ✅ shared pool — no new connection created
        cur  = conn.cursor()
        cur.execute(
            "INSERT INTO search_history (user_id, search_query) VALUES (%s, %s)",
            (user_id, query[:255])
        )
        conn.commit()
    except Exception as e:
        print(f"[SearchLog] Failed to log search: {e}")
    finally:
        cur.close()
        conn.close()            # ✅ returns connection back to pool


# ─────────────────────────────────────────────
# ENDPOINTS
# ─────────────────────────────────────────────

@recommend_bp.route("/recommend/search", methods=["GET"])
def search():
    """
    Natural language product search with optional personalisation.

    GET /api/recommend/search
        ?q=red wireless headphones
        &top_n=10
        &category=Electronics       (optional filter)
        &max_price=500              (optional filter)
        &min_rating=4.0             (optional filter)

    Authorization: Bearer <jwt>   (optional — personalises results if provided)
    """
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Query parameter 'q' is required"}), 400

    top_n   = min(int(request.args.get("top_n", 10)), 50)
    user_id = optional_user_id()

    # Log the search for future collaborative training
    _log_search(user_id, query)

    filters = {}
    if request.args.get("category"):
        filters["category"]   = request.args["category"]
    if request.args.get("max_price"):
        filters["max_price"]  = float(request.args["max_price"])
    if request.args.get("min_rating"):
        filters["min_rating"] = float(request.args["min_rating"])

    try:
        engine  = get_engine()
        results = engine.search(query, user_id=user_id, top_n=top_n, filters=filters or None)
        return jsonify({
            "query":        query,
            "personalised": user_id is not None,
            "count":        len(results),
            "results":      results,
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500


@recommend_bp.route("/recommend/similar/<int:product_id>", methods=["GET"])
def similar(product_id: int):
    """
    Products similar to a given product (for product detail pages).

    GET /api/recommend/similar/42?top_n=8
    """
    top_n = min(int(request.args.get("top_n", 8)), 30)
    try:
        engine  = get_engine()
        results = engine.similar_products(product_id, top_n=top_n)
        return jsonify({
            "source_product_id": product_id,
            "count":             len(results),
            "results":           results,
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


@recommend_bp.route("/recommend/feed", methods=["GET"])
@require_auth
def personalised_feed(user_id: int):
    """
    Personalised product feed for logged-in users (home page).

    GET /api/recommend/feed?top_n=12
    Authorization: Bearer <jwt>

    Fallback cascade:
      1. Collaborative + popularity feed (warm user)
      2. Trending products (cold user / insufficient data)
    """
    top_n = min(int(request.args.get("top_n", 12)), 50)
    try:
        engine  = get_engine()
        results = engine.personalised_feed(user_id, top_n=top_n)

        if not results:
            # Fallback → popularity-ranked trending products (no weak keyword search)
            results = engine.trending_products(top_n=top_n)
            personalised = False
        else:
            personalised = True

        return jsonify({
            "user_id":      user_id,
            "personalised": personalised,
            "count":        len(results),
            "results":      results,
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


@recommend_bp.route("/recommend/trending", methods=["GET"])
def trending():
    """
    Top products ranked by popularity (rating × log-reviews).
    Available to all users — no auth required.

    GET /api/recommend/trending?top_n=12
    """
    top_n = min(int(request.args.get("top_n", 12)), 50)
    try:
        engine  = get_engine()
        results = engine.trending_products(top_n=top_n)
        return jsonify({
            "count":   len(results),
            "results": results,
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


@recommend_bp.route("/recommend/outfit/<int:product_id>", methods=["GET"])
def outfit(product_id: int):
    """
    Outfit / matching accessory suggestions for a given product.
    Uses content similarity filtered to complementary categories.

    GET /api/recommend/outfit/42
    """
    OUTFIT_MAP = {
        "shirts":       ["pants", "trousers", "jeans", "jackets", "shoes"],
        "dresses":      ["heels", "sandals", "handbags", "jewellery"],
        "shoes":        ["socks", "insoles", "shoe care"],
        "laptops":      ["laptop bags", "mouse", "keyboard", "headphones", "stands"],
        "smartphones":  ["cases", "screen protectors", "chargers", "earphones"],
        "cameras":      ["lenses", "tripods", "camera bags", "memory cards"],
    }

    try:
        engine = get_engine()

        if engine.products_df is None or product_id not in engine.products_df.index:
            return jsonify({"error": "Product not found"}), 404

        source_category = str(
            engine.products_df.loc[product_id, "category"]
        ).lower()
        complementary = []
        for key, cats in OUTFIT_MAP.items():
            if key in source_category:
                complementary = cats
                break

        similar = engine.similar_products(product_id, top_n=50)

        if complementary:
            similar = [
                p for p in similar
                if any(c in p.get("category", "").lower() for c in complementary)
            ]

        return jsonify({
            "source_product_id": product_id,
            "source_category":   source_category,
            "count":             len(similar[:8]),
            "results":           similar[:8],
        })
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 503


@recommend_bp.route("/recommend/health", methods=["GET"])
def health():
    """Quick health-check for the recommendation service."""
    engine_ready = _engine is not None
    collab_ready = engine_ready and _engine.collab_model.is_fitted
    pop_ready    = engine_ready and bool(_engine._pop_scores)
    return jsonify({
        "status":                  "ok" if engine_ready else "degraded",
        "content_model_ready":     engine_ready,
        "collab_model_ready":      collab_ready,
        "popularity_scores_ready": pop_ready,
        "product_count":           len(_engine._pop_scores) if engine_ready else 0,
    }), 200 if engine_ready else 503