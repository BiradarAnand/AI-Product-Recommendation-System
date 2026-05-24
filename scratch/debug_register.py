import requests, json, sys

url = "https://ai-product-recommendation-system-by60.onrender.com/api/auth/register"
payload = {
    "name": "TestUser",
    "email": f"test_user_{int(__import__('time').time())}@example.com",
    "password": "Password123"
}

try:
    r = requests.post(url, json=payload, timeout=30)  # increased timeout to 30 seconds
    print('Status:', r.status_code)
    try:
        print('JSON:', r.json())
    except Exception:
        print('Text:', r.text)
except Exception as e:
    print('Error:', e)
