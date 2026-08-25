from datetime import datetime
from db import get_db
from .base_agent import BaseAgent

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Memory Agent",
            description="Manages short-term and long-term user context, including recent searches and wishlists."
        )

    def process(self, message: str, context: dict, **kwargs) -> dict:
        """
        The memory agent retrieves context for the user and optionally saves the new message.
        `context` should contain 'user_id' and 'action' (e.g., 'retrieve' or 'save').
        """
        user_id = context.get("user_id")
        action = kwargs.get("action", "retrieve")
        
        if action == "retrieve":
            return self.fetch_user_context(user_id)
        elif action == "save":
            self.save_search(user_id, message)
            return {"status": "saved"}
        
        return {}

    def fetch_user_context(self, user_id) -> dict:
        if not user_id:
            return {}
        try:
            conn = get_db()
            cur  = conn.cursor(dictionary=True)
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
                "recent_searches":     searches,
                "wishlist_categories": list({i["category"] for i in wish}),
                "wishlist_brands":     list({i["brand"]    for i in wish}),
            }
        except Exception as e:
            print(f"[{self.name}] fetch_user_context error: {e}")
            return {}

    def save_search(self, user_id, query: str):
        if not user_id or not query:
            return
        try:
            conn = get_db()
            cur  = conn.cursor()
            try:
                cur.execute(
                    "INSERT INTO search_history (user_id, search_query, searched_at) "
                    "VALUES (%s, %s, %s)",
                    (user_id, query, datetime.utcnow()),
                )
                conn.commit()
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            print(f"[{self.name}] save_search error: {e}")
