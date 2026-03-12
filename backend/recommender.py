from typing import List

class RecommendationEngine:
    def __init__(self):
        self.modelVersion = "1.0"
        
    def generateRecommendations(self, user_id: int, browsing_history: List[int]) -> List[dict]:
        # Mock ML recommendation logic
        print(f"[ML Model] Generating recommendations for user {user_id} based on history: {browsing_history}")
        
        # In a real app, this would use collaborative filtering, matrix factorization, etc.
        return [
            {"id": 101, "title": "AI Smart Watch", "price": 199.99, "category": "Electronics", "imageUrl": "smartwatch.jpg"},
            {"id": 102, "title": "Wireless Earbuds", "price": 89.99, "category": "Audio", "imageUrl": "earbuds.jpg"},
            {"id": 103, "title": "Ergonomic Desk Chair", "price": 149.99, "category": "Furniture", "imageUrl": "chair.jpg"}
        ]
