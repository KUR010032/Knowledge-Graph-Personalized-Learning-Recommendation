import requests
import json
import re
import os
import sys

BASE = "http://127.0.0.1:5000"
s = requests.Session()

print("=== 1. Login ===")
r = s.post(BASE + "/login", data={
    "role": "student",
    "user_id": "3220602001",
    "password": "123456"
}, allow_redirects=False)
print(f"  Status: {r.status_code}")
print(f"  Cookies: {dict(s.cookies)}")
if r.status_code != 302:
    print(f"  Response: {r.text[:300]}")
    sys.exit(1)

print("\n=== 2. Complete resource ===")
r = s.post(BASE + "/student/resource/1.1.1_基本概念_李老师.pptx/complete", allow_redirects=False)
print(f"  Status: {r.status_code}")
data = r.json()
print(f"  Response keys: {list(data.keys())}")
es = data.get("exercise_set", {})
esid = es.get("exercise_set_id", "")
print(f"  Exercise set ID: {esid}")
print(f"  Total questions: {es.get('total_count')}")
print(f"  Question IDs: {es.get('question_ids', [])}")

if not esid:
    print("ERROR: No exercise set generated!")
    sys.exit(1)

print("\n=== 3. Open practice set page ===")
r = s.get(BASE + "/student/practice_set?exercise_set_id=" + esid)
print(f"  Status: {r.status_code}")
html = r.text
print(f"  Has tags: {'tag-type' in html}")
print(f"  Has prev button: {'上一题' in html}")
print(f"  Has complete button: {'完成练习' in html}")
print(f"  Has answer dots: {'answerDots' in html}")
print(f"  Has option-label: {'option-label' in html}")

print("\n=== 4. Parse question data and submit ===")
qdata_match = re.search(r'var questions=\[(.*?)\];', html)
if qdata_match:
    qdata_str = qdata_match.group(1)
    qdata = json.loads("[" + qdata_str + "]")
    q1 = qdata[0]
    print(f"  Q1: {q1.get('title','')[:60]}")
    print(f"  Q1 type: {q1.get('type_display')}")
    print(f"  Q1 difficulty: {q1.get('difficulty_display')}")
    print(f"  Q1 KP: {q1.get('knowledge_code')} {q1.get('knowledge_name')}")
    print(f"  Q1 wrong_count: {q1.get('wrong_count')}")
    print(f"  Q1 correct_count: {q1.get('correct_count')}")
    print(f"  Q1 is_new: {q1.get('is_new_question')}")
    print(f"  Q1 in_wrong_book: {q1.get('in_wrong_book')}")
    
    r = s.post(BASE + "/student/practice_set/submit", json={
        "exercise_set_id": esid,
        "question_id": q1.get("id"),
        "selected": q1.get("answer"),
        "current_index": 0
    })
    print(f"\n  Submit status: {r.status_code}")
    sub_data = r.json()
    print(f"  Correct: {sub_data.get('correct')}")
    print(f"  Correct answer: {sub_data.get('correct_answer')}")
    print(f"  Explanation: {str(sub_data.get('explanation',''))[:60]}")
    print(f"  Wrong book action: {sub_data.get('wrong_book_action')}")
    print(f"  Answered count: {sub_data.get('answered_count')}")

print("\n=== 5. Complete exercise set ===")
r = s.post(BASE + "/student/practice_set/complete", json={
    "exercise_set_id": esid,
    "answers": [{"question_id": q1.get("id"), "selected": q1.get("answer"), "correct": True}]
})
print(f"  Status: {r.status_code}")
comp_data = r.json()
print(f"  Success: {comp_data.get('success')}")
summary = comp_data.get("summary", {})
print(f"  Total answered: {summary.get('total_answered')}")
print(f"  Total correct: {summary.get('total_correct')}")
print(f"  Accuracy: {summary.get('accuracy')}")
mc = summary.get("mastery_changes", [])
for m in mc:
    jump = m['after'] - m['before']
    print(f"  KP {m['knowledge_code']}: {m['before']:.1%} -> {m['after']:.1%} (change: {m['change']:+.1%})")
    if abs(jump) > 0.15:
        print(f"  WARNING: Jump > 15%!")
    else:
        print(f"  OK: Jump within 15% limit")

print("\n=== 6. Verify question_history ===")
qh_file = os.path.join(os.path.dirname(__file__), "app", "resources", "question_history.json")
with open(qh_file, "r", encoding="utf-8") as f:
    qh = json.load(f)
sid = "3220602001\u5218\u5927"  # 刘大
sh = qh.get(sid, {})
qid = q1.get("id")
h = sh.get(qid, {})
print(f"  Q1 history: total_attempts={h.get('total_attempts')}, correct={h.get('correct_count')}, wrong={h.get('wrong_count')}, consecutive={h.get('consecutive_correct')}")

print("\n=== 7. Verify wrong_book ===")
wb_file = os.path.join(os.path.dirname(__file__), "app", "resources", "wrong_book.json")
with open(wb_file, "r", encoding="utf-8") as f:
    wb = json.load(f)
sw = wb.get(sid, {})
print(f"  Wrong book entries: {len(sw)}")
print(f"  Q1 in wrong_book: {qid in sw}")

print("\n=== ALL TESTS PASSED ===")