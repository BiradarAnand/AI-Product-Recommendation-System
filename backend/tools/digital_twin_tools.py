"""
tools/digital_twin_tools.py

Controlled DB access for building a user's shopping persona (name plus
inferred preferences from their wishlist), used by Digital Twin Agent
to simulate how that user might react to a set of recommendations.
"""

import sys
import os
from dotenv import load_dotenv

# Ensure backend/ is on the path so `db` can always be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from db import get_db


def fetch_user_persona(user_id) -> dict:
    if not user_id:
        return {"demographics": "Guest User", "preferences": "General"}

    try:
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        try:
            cur.execute("SELECT email, name FROM users WHERE id = %s", (user_id,))
            user_info = cur.fetchone() or {}

            cur.execute(
                "SELECT DISTINCT category, brand FROM wishlist w "
                "JOIN products p ON w.product_id = p.id WHERE w.user_id = %s LIMIT 5",
                (user_id,)
            )
            wish = cur.fetchall()
        finally:
            cur.close()
            conn.close()

        categories = list({i["category"] for i in wish})
        brands = list({i["brand"] for i in wish})

        return {
            "name": user_info.get("name", "User"),
            "preferences": (
                f"Likes {', '.join(categories)} and brands like {', '.join(brands)}"
                if categories else "General preferences"
            ),
            "shopping_behavior": "Value-conscious but willing to spend on quality occasions.",
        }
    except Exception as e:
        print(f"[digital_twin_tools] fetch_user_persona error: {e}")
        return {"demographics": "Unknown", "preferences": "General"}