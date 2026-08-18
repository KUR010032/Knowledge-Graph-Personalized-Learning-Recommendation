import requests
import json

s = requests.Session()

# Get the login page
r = s.get('http://127.0.0.1:5000/login')
print('Login page status:', r.status_code)
print('Cookies after GET:', dict(s.cookies))
print('Login headers:', dict(r.headers))

# Try POST login with form data
r2 = s.post('http://127.0.0.1:5000/login', data={'username': '3220602004', 'password': '123456'}, allow_redirects=False)
print('Login POST status:', r2.status_code)
print('Login POST headers:', dict(r2.headers))
print('Cookies after POST:', dict(s.cookies))
print('Location:', r2.headers.get('Location', 'None'))
print('Response text first 300:', r2.text[:300])