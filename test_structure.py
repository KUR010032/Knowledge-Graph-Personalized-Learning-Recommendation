import requests, json

s = requests.Session()
s.post('http://127.0.0.1:5050/login', data={'role': 'student', 'user_id': '3220602001', 'password': '123456'}, allow_redirects=False)
r = s.get('http://127.0.0.1:5050/student/recommend/data?t=1&refresh=1')
d = json.loads(r.text)

# Print structure of first target's first resource
t0 = d.get('targets', [])[0] if d.get('targets') else {}
res0 = t0.get('resources', [])[0] if t0.get('resources') else {}
print("=== Resource field keys ===")
print(json.dumps(res0, ensure_ascii=False, indent=2)[:800])

print("\n=== Question field keys ===")
qs0 = t0.get('questions', [])[0] if t0.get('questions') else {}
print(json.dumps(qs0, ensure_ascii=False, indent=2)[:800])

print("\n=== Target field keys ===")
t0_print = {k: v for k, v in t0.items() if k not in ('resources', 'questions')}
print(json.dumps(t0_print, ensure_ascii=False, indent=2)[:800])