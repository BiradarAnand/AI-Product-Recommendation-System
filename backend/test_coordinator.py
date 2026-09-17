import os, sys
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

from agents.coordinator_agent import CoordinatorAgent

coordinator = CoordinatorAgent()

test_messages = [
    ("gym outfit",         {}),
    ("job interview",      {}),
    ("casual outing",      {}),
    ("jeans under 2000",   {}),
    ("watches",            {}),
    ("date night",         {"budget": "mid"}),
]

print("--- END-TO-END COORDINATOR AGENT TESTS ---\n")

for msg, refinements in test_messages:
    print(f"MSG: '{msg}'")
    ctx = {"user_id": None, "history": [], "refinements": refinements}
    try:
        result = coordinator.process(msg, ctx)
        rtype    = result.get("type", "unknown")
        products = result.get("products", [])
        reply    = (result.get("reply") or "")[:80]
        outfit   = result.get("outfit", {})
        status   = result.get("status", "")
        print(f"  type={rtype} | status={status} | products={len(products)} | outfit_slots={list(outfit.keys())}")
        print(f"  reply: {reply}")
        if products:
            p = products[0]
            print(f"  top pick: {p.get('name','?')[:45]} | {p.get('price')} | {p.get('source','internal')}")
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback; traceback.print_exc()
    print()

print("=== COORDINATOR TESTS DONE ===")
