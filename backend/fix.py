"""
fix_images_search.py
──────────────────────
Uses Unsplash SEARCH API (not random) to fetch relevant product images.

Query = "{brand} {category}" e.g. "Nike Sports Shoes", "Levi's Jeans"

How it works:
  1. Find all unique brand+category groups in your DB
  2. Search Unsplash for each group → get 10 relevant photos
  3. Assign photos to products by rotating through the 10
  4. Products with same brand+category get varied but relevant photos

Result:
  Nike Sports Shoes  → 10 actual Nike/shoe photos
  Levi's Jeans       → 10 actual Levi's/denim photos
  Titan Watches      → 10 actual watch photos
  (not a generic clothing store interior)

Unsplash free tier: 50 requests/hour
If you have many brand+category groups, the script pauses automatically.

Run:
    pip install requests
    Add UNSPLASH_ACCESS_KEY to your .env
    python fix_images_search.py
"""

import os
import time
import json
import requests
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# ── Config ────────────────────────────────────────────────────
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")
PHOTOS_PER_GROUP    = 10    # fetch this many photos per brand+category
REQUESTS_PER_HOUR   = 45    # stay under 50/hour free limit

# ── Category-only fallback queries (if brand search returns nothing) ──
# Used when "FlyingMachine Shirts" returns 0 results
CATEGORY_QUERIES = {
    "Shirts":       "men dress shirt fashion",
    "Tshirts":      "men casual tshirt",
    "Jeans":        "men denim jeans",
    "Trousers":     "men formal trousers",
    "Track Pants":  "men sportswear jogger pants",
    "Casual Shoes": "men casual sneakers shoes",
    "Sports Shoes": "men running athletic shoes",
    "Watches":      "wristwatch timepiece",
    "Blazers":      "men blazer formal jacket",
    "Formal Shoes": "men formal leather shoes",
    "Sneakers":     "men sneakers streetwear",
    "Kurtas":       "men kurta ethnic wear",
    "Ethnic Wear":  "men ethnic traditional clothing",
    "Activewear":   "men gym activewear workout",
    "Shorts":       "men casual shorts",
    "Caps":         "men cap hat fashion",
    "Sunglasses":   "men sunglasses fashion",
}


def get_db():
    return mysql.connector.connect(**DB_CONFIG)


def search_unsplash(query: str, count: int = 10) -> list:
    """
    Search Unsplash for a query. Returns list of image URLs.
    Falls back to empty list on any error.
    """
    if not UNSPLASH_ACCESS_KEY:
        return []

    try:
        url = "https://api.unsplash.com/search/photos"
        params = {
            "query":       query,
            "per_page":    count,
            "orientation": "squarish",
            "content_filter": "high",
        }
        headers = {
            "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}",
            "Accept-Version": "v1",
        }
        res  = requests.get(url, params=params, headers=headers, timeout=10)

        if res.status_code == 429:
            print("  [!] Rate limit hit. Waiting 60 seconds...")
            time.sleep(60)
            return search_unsplash(query, count)

        res.raise_for_status()
        data    = res.json()
        results = data.get("results", [])
        urls    = [p["urls"]["regular"] for p in results if "urls" in p]
        return urls

    except Exception as e:
        print(f"  [!] Unsplash error for '{query}': {e}")
        return []


def fix_images():
    if not UNSPLASH_ACCESS_KEY:
        print("ERROR: UNSPLASH_ACCESS_KEY not set in .env")
        print("Get your free key at: https://unsplash.com/developers")
        return

    print("=" * 60)
    print("Fixing product images with Unsplash Search API")
    print("=" * 60)

    db  = get_db()
    cur = db.cursor(dictionary=True)

    # ── Step 1: Get all unique brand+category groups ──────────
    cur.execute("""
        SELECT brand, category, COUNT(*) as cnt
        FROM products
        GROUP BY brand, category
        ORDER BY cnt DESC
    """)
    groups = cur.fetchall()
    print(f"\nFound {len(groups)} unique brand+category groups")
    print(f"Fetching {PHOTOS_PER_GROUP} images per group...")
    print(f"This will use ~{len(groups)} Unsplash API calls\n")

    # ── Step 2: Fetch photos for each group ───────────────────
    image_cache = {}   # (brand, category) → [url, url, ...]
    total_calls = 0

    for i, group in enumerate(groups):
        brand    = (group["brand"]    or "").strip().rstrip("\r")
        category = (group["category"] or "").strip()
        key      = (brand, category)

        # Build search query — "Nike Sports Shoes" style
        query = f"{brand} {category}".strip()

        print(f"  [{i+1}/{len(groups)}] Searching: '{query}' ({group['cnt']} products)...")
        urls = search_unsplash(query, PHOTOS_PER_GROUP)
        total_calls += 1

        # Fallback to category-only if brand search returns nothing
        if not urls:
            fallback_query = CATEGORY_QUERIES.get(category, category)
            print(f"         No results -> trying fallback: '{fallback_query}'")
            urls = search_unsplash(fallback_query, PHOTOS_PER_GROUP)
            total_calls += 1

        if urls:
            image_cache[key] = urls
            print(f"         Got {len(urls)} photos ✓")
        else:
            image_cache[key] = []
            print(f"         No photos found — will use category placeholder")

        # Rate limit: pause every 45 calls
        if total_calls > 0 and total_calls % REQUESTS_PER_HOUR == 0:
            print(f"\n  Pausing 65 seconds (rate limit)...\n")
            time.sleep(65)
        else:
            time.sleep(1.3)   # ~45 requests/minute to be safe

    # ── Step 3: Update products with relevant images ──────────
    print(f"\nUpdating product images in database...")

    cur.execute("SELECT id, brand, category FROM products ORDER BY id")
    products = cur.fetchall()

    updated = 0
    skipped = 0

    # Track position per group for rotation
    group_position = {}

    for product in products:
        pid      = product["id"]
        brand    = (product["brand"]    or "").strip().rstrip("\r")
        category = (product["category"] or "").strip()
        key      = (brand, category)

        urls = image_cache.get(key, [])

        if not urls:
            skipped += 1
            continue

        # Rotate through the pool
        pos = group_position.get(key, 0)
        url = urls[pos % len(urls)]
        group_position[key] = pos + 1

        cur.execute(
            "UPDATE products SET image_url = %s WHERE id = %s",
            (url, pid)
        )
        updated += 1

        if updated % 1000 == 0:
            db.commit()
            print(f"  Updated {updated}/{len(products)}...")

    db.commit()
    cur.close()
    db.close()

    print(f"\n{'=' * 60}")
    print(f"Done!")
    print(f"  Groups fetched : {len(groups)}")
    print(f"  API calls used : {total_calls}")
    print(f"  Products updated : {updated}")
    print(f"  Products skipped : {skipped} (no images found)")
    print(f"\nNext steps:")
    print(f"  1. python train_models.py")
    print(f"  2. python app.py")
    print("=" * 60)


if __name__ == "__main__":
    fix_images()