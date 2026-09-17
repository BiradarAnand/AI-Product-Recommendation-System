import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from .base_agent import BaseAgent
from tools.product_search import search_internal, search_external

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))



class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Search Agent",
            description=(
                "Translates natural language into database filters, retrieves "
                "catalog items, and falls back to an external source when "
                "nothing matches internally."
            )
        )

    def process(self, message: str, context: dict, **kwargs) -> dict:
        """
        `context` should contain 'user_context' from MemoryAgent and 'history'.
        """
        user_context = context.get("user_context", {})
        history = context.get("history", [])

        try:
            filters = self.extract_filters(message, user_context)

            products = search_internal(filters, limit=12)
            source = "internal"

            if not products:
                # Try a broader keyword fallback using internal DB first
                kw = filters.get("keyword") or message
                broad = search_internal({"keyword": kw}, limit=8)
                if broad:
                    products = broad
                else:
                    # Last resort: BuyWhere external
                    products = search_external(kw, limit=6)
                    source = "external" if products else "none"

            if products:
                reply = self.generate_general_reply(
                    message, products, user_context, history, source
                )
                return {
                    "type": "general",
                    "reply": reply,
                    "products": products,
                    "outfit": {},
                    "filters_used": filters,
                    "source": source,
                    "status": "success",
                }

            return {
                "status": "no_results",
                "filters_used": filters,
                "reply": (
                    "I couldn't find a match in our store or online right now — "
                    "want to try different keywords or a wider budget?"
                ),
            }
        except Exception as e:
            print(f"[{self.name}] error: {e}")
            import traceback
            traceback.print_exc()
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

Available categories (use EXACTLY these names):
Track Pants, Sports Shoes, Tshirts, Casual Shoes, Watches, Shirts,
Jeans, Trousers, Blazers, Formal Shoes, Sneakers, Kurtas, Ethnic Wear,
Activewear, Shorts, Caps, Sunglasses

Return JSON with these optional keys (omit keys that are not mentioned):
{
  "categories": [list of matching category strings from the list above],
  "brand":      string,
  "keyword":    string,
  "max_price":  number,
  "min_price":  number,
  "min_rating": number (1-5)
}

For occasions, map to multiple categories:
- gym/sports/fitness -> ["Tshirts", "Track Pants", "Sports Shoes", "Activewear"]
- office/formal/interview -> ["Shirts", "Trousers", "Formal Shoes", "Watches"]
- casual/weekend -> ["Tshirts", "Jeans", "Casual Shoes"]
- wedding/function -> ["Shirts", "Trousers", "Blazers", "Watches"]
"""
        resp = groq_client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message + context_hint},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = re.sub(r"```json|```", "", resp.choices[0].message.content.strip()).strip()
        try:
            return json.loads(raw)
        except Exception:
            return {"keyword": message}

    def generate_general_reply(
        self, message: str, products: list, user_context: dict,
        chat_history: list, source: str = "internal",
    ) -> str:
        def _price_str(p):
            currency = p.get("currency") or "INR"
            symbol = "₹" if currency == "INR" else f"{currency} "
            price = p.get("price")
            return f"{symbol}{price}" if price is not None else "price unavailable"

        product_summary = "\n".join(
            f"- {p['name']} | {p.get('brand') or ''} | {_price_str(p)} "
            f"| {'⭐' + str(p['rating']) if p.get('rating') is not None else 'no rating'}"
            f" | {p.get('category') or ''}"
            for p in products
        ) or "No exact matches found."

        wish_hint = ""
        if user_context.get("wishlist_categories"):
            wish_hint = (
                f"The user has previously saved items from: "
                f"{', '.join(set(user_context['wishlist_categories']))}. "
                "Mention this only if relevant."
            )

        source_hint = (
            "These products are NOT in our store catalog — they were found "
            "externally via a product search service. Be upfront that they aren't "
            "purchasable on this platform yet, present them as reference/inspiration only, "
            "and if a price is shown in a non-INR currency, state the currency clearly rather than implying ₹."
            if source == "external"
            else "These products ARE in our store catalog and can be purchased directly."
        )

        system = f"""You are a helpful and friendly shopping assistant for an Indian e-commerce store.
Recommend products and explain briefly why they match the user's needs.
Keep responses to 2-4 sentences. Use ₹ for prices. Be warm and helpful.
{wish_hint}

{source_hint}

Matching products:
{product_summary}

Rules:
- Mention 2-3 top picks by name with a short reason
- Never invent products not in the list above
- Never claim external products are in stock or purchasable here
- If the user asks a general question (not product search), just answer helpfully
"""
        messages = [{"role": "system", "content": system}]
        for turn in chat_history[-4:]:
            messages.append({"role": turn["role"], "content": turn["content"]})
        messages.append({"role": "user", "content": message})

        resp = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.7,
            max_tokens=400,
        )
        return resp.choices[0].message.content.strip()