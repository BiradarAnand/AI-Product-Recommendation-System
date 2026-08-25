from .base_agent import BaseAgent
from .memory_agent import MemoryAgent
from .search_agent import SearchAgent
from .recommendation_agent import RecommendationAgent
from .digital_twin_agent import DigitalTwinAgent
from occasion_nlp import OCCASION_LABELS, OCCASION_ICONS
from occasion_engine import OCCASION_CATEGORIES

class CoordinatorAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Coordinator Agent",
            description="Central orchestrator that routes user queries to the appropriate agent."
        )
        self.memory = MemoryAgent()
        self.search = SearchAgent()
        self.recommendation = RecommendationAgent()
        self.digital_twin = DigitalTwinAgent()

    def process(self, message: str, context: dict, **kwargs) -> dict:
        user_id = context.get("user_id")
        history = context.get("history", [])
        refinements = context.get("refinements", {})

        # 1. Ask Memory Agent for context
        mem_context = self.memory.process(message, {"user_id": user_id}, action="retrieve")
        
        agent_context = {
            "user_id": user_id,
            "user_context": mem_context,
            "history": history,
            "refinements": refinements
        }

        # 2. Try Recommendation Agent (Occasion-based)
        rec_result = self.recommendation.process(message, agent_context)
        
        final_result = None
        if rec_result.get("status") == "success":
            final_result = rec_result
        else:
            # Check if user explicitly asked for a purpose/occasion help
            lower_msg = message.lower()
            if any(k in lower_msg for k in ["purpose", "occasion", "what should i wear", "help me decide"]):
                final_result = {
                    "type": "clarify",
                    "reply": "I can certainly help you find outfits based on your purpose! What specific occasion are you dressing for? (e.g. gym, office, date night)",
                    "occasions": [
                        {"key": k, "label": OCCASION_LABELS[k], "icon": OCCASION_ICONS[k]}
                        for k in OCCASION_CATEGORIES
                    ],
                    "products": [],
                    "outfit": {},
                    "nlp": rec_result.get("nlp")
                }
            else:
                # 3. Fallback to Search Agent
                search_result = self.search.process(message, agent_context)
                if search_result.get("status") == "success":
                    final_result = search_result
                    if "nlp" not in final_result:
                        final_result["nlp"] = rec_result.get("nlp")
                else:
                    # 4. Clarify
                    final_result = {
                        "type": "clarify",
                        "reply": "I'm not sure what you're looking for 🤔 Could you pick an occasion below or describe what you need?",
                        "occasions": [
                            {"key": k, "label": OCCASION_LABELS[k], "icon": OCCASION_ICONS[k]}
                            for k in OCCASION_CATEGORIES
                        ],
                        "products": [],
                        "outfit": {},
                        "nlp": rec_result.get("nlp")
                    }

        # 5. Save the search
        self.memory.process(message, {"user_id": user_id}, action="save")

        # 6. Evaluate with Digital Twin if we have products
        products = final_result.get("products", [])
        if products and user_id:
            dt_result = self.digital_twin.process(message, {"user_id": user_id, "products": products})
            if dt_result.get("status") == "success":
                final_result["digital_twin_evaluation"] = dt_result["evaluation"]
                final_result["digital_twin_persona"] = dt_result["persona"]
        
        return final_result
