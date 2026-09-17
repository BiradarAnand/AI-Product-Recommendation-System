import sqlite3
conn = sqlite3.connect('amazon_catalog.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("SELECT name, image_url FROM products WHERE category LIKE '%shoes%' LIMIT 5")
for r in cur.fetchall():
    print(r['name'][:40], ' | ', r['image_url'])
