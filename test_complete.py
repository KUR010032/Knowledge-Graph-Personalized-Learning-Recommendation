import requests
import sys

BASE = "http://127.0.0.1:5000"
s = requests.Session()

r = s.post(BASE + "/login", data={
    "role": "student",
    "user_id": "3220602001",
    "password": "123456"
}, allow_redirects=False)
print("Login OK")

r = s.post(BASE + "/student/resource/1.1.1_基本概念_李老师.pptx/complete", allow_redirects=False)
data = r.json()
esid = data["exercise_set"]["exercise_set_id"]
print(f"ESID: {esid}")

r = s.get(BASE + "/student/practice_set?exercise_set_id=" + esid)
print(f"Page: {r.status_code}")

import re, json
qdata_match = re.search(r'var questions=\[(.*?)\];', r.text)
if qdata_match:
    qdata_str = qdata_match.group(1)
    qdata = json.loads("[" + qdata_str + "]")
    q1 = qdata[0]
    qid = q1["id"]
    ans = q1["answer"]
    print(f"Q1: {qid}, answer={ans}")
else:
    print("NO QUESTION DATA")
    sys.exit(1)

r = s.post(BASE + "/student/practice_set/submit", json={
    "exercise_set_id": esid,
    "question_id": qid,
    "selected": ans,
    "current_index": 0
})
print(f"Submit: {r.status_code}")
print(f"Submit data: {r.json()}")

r = s.post(BASE + "/student/practice_set/complete", json={
    "exercise_set_id": esid,
    "answers": [{"question_id": qid, "selected": ans, "correct": True}]
})
print(f"Complete status: {r.status_code}")
if r.status_code == 500:
    print(f"Error: {r.text[:800]}")
else:
    try:
        comp = r.json()
        print(f"Complete: {comp}")
    except:
        print(f"Raw: {r.text[:500]}")