"""
tools/memory_tools.py

Controlled DB access for user context: recent searches and wishlist
categories/brands. Mirrors the separation used in tools/product_search.py
so agents never talk to the database directly.
"""

from datetime import datetime, timezone
import sys
import os
from dotenv import load_dotenv

# Ensure backend/ is on the path so `db` can always be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from db import get_db


def fetch_user_context(user_id) -> dict:
    if not user_id:
        return {}
    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
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
        finally:
            cur.close()
            conn.close()

        return {
            "recent_searches": searches,
            "wishlist_categories": list({i["category"] for i in wish}),
            "wishlist_brands": list({i["brand"] for i in wish}),
        }
    except Exception as e:
        print(f"[memory_tools] fetch_user_context error: {e}")
        return {}


def save_search(user_id, query: str):
    if not user_id or not query:
        return
    try:
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO search_history (user_id, search_query, searched_at) "
                "VALUES (%s, %s, %s)",
                (user_id, query, datetime.now(timezone.utc)),
            )
            conn.commit()
        finally:
            cur.close()
            conn.close()
    except Exception as e:
        print(f"[memory_tools] save_search error: {e}")