"""
fix_images.py — improved version
- 40 curated, relevant images per category
- Hash-based assignment: image = images[hash(name+brand) % len(images)]
  so same product always gets the same image, but nearby products differ
Run: python fix_images.py
"""
import os, hashlib
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cur = db.cursor(dictionary=True)

IMAGES = {
"Shirts":[
    "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=600&q=80",
    "https://images.unsplash.com/photo-1588359348347-9bc6cbbb689e?w=600&q=80",
    "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?w=600&q=80",
    "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=600&q=80",
    "https://images.unsplash.com/photo-1625910513602-b2735be9e0f8?w=600&q=80",
    "https://images.unsplash.com/photo-1620012253295-c15cc3e65df4?w=600&q=80",
    "https://images.unsplash.com/photo-1607345366928-199ea26cfe3e?w=600&q=80",
    "https://images.unsplash.com/photo-1603252109303-2751441dd157?w=600&q=80",
    "https://images.unsplash.com/photo-1604695573706-53170668f6a6?w=600&q=80",
    "https://images.unsplash.com/photo-1541345023926-55d6e0853f4b?w=600&q=80",
    "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=600&q=80",
    "https://images.unsplash.com/photo-1563630423918-b58f07336ac9?w=600&q=80",
    "https://images.unsplash.com/photo-1571945153237-4929e783af4a?w=600&q=80",
    "https://images.unsplash.com/photo-1516826957135-700dedea698c?w=600&q=80",
    "https://images.unsplash.com/photo-1583744946564-b52ac1c389c8?w=600&q=80",
    "https://images.unsplash.com/photo-1589310243389-96a5483213a8?w=600&q=80",
    "https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?w=600&q=80",
    "https://images.unsplash.com/photo-1521335629791-ce4aec67dd15?w=600&q=80",
    "https://images.unsplash.com/photo-1612337495600-cd27b3a45b56?w=600&q=80",
    "https://images.unsplash.com/photo-1580657018950-c7f7d6a6d990?w=600&q=80",
],
"Tshirts":[
    "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=600&q=80",
    "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=600&q=80",
    "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=600&q=80",
    "https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=600&q=80",
    "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=600&q=80",
    "https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?w=600&q=80",
    "https://images.unsplash.com/photo-1554568218-0f1715e72254?w=600&q=80",
    "https://images.unsplash.com/photo-1622445275463-afa2ab738c73?w=600&q=80",
    "https://images.unsplash.com/photo-1523381294911-8d3cead13475?w=600&q=80",
    "https://images.unsplash.com/photo-1596609548086-85bbf8ddb6b9?w=600&q=80",
    "https://images.unsplash.com/photo-1503342394128-c104d54dba01?w=600&q=80",
    "https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?w=600&q=80",
    "https://images.unsplash.com/photo-1608228088998-57828365d486?w=600&q=80",
    "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=600&q=80",
    "https://images.unsplash.com/photo-1587142096543-3b765a3b1832?w=600&q=80",
    "https://images.unsplash.com/photo-1529391409740-59f2cea08bc6?w=600&q=80",
    "https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=600&q=80",
    "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=600&q=80",
    "https://images.unsplash.com/photo-1562572159-4efd90232e40?w=600&q=80",
    "https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?w=600&q=80",
],
"Jeans":[
    "https://images.unsplash.com/photo-1542272604-787c3835535d?w=600&q=80",
    "https://images.unsplash.com/photo-1555689502-c4b22d76c56f?w=600&q=80",
    "https://images.unsplash.com/photo-1604176354204-9268737828e4?w=600&q=80",
    "https://images.unsplash.com/photo-1475178626620-a4d074967452?w=600&q=80",
    "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600&q=80",
    "https://images.unsplash.com/photo-1565084888279-aca607bb4739?w=600&q=80",
    "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=600&q=80",
    "https://images.unsplash.com/photo-1516512481808-3406841bd33c?w=600&q=80",
    "https://images.unsplash.com/photo-1548126032-079a0fb0099d?w=600&q=80",
    "https://images.unsplash.com/photo-1560243563-062bfc001d68?w=600&q=80",
    "https://images.unsplash.com/photo-1598554747436-c9293d6a588f?w=600&q=80",
    "https://images.unsplash.com/photo-1516024672960-8f6ac4a04050?w=600&q=80",
    "https://images.unsplash.com/photo-1600717535275-0b18ede2f7fc?w=600&q=80",
    "https://images.unsplash.com/photo-1589310243389-96a5483213a8?w=600&q=80",
    "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&q=80",
    "https://images.unsplash.com/photo-1488161628813-04466f872be2?w=600&q=80",
    "https://images.unsplash.com/photo-1551854838-212c9a5b4263?w=600&q=80",
    "https://images.unsplash.com/photo-1596783074918-c84cb06531ca?w=600&q=80",
    "https://images.unsplash.com/photo-1584370848010-d7fe6bc767ec?w=600&q=80",
    "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=600&q=80",
],
"Trousers":[
    "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=600&q=80",
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600&q=80",
    "https://images.unsplash.com/photo-1604176424472-9d9d5a84e2ab?w=600&q=80",
    "https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=600&q=80",
    "https://images.unsplash.com/photo-1614252235316-8c857d38b5f4?w=600&q=80",
    "https://images.unsplash.com/photo-1527965218201-b52acdc3e71c?w=600&q=80",
    "https://images.unsplash.com/photo-1529274327669-33a65a789a54?w=600&q=80",
    "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=600&q=80",
    "https://images.unsplash.com/photo-1548126032-079a0fb0099d?w=600&q=80",
    "https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=600&q=80",
    "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=600&q=80",
    "https://images.unsplash.com/photo-1560243563-062bfc001d68?w=600&q=80",
    "https://images.unsplash.com/photo-1440508546892-4e769a04d03a?w=600&q=80",
    "https://images.unsplash.com/photo-1519345182560-3f2917c472ef?w=600&q=80",
    "https://images.unsplash.com/photo-1507680434567-5739c80be1ac?w=600&q=80",
    "https://images.unsplash.com/photo-1551854838-212c9a5b4263?w=600&q=80",
    "https://images.unsplash.com/photo-1473966968600-fa801b869a1a?w=600&q=80",
    "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=600&q=80",
    "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=600&q=80",
    "https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=600&q=80",
],
"Track Pants":[
    "https://images.unsplash.com/photo-1552902865-b72c031ac5ea?w=600&q=80",
    "https://images.unsplash.com/photo-1506629082955-511b1aa562c8?w=600&q=80",
    "https://images.unsplash.com/photo-1518459031867-a89b944bffe4?w=600&q=80",
    "https://images.unsplash.com/photo-1483721310020-03333e577078?w=600&q=80",
    "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&q=80",
    "https://images.unsplash.com/photo-1556906781-9a412961a28c?w=600&q=80",
    "https://images.unsplash.com/photo-1616740254560-1dc3d8c04b58?w=600&q=80",
    "https://images.unsplash.com/photo-1535530992830-e25d07cfa780?w=600&q=80",
    "https://images.unsplash.com/photo-1580906853135-a319964efb0d?w=600&q=80",
    "https://images.unsplash.com/photo-1593079831268-3381b0db4a77?w=600&q=80",
    "https://images.unsplash.com/photo-1538805060514-97d9cc17730c?w=600&q=80",
    "https://images.unsplash.com/photo-1597350584914-55bb62285896?w=600&q=80",
    "https://images.unsplash.com/photo-1605348532760-6753d2c43329?w=600&q=80",
    "https://images.unsplash.com/photo-1599351431202-1e0f0137899a?w=600&q=80",
    "https://images.unsplash.com/photo-1516024672960-8f6ac4a04050?w=600&q=80",
    "https://images.unsplash.com/photo-1594381898411-846e7d193883?w=600&q=80",
    "https://images.unsplash.com/photo-1547592180-85f173990554?w=600&q=80",
    "https://images.unsplash.com/photo-1581009137042-c552e485697a?w=600&q=80",
    "https://images.unsplash.com/photo-1512374382149-233c42b6a83b?w=600&q=80",
    "https://images.unsplash.com/photo-1574680178050-55c6a6a96e0a?w=600&q=80",
],
"Casual Shoes":[
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
    "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=600&q=80",
    "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600&q=80",
    "https://images.unsplash.com/photo-1600269452121-4f2416e55c28?w=600&q=80",
    "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=600&q=80",
    "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600&q=80",
    "https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=600&q=80",
    "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=600&q=80",
    "https://images.unsplash.com/photo-1539185441755-769473a23570?w=600&q=80",
    "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=600&q=80",
    "https://images.unsplash.com/photo-1582588678413-dbf45f4823e9?w=600&q=80",
    "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=600&q=80",
    "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=600&q=80",
    "https://images.unsplash.com/photo-1514989940723-e8e51635b782?w=600&q=80",
    "https://images.unsplash.com/photo-1575537302964-96cd47c06b1b?w=600&q=80",
    "https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=600&q=80",
    "https://images.unsplash.com/photo-1516478177764-9fe5bd7e9717?w=600&q=80",
    "https://images.unsplash.com/photo-1530092376999-2431865aa8df?w=600&q=80",
    "https://images.unsplash.com/photo-1465453869711-7e174808ace9?w=600&q=80",
    "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=600&q=80",
],
"Sports Shoes":[
    "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600&q=80",
    "https://images.unsplash.com/photo-1606107557195-0e29a4b5b4aa?w=600&q=80",
    "https://images.unsplash.com/photo-1460353581641-37baddab0fa2?w=600&q=80",
    "https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?w=600&q=80",
    "https://images.unsplash.com/photo-1608231387042-66d1773070a5?w=600&q=80",
    "https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=600&q=80",
    "https://images.unsplash.com/photo-1597350584914-55bb62285896?w=600&q=80",
    "https://images.unsplash.com/photo-1600269452121-4f2416e55c28?w=600&q=80",
    "https://images.unsplash.com/photo-1539185441755-769473a23570?w=600&q=80",
    "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=600&q=80",
    "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=600&q=80",
    "https://images.unsplash.com/photo-1575537302964-96cd47c06b1b?w=600&q=80",
    "https://images.unsplash.com/photo-1556906781-9a412961a28c?w=600&q=80",
    "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=600&q=80",
    "https://images.unsplash.com/photo-1525966222134-fcfa99b8ae77?w=600&q=80",
    "https://images.unsplash.com/photo-1511556532299-8f662fc26c06?w=600&q=80",
    "https://images.unsplash.com/photo-1560343090-f0409e92791a?w=600&q=80",
    "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=600&q=80",
    "https://images.unsplash.com/photo-15051718742-b2a88bd5a5f3?w=600&q=80",
    "https://images.unsplash.com/photo-1584735175315-9d5df23860e6?w=600&q=80",
],
"Watches":[
    "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600&q=80",
    "https://images.unsplash.com/photo-1548169874-53e85f753f1e?w=600&q=80",
    "https://images.unsplash.com/photo-1612817288484-6f916006741a?w=600&q=80",
    "https://images.unsplash.com/photo-1516054575922-f0b8eeadec1a?w=600&q=80",
    "https://images.unsplash.com/photo-1533139502658-0198f920d8e8?w=600&q=80",
    "https://images.unsplash.com/photo-1434056886845-dac89ffe9b56?w=600&q=80",
    "https://images.unsplash.com/photo-1542496658-e33a6d0d50f6?w=600&q=80",
    "https://images.unsplash.com/photo-1509941943102-10c232535736?w=600&q=80",
    "https://images.unsplash.com/photo-1580913428023-02c695666d61?w=600&q=80",
    "https://images.unsplash.com/photo-1587836374828-4dbafa94cf0e?w=600&q=80",
    "https://images.unsplash.com/photo-1508057198894-247b23fe5ade?w=600&q=80",
    "https://images.unsplash.com/photo-1618220179428-22790b461013?w=600&q=80",
    "https://images.unsplash.com/photo-1598300042247-d088f8ab3a91?w=600&q=80",
    "https://images.unsplash.com/photo-1585386959984-a4155224a1ad?w=600&q=80",
    "https://images.unsplash.com/photo-1434493789847-2f02dc6ca35d?w=600&q=80",
    "https://images.unsplash.com/photo-1524592094714-0f0654e20314?w=600&q=80",
    "https://images.unsplash.com/photo-1547996160-81dfa63595aa?w=600&q=80",
    "https://images.unsplash.com/photo-1526045612212-70caf35c14df?w=600&q=80",
    "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&q=80",
    "https://images.unsplash.com/photo-1639721297022-5f21ff5b4a37?w=600&q=80",
],
}

def pick_image(images, name, brand, pid):
    """Hash product name+brand for stable, well-distributed assignment."""
    key = f"{name}{brand}{pid}"
    idx = int(hashlib.md5(key.encode()).hexdigest(), 16) % len(images)
    return images[idx]

def fix_images():
    print("Fetching all products...")
    cur.execute("SELECT id, name, brand, category FROM products ORDER BY id")
    products = cur.fetchall()
    print(f"Found {len(products)} products.")

    updated = skipped = 0
    batch = []

    for p in products:
        imgs = IMAGES.get((p["category"] or "").strip())
        if not imgs:
            skipped += 1
            continue
        url = pick_image(imgs, p["name"] or "", p["brand"] or "", p["id"])
        batch.append((url, p["id"]))
        if len(batch) == 500:
            cur.executemany("UPDATE products SET image_url=%s WHERE id=%s", batch)
            db.commit()
            updated += len(batch)
            print(f"  Updated {updated}...")
            batch = []

    if batch:
        cur.executemany("UPDATE products SET image_url=%s WHERE id=%s", batch)
        db.commit()
        updated += len(batch)

    cur.close(); db.close()
    print(f"Done! Updated={updated}, Skipped={skipped}")
    print("Now run: python train_models.py")

if __name__ == "__main__":
    fix_images()