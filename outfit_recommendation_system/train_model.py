import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import NearestNeighbors
from sklearn.tree import DecisionTreeClassifier
import pickle
import random
import os

print("Generating enhanced dataset for Ecommerce Integration...")
categories = ['Top', 'Bottom', 'Footwear', 'Accessory']
occasions = ['office', 'casual', 'party', 'wedding', 'gym', 'travel', 'interview']
weathers = ['hot', 'cold', 'rainy']
genders = ['male', 'female', 'unisex']
styles = ['formal', 'casual', 'sporty', 'traditional', 'trendy']
colors = ['black', 'white', 'blue', 'red', 'green', 'grey', 'yellow', 'pink']

brands = ['Nike', 'Adidas', 'Puma', 'Zara', 'H&M', 'Levi\'s', 'Allen Solly', 'Biba', 'Manyavar', 'Fossil']
websites = ['Amazon', 'Myntra', 'Ajio', 'Flipkart', 'Nykaa Fashion']

data = []
for i in range(2000):
    cat = random.choice(categories)
    occ = random.choice(occasions)
    wea = random.choice(weathers)
    gen = random.choice(genders)
    
    if occ in ['office', 'interview']:
        sty = 'formal'
    elif occ == 'gym':
        sty = 'sporty'
    elif occ in ['party', 'wedding']:
        sty = random.choice(['trendy', 'traditional', 'formal'])
    else:
        sty = random.choice(['casual', 'trendy', 'sporty'])

    col = random.choice(colors)
    brand = random.choice(brands)
    price = round(random.uniform(15.0, 150.0), 2)
    rating = round(random.uniform(3.0, 5.0), 1)
    website = random.choice(websites)
    
    # Mock image links
    img = f"https://via.placeholder.com/150/{random.choice(['c2a884', 'a88e6a', '1a1625', 'beb6ce'])}/ffffff?text={cat}+{brand}"
    buy_link = f"https://www.{website.lower().replace(' ', '')}.com/search?q={col}+{sty}+{cat}"

    name = f"{brand} {col.capitalize()} {sty.capitalize()} {cat}"
    data.append([i, name, cat, occ, wea, gen, sty, col, brand, price, rating, website, img, buy_link])

df = pd.DataFrame(data, columns=['item_id', 'name', 'category', 'occasion', 'weather', 'gender', 'style', 'color', 'brand', 'price', 'rating', 'website', 'img', 'buy_link'])
df.to_csv('dataset.csv', index=False)
print("Enhanced Dataset 'dataset.csv' generated with ecommerce fields.")

print("Encoding feature vectors...")
features = ['occasion', 'weather', 'gender', 'style', 'color']
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
encoded_features = encoder.fit_transform(df[features])

print("Training Recommendation Engine (KNN)...")
knn = NearestNeighbors(n_neighbors=150, metric='cosine', n_jobs=1)
knn.fit(encoded_features)

print("Training Popularity Engine (Decision Tree)...")
df['is_popular'] = np.where(df['rating'] > 4.2, 1, 0)
dtree = DecisionTreeClassifier(max_depth=5)
dtree.fit(encoded_features, df['is_popular'])

print("Saving updated models...")
with open('model_knn.pkl', 'wb') as f:
    pickle.dump(knn, f)
with open('model_dtree.pkl', 'wb') as f:
    pickle.dump(dtree, f)
with open('encoder.pkl', 'wb') as f:
    pickle.dump(encoder, f)

print("All Models and Encoders saved successfully.")
