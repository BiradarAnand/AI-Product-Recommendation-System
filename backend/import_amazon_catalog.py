import sqlite3
import pandas as pd
import os

DB_PATH = "amazon_catalog.db"
CSV_DIR = r"C:\Users\birad\Desktop\LLM - AI\Desc\archive (1)"

def clean_price(price_str):
    if pd.isna(price_str):
        return 0.0
    price_str = str(price_str).replace('₹', '').replace(',', '').replace('', '').strip()
    try:
        return float(price_str)
    except:
        return 0.0

def clean_int(val):
    if pd.isna(val):
        return 0
    val = str(val).replace(',', '').strip()
    try:
        return int(val)
    except:
        return 0

def clean_float(val):
    if pd.isna(val):
        return 0.0
    try:
        return float(val)
    except:
        return 0.0

def get_brand(name):
    if pd.isna(name):
        return "Unknown"
    return str(name).split(' ')[0]

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            category TEXT,
            sub_category TEXT,
            price REAL,
            actual_price REAL,
            stock INTEGER DEFAULT 100,
            rating REAL,
            reviews INTEGER,
            image_url TEXT,
            link TEXT,
            brand TEXT
        )
    ''')
    
    # Clear existing data so we don't duplicate on multiple runs
    cursor.execute('DELETE FROM products')
    conn.commit()
    return conn

def import_all_data():
    conn = init_db()
    cursor = conn.cursor()
    
    total_imported = 0
    
    for filename in os.listdir(CSV_DIR):
        if not filename.endswith(".csv"):
            continue
            
        # Skip the massive master file, we are building from individuals
        if filename == "Amazon-Products.csv":
            continue
            
        filepath = os.path.join(CSV_DIR, filename)
        
        # Derive a clean category name from the filename
        fallback_category = filename.replace(".csv", "").replace("All ", "").strip()
        
        print(f"Processing {filename}...")
        try:
            df = pd.read_csv(filepath)
            
            # Limit to top 500 per category to keep DB fast and light (~70k products total)
            df = df.head(500)
            
            count = 0
            for _, row in df.iterrows():
                name = str(row.get('name', ''))
                if pd.isna(name) or not name.strip():
                    continue
                    
                main_category = str(row.get('main_category', fallback_category))
                sub_category = str(row.get('sub_category', fallback_category))
                
                # Sometime main_category is empty in the CSV
                if pd.isna(main_category) or not main_category.strip() or main_category == "nan":
                    main_category = fallback_category
                if pd.isna(sub_category) or not sub_category.strip() or sub_category == "nan":
                    sub_category = fallback_category

                image = str(row.get('image', ''))
                link = str(row.get('link', ''))
                
                rating = clean_float(row.get('ratings', 0))
                reviews = clean_int(row.get('no_of_ratings', 0))
                discount_price = clean_price(row.get('discount_price', '0'))
                actual_price = clean_price(row.get('actual_price', '0'))
                
                # If discount is 0, use actual, else use discount as the display price
                price = discount_price if discount_price > 0 else actual_price
                if price <= 0:
                    price = 999.0 # fallback price
                
                brand = get_brand(name)
                
                cursor.execute('''
                    INSERT INTO products 
                    (name, description, category, sub_category, price, actual_price, rating, reviews, image_url, link, brand)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (name, sub_category, main_category, sub_category, price, actual_price, rating, reviews, image, link, brand))
                
                count += 1
                
            conn.commit()
            print(f"Inserted {count} products from {filename}.")
            total_imported += count
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    conn.close()
    print(f"Migration complete! Total products imported: {total_imported}")

if __name__ == "__main__":
    import_all_data()
