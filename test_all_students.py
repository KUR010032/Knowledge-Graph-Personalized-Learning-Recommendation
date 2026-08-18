import requests, json

def test_student(uid, pwd, name):
    s = requests.Session()
    s.post('http://127.0.0.1:5050/login', data={'role': 'student', 'user_id': uid, 'password': pwd}, allow_redirects=False)
    r = s.get('http://127.0.0.1:5050/student/recommend/data?t=1&refresh=1')
    d = json.loads(r.text)

    print(f'\n{"="*60}')
    print(f'Student: {name} ({uid})')
    print(f'Type: {d.get("recommend_type")}, avg_mastery: {d.get("avg_mastery")}')
    targets = d.get('targets', [])
    codes = [t.get('code') for t in targets]
    print(f'Targets ({len(targets)}): {codes}')
    all_313 = all(c == '3.1.3' for c in codes)
    print(f'All 3.1.3: {all_313}')
    
    for t in targets:
        code = t.get('code')
        resources = t.get('resources', [])
        resource_kps = list(set(r.get('knowledge_id') for r in resources))
        questions = t.get('questions', [])
        question_kps = list(set(q.get('knowledge_id') for q in questions))
        print(f'  {code}: {len(resources)} resources (kps:{resource_kps}), {len(questions)} questions (kps:{question_kps})')
    
    return s, d

# Test student 刘大
s, d = test_student('3220602001', '123456', '刘大')
# Test student 李四
test_student('3220602004', '123456', '李四')
# Test student 王五
test_student('3220602005', '123456', '王五')