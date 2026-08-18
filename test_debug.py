import requests

BASE = "http://127.0.0.1:5000"
s = requests.Session()

# Login as teacher
r = s.post(f"{BASE}/login", data={"username": "1000002401", "password": "admin1"}, allow_redirects=True)
print(f"Login status: {r.status_code}, URL: {r.url}")
print(f"Cookies: {s.cookies.get_dict()}")

# Access question bank page
r = s.get(f"{BASE}/teacher/question-bank")
print(f"Page status: {r.status_code}")
print(f"URL: {r.url}")
html = r.text
print(f"HTML length: {len(html)}")

# Check patterns
print(f"\nHas 'questionModalHTML': {'questionModalHTML' in html}")
print(f"Has 'openQuestionModal': {'openQuestionModal' in html}")
print(f"Has 'saveQuestion': {'saveQuestion' in html}")
print(f"Has 'parseQuickInput': {'parseQuickInput' in html}")
print(f"Has 'questionBank': {'questionBank' in html}")
print(f"Has 'prompt(': {'prompt(' in html}")
print(f"Has 'editQuestion': {'editQuestion' in html}")
print(f"Has 'load();': {'load();' in html}")
print(f"Has 'TEACHER_QUESTION_UI_JS': {'TEACHER_QUESTION_UI_JS' in html}")

# Find the biggest script tag
scripts = []
start = 0
while True:
    idx = html.find('<script>', start)
    if idx < 0:
        break
    end_idx = html.find('</script>', idx)
    if end_idx < 0:
        break
    scripts.append((idx, end_idx, html[idx:end_idx+9]))
    start = end_idx + 9

print(f"\nNumber of script tags: {len(scripts)}")
for i, (s, e, content) in enumerate(scripts):
    print(f"\nScript {i}: {s}-{e} (len={e-s})")
    print(f"  Last 200 chars: ...{content[-200:]}")