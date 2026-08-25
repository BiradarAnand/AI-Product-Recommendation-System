import os
from groq import Groq
from .base_agent import BaseAgent

from occasion_nlp import classify_occasion, OCCASION_LABELS, OCCASION_ICONS
from occasion_engine import (
    fetch_outfit_set,
    fetch_occasion_products,
    get_user_preferences,
    OCCASION_CATEGORIES,
)

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

OCCASION_CONFIDENCE_THRESHOLD = 0.15

class RecommendationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Recommendation Agent",
            description="Expert at occasion-based styling and personalized outfit matching."
        )

    def process(self, message: str, context: dict, **kwargs) -> dict:
        """
        Process occasion-based queries.
        `context` should contain 'user_context', 'history', 'user_id', 'refinements'.
        """
        user_id = context.get("user_id")
        user_context = context.get("user_context", {})
        history = context.get("history", [])
        refinements = context.get("refinements", {})

        prefs = get_user_preferences(user_id) if user_id else {}

        nlp_result = classify_occasion(message)
        occasion   = nlp_result["occasion"]
        confidence = nlp_result["confidence"]
        nlp_meta   = {
            "confidence":   confidence,
            "method":       nlp_result["method"],
            "alternatives": nlp_result.get("alternatives", []),
        }

        # If it doesn't meet confidence, return a signal for coordinator to clarify or fallback
        if not occasion or confidence < OCCASION_CONFIDENCE_THRESHOLD:
            return {
                "status": "low_confidence",
                "nlp": nlp_meta
            }

        try:
            outfit   = fetch_outfit_set(occasion, prefs, refinements)
            products = fetch_occasion_products(occasion, prefs, refinements)
            top12    = products[:12]

            if not outfit and not top12:
                return {
                    "status": "no_results",
                    "occasion": occasion,
                    "reply": (
                        f"Hmm, I couldn't find products for "
                        f"{OCCASION_LABELS.get(occasion, occasion)} right now. "
                        "Try adjusting your budget filter."
                    ),
                    "nlp": nlp_meta
                }

            reply = self.generate_occasion_reply(
                message, occasion,
                OCCASION_LABELS.get(occasion, occasion),
                outfit, top12, user_context, history,
            )

            return {
                "status": "success",
                "type": "occasion",
                "occasion": occasion,
                "occasion_label": OCCASION_LABELS.get(occasion, occasion),
                "occasion_icon": OCCASION_ICONS.get(occasion, "🛍️"),
                "reply": reply,
                "products": top12,
                "outfit": outfit,
                "nlp": nlp_meta
            }
        except Exception as e:
            print(f"[{self.name}] error: {e}")
            import traceback; traceback.print_exc()
            return {"status": "error", "error": str(e)}

    def generate_occasion_reply(self, message: str, occasion_key: str, occasion_label: str,
                                 outfit: dict, products: list,
                                 user_context: dict, chat_history: list) -> str:
        outfit_summary = "\n".join(
            f"- {slot.upper()}: {item['name']} | {item['brand']} | ₹{item['price']} "
            f"| match {item.get('match_pct', '?')}%"
            for slot, item in outfit.items()
        ) if outfit else "No outfit set found."

        top_products = "\n".join(
            f"- {p['name']} | {p['brand']} | ₹{p['price']} | ⭐{p['rating']}"
            for p in products[:5]
        ) or "No additional products found."

        wish_hint = ""
        if user_context.get("wishlist_categories"):
            wish_hint = (
                f"User has saved interest in: "
                f"{', '.join(set(user_context['wishlist_categories']))}."
            )

        system = f"""You are a warm, friendly fashion assistant for an Indian e-commerce app.
The user needs an outfit for: {occasion_label}
{wish_hint}

Curated 4-piece outfit:
{outfit_summary}

More matching products:
{top_products}

Write 2-3 sentences explaining:
1. Why this outfit works for {occasion_label}
2. One specific highlight from the curated set (mention item name + price)
Keep it conversational, encouraging, and specific. Use ₹ for prices.
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
