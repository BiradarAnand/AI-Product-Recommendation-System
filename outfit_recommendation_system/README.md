# Purpose-Based Smart Outfit Recommendation System

A full-stack machine learning project that recommends clothing outfits based on the purpose of the event, weather conditions, user preferences, and fashion trends. 

## Features
- **User Input Module**: Select occasion, weather, gender, style, and color.
- **Machine Learning**: Uses K-Nearest Neighbors (KNN) to perform content-based filtering on a dataset of outfit items.
- **Frontend Dashboard**: A stunning, modern dark-mode UI with glassmorphism that showcases curated outfits across categories (Top, Bottom, Footwear, Accessories).
- **Backend**: Built with FastAPI for blazing fast recommendations.

## How to Run

1. Open a terminal in this directory (`outfit_recommendation_system`).
2. Install requirements using:
   ```bash
   pip install fastapi uvicorn pandas scikit-learn numpy jinja2 python-multipart
   ```
3. Generate the dataset and train the ML models:
   ```bash
   python train_model.py
   ```
4. Start the live FastAPI server:
   ```bash
   uvicorn app:app --reload --port 8000
   ```
5. Open your browser to http://127.0.0.1:8000
