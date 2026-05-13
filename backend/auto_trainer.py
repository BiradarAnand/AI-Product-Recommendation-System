"""
auto_trainer.py
────────────────
Automatically retrains ML models in the background.
No need to run train_models.py manually ever again.

Add to app.py:
    from auto_trainer import start_auto_trainer
    start_auto_trainer()   ← call once after load_engine()

Retraining happens:
  - Every night at 2 AM automatically
  - Immediately when a user adds to cart/wishlist (after 10 interactions)
  - On demand via POST /api/admin/retrain
"""

import threading
import time
import os
import schedule
import mysql.connector
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

_retrain_lock        = threading.Lock()
_interactions_since  = 0      # count new interactions since last retrain
RETRAIN_THRESHOLD    = 10     # retrain after this many new interactions


# def get_db():
#     return mysql.connector.connect(**DB_CONFIG)


def run_training():
    """Full retrain — same logic as train_models.py."""
    global _interactions_since

    if not _retrain_lock.acquire(blocking=False):
        print("[AutoTrainer] Already retraining — skipped")
        return

    try:
        print(f"[AutoTrainer] Starting retrain at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        from recommendation_engine import HybridRecommendationEngine

        conn = get_db()
        cur  = conn.cursor(dictionary=True)

        # Load products
        cur.execute("""
            SELECT id, name, category, brand, price,
                   rating, image_url, description,
                   COALESCE(stock, 0)   AS stock,
                   COALESCE(reviews, 0) AS reviews
            FROM products
        """)
        rows = cur.fetchall()
        products_df = pd.DataFrame(rows)

        # Clean \r from text columns
        for col in products_df.select_dtypes(include="object").columns:
            products_df[col] = products_df[col].astype(str)\
                .str.replace("\r", "", regex=False)\
                .str.replace("\n", " ", regex=False)\
                .str.strip()

        # Load interactions
        dfs = []
        try:
            cur.execute("SELECT user_id, product_id, 3 AS weight FROM wishlist")
            rows = cur.fetchall()
            if rows: dfs.append(pd.DataFrame(rows))
        except: pass

        try:
            cur.execute("SELECT user_id, product_id, 5 AS weight FROM cart")
            rows = cur.fetchall()
            if rows: dfs.append(pd.DataFrame(rows))
        except: pass

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
            if rows: dfs.append(pd.DataFrame(rows))
        except: pass

        cur.close()
        conn.close()

        interactions_df = (
            pd.concat(dfs, ignore_index=True)
            .groupby(["user_id", "product_id"], as_index=False)["weight"].sum()
        ) if dfs else pd.DataFrame(columns=["user_id", "product_id", "weight"])

        print(f"[AutoTrainer] {len(products_df)} products, {len(interactions_df)} interactions")

        # Train and save
        engine = HybridRecommendationEngine()
        engine.train(products_df, interactions_df)
        engine.save()

        # Reload the running engine in recommend_routes
        import recommend_routes
        recommend_routes._engine = HybridRecommendationEngine()
        recommend_routes._engine.load()

        _interactions_since = 0
        print(f"[AutoTrainer] Retrain complete ✓")

    except Exception as e:
        print(f"[AutoTrainer] Retrain failed: {e}")
        import traceback; traceback.print_exc()
    finally:
        _retrain_lock.release()


def notify_new_interaction():
    """
    Call this from cart/wishlist routes after a user adds an item.
    Triggers retrain after RETRAIN_THRESHOLD new interactions.
    """
    global _interactions_since
    _interactions_since += 1
    print(f"[AutoTrainer] New interaction ({_interactions_since}/{RETRAIN_THRESHOLD})")

    if _interactions_since >= RETRAIN_THRESHOLD:
        print("[AutoTrainer] Threshold reached — retraining in background...")
        thread = threading.Thread(target=run_training, daemon=True)
        thread.start()


def _run_schedule():
    """Background thread that runs the schedule."""
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_auto_trainer():
    """
    Call this once in app.py after load_engine().
    Sets up:
      - Nightly retrain at 2:00 AM
      - Background schedule thread
    """
    # Schedule nightly retrain at 2 AM
    schedule.every().day.at("02:00").do(run_training)

    # Start background thread
    thread = threading.Thread(target=_run_schedule, daemon=True)
    thread.start()
    print("[AutoTrainer] Started — retrains nightly at 2 AM + after every 20 interactions")