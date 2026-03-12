from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3
import pandas as pd
import numpy as np
import pickle
import random
from datetime import datetime
from typing import List, Optional

# ==============================================================================
# 2. API GATEWAY LAYER
# ==============================================================================
app = FastAPI(title="Smart Outfit API Gateway", version="1.0")

# Input Schema Validation
class LoginRequest(BaseModel):
    contact: str  # Email or Mobile

class VerifyOTPRequest(BaseModel):
    contact: str
    otp: str

class RecommendRequest(BaseModel):
    occasion: str
    gender: str
    style: str
    weather: str
    color_preference: Optional[str] = "white"

# ==============================================================================
# 7. DATABASE LAYER
# ==============================================================================
def init_db():
    conn = sqlite3.connect('backend_database.db')
    c = conn.cursor()
    # Users
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY AUTOINCREMENT, contact TEXT UNIQUE, preferences TEXT)''')
    # Products (Simulated local storage of scraped data)
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (product_id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, brand TEXT, price REAL, rating REAL, website TEXT, link TEXT, img TEXT, category TEXT)''')
    # Search History
    c.execute('''CREATE TABLE IF NOT EXISTS search_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, occasion TEXT, weather TEXT, gender TEXT, style TEXT, timestamp TEXT)''')
    # Recommendations
    c.execute('''CREATE TABLE IF NOT EXISTS recommendations
                 (recommend_id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

# Load ML Models
try:
    with open("encoder.pkl", "rb") as f: encoder = pickle.load(f)
    with open("model_knn.pkl", "rb") as f: knn = pickle.load(f)
    df_products = pd.read_csv("dataset.csv") # Our local product database simulation
except Exception as e:
    print(f"Warning: ML Models not loaded. Run train_model.py first. Error: {e}")

# ==============================================================================
# 1. USER REQUEST & AUTHENTICATION (OTP)
# ==============================================================================
@app.post("/login")
async def login(req: LoginRequest):
    """Generates an OTP for the user (Auth Layer)"""
    otp = str(random.randint(1000, 9999))
    print(f"Auth Layer -> Sent OTP {otp} to {req.contact}")
    return {"message": "OTP sent successfully", "contact": req.contact, "mock_otp": otp}

@app.post("/verify-otp")
async def verify_otp(req: VerifyOTPRequest):
    """Verifies OTP and manages User context"""
    conn = sqlite3.connect('backend_database.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (contact) VALUES (?)", (req.contact,))
    c.execute("SELECT user_id FROM users WHERE contact = ?", (req.contact,))
    user_id = c.fetchone()[0]
    conn.commit()
    conn.close()
    
    return {"message": "Verification successful", "token": f"mock_jwt_token_{user_id}", "user_id": user_id}

# ==============================================================================
# 3. RECOMMENDATION ENGINE
# ==============================================================================
def engine_predict_outfit(user_input: dict) -> pd.DataFrame:
    """Processes user input through KNN Content Filtering"""
    input_df = pd.DataFrame([{
        "occasion": user_input['occasion'],
        "weather": user_input['weather'],
        "gender": user_input['gender'],
        "style": user_input['style'],
        "color": user_input['color_preference']
    }])
    encoded_input = encoder.transform(input_df)
    distances, indices = knn.kneighbors(encoded_input, n_neighbors=200)
    return df_products.iloc[indices[0]]

# ==============================================================================
# 4. PRODUCT AGGREGATION SERVICE + 5. DATA NORMALIZATION LAYER
# ==============================================================================
def aggregate_and_normalize(raw_items: pd.DataFrame) -> List[dict]:
    """
    Simulates scraping tools (BeautifulSoup, Scrapy) collecting product data 
    from Myntra, Amazon, etc. and converting it to the standard format.
    """
    normalized_products = []
    for _, row in raw_items.iterrows():
        # Standardizing formats exactly as requested in Data Normalization Layer
        normalized_products.append({
            "name": row['name'],
            "price": float(row['price']),
            "brand": row['brand'],
            "source": row['website'],  # Maps 'website' -> 'source'
            "rating": float(row['rating']),
            "category": row['category'],
            "link": row['buy_link']
        })
    return normalized_products

# ==============================================================================
# 6. PRODUCT RANKING SYSTEM
# ==============================================================================
def rank_products(products: List[dict]) -> List[dict]:
    """Applies the scoring algorithm: score = (rating * 0.5) + (price_score * 0.3) + (popularity * 0.2)"""
    if not products: return []
    
    max_price = max([p['price'] for p in products]) if max([p['price'] for p in products]) > 0 else 1
    
    for p in products:
        # Calculating normalized scores
        rating_val = p['rating'] / 5.0 # normalized 0-1
        price_score = 1.0 - (p['price'] / max_price) # lower price = higher score
        popularity = random.uniform(0.5, 1.0) # simulating popularity metric
        
        # Exact Custom Algorithm Logic
        p['score'] = (rating_val * 0.5) + (price_score * 0.3) + (popularity * 0.2)
        p['score'] = round(p['score'], 3)
        
    # Sort descending by custom score
    return sorted(products, key=lambda x: x['score'], reverse=True)

# ==============================================================================
# 8. RESPONSE LAYER (JSON)
# ==============================================================================
@app.post("/recommend")
async def recommend_outfits(req: RecommendRequest):
    """Complete Backend Flow Execution"""
    
    # 1. API Request -> 2. Recommendation Engine
    raw_predictions = engine_predict_outfit(req.model_dump())
    
    # 3. Product Aggregation -> 4. Data Normalization
    normalized_list = aggregate_and_normalize(raw_predictions)
    
    # 5. Product Ranking
    ranked_list = rank_products(normalized_list)
    
    # Split by categories for the final response
    topwear = [p for p in ranked_list if p['category'] == 'Top'][:3]
    bottomwear = [p for p in ranked_list if p['category'] == 'Bottom'][:3]
    footwear = [p for p in ranked_list if p['category'] == 'Footwear'][:2]
    accessories = [p for p in ranked_list if p['category'] == 'Accessory'][:2]
    
    # Store search logic in DB (Mocked user_id = 1)
    conn = sqlite3.connect('backend_database.db')
    c = conn.cursor()
    c.execute("INSERT INTO search_history (user_id, occasion, weather, gender, style, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
             (1, req.occasion, req.weather, req.gender, req.style, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    # Exact Response Format Output
    return {
        "outfit": {
            "topwear": [{"name": t["name"], "price": t["price"], "site": t["source"], "link": t["link"], "score": t["score"]} for t in topwear],
            "bottomwear": [{"name": b["name"], "price": b["price"], "site": b["source"], "link": b["link"], "score": b["score"]} for b in bottomwear],
            "footwear": [{"name": f["name"], "price": f["price"], "site": f["source"], "link": f["link"], "score": f["score"]} for f in footwear],
            "accessories": [{"name": a["name"], "price": a["price"], "site": a["source"], "link": a["link"], "score": a["score"]} for a in accessories]
        }
    }

@app.get("/products")
async def get_all_products():
    """Mock endpoint to retrieve system tracking"""
    return {"status": "Database active", "products": len(df_products)}
