from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pickle
import pandas as pd
import numpy as np
import os
import random
import sqlite3
from datetime import datetime

app = FastAPI()

# Database Initialization
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS search_history
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, contact TEXT, occasion TEXT, weather TEXT, gender TEXT, style TEXT, color TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS recommendations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, search_id INTEGER, recommended_items TEXT, timestamp TEXT)''')
    conn.commit()
    conn.close()

init_db()

if not os.path.exists('static'):
    os.makedirs('static')
if not os.path.exists('templates'):
    os.makedirs('templates')

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Mock Sessions Database
sessions = {}

# Load models and dataset
with open("encoder.pkl", "rb") as f:
    encoder = pickle.load(f)

with open("model_knn.pkl", "rb") as f:
    knn = pickle.load(f)

df = pd.read_csv("dataset.csv")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home / Landing Page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login Page (Email / Phone)"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/send_otp", response_class=RedirectResponse)
async def send_otp(request: Request, contact_info: str = Form(...)):
    """Mock OTP Generation Process"""
    # For demo purposes, OTP is fixed or mock generated
    otp = str(random.randint(1000, 9999))
    print(f"MOCK OTP for {contact_info} is: {otp}")
    
    # Redirecting to Verify Page
    url = f"/otp?contact={contact_info}"
    return RedirectResponse(url=url, status_code=303)

@app.get("/otp", response_class=HTMLResponse)
async def otp_page(request: Request, contact: str = ""):
    """Verify OTP Page"""
    return templates.TemplateResponse("otp.html", {"request": request, "contact": contact})

@app.post("/verify_otp", response_class=RedirectResponse)
async def verify_otp(request: Request, otp: str = Form(...)):
    """Mock verification endpoint - forwards to recommendation form on success"""
    # Accept any OTP for testing
    return RedirectResponse(url="/recommend_form", status_code=303)

@app.get("/recommend_form", response_class=HTMLResponse)
async def recommend_form(request: Request):
    """Recommendation Form (Occasion, Weather, etc.)"""
    return templates.TemplateResponse("recommend_form.html", {"request": request})

@app.post("/recommend", response_class=HTMLResponse)
async def recommend(request: Request):
    """Prediction Logic and Results Page"""
    form = await request.form()
    occasion = form.get("occasion")
    weather = form.get("weather")
    gender = form.get("gender")
    style = form.get("style")
    color = form.get("color")

    # Encode user input
    user_input = pd.DataFrame([{
        "occasion": occasion,
        "weather": weather,
        "gender": gender,
        "style": style,
        "color": color
    }])
    
    encoded_input = encoder.transform(user_input)

    # Find nearest neighbors
    distances, indices = knn.kneighbors(encoded_input, n_neighbors=100)
    
    # Fetch recommended items (Data Normalization Layer & Product Ranking)
    recommended_items = df.iloc[indices[0]]
    
    # Product Ranking Engine: Prioritize higher ratings, then lower prices
    ranked_items = recommended_items.sort_values(by=['rating', 'price'], ascending=[False, True])

    top = ranked_items[ranked_items['category'] == 'Top'].head(2).to_dict(orient='records')
    bottom = ranked_items[ranked_items['category'] == 'Bottom'].head(2).to_dict(orient='records')
    footwear = ranked_items[ranked_items['category'] == 'Footwear'].head(2).to_dict(orient='records')
    accessory = ranked_items[ranked_items['category'] == 'Accessory'].head(2).to_dict(orient='records')

    outfit = {
        "Top": top[0] if top else None,
        "Bottom": bottom[0] if bottom else None,
        "Footwear": footwear[0] if footwear else None,
        "Accessory": accessory[0] if accessory else None
    }
    
    # Store Search History in DB (Mock User Tracker)
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("INSERT INTO search_history (contact, occasion, weather, gender, style, color, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
              ("guest_user", occasion, weather, gender, style, color, datetime.now().isoformat()))
    search_id = c.lastrowid
    # Logging Recommendations
    rec_names = f"{outfit['Top']['name'] if outfit['Top'] else ''}, {outfit['Bottom']['name'] if outfit['Bottom'] else ''}"
    c.execute("INSERT INTO recommendations (search_id, recommended_items, timestamp) VALUES (?, ?, ?)",
              (search_id, rec_names, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    
    return templates.TemplateResponse("recommend.html", {
        "request": request, 
        "outfit": outfit, 
        "user_pref": user_input.to_dict(orient='records')[0]
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """User Activity Dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About the System"""
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Contact Page"""
    return templates.TemplateResponse("contact.html", {"request": request})
