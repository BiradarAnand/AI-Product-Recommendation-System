import os
import json
import re
from groq import Groq
from .base_agent import BaseAgent
from db import get_db

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class DigitalTwinAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Digital Twin Agent",
            description="Simulates a user persona to evaluate recommendations and provide feedback."
        )

    def process(self, message: str, context: dict, **kwargs) -> dict:
        """
        Evaluate recommendations as the user's digital twin.
        `context` should contain 'user_id' and 'products'.
        """
        user_id = context.get("user_id")
        products = context.get("products", [])
        
        if not products:
            return {"status": "no_products"}

        persona = self.fetch_user_persona(user_id)
        evaluation = self.evaluate_products(persona, products, message)
        
        return {
            "status": "success",
            "evaluation": evaluation,
            "persona": persona
        }

    def fetch_user_persona(self, user_id) -> dict:
        if not user_id:
            return {"demographics": "Guest User", "preferences": "General"}
            
        try:
            conn = get_db()
            cur = conn.cursor(dictionary=True)
            try:
                # Assuming users table has some demographic info or we extrapolate from wishlist
                cur.execute("SELECT email, name FROM users WHERE id = %s", (user_id,))
                user_info = cur.fetchone() or {}
                
                cur.execute(
                    "SELECT DISTINCT category, brand FROM wishlist w JOIN products p ON w.product_id = p.id WHERE w.user_id = %s LIMIT 5",
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
                "preferences": f"Likes {', '.join(categories)} and brands like {', '.join(brands)}" if categories else "General preferences",
                "shopping_behavior": "Value-conscious but willing to spend on quality occasions."
            }
        except Exception as e:
            print(f"[{self.name}] fetch_user_persona error: {e}")
            return {"demographics": "Unknown", "preferences": "General"}

    def evaluate_products(self, persona: dict, products: list, original_query: str) -> dict:
        product_summary = "\n".join(
            f"- ID: {p['id']} | {p['name']} | {p['brand']} | ₹{p['price']} | {p['category']}"
            for p in products[:5]
        )

        system = f"""You are a Digital Twin simulating an online shopper.
Your Persona:
- Name: {persona.get('name', 'Shopper')}
- Preferences: {persona.get('preferences', 'None specified')}
- Behavior: {persona.get('shopping_behavior', 'Standard')}

The AI Shopping Assistant has recommended the following products based on the query: "{original_query}"

Products:
{product_summary}

Your task: Evaluate the relevance of these products to your persona and the query.
Return a JSON object with:
{{
  "overall_rating": number (1-10),
  "feedback": "string explaining your thoughts",
  "approved_product_ids": [list of IDs you actually like]
}}
"""
        try:
            resp = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": "Please evaluate the recommendations."}
                ],
                temperature=0.3,
                max_tokens=300,
            )
            raw = re.sub(r"```json|```", "", resp.choices[0].message.content.strip()).strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[{self.name}] evaluate_products error: {e}")
            return {"overall_rating": 5, "feedback": "Evaluation failed.", "approved_product_ids": []}
