"""
generate_products.py
─────────────────────
Generates ~8000 realistic products across 8 categories with
real product images fetched from Unsplash API.

Setup:
    1. Get free Unsplash API key at unsplash.com/developers
    2. Add UNSPLASH_ACCESS_KEY=your_key to your .env file
    3. Run: python generate_products.py
"""

import os, random, time, json
import urllib.request, urllib.parse
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")


BRANDS = {
    "Shirts":       ["Raymond","Arrow","Van Heusen","Louis Philippe","Peter England","Allen Solly","Park Avenue","Blackberrys","Wills Lifestyle","ColorPlus","United Colors of Benetton","Pepe Jeans","Flying Machine","Killer","Spykar"],
    "Jeans":        ["Levi's","Wrangler","Lee","Pepe Jeans","Spykar","Flying Machine","Killer","Jack & Jones","Numero Uno","U.S. Polo Assn.","Roadster","Breakbounce","Mufti","Highlander","HRX"],
    "Watches":      ["Titan","Fastrack","Casio","Timex","Fossil","Seiko","Orient","Sonata","Maxima","Q&Q","Police","Daniel Klein","MVMT","Tommy Hilfiger","Guess"],
    "Track Pants":  ["Nike","Adidas","Puma","Reebok","Under Armour","HRX","Wildcraft","Fila","Asics","New Balance","Kappa","Lotto","Vector X","Nivia","Campus"],
    "Tshirts":      ["Nike","Adidas","Puma","Levis","Tommy Hilfiger","H&M","Zara","Gap","Superdry","Jack & Jones","United Colors of Benetton","HRX","Roadster","Bewakoof","The Souled Store"],
    "Casual Shoes": ["Nike","Adidas","Puma","Reebok","Skechers","Bata","Woodland","Red Tape","Clarks","Hush Puppies","Lee Cooper","Fila","New Balance","Converse","Vans"],
    "Sports Shoes": ["Nike","Adidas","Puma","Reebok","Asics","New Balance","Under Armour","Saucony","Brooks","Mizuno","Fila","Lotto","Campus","Vector X","Nivia"],
    "Trousers":     ["Raymond","Arrow","Van Heusen","Louis Philippe","Peter England","Allen Solly","Park Avenue","Blackberrys","Excalibur","ColorPlus","Pepe Jeans","Jack & Jones","Mufti","Highlander","Roadster"],
}

UNSPLASH_QUERIES = {
    "Shirts":       "men formal shirt fashion",
    "Jeans":        "men denim jeans fashion",
    "Watches":      "wristwatch luxury timepiece",
    "Track Pants":  "men sportswear track pants",
    "Tshirts":      "men casual tshirt fashion",
    "Casual Shoes": "men casual sneakers shoes",
    "Sports Shoes": "men running sports shoes",
    "Trousers":     "men formal trousers fashion",
}

FALLBACK_IMAGES = {
    "Shirts":       "https://via.placeholder.com/400x400.png?text=Shirt",
    "Jeans":        "https://via.placeholder.com/400x400.png?text=Jeans",
    "Watches":      "https://via.placeholder.com/400x400.png?text=Watch",
    "Track Pants":  "https://via.placeholder.com/400x400.png?text=Track+Pants",
    "Tshirts":      "https://via.placeholder.com/400x400.png?text=Tshirt",
    "Casual Shoes": "https://via.placeholder.com/400x400.png?text=Casual+Shoes",
    "Sports Shoes": "https://via.placeholder.com/400x400.png?text=Sports+Shoes",
    "Trousers":     "https://via.placeholder.com/400x400.png?text=Trousers",
}

COLORS     = ["Black","Navy Blue","White","Grey","Olive Green","Beige","Brown","Maroon","Royal Blue","Charcoal","Khaki","Dark Green","Sky Blue","Off White","Camel","Rust","Teal","Burgundy","Midnight Blue","Stone"]
FITS       = ["Regular Fit","Slim Fit","Comfort Fit","Relaxed Fit","Tailored Fit","Classic Fit"]
MATERIALS  = ["Cotton","Polyester","Cotton Blend","Linen","Wool Blend","Nylon","Spandex Blend","Denim","Flex Fabric","Mesh"]
ADJECTIVES = ["Premium","Classic","Essential","Modern","Signature","Elite","Active","Urban","Casual","Formal","Heritage","Performance","Everyday","Contemporary","Comfort"]

NAME_TEMPLATES = {
    "Shirts":       ["{adj} {color} {fit} Formal Shirt","{adj} {color} Casual Shirt","{color} Oxford {fit} Shirt","{adj} Striped {fit} Shirt","{color} Linen {fit} Shirt","{adj} Check Pattern Shirt","{color} Poplin {fit} Shirt","{adj} {color} Business Shirt"],
    "Jeans":        ["{adj} {color} {fit} Jeans","{color} Stretch {fit} Jeans","{adj} Washed {fit} Denim Jeans","{color} {fit} Stretchable Jeans","{adj} {color} Mid-Rise Jeans","{color} Distressed {fit} Jeans","{adj} Dark Wash {fit} Jeans"],
    "Watches":      ["{adj} Analog {color} Dial Watch","{adj} Digital Sports Watch","{color} Dial Chronograph Watch","{adj} Stainless Steel Watch","{adj} Mesh Strap Analog Watch","{color} Leather Strap Watch","{adj} Multi-Function Watch","{adj} Water Resistant Watch"],
    "Track Pants":  ["{adj} {color} Training Track Pants","{color} Dry-Fit Track Pants","{adj} Jogger Track Pants","{color} {fit} Running Pants","{adj} {color} Sports Track Pants","{adj} Moisture-Wicking Track Pants","{color} Fleece Track Pants"],
    "Tshirts":      ["{adj} {color} Round Neck T-Shirt","{color} Graphic Print T-Shirt","{adj} {color} Polo T-Shirt","{color} V-Neck T-Shirt","{adj} Oversized T-Shirt","{color} Printed Half Sleeve T-Shirt","{adj} {color} Sports T-Shirt","{color} Henley T-Shirt"],
    "Casual Shoes": ["{adj} {color} Canvas Sneakers","{color} Lace-Up Casual Shoes","{adj} {color} Loafers","{adj} Slip-On Casual Shoes","{color} Boat Shoes","{adj} {color} Derby Shoes","{adj} Moccasin Casual Shoes","{color} Suede Casual Shoes"],
    "Sports Shoes": ["{adj} {color} Running Shoes","{color} Training Shoes","{adj} Cushioned Running Shoes","{adj} {color} Gym Shoes","{color} Lightweight Running Shoes","{adj} Stability Running Shoes","{adj} {color} Cross Training Shoes","{color} Breathable Sports Shoes"],
    "Trousers":     ["{adj} {color} {fit} Formal Trousers","{color} Flat Front {fit} Trousers","{adj} {color} Chinos","{color} {fit} Business Trousers","{adj} Pleated Formal Trousers","{color} Stretch {fit} Trousers","{adj} {color} Smart Casual Trousers","{color} Linen Blend Trousers"],
}

DESCRIPTIONS = {
    "Shirts":       "A {adj_l} {color_l} {fit_l} shirt crafted from premium {material}. Features a clean finish with a comfortable silhouette, perfect for both formal occasions and smart-casual wear. Easy to maintain and long-lasting fabric quality.",
    "Jeans":        "These {color_l} {fit_l} jeans are made from high-quality {material} for a comfortable and stylish look. Features a durable construction with a modern cut. Suitable for everyday casual wear and outings.",
    "Watches":      "An elegant timepiece featuring a {color_l} dial with precise quartz movement. Built with a durable case and a comfortable strap. Water-resistant and suitable for daily wear.",
    "Track Pants":  "{adj} track pants designed for high-performance training and everyday comfort. Made from breathable {material} fabric that wicks moisture away. Features an elastic waistband with a drawstring for a secure fit.",
    "Tshirts":      "A comfortable {color_l} t-shirt made from soft {material} fabric. Features a regular fit with a clean neckline. Great for casual daily wear, gym, or outdoor activities.",
    "Casual Shoes": "{adj} casual shoes designed for all-day comfort and style. Features a durable outsole with cushioned insole for long-lasting wear. Versatile enough for everyday use and casual outings.",
    "Sports Shoes": "High-performance {color_l} sports shoes engineered for {adj_l} athletic activity. Features responsive cushioning and a breathable upper mesh. Lightweight construction with superior grip on all surfaces.",
    "Trousers":     "{adj} {color_l} {fit_l} trousers tailored for a sharp and professional look. Made from {material} for a smooth drape and comfortable fit throughout the day. Ideal for office wear and formal events.",
}

PRICE_RANGES = {
    "Shirts": (499,3999), "Jeans": (799,4999), "Watches": (699,9999),
    "Track Pants": (399,2999), "Tshirts": (299,2499), "Casual Shoes": (699,5999),
    "Sports Shoes": (999,7999), "Trousers": (599,4499),
}

PRODUCTS_PER_CATEGORY = 1000


def fetch_image_pool(category: str, count: int = 30) -> list:
    if not UNSPLASH_ACCESS_KEY:
        print(f"  [!] No UNSPLASH_ACCESS_KEY — using placeholder for '{category}'")
        return [FALLBACK_IMAGES[category]]
    query = UNSPLASH_QUERIES[category]
    url   = (f"https://api.unsplash.com/photos/random"
             f"?query={urllib.parse.quote(query)}&count={count}"
             f"&orientation=squarish&client_id={UNSPLASH_ACCESS_KEY}")
    try:
        req = urllib.request.Request(url, headers={"Accept-Version": "v1"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        urls = [p["urls"]["regular"] for p in data if "urls" in p]
        if urls:
            print(f"  [Unsplash] {len(urls)} images fetched for '{category}'")
            return urls
        return [FALLBACK_IMAGES[category]]
    except Exception as e:
        print(f"  [!] Unsplash error for '{category}': {e}")
        return [FALLBACK_IMAGES[category]]


def generate_product(category: str, image_pool: list) -> dict:
    brand = random.choice(BRANDS[category])
    color = random.choice(COLORS)
    fit   = random.choice(FITS)
    mat   = random.choice(MATERIALS)
    adj   = random.choice(ADJECTIVES)
    name  = f"{brand} {random.choice(NAME_TEMPLATES[category]).format(adj=adj,color=color,fit=fit)}"
    desc  = DESCRIPTIONS[category].format(adj=adj,adj_l=adj.lower(),color=color,color_l=color.lower(),fit=fit,fit_l=fit.lower(),material=mat.lower())
    pmin, pmax = PRICE_RANGES[category]
    return {
        "name": name, "description": desc, "category": category,
        "price": random.randint(pmin//100, pmax//100)*100,
        "stock": random.randint(5,500), "rating": round(random.uniform(3.0,5.0),1),
        "reviews": random.randint(10,5000), "image_url": random.choice(image_pool), "brand": brand,
    }


def insert_products(image_pools: dict) -> int:
    conn = mysql.connector.connect(**DB_CONFIG)
    cur  = conn.cursor()
    SQL  = "INSERT INTO products (name,description,category,price,stock,rating,reviews,image_url,brand) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    total = 0
    for category, pool in image_pools.items():
        print(f"  Inserting {PRODUCTS_PER_CATEGORY} '{category}' products...")
        batch = []
        for _ in range(PRODUCTS_PER_CATEGORY):
            p = generate_product(category, pool)
            batch.append((p["name"],p["description"],p["category"],p["price"],p["stock"],p["rating"],p["reviews"],p["image_url"],p["brand"]))
            if len(batch) == 500:
                cur.executemany(SQL, batch); conn.commit(); total += len(batch); batch = []
        if batch:
            cur.executemany(SQL, batch); conn.commit(); total += len(batch)
        print(f"  ✓ {category} done")
    cur.close(); conn.close()
    return total


if __name__ == "__main__":
    print("=" * 55)
    print("Product Generator — Unsplash Images")
    print("=" * 55)
    if not UNSPLASH_ACCESS_KEY:
        print("\n[WARNING] UNSPLASH_ACCESS_KEY not set in .env")
        print("Get a free key at: https://unsplash.com/developers\n")

    print("Step 1: Fetching image pools from Unsplash...")
    image_pools = {}
    for cat in BRANDS:
        image_pools[cat] = fetch_image_pool(cat, count=30)
        time.sleep(0.3)

    print(f"\nStep 2: Generating {PRODUCTS_PER_CATEGORY*8:,} products...\n")
    total = insert_products(image_pools)

    print(f"\n{'='*55}")
    print(f"Done! {total:,} products inserted.")
    print(f"Total in DB: ~{2000+total:,} products")
    print(f"Next: python train_models.py")
    print("="*55)
