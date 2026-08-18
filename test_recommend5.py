import requests
import json

s = requests.Session()

# Login with correct form fields
r2 = s.post('http://127.0.0.1:5000/login', data={'role': 'student', 'user_id': '3220602004', 'password': '123456'}, allow_redirects=False)
print('Login POST status:', r2.status_code)
print('Cookies after POST:', dict(s.cookies))
print('Location:', r2.headers.get('Location', 'None'))

if r2.status_code == 302:
    # Follow redirect
    r3 = s.get('http://127.0.0.1:5000' + r2.headers['Location'])
    print('After redirect:', r3.status_code, len(r3.text))

rr = s.get('http://127.0.0.1:5000/student/recommend/data?refresh=1&t=999')
print('Data status:', rr.status_code)
data = rr.json()
print('Success:', data.get('success'))
print('Recommend type:', data.get('recommend_type'))
print('Avg mastery:', data.get('avg_mastery'))
print('Weak count:', data.get('weak_count'))
print('Targets count:', len(data.get('targets', [])))
for i, t in enumerate(data.get('targets', [])[:10]):
    print(f'  T{i+1}: {t.get("code")} "{t.get("name")}" m={t.get("mastery")} s={t.get("status")}')
    print(f'    Resources: {len(t.get("resources", []))}')
    for r in t.get('resources', []):
        print(f'      R: {r.get("knowledge_id")} type={r.get("type")} rel={r.get("relation_label")} url={r.get("watch_url")}')
    print(f'    Questions: {len(t.get("questions", []))}')
    for q in t.get('questions', []):
        print(f'      Q: {q.get("question_id")} kp={q.get("knowledge_id")} diff={q.get("difficulty")} url={q.get("practice_url")}')