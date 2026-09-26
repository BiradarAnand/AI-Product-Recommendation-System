import sys
import os

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from agents.search_agent import SearchAgent

def test():
    agent = SearchAgent()
    
    queries = [
        "wireless headphones",
        "running shoes under 2000"
    ]
    
    for q in queries:
        print(f"\n--- Testing Query: '{q}' ---")
        response = agent.search_products(query=q, top_n=3)
        print(json.dumps(response, indent=2))

if __name__ == '__main__':
    test()
