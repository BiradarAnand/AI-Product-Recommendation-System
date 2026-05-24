import requests, json
url = 'https://ai-product-recommendation-system-by60.onrender.com/api/auth/login'
payload = {
    'email': 'existing_user@example.com',
    'password': 'Password123'
}
try:
    r = requests.post(url, json=payload, timeout=15)
    print('Status:', r.status_code)
    try:
        print('JSON:', r.json())
    except Exception:
        print('Text:', r.text)
except Exception as e:
    print('Error:', e)
