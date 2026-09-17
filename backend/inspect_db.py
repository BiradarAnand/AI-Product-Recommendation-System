import sqlite3, os
conn = sqlite3.connect("amazon_catalog.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in cur.fetchall()])
cur.execute("PRAGMA table_info(products)")
cols = cur.fetchall()
print("Columns:")
for c in cols:
    print(" ", dict(c))
cur.execute("SELECT COUNT(*) FROM products")
print("Count:", cur.fetchone()[0])
cur.execute("SELECT DISTINCT category FROM products LIMIT 30")
cats = [r[0] for r in cur.fetchall()]
print("Categories:", cats)
cur.execute("SELECT id, name, brand, category, price, rating, image_url, stock FROM products LIMIT 3")
rows = cur.fetchall()
for r in rows:
    print("Sample:", dict(r))
conn.close()
