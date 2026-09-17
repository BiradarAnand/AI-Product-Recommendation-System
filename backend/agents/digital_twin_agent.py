import os
import json
import re
from dotenv import load_dotenv
from groq import Groq
from .base_agent import BaseAgent
from tools.digital_twin_tools import fetch_user_persona

load_dotenv()

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

        persona = fetch_user_persona(user_id)
        evaluation = self.evaluate_products(persona, products, message)

        return {
            "status": "success",
            "evaluation": evaluation,
            "persona": persona
        }

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
                model="openai/gpt-oss-20b",
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