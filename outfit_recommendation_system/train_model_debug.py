import os
print("Starting script...")
import random
print("Imported random")
import pickle
print("Imported pickle")
import pandas as pd
print("Imported pandas")
import numpy as np
print("Imported numpy")
from sklearn.preprocessing import OneHotEncoder
from sklearn.neighbors import NearestNeighbors
from sklearn.tree import DecisionTreeClassifier
print("Imported sklearn")

# 1. Dataset Generation
print("Generating dataset...")
categories = ['Top', 'Bottom', 'Footwear', 'Accessory']
occasions = ['office', 'casual', 'party', 'wedding', 'gym', 'travel', 'interview']
weathers = ['hot', 'cold', 'rainy']
genders = ['male', 'female', 'unisex']
styles = ['formal', 'casual', 'sporty', 'traditional', 'trendy']
colors = ['black', 'white', 'blue', 'red', 'green', 'grey', 'yellow', 'pink']

# Creating logical combinations to make dataset somewhat realistic
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
    
    name = f"{col.capitalize()} {sty.capitalize()} {cat} for {occ.capitalize()}"
    data.append([i, name, cat, occ, wea, gen, sty, col])

print("Creating dataframe...")
df = pd.DataFrame(data, columns=['item_id', 'name', 'category', 'occasion', 'weather', 'gender', 'style', 'color'])
df.to_csv('dataset.csv', index=False)
print("Dataset 'dataset.csv' generated with 2000 items.")

# 2. Preprocessing & Feature Engineering
print("Encoding features...")
features = ['occasion', 'weather', 'gender', 'style', 'color']
encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
encoded_features = encoder.fit_transform(df[features])

# 3. Model Training
print("Training KNN...")
knn = NearestNeighbors(n_neighbors=50, metric='cosine', n_jobs=1)
knn.fit(encoded_features)

print("Training DTree...")
df['is_popular'] = np.random.choice([0, 1], size=len(df), p=[0.7, 0.3])
dtree = DecisionTreeClassifier(max_depth=5)
dtree.fit(encoded_features, df['is_popular'])

# 4. Save Models and Encoders
print("Saving models...")
with open('model_knn.pkl', 'wb') as f:
    pickle.dump(knn, f)

with open('model_dtree.pkl', 'wb') as f:
    pickle.dump(dtree, f)

with open('encoder.pkl', 'wb') as f:
    pickle.dump(encoder, f)

print("Models (KNN, Decision Tree) and Encoder saved successfully.")
