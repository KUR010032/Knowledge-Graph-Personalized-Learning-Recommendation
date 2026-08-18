import requests
import json

s = requests.Session()
r = s.post('http://127.0.0.1:5000/login', json={'username': '3220602004', 'password': '123456'})
print('Login status:', r.status_code)
print('Login response:', r.text[:500])
rr = s.get('http://127.0.0.1:5000/student/recommend/data?refresh=1&t=999')
print('Data status:', rr.status_code)
print('Data response:', rr.text[:3000])