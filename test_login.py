import requests
import json

BASE = "http://127.0.0.1:5000"
s = requests.Session()

print("=== Login ===")
r = s.post(BASE + "/login", data={"username": "3220602001", "password": "123456"}, allow_redirects=False)
print(f"Status: {r.status_code}")
print(f"Headers: {dict(r.headers)}")
print(f"Cookies: {dict(s.cookies)}")
print(f"Response text: {r.text[:500]}")