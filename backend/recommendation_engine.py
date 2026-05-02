import os
import json
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import MinMaxScaler


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
MODEL_DIR = "models"
os.makedirs(MODEL_DIR, exist_ok=True)

CONTENT_WEIGHT    = 0.65   # weight for TF-IDF content similarity
COLLAB_WEIGHT     = 0.25   # weight for collaborative SVD score
POPULARITY_WEIGHT = 0.10   # weight for rating × log-review popularity
MIN_INTERACTIONS  = 5      # min interactions before collaborative model is used
SVD_COMPONENTS    = 50     # latent factors for SVD


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _build_product_text(row: pd.Series) -> str:
    """
    Combine product fields into a single searchable string.
    category and brand are repeated so TF-IDF assigns them higher weight.
    """
    name        = str(row.get("name", ""))
    category    = str(row.get("category", ""))
    brand       = str(row.get("brand", ""))
    description = str(row.get("description", ""))

    parts = [
        name,
        category, category,   # repeat → higher IDF weight
        brand, brand,          # repeat → higher IDF weight
        description,
    ]
    return " ".join(p for p in parts if p and p.strip() and p != "nan").lower()


def _safe_minmax(arr: np.ndarray) -> np.ndarray:
    """MinMax normalise to [0, 1]; returns zeros if all values identical."""
    mn, mx = float(arr.min()), float(arr.max())
    if mx - mn < 1e-9:
        return np.zeros_like(arr, dtype=float)
    return (arr - mn) / (mx - mn)


# ─────────────────────────────────────────────
# CONTENT-BASED MODEL
# ─────────────────────────────────────────────
class ContentBasedModel:
    """
    TF-IDF vectorizer on product text → cosine similarity.
    Handles natural language queries and similar-product lookup.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),      # unigrams + bigrams
            max_features=15_000,
            stop_words="english",
            sublinear_tf=True,       # dampen term frequency
        )
        self.tfidf_matrix = None
        self.product_ids  = []       # parallel list to matrix rows

    def fit(self, products_df: pd.DataFrame):
        """Train on products DataFrame (must have id column)."""
        products_df = products_df.copy()
        products_df["_text"] = products_df.apply(_build_product_text, axis=1)
        self.tfidf_matrix = self.vectorizer.fit_transform(products_df["_text"])
        self.product_ids  = products_df["id"].tolist()
        print(f"[ContentBased] Fitted on {len(self.product_ids)} products.")

    def query(self, text: str, top_n: int = 10) -> list[dict]:
        """Score all products against a free-text query."""
        q_vec  = self.vectorizer.transform([text.lower()])
        scores = cosine_similarity(q_vec, self.tfidf_matrix).flatten()
        top_idx = scores.argsort()[::-1][:top_n]
        return [
            {"product_id": self.product_ids[i], "content_score": float(scores[i])}
            for i in top_idx if scores[i] > 0
        ]

    def similar(self, product_id: int, top_n: int = 10) -> list[dict]:
        """Find products similar to a given product_id."""
        if product_id not in self.product_ids:
            return []
        idx    = self.product_ids.index(product_id)
        scores = cosine_similarity(
            self.tfidf_matrix[idx], self.tfidf_matrix
        ).flatten()
        scores[idx] = 0  # exclude self
        top_idx = scores.argsort()[::-1][:top_n]
        return [
            {"product_id": self.product_ids[i], "content_score": float(scores[i])}
            for i in top_idx if scores[i] > 0
        ]

    def save(self):
        with open(f"{MODEL_DIR}/content_model.pkl", "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load():
        with open(f"{MODEL_DIR}/content_model.pkl", "rb") as f:
            return pickle.load(f)

# ─────────────────────────────────────────────
# COLLABORATIVE FILTERING MODEL (SVD)
# ─────────────────────────────────────────────
class CollaborativeModel:
    """
    SVD on user-item interaction matrix (implicit feedback).
    Falls back gracefully when data is sparse.
    """

    def __init__(self):
        self.svd          = TruncatedSVD(n_components=SVD_COMPONENTS, random_state=42)
        self.user_factors = None    # (n_users, k)
        self.item_factors = None    # (n_items, k)
        self.user_index   = {}      # user_id → matrix row
        self.item_index   = {}      # product_id → matrix col
        self.is_fitted    = False

    def fit(self, interactions_df: pd.DataFrame):
        """
        interactions_df must have: user_id, product_id, weight
        weight: 1=search-match, 3=wishlist, 5=cart, star-rating value used directly
        """
        if interactions_df.empty or len(interactions_df) < MIN_INTERACTIONS:
            print("[Collaborative] Not enough data — skipping fit.")
            return

        users    = interactions_df["user_id"].unique().tolist()
        products = interactions_df["product_id"].unique().tolist()
        self.user_index = {u: i for i, u in enumerate(users)}
        self.item_index = {p: i for i, p in enumerate(products)}

        matrix = np.zeros((len(users), len(products)), dtype=np.float32)
        for _, row in interactions_df.iterrows():
            ui = self.user_index[row["user_id"]]
            pi = self.item_index[row["product_id"]]
            matrix[ui, pi] = row["weight"]

        n_components = min(SVD_COMPONENTS, *matrix.shape)
        self.svd = TruncatedSVD(n_components=n_components, random_state=42)
        self.user_factors = self.svd.fit_transform(matrix)   # (users, k)
        self.item_factors = self.svd.components_.T           # (items, k)
        self.is_fitted    = True
        print(f"[Collaborative] Fitted — {len(users)} users, {len(products)} products.")

    def recommend(self, user_id: int, top_n: int = 10) -> list[dict]:
        """Return predicted scores for all items for a given user."""
        if not self.is_fitted or user_id not in self.user_index:
            return []
        ui     = self.user_index[user_id]
        scores = self.user_factors[ui] @ self.item_factors.T  # (n_items,)
        top_idx = scores.argsort()[::-1][:top_n]
        id_map  = {v: k for k, v in self.item_index.items()}
        return [
            {"product_id": id_map[i], "collab_score": float(scores[i])}
            for i in top_idx
        ]

    def save(self):
        with open(f"{MODEL_DIR}/collab_model.pkl", "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def load():
        with open(f"{MODEL_DIR}/collab_model.pkl", "rb") as f:
            return pickle.load(f)


# ─────────────────────────────────────────────
# HYBRID ENGINE
# ─────────────────────────────────────────────
class HybridRecommendationEngine:
    """
    Combines ContentBasedModel + CollaborativeModel + Popularity Boost.

    Scoring formula:
        logged-in + collab data:
            score = 0.65*content + 0.25*collab + 0.10*popularity
        cold / no collab data:
            score = 0.80*content + 0.20*popularity
    """

    def __init__(self):
        self.content_model = ContentBasedModel()
        self.collab_model  = CollaborativeModel()
        self.products_df   = None
        self._pop_scores: dict[int, float] = {}   # product_id → [0,1] popularity

    # ── TRAINING ────────────────────────────────

    def train(self, products_df: pd.DataFrame, interactions_df: pd.DataFrame):
        """
        products_df  : id, name, category, brand, description,
                       price, rating, stock, reviews, image_url
        interactions_df : user_id, product_id, weight
        """
        self.products_df = products_df.set_index("id")
        self.content_model.fit(products_df)
        self.collab_model.fit(interactions_df)
        self._build_popularity_scores(products_df)
        print("[Hybrid] Training complete.")

    def _build_popularity_scores(self, products_df: pd.DataFrame):
        """
        Popularity = 0.6 * normalised_rating + 0.4 * normalised_log_reviews
        Stored as [0, 1] scores keyed by product id.
        """
        ratings = products_df["rating"].fillna(0).astype(float).values
        reviews = np.log1p(products_df["reviews"].fillna(0).astype(float).values)

        r_norm  = _safe_minmax(ratings)
        rv_norm = _safe_minmax(reviews)
        pop     = 0.6 * r_norm + 0.4 * rv_norm

        self._pop_scores = dict(zip(products_df["id"].tolist(), pop.tolist()))
        print(f"[Hybrid] Popularity scores built for {len(self._pop_scores)} products.")

    # ── INFERENCE ───────────────────────────────

    def search(
        self,
        query: str,
        user_id: int | None = None,
        top_n: int = 10,
        filters: dict | None = None,
    ) -> list[dict]:
        """
        Natural language search with personalisation + popularity boost.

        filters = {"category": "Electronics", "max_price": 500, "min_rating": 4.0}
        """
        fetch_n = top_n * 4   # over-fetch candidates before re-ranking

        # 1. Content similarity
        content_results = self.content_model.query(query, top_n=fetch_n)
        scores_map: dict[int, float] = {
            r["product_id"]: r["content_score"] for r in content_results
        }

        # If nothing matched content at all, seed with all known products at score 0
        # so popularity can still order them (handles abstract queries)
        if not scores_map and self._pop_scores:
            scores_map = {pid: 0.0 for pid in self._pop_scores}

        # 2. Normalise content scores
        if scores_map:
            c_arr  = np.array(list(scores_map.values()))
            c_norm = _safe_minmax(c_arr)
            scores_map = dict(zip(scores_map.keys(), c_norm.tolist()))

        # 3. Collaborative scores (normalised)
        collab_map: dict[int, float] = {}
        if user_id and self.collab_model.is_fitted:
            collab_results = self.collab_model.recommend(user_id, top_n=fetch_n)
            raw_collab = {r["product_id"]: r["collab_score"] for r in collab_results}
            if raw_collab:
                cv_arr  = np.array(list(raw_collab.values()))
                cv_norm = _safe_minmax(cv_arr)
                collab_map = dict(zip(raw_collab.keys(), cv_norm.tolist()))

        # 4. Combine scores
        candidate_ids = set(scores_map) | set(collab_map)
        if not candidate_ids:
            candidate_ids = set(self._pop_scores.keys())

        has_collab = bool(user_id and collab_map)
        final_scores: dict[int, float] = {}
        for pid in candidate_ids:
            cs  = scores_map.get(pid, 0.0)
            col = collab_map.get(pid, 0.0)
            pop = self._pop_scores.get(pid, 0.0)

            if has_collab:
                final_scores[pid] = (
                    CONTENT_WEIGHT    * cs
                    + COLLAB_WEIGHT   * col
                    + POPULARITY_WEIGHT * pop
                )
            else:
                # Redistribute collab weight between content and popularity
                final_scores[pid] = (
                    (CONTENT_WEIGHT + COLLAB_WEIGHT * 0.5) * cs
                    + (POPULARITY_WEIGHT + COLLAB_WEIGHT * 0.5) * pop
                )

        # 5. Apply filters
        if filters and self.products_df is not None:
            final_scores = self._apply_filters(final_scores, filters)

        # 6. Sort and build result list
        ranked = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return self._enrich(ranked, query=query)

    def similar_products(self, product_id: int, top_n: int = 8) -> list[dict]:
        """
        Products similar to a given product.
        Blends content similarity (80%) with popularity (20%) so that
        high-quality products rank above obscure near-duplicates.
        """
        results = self.content_model.similar(product_id, top_n=top_n * 3)
        if not results:
            return []

        sim_arr  = np.array([r["content_score"] for r in results])
        sim_norm = _safe_minmax(sim_arr)

        ranked = []
        for r, s_norm in zip(results, sim_norm):
            pid     = r["product_id"]
            pop     = self._pop_scores.get(pid, 0.0)
            blended = 0.80 * s_norm + 0.20 * pop
            ranked.append((pid, blended))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return self._enrich(ranked[:top_n])

    def personalised_feed(self, user_id: int, top_n: int = 12) -> list[dict]:
        """Collaborative + popularity recommendations for the home feed."""
        if not self.collab_model.is_fitted:
            return []
        results = self.collab_model.recommend(user_id, top_n=top_n * 2)
        if not results:
            return []

        collab_raw = {r["product_id"]: r["collab_score"] for r in results}
        cv_arr     = np.array(list(collab_raw.values()))
        cv_norm    = _safe_minmax(cv_arr)
        collab_norm = dict(zip(collab_raw.keys(), cv_norm.tolist()))

        ranked = []
        for pid, col in collab_norm.items():
            pop     = self._pop_scores.get(pid, 0.0)
            blended = 0.75 * col + 0.25 * pop
            ranked.append((pid, blended))

        ranked.sort(key=lambda x: x[1], reverse=True)
        return self._enrich(ranked[:top_n])

    def trending_products(self, top_n: int = 12) -> list[dict]:
        """
        Return top products ranked purely by popularity score.
        Used as cold-start fallback for guests / new users with no history.
        """
        if not self._pop_scores:
            return []
        ranked = sorted(self._pop_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
        return self._enrich(ranked)

    # ── UTILS ───────────────────────────────────

    def _apply_filters(self, scores_map: dict, filters: dict) -> dict:
        """Remove products that don't match filter criteria."""
        filtered = {}
        for pid, score in scores_map.items():
            if pid not in self.products_df.index:
                continue
            row = self.products_df.loc[pid]
            if "category" in filters and row.get("category") != filters["category"]:
                continue
            if "max_price" in filters and float(row.get("price", 0)) > filters["max_price"]:
                continue
            if "min_rating" in filters and float(row.get("rating", 0)) < filters["min_rating"]:
                continue
            if "brand" in filters and str(row.get("brand", "")).lower() != filters["brand"].lower():
                continue
            filtered[pid] = score
        return filtered

    def _enrich(self, ranked: list[tuple], query: str = "") -> list[dict]:
        """Attach product metadata to ranked (id, score) pairs."""
        results = []
        for pid, score in ranked:
            record = {"id": pid, "recommendation_score": round(score, 4)}
            if self.products_df is not None and pid in self.products_df.index:
                row = self.products_df.loc[pid]
                record.update({
                    "name":        row.get("name", ""),
                    "category":    row.get("category", ""),
                    "brand":       row.get("brand", ""),
                    "price":       float(row.get("price", 0)),
                    "rating":      float(row.get("rating", 0)),
                    "reviews":     int(row.get("reviews", 0)),
                    "stock":       int(row.get("stock", 0)),
                    "image_url":   row.get("image_url", ""),
                    "description": row.get("description", ""),
                })
            results.append(record)
        return results

    # ── PERSISTENCE ─────────────────────────────

    def save(self):
        self.content_model.save()
        self.collab_model.save()
        self.products_df.to_pickle(f"{MODEL_DIR}/products_df.pkl")
        with open(f"{MODEL_DIR}/pop_scores.json", "w") as f:
            json.dump({str(k): v for k, v in self._pop_scores.items()}, f)
        print("[Hybrid] Models saved.")

    def load(self):
        self.content_model = ContentBasedModel.load()
        self.collab_model  = CollaborativeModel.load()
        self.products_df   = pd.read_pickle(f"{MODEL_DIR}/products_df.pkl")
        try:
            with open(f"{MODEL_DIR}/pop_scores.json") as f:
                raw = json.load(f)
            self._pop_scores = {int(k): v for k, v in raw.items()}
        except FileNotFoundError:
            print("[Hybrid] pop_scores.json not found — rebuilding from products_df.")
            self._build_popularity_scores(self.products_df.reset_index())
        print("[Hybrid] Models loaded.")
        return self
