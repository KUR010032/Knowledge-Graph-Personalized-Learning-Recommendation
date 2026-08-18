# -*- coding: utf-8 -*-
"""Final verification - check student records API response for enrichment."""
import json
import urllib.request
import http.cookiejar
import urllib.parse

BASE = "http://127.0.0.1:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def api(method, path, data=None):
    url = BASE + path
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers={"Content-Type": "application/json"}, method=method)
    else:
        req = urllib.request.Request(url, method=method)
    try:
        resp = opener.open(req)
        return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": str(e.code), "body": e.read().decode("utf-8")}

# Login
login_data = urllib.parse.urlencode({"role": "student", "user_id": "3220602001", "password": "123456"}).encode("utf-8")
req = urllib.request.Request(BASE + "/login", data=login_data, method="POST")
try:
    resp = opener.open(req)
    resp.read()
except:
    pass

# Get records
result = api("GET", "/student/records/data")
if result.get("success"):
    s = result.get("summary", {})
    print("=== 统计摘要 ===")
    print(f"总记录: {s.get('total')}")
    print(f"视频学习: {s.get('video')}")
    print(f"文档学习: {s.get('document')}")
    print(f"练习: {s.get('exercise')}")
    print(f"本月记录: {s.get('month')}")
    print(f"本周记录: {s.get('week')}")
    
    records = result.get("records", [])
    
    # Check for "资源不存在" in records
    bad = [r for r in records if "资源不存在" in str(r.get("resource_name","")) or "资源不存在" in str(r.get("knowledge_point",""))]
    print(f"\n包含\"资源不存在\"的记录: {len(bad)}")
    
    # Check teacher enrichment
    no_teacher = [r for r in records if not r.get("teacher")]
    print(f"缺少teacher字段的记录: {len(no_teacher)}")
    
    # Check for the test resource
    test_rid = "teaching_materials/1.1.1_基本概念_陈老师.mp4"
    test_recs = [r for r in records if test_rid in str(r.get("resource_id",""))]
    print(f"\n测试资源 '{test_rid}' 的记录数: {len(test_recs)}")
    for r in test_recs:
        print(f"  record_id: {r.get('record_id')}")
        print(f"  action_type: {r.get('action_type')}")
        print(f"  status: {r.get('status')}")
        print(f"  resource_title: {r.get('resource_title')}")
        print(f"  resource_type: {r.get('resource_type')}")
        print(f"  teacher: {r.get('teacher')}")
        print(f"  knowledge_point: {r.get('knowledge_point')}")
        print(f"  resource_exists: {r.get('resource_exists')}")
        print()
    
    # Show a few enriched records
    print("=== 富化后的记录样例 ===")
    for r in records[:3]:
        print(f"  title={r.get('resource_title')}, type={r.get('resource_type')}, teacher={r.get('teacher')}, kp={r.get('knowledge_point')}, exists={r.get('resource_exists')}")
else:
    print(f"Error: {result}")

print("\n=== DONE ===")