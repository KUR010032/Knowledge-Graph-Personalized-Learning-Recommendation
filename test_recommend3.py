import requests
import json

s = requests.Session()

# Try form data login
r = s.post('http://127.0.0.1:5000/login', data={'username': '3220602004', 'password': '123456'})
print('Login status:', r.status_code)
print('Cookies:', dict(s.cookies))
if 'error' in r.text.lower() or 'fail' in r.text.lower():
    print('Login page returned:', 'login' in r.text[:100].lower())

rr = s.get('http://127.0.0.1:5000/student/recommend/data?refresh=1&t=999')
print('Data status:', rr.status_code)
print('Data response:', rr.text[:3000])