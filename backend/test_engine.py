from recommendation_engine import HybridRecommendationEngine

e = HybridRecommendationEngine().load()

print("=== Trending (cold-start / popularity) ===")
for p in e.trending_products(top_n=5):
    print(f"  score={p['recommendation_score']}  {p['name']}  rating={p['rating']}  reviews={p['reviews']}")

print()
print("=== Search: formal shirt ===")
for p in e.search("formal shirt", top_n=5):
    print(f"  score={p['recommendation_score']}  {p['name']}  cat={p['category']}  brand={p['brand']}")

print()
print("=== Search: sports shoes running ===")
for p in e.search("sports shoes running", top_n=5):
    print(f"  score={p['recommendation_score']}  {p['name']}  cat={p['category']}  brand={p['brand']}")

print()
print("=== Similar to product 1 ===")
for p in e.similar_products(1, top_n=4):
    print(f"  score={p['recommendation_score']}  {p['name']}  cat={p['category']}")
