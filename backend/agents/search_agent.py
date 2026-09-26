import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from recommendation_engine import HybridRecommendationEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SearchAgent:
    """
    Modular Search Agent that uses the HybridRecommendationEngine
    to process natural-language product queries and return structured results.
    """
    def __init__(self):
        self.engine = HybridRecommendationEngine()
        try:
            self.engine.load()
            logger.info("SearchAgent: HybridRecommendationEngine loaded successfully.")
        except Exception as e:
            logger.error(f"SearchAgent: Failed to load HybridRecommendationEngine: {e}")
            self.engine = None
    
    def search_products(self, query: str, user_id: int = None, top_n: int = 10, filters: dict = None) -> dict:
        """
        Process a natural language product query.
        
        Args:
            query (str): The natural language query.
            user_id (int, optional): Optional user ID for personalized results.
            top_n (int): Number of results to return.
            filters (dict, optional): Additional filters (category, max_price, min_rating, brand).
            
        Returns:
            dict: Structured response with status, count, and results list.
        """
        if not self.engine:
            return {
                "status": "error",
                "message": "Recommendation engine is not initialized.",
                "results": [],
                "count": 0
            }
            
        if not query or not query.strip():
            return {
                "status": "error",
                "message": "Query cannot be empty.",
                "results": [],
                "count": 0
            }
            
        try:
            raw_results = self.engine.search(query=query, user_id=user_id, top_n=top_n, filters=filters)
            
            structured_results = []
            for item in raw_results:
                structured_results.append({
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "category": item.get("category"),
                    "price": item.get("price"),
                    "rating": item.get("rating"),
                    "reviews": item.get("reviews"),
                    "brand": item.get("brand"),
                    "image_url": item.get("image_url")
                })
                
            return {
                "status": "success",
                "message": f"Found {len(structured_results)} results for '{query}'.",
                "results": structured_results,
                "count": len(structured_results)
            }
            
        except Exception as e:
            logger.error(f"SearchAgent: Error during search: {e}")
            return {
                "status": "error",
                "message": f"An error occurred during search: {str(e)}",
                "results": [],
                "count": 0
            }
