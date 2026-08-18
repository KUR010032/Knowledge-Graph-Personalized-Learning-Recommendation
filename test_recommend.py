import requests
import json
import time

s = requests.Session()
s.post('http://127.0.0.1:5000/login', json={'username': '3220602004', 'password': '123456'})
r = s.get('http://127.0.0.1:5000/student/recommend/data?refresh=1&t=999')
data = r.json()
print('=== LISI (3220602004) ===')
print('recommend_type:', data.get('recommend_type'))
print('avg_mastery:', data.get('avg_mastery'))
print('basis:', data.get('basis'))
print('weak_count:', data.get('weak_count'))
print()
for i, t in enumerate(data.get('targets', [])):
    print(f'Target {i+1}: {t.get("code")} "{t.get("name")}" mastery={t.get("mastery")} status={t.get("status")}')
    for r in t.get('resources', []):
        print(f'  R: {r.get("knowledge_id")} type={r.get("type")} relation={r.get("relation_label")} watch_url={r.get("watch_url")}')
    for q in t.get('questions', []):
        print(f'  Q: qid={q.get("question_id")} kp={q.get("knowledge_id")} diff={q.get("difficulty")} practice_url={q.get("practice_url")}')
    print()

print()
print('=== LIUDA ===')
s2 = requests.Session()
s2.post('http://127.0.0.1:5000/login', json={'username': '3220602001', 'password': '123456'})
r2 = s2.get('http://127.0.0.1:5000/student/recommend/data?refresh=1&t=999')
data2 = r2.json()
print('recommend_type:', data2.get('recommend_type'))
for i, t in enumerate(data2.get('targets', [])):
    print(f'Target {i+1}: {t.get("code")} "{t.get("name")}" mastery={t.get("mastery")} status={t.get("status")}')
    for r in t.get('resources', []):
        print(f'  R: {r.get("knowledge_id")} type={r.get("type")} relation={r.get("relation_label")}')
    for q in t.get('questions', []):
        print(f'  Q: qid={q.get("question_id")} kp={q.get("knowledge_id")} diff={q.get("difficulty")}')
    print()

print()
print('=== ZHAOLIU ===')
s3 = requests.Session()
s3.post('http://127.0.0.1:5000/login', json={'username': '3220602006', 'password': '123456'})
r3 = s3.get('http://127.0.0.1:5000/student/recommend/data?refresh=1&t=999')
data3 = r3.json()
print('recommend_type:', data3.get('recommend_type'))
for i, t in enumerate(data3.get('targets', [])):
    print(f'Target {i+1}: {t.get("code")} "{t.get("name")}" mastery={t.get("mastery")} status={t.get("status")}')
    for r in t.get('resources', []):
        print(f'  R: {r.get("knowledge_id")} type={r.get("type")} relation={r.get("relation_label")}')
    for q in t.get('questions', []):
        print(f'  Q: qid={q.get("question_id")} kp={q.get("knowledge_id")} diff={q.get("difficulty")}')
    print()