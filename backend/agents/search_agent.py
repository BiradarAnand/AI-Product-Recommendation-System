import os
import json
import re
from groq import Groq
from db import get_db, get_catalog_db
from .base_agent import BaseAgent

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Search Agent",
            description="Translates natural language into database filters and retrieves catalog items."
        )

    def process(self, message: str, context: dict, **kwargs) -> dict:
        """
        Process general search queries.
        `context` should contain 'user_context' from MemoryAgent and 'history' (chat history).
        """
        user_context = context.get("user_context", {})
        history = context.get("history", [])
        
        try:
            filters = self.extract_filters(message, user_context)
            products = self.fetch_general_products(filters, limit=6)
            
            if products:
                reply = self.generate_general_reply(message, products, user_context, history)
                return {
                    "type": "general",
                    "reply": reply,
                    "products": products,
                    "outfit": {},
                    "filters_used": filters,
                    "status": "success"
                }
            return {
                "status": "no_results",
                "filters_used": filters
            }
        except Exception as e:
            print(f"[{self.name}] error: {e}")
            import traceback; traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def extract_filters(self, message: str, user_context: dict) -> dict:
        context_hint = ""
        if user_context.get("recent_searches"):
            context_hint = (
                f"\nUser recently searched: "
                f"{', '.join(user_context['recent_searches'][:3])}"
            )

        system = """You are a filter-extraction assistant for an e-commerce app.
Extract product search filters from the user message and return ONLY valid JSON.

Available categories:
Track Pants, Sports Shoes, Tshirts, Casual Shoes, Watches, Shirts,
Jeans, Trousers, Blazers, Formal Shoes, Sneakers, Kurtas, Ethnic Wear,
Activewear, Shorts, Caps, Sunglasses

Return JSON with these optional keys (omit keys that are not mentioned):
{
  "category":   string,
  "brand":      string,
  "keyword":    string,
  "max_price":  number,
  "min_price":  number,
  "min_rating": number (1-5)
}
"""
        resp = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": message + context_hint},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = re.sub(r"```json|```", "", resp.choices[0].message.content.strip()).strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"keyword": message}

    def fetch_general_products(self, filters: dict, limit: int = 6) -> list:
        conditions = ["stock > 0"]
        params     = []

        if filters.get("category"):
            conditions.append("LOWER(category) LIKE ?")
            params.append(f"%{filters['category'].lower()}%")
        if filters.get("brand"):
            conditions.append("LOWER(brand) LIKE ?")
            params.append(f"%{filters['brand'].lower()}%")
        if filters.get("max_price"):
            conditions.append("price <= ?")
            params.append(filters["max_price"])
        if filters.get("min_price"):
            conditions.append("price >= ?")
            params.append(filters["min_price"])
        if filters.get("min_rating"):
            conditions.append("rating >= ?")
            params.append(filters["min_rating"])
        if filters.get("keyword"):
            conditions.append(
                "(LOWER(name) LIKE ? OR LOWER(description) LIKE ? OR LOWER(brand) LIKE ?)"
            )
            kw = f"%{filters['keyword'].lower()}%"
            params.extend([kw, kw, kw])

        where = " AND ".join(conditions)
        sql   = f"""
            SELECT id, name, description, category, price, stock,
                   rating, reviews, image_url, brand
            FROM products
            WHERE {where}
            ORDER BY rating DESC, reviews DESC
            LIMIT ?
        """
        params.append(limit)

        try:
            conn = get_catalog_db()
            cur  = conn.cursor()
            try:
                cur.execute(sql, params)
                rows = [dict(row) for row in cur.fetchall()]
            finally:
                cur.close()
                conn.close()

            for r in rows:
                r["price"]   = float(r["price"]  or 0)
                r["rating"]  = float(r["rating"] or 0)
                r["reviews"] = int(r["reviews"]  or 0)
            return rows
        except Exception as e:
            print(f"[{self.name}] fetch_general_products error: {e}")
            import traceback; traceback.print_exc()
            return []

    def generate_general_reply(self, message: str, products: list,
                                user_context: dict, chat_history: list) -> str:
        product_summary = "\n".join(
            f"- {p['name']} | {p['brand']} | ₹{p['price']} "
            f"| ⭐{p['rating']} | {p['category']}"
            for p in products
        ) or "No exact matches found."

        wish_hint = ""
        if user_context.get("wishlist_categories"):
            wish_hint = (
                f"The user has previously saved items from: "
                f"{', '.join(set(user_context['wishlist_categories']))}. "
                "Mention this only if relevant."
            )

        system = f"""You are a helpful and friendly shopping assistant for an Indian e-commerce store.
Recommend products and explain briefly why they match the user's needs.
Keep responses to 2-4 sentences. Use ₹ for prices. Be warm and helpful.
{wish_hint}

Matching products:
{product_summary}

Rules:
- Mention 2-3 top picks by name with a short reason
- If no products found, ask a clarifying question
- Never invent products not in the list above
- If the user asks a general question (not product search), just answer helpfully
"""
        messages = [{"role": "system", "content": system}]
        for turn in chat_history[-4:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": message})

        resp = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()
