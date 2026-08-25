import os
import json
from dotenv import load_dotenv

# Load env before importing agents to ensure API keys exist
load_dotenv()

from agents.coordinator_agent import CoordinatorAgent

def run_test():
    coordinator = CoordinatorAgent()
    message = "I have a beach wedding and need something cool."
    print(f"Testing MAS with message: '{message}'")
    
    context = {
        "user_id": 1, # Mock user ID
        "history": [],
        "refinements": {}
    }
    
    result = coordinator.process(message, context)
    print("Result Type:", result.get("type"))
    if "digital_twin_evaluation" in result:
        print("Digital Twin Evaluation:")
        print(json.dumps(result["digital_twin_evaluation"], indent=2))

if __name__ == "__main__":
    run_test()
