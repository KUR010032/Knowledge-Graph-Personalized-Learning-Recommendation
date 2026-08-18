import json, time, sys
sys.path.insert(0, 'app')
from app import kgcf_recommend_data, _KGCF_RECOMMEND_CACHE

_KGCF_RECOMMEND_CACHE.clear()

t0 = time.time()
data = kgcf_recommend_data("3220602004", max_targets=6)
t1 = time.time()

print("=== 李四 (3220602004) 推荐结果 JSON 结构验证 ===")
print("耗时: %.0fms" % ((t1 - t0) * 1000))
print()

s = data["student"]
print("Student: id=%s, name=%s, type=%s" % (s["id"], s["name"], s["type"]))
print("Recommend Type: %s" % data["recommend_type"])
print("Avg Mastery: %.3f" % data["avg_mastery"])

print()
for i, t in enumerate(data["targets"]):
    print("--- Target %d: %s (%s) mastery=%.3f status=%s ---" % (
        i+1, t.get("knowledge_id", t.get("code")), t.get("knowledge_name", t.get("name")),
        t["mastery"], t["status"]))
    print("  Reason: %s" % t["reason"])

    print("  Resources:")
    for r in t["resources"]:
        print("    [%s] %s | relation=%s | kp=%s | score=%.3f" % (
            r["type"], r["title"][:50], r.get("relation", r.get("relation_label", "?")),
            r["knowledge_id"], r["score"]))

    print("  Questions:")
    for q in t["questions"]:
        print("    [%s] %s | reason=%s | kp=%s" % (
            q["difficulty"], q.get("title", q.get("question", ""))[:50],
            q["reason"], q.get("knowledge_id", "?")))

print()
print("=== 结构化检查 ===")
has_3_1_3 = False
for t in data["targets"]:
    for r in t["resources"]:
        if r["knowledge_id"] == "3.1.3":
            has_3_1_3 = True
            print("WARNING: 3.1.3 found in resources!")
    for q in t["questions"]:
        if q.get("knowledge_id") == "3.1.3":
            has_3_1_3 = True
            print("WARNING: 3.1.3 found in questions!")

if not has_3_1_3:
    print("OK: 3.1.3 NOT in any recommendation")

all_have_resources = all(len(t["resources"]) > 0 for t in data["targets"])
all_have_questions = all(len(t["questions"]) > 0 for t in data["targets"])
all_have_relation = all(
    all("relation" in r for r in t["resources"])
    for t in data["targets"]
)

print("All targets have resources: %s" % all_have_resources)
print("All targets have questions: %s" % all_have_questions)
print("All resources have relation field: %s" % all_have_relation)

print()
print("JSON sample (first target):")
sample = data["targets"][0].copy()
sample["resources"] = sample["resources"][:2]
sample["questions"] = sample["questions"][:1]
print(json.dumps(sample, ensure_ascii=False, indent=2))