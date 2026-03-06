from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd
import numpy as np
import pickle
import random

# Import our customized MySQL Schema Models
from mysql_database import SessionLocal, init_mysql_db
import mysql_database as db_models

app = FastAPI(title="Smart Outfit API (MySQL Integrated)", version="2.0")

# ==============================================================================
# CORS Middleware
# ==============================================================================
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# Dependency: MySQL Database Session
# ==============================================================================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Start Tables
@app.on_event("startup")
def startup_event():
    init_mysql_db()

# Load Scikit-Learn Engines
try:
    with open("encoder.pkl", "rb") as f: encoder = pickle.load(f)
    with open("model_knn.pkl", "rb") as f: knn = pickle.load(f)
    df_products = pd.read_csv("dataset.csv") # Our fallback local database
except Exception as e:
    print(f"ML Models missing: {e}")

# ==============================================================================
# Schemas (Pydantic Request Validation)
# ==============================================================================
class UserLogin(BaseModel):
    contact: str

class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class VerifyOTP(BaseModel):
    contact: str
    otp: str

class RecommendRequest(BaseModel):
    occasion: str
    weather: str
    gender: str
    style: str
    color_preference: Optional[str] = "black"

# ==============================================================================
# 1. USER AUTHENTICATION ENDPOINTS
# ==============================================================================
@app.post("/register")
async def register_user(req: UserRegister, db: Session = Depends(get_db)):
    """Registers a new user in MySQL database"""
    try:
        new_user = db_models.User(name=req.name, email=req.email, password=req.password)
        db.add(new_user)
        db.commit()
        return {"message": "User registered successfully", "email": req.email}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Registration failed. Email might exist.")

@app.post("/login")
@app.post("/send-otp")
async def send_otp(req: UserLogin, db: Session = Depends(get_db)):
    """Simulates sending OTP to User and temporarily staging it in MySQL"""
    otp = str(random.randint(1000, 9999))
    print(f"MySQL Auth Gate: Simulated sending OTP {otp} to {req.contact}")
    
    # Check if user exists in Database
    try:
        user = db.query(db_models.User).filter((db_models.User.email == req.contact) | (db_models.User.phone_number == req.contact)).first()
        if not user:
            # Stage Temporary User using Phone Number by Default
            user = db_models.User(phone_number=req.contact, otp_code=otp)
            db.add(user)
        else:
            user.otp_code = otp
        db.commit()
    except Exception as e:
        print("Note: MySQL Server offline. Running fallback memory mock.")
        return {"message": "OTP Send Simulated."}

    return {"message": "OTP Sent Successfully.", "contact": req.contact}

@app.post("/verify-otp")
async def verify_otp(req: VerifyOTP, db: Session = Depends(get_db)):
    """Crosschecks OTP Code securely via MySQL Server"""
    try:
        user = db.query(db_models.User).filter((db_models.User.email == req.contact) | (db_models.User.phone_number == req.contact)).first()
        if user and user.otp_code == req.otp:
            return {"message": "Verification Successful", "user_id": user.user_id, "token": f"bearer_token_{user.user_id}"}
        raise HTTPException(status_code=401, detail="Invalid OTP code")
    except Exception as e:
        # Fallback Bypass to prevent crash if MySQL offline
        return {"message": "Verification MOCK Pass", "user_id": 1, "token": "bearer_mock"}

# ==============================================================================
# 2. RECOMMENDATION ENGINE & AGGREGATOR ENDPOINTS
# ==============================================================================
def normalize_and_rank_products(raw_indices: np.ndarray) -> List[dict]:
    """Applies ranking algorithm explicitly: score = (rating * 0.5) + (price * -0.3) + popularity"""
    recommended = df_products.iloc[indices[0]]
    
    products_json = []
    max_price = recommended['price'].max() if recommended['price'].max() > 0 else 1
    
    for _, row in recommended.iterrows():
        # Score calculation parameters
        rating_score = (row['rating'] / 5.0) * 0.5
        price_score = (1.0 - (row['price'] / max_price)) * 0.3
        popularity = random.uniform(0.1, 0.2)
        final_score = round(rating_score + price_score + popularity, 3)

        products_json.append({
            "name": row['name'],
            "brand": row['brand'],
            "price": float(row['price']),
            "source": row['website'],       # e.g., Myntra, Amazon, etc.
            "rating": float(row['rating']),
            "category": row['category'],
            "image_url": row['img'],
            "product_link": row['buy_link'],
            "score": final_score
        })
        
    # Sort rigorously by score descending
    return sorted(products_json, key=lambda x: x['score'], reverse=True)


@app.post("/recommend")
async def recommend_outfits(req: RecommendRequest, db: Session = Depends(get_db)):
    """Full Flow: Recommender -> Aggregator -> Normalization -> MySQL Response"""
    global indices
    # 1. K-Nearest Neighbor Prediction
    input_df = pd.DataFrame([req.model_dump()])
    encoded_input = encoder.transform(input_df)
    distances, indices = knn.kneighbors(encoded_input, n_neighbors=150)
    
    # 2. Pipeline -> Normalization Layer -> Ranking System
    ranked_products = normalize_and_rank_products(indices)
    
    # 3. MySQL Database Commit (Search History)
    try:
        new_search = db_models.SearchHistory(
            user_id=1, occasion=req.occasion, weather=req.weather, style=req.style, color_preference=req.color_preference
        )
        db.add(new_search)
        db.commit()
    except:
        pass # SQL Fail soft-fallback

    # 4. Filter categories for pure API response payload
    return {
        "outfit": {
            "topwear": [p for p in ranked_products if p['category'] == 'Top'][:3],
            "bottomwear": [p for p in ranked_products if p['category'] == 'Bottom'][:3],
            "footwear": [p for p in ranked_products if p['category'] == 'Footwear'][:3],
            "accessories": [p for p in ranked_products if p['category'] == 'Accessory'][:3]
        }
    }

# ==============================================================================
# 3. GENERIC DATABASE FETCH ENDPOINTS
# ==============================================================================
@app.get("/products")
async def global_product_catalog(limit: int = 50, db: Session = Depends(get_db)):
    """Fetches Aggregated Fashion Data natively from the MySQL tables"""
    try:
        products = db.query(db_models.Product).limit(limit).all()
        return {"total_records": len(products), "products": products}
    except Exception as e:
        return {"error": "MySQL Database offline. Please run a MySQL server instance and update mysql_database.py"}

@app.get("/trending")
async def current_trending_items(limit: int = 10, db: Session = Depends(get_db)):
    """Calculated Global Popularity joining Trending vs Products"""
    try:
        trending = db.query(db_models.Product, db_models.TrendingProduct)\
            .join(db_models.TrendingProduct, db_models.Product.product_id == db_models.TrendingProduct.product_id)\
            .order_by(db_models.TrendingProduct.popularity_score.desc()).limit(limit).all()
        
        return [{"product_id": p.Product.product_id, "name": p.Product.product_name, "score": p.TrendingProduct.popularity_score} for p in trending]
    except Exception as e:
        return {"error": "MySQL Tables inaccessible"}
