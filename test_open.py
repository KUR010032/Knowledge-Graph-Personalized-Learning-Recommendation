import requests, json

# Test if student named "Zhou" or others have 3.1.3 focus
# Also test resource watch URLs

s = requests.Session()
s.post('http://127.0.0.1:5050/login', data={'role': 'student', 'user_id': '3220602001', 'password': '123456'}, allow_redirects=False)
r = s.get('http://127.0.0.1:5050/student/recommend/data?t=1&refresh=1')
d = json.loads(r.text)

# Test resource opening
for t in d.get('targets', []):
    for res in t.get('resources', []):
        rid = res.get('resource_id', '')
        title = res.get('title', '')
        rtype = res.get('type', '')
        
        # Test the watch URL
        if rtype == '视频':
            url = f'http://127.0.0.1:5050/student/watch/' + rid
            # Don't URL encode, test as-is
            r2 = s.get(url, allow_redirects=False)
            print(f'Watch URL: /student/watch/{rid[:50]} -> Status: {r2.status_code}')
            if r2.status_code >= 400:
                print(f'  ERROR: {r2.status_code}')
        else:
            url = f'http://127.0.0.1:5050/student/view/' + rid
            r2 = s.get(url, allow_redirects=False)
            print(f'View URL: /student/view/{rid[:50]} -> Status: {r2.status_code}')
            if r2.status_code >= 400:
                print(f'  ERROR: {r2.status_code}')
        break  # Just test first resource
    break  # Just test first target

# Test question submit
print('\n--- Test Question Submit ---')
r = s.post('http://127.0.0.1:5050/student/questions/submit',
    json={'question_id': 'q1_1_1_1', 'answer': 'A'},
    headers={'Content-Type': 'application/json'})
print(f'Submit response: {r.status_code}')
try:
    result = r.json()
    print(json.dumps(result, ensure_ascii=False, indent=2)[:500])
except:
    print(r.text[:200])