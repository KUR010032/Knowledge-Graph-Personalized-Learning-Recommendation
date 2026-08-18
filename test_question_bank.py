import requests
import json
import sys

BASE = "http://127.0.0.1:5000"
s = requests.Session()

# 1. Login as teacher
print("=== 1. Login as teacher ===")
r = s.post(f"{BASE}/login", data={"username": "1000002401", "password": "admin1"}, allow_redirects=False)
print(f"Login status: {r.status_code}")

# 2. Access question bank page
print("\n=== 2. Access question bank page ===")
r = s.get(f"{BASE}/teacher/question-bank")
print(f"Status: {r.status_code}")
html = r.text
# Check for modal
print(f"Has modal HTML: {'questionModal' in html}")
print(f"Has questionModalHTML: {'questionModalHTML' in html}")
print(f"Has openQuestionModal: {'openQuestionModal' in html}")
print(f"Has saveQuestion: {'saveQuestion' in html}")
print(f"Has parseQuickInput: {'parseQuickInput' in html}")
print(f"Has closeQuestionModal: {'closeQuestionModal' in html}")
# Check NO prompt
print(f"Has prompt(): {'prompt(' in html}")
print(f"Has window.prompt: {'window.prompt' in html}")

# 3. Get questions data
print("\n=== 3. Get questions data ===")
r = s.get(f"{BASE}/teacher/questions/data")
data = r.json()
questions = data.get("questions", [])
print(f"Total questions: {len(questions)}")
if questions:
    q = questions[0]
    print(f"First question ID: {q.get('id')}")
    print(f"First question fields: {list(q.keys())[:10]}")

# 4. Test adding a question
print("\n=== 4. Test adding a question ===")
payload = {
    "question": "测试题目：活锁与死锁的区别",
    "title": "测试题目：活锁与死锁的区别",
    "type": "single_choice",
    "difficulty": "medium",
    "knowledge_point": "3.4.7 活锁",
    "knowledge_name": "3.4.7 活锁",
    "knowledge_id": "3.4.7",
    "chapter_id": "3",
    "chapter_name": "第3章",
    "options": [
        "A. 活锁中进程状态不断变化",
        "B. 活锁中进程永久阻塞",
        "C. 活锁由硬件故障引起",
        "D. 活锁不影响系统性能"
    ],
    "answer": "A",
    "analysis": "测试解析：活锁中进程仍在运行",
    "explanation": "测试解析：活锁中进程仍在运行"
}
r = s.post(f"{BASE}/teacher/questions/add", json=payload)
print(f"Add status: {r.status_code}")
print(f"Add result: {r.json()}")

# 5. Verify question was written to questions.json
print("\n=== 5. Verify questions.json ===")
with open("resources/questions.json", "r", encoding="utf-8") as f:
    qdata = json.load(f)
test_qs = [q for q in qdata.get("questions", []) if "测试题目" in str(q.get("question", ""))]
print(f"Test questions found in questions.json: {len(test_qs)}")
if test_qs:
    print(f"Test question: {json.dumps(test_qs[0], ensure_ascii=False, indent=2)[:500]}")

# 6. Clean up - delete test question
print("\n=== 6. Clean up test question ===")
if test_qs:
    for tq in test_qs:
        qid = tq.get("id")
        r = s.post(f"{BASE}/teacher/questions/{qid}/delete")
        print(f"Delete {qid}: {r.json()}")

print("\n=== ALL TESTS COMPLETE ===")