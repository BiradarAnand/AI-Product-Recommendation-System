"""
train_models.py  — improved version
- Loads ratings table as strong interaction signal (weight = star value)
- Strips \\r and whitespace from all text columns
- Uses SQLAlchemy-safe cursor
- Loads from actual DB config via .env
"""

import os
import pandas as pd
import mysql.connector
from recommendation_engine import HybridRecommendationEngine
from dotenv import load_dotenv

load_dotenv()

# ── DB Config — matches your app.py ───────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST",     "127.0.0.1"),
    "port":     int(os.getenv("DB_PORT", 3305)),
    "user":     os.getenv("DB_USER",     "root"),
    "password": os.getenv("DB_PASSWORD", "Passwordmysql"),
    "database": os.getenv("DB_NAME",     "myecomerce"),
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Strip \\r, \\n, and extra spaces from all string columns."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.replace("\\r", "", regex=False)\
                                      .str.replace("\\n", " ", regex=False)\
                                      .str.strip()
    return df


# ── Load products ──────────────────────────────────────────────────
def load_products() -> pd.DataFrame:
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT id, name, category, brand, price,
               rating, image_url, description,
               COALESCE(stock, 0)   AS stock,
               COALESCE(reviews, 0) AS reviews
        FROM products
    """)
    rows = cur.fetchall()
    cur.close(); conn.close()

    df = pd.DataFrame(rows)
    df = clean_df(df)

    for col in ["name", "category", "brand", "description"]:
        df[col] = df[col].fillna("").astype(str)

    print(f"[Loader] Loaded {len(df)} products.")
    print(f"[Loader] Sample brands: {df['brand'].unique()[:5].tolist()}")
    return df


# ── Load interactions ──────────────────────────────────────────────
def load_interactions() -> pd.DataFrame:
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)

    dfs = []

    # Wishlist interactions — weight 3
    try:
        cur.execute("SELECT user_id, product_id, 3 AS weight FROM wishlist")
        rows = cur.fetchall()
        if rows:
            dfs.append(pd.DataFrame(rows))
            print(f"[Loader] Wishlist interactions: {len(rows)}")
    except Exception as e:
        print(f"[Loader] Wishlist skip: {e}")

    # Search history → matched products — weight 1
    try:
        cur.execute("""
            SELECT sh.user_id, p.id AS product_id, 1 AS weight
            FROM search_history sh
            JOIN products p
              ON LOWER(p.name)     LIKE CONCAT('%', LOWER(sh.search_query), '%')
              OR LOWER(p.category) LIKE CONCAT('%', LOWER(sh.search_query), '%')
            LIMIT 50000
        """)
        rows = cur.fetchall()
        if rows:
            dfs.append(pd.DataFrame(rows))
            print(f"[Loader] Search history interactions: {len(rows)}")
    except Exception as e:
        print(f"[Loader] Search history skip: {e}")

    # Cart interactions — weight 5 (strong signal)
    try:
        cur.execute("SELECT user_id, product_id, 5 AS weight FROM cart")
        rows = cur.fetchall()
        if rows:
            dfs.append(pd.DataFrame(rows))
            print(f"[Loader] Cart interactions: {len(rows)}")
    except Exception as e:
        print(f"[Loader] Cart skip: {e}")

    # ── NEW: Ratings — use star value directly as weight (1–5) ──────
    # A 5-star rating is a stronger signal than a wishlist add.
    try:
        cur.execute("""
            SELECT user_id, product_id, rating AS weight
            FROM ratings
            WHERE rating IS NOT NULL
        """)
        rows = cur.fetchall()
        if rows:
            dfs.append(pd.DataFrame(rows))
            print(f"[Loader] Rating interactions: {len(rows)}")
    except Exception as e:
        print(f"[Loader] Ratings skip: {e}")

    cur.close(); conn.close()

    if not dfs:
        print("[Loader] No interaction data — collaborative model will be skipped.")
        return pd.DataFrame(columns=["user_id", "product_id", "weight"])

    interactions = (
        pd.concat(dfs, ignore_index=True)
        .groupby(["user_id", "product_id"], as_index=False)["weight"]
        .sum()
    )

    print(f"[Loader] Total interactions: {len(interactions)} "
          f"from {interactions['user_id'].nunique()} users.")
    return interactions


# ── Train ──────────────────────────────────────────────────────────
def train():
    print("=" * 50)
    print("Starting model training...")
    print("=" * 50)

    products_df     = load_products()
    interactions_df = load_interactions()

    engine = HybridRecommendationEngine()
    engine.train(products_df, interactions_df)
    engine.save()

    print("=" * 50)
    print("Training complete. Models saved to ./models/")
    print("=" * 50)


if __name__ == "__main__":
    train()