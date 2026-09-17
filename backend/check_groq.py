import requests, os
from dotenv import load_dotenv
load_dotenv()

key = os.getenv("GROQ_API_KEY")
headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

# List available models
resp = requests.get("https://api.groq.com/openai/v1/models", headers=headers, timeout=10)
print("Status:", resp.status_code)
data = resp.json()
models = [m["id"] for m in data.get("data", [])]
for m in sorted(models):
    print(" -", m)
