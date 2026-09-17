import sqlite3
conn = sqlite3.connect("amazon_catalog.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
cats = [r[0] for r in cur.fetchall()]
print("ALL CATEGORIES:", cats)

cur.execute("SELECT COUNT(*) FROM products WHERE category LIKE '%clothing%'")
print("Clothing count:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM products WHERE category LIKE '%shoes%'")
print("Shoes count:", cur.fetchone()[0])

cur.execute("SELECT COUNT(*) FROM products WHERE category LIKE '%sport%'")
print("Sports count:", cur.fetchone()[0])

# Check sub_categories
cur.execute("SELECT DISTINCT sub_category FROM products WHERE category LIKE '%clothing%' ORDER BY sub_category LIMIT 30")
subs = [r[0] for r in cur.fetchall()]
print("Clothing sub_categories:", subs)

cur.execute("SELECT DISTINCT sub_category FROM products WHERE category LIKE '%shoes%' ORDER BY sub_category LIMIT 20")
shoe_subs = [r[0] for r in cur.fetchall()]
print("Shoe sub_categories:", shoe_subs)

cur.execute("SELECT DISTINCT sub_category FROM products WHERE category LIKE '%sport%' ORDER BY sub_category LIMIT 20")
sport_subs = [r[0] for r in cur.fetchall()]
print("Sport sub_categories:", sport_subs)

conn.close()
