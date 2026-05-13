"""
auto_trainer.py
────────────────
Automatically retrains ML models in the background.
"""

import threading
import time
import os
import schedule
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from db import get_db

load_dotenv()

_retrain_lock       = threading.Lock()
_interactions_since = 0
RETRAIN_THRESHOLD   = 10


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
        try:
            cur.execute("""
                SELECT id, name, category, brand, price,
                       rating, image_url, description,
                       COALESCE(stock, 0)   AS stock,
                       COALESCE(reviews, 0) AS reviews
                FROM products
            """)
            rows = cur.fetchall()
            products_df = pd.DataFrame(rows)

            for col in products_df.select_dtypes(include="object").columns:
                products_df[col] = (
                    products_df[col].astype(str)
                    .str.replace("\r", "", regex=False)
                    .str.replace("\n", " ", regex=False)
                    .str.strip()
                )

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
        finally:
            cur.close()
            conn.close()

        interactions_df = (
            pd.concat(dfs, ignore_index=True)
            .groupby(["user_id", "product_id"], as_index=False)["weight"].sum()
        ) if dfs else pd.DataFrame(columns=["user_id", "product_id", "weight"])

        print(f"[AutoTrainer] {len(products_df)} products, {len(interactions_df)} interactions")

        engine = HybridRecommendationEngine()
        engine.train(products_df, interactions_df)
        engine.save()

        import recommend_routes
        recommend_routes._engine = HybridRecommendationEngine()
        recommend_routes._engine.load()

        _interactions_since = 0
        print("[AutoTrainer] Retrain complete ✓")

    except Exception as e:
        print(f"[AutoTrainer] Retrain failed: {e}")
        import traceback; traceback.print_exc()
    finally:
        _retrain_lock.release()


def notify_new_interaction():
    """Call from cart/wishlist routes after a user adds an item."""
    global _interactions_since
    _interactions_since += 1
    print(f"[AutoTrainer] New interaction ({_interactions_since}/{RETRAIN_THRESHOLD})")

    if _interactions_since >= RETRAIN_THRESHOLD:
        print("[AutoTrainer] Threshold reached — retraining in background...")
        threading.Thread(target=run_training, daemon=True).start()


def _run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)


def start_auto_trainer():
    schedule.every().day.at("02:00").do(run_training)
    threading.Thread(target=_run_schedule, daemon=True).start()
    print("[AutoTrainer] Started — retrains nightly at 2 AM + after every 20 interactions")