from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import UserLogin, UserRegister, Product, Order
from recommender import RecommendationEngine

app = FastAPI(title="AI Product Recommendation API")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

recommender = RecommendationEngine()

# --- Auth Routes ---
@app.post("/api/register")
def register(user: UserRegister):
    return {"message": "User registered successfully", "userId": 1, "name": user.name}

@app.post("/api/login")
def login(user: UserLogin):
    if len(user.password) >= 8:
        return {"message": "Login successful", "token": "mock_jwt_token", "userId": 1}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# --- Product Routes ---
@app.get("/api/products")
def get_products():
    return [
        {"id": 1, "title": "Laptop Pro", "price": 1099.99, "category": "Computers", "imageUrl": "laptop.jpg"},
        {"id": 2, "title": "Smartphone X", "price": 799.99, "category": "Phones", "imageUrl": "phone.jpg"},
    ]

@app.get("/api/recommendations/{user_id}")
def get_recommendations(user_id: int, history: str = ""):
    # History can be comma-separated product IDs passed by frontend
    history_list = [int(x) for x in history.split(",")] if history else []
    recommendations = recommender.generateRecommendations(user_id, history_list)
    return {"userId": user_id, "recommendations": recommendations}

# --- Cart/Order Routes ---
@app.post("/api/orders")
def create_order(order: Order):
    return {"message": "Order placed successfully", "orderId": order.orderId, "status": "Confirmed"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
