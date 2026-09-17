import os, sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from tools.product_search import search_internal, search_external

print("--- TEST 1: search_internal ---")
tests = [
    ("Jeans",        {"categories": ["Jeans"]}, 3),
    ("Tshirts",      {"categories": ["Tshirts"]}, 3),
    ("Sports combo", {"categories": ["Sports Shoes", "Track Pants"]}, 4),
    ("Watches",      {"categories": ["Watches"]}, 3),
    ("Casual Shoes", {"categories": ["Casual Shoes"]}, 3),
    ("Shirts",       {"categories": ["Shirts"]}, 3),
    ("Jeans <1500",  {"categories": ["Jeans"], "max_price": 1500}, 3),
    ("Keyword jeans",{"keyword": "jeans"}, 3),
]
all_pass = True
for label, filters, limit in tests:
    r = search_internal(filters, limit=limit)
    status = "OK" if r else "FAIL"
    if not r:
        all_pass = False
    first = r[0]["name"][:45] if r else "no results"
    print(f"  [{status}] {label}: {len(r)} results — {first}")

print()
print("--- TEST 2: occasion engine ---")
from occasion_engine import _fetch_candidates, fetch_occasion_products, fetch_outfit_set

cases = [
    ("Shirts+Trousers",           ["Shirts", "Trousers"]),
    ("Sports",                    ["Track Pants", "Sports Shoes", "Tshirts"]),
    ("Casual",                    ["Jeans", "Tshirts", "Casual Shoes"]),
]
for label, cats in cases:
    r = _fetch_candidates(cats, 0, 999999)
    status = "OK" if r else "FAIL"
    if not r:
        all_pass = False
    print(f"  [{status}] {label}: {len(r)} candidates")

print()
print("--- TEST 2b: fetch_occasion_products ---")
for occ in ["sports", "job_interview", "casual_outing", "date_night"]:
    prods = fetch_occasion_products(occ, {}, {})
    status = "OK" if prods else "FAIL"
    if not prods:
        all_pass = False
    first = prods[0]["name"][:40] if prods else "no results"
    print(f"  [{status}] {occ}: {len(prods)} — {first}")

print()
print("--- TEST 2c: fetch_outfit_set ---")
for occ in ["sports", "job_interview"]:
    outfit = fetch_outfit_set(occ, {}, {})
    slots = list(outfit.keys())
    status = "OK" if len(slots) >= 2 else "FAIL"
    if len(slots) < 2:
        all_pass = False
    print(f"  [{status}] {occ} outfit slots: {slots}")

print()
print("--- TEST 3: BuyWhere external ---")
ext = search_external("gym t-shirt", limit=3)
print(f"  BuyWhere: {len(ext)} results {'(OK)' if ext else '(API down/no results)'}")

print()
print("=== SUMMARY:", "ALL PASS" if all_pass else "SOME FAILURES — see above" , "===")
