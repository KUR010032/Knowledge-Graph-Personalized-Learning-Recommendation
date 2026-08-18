# -*- coding: utf-8 -*-
import sys, json, os, io, time, importlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'app')

# Force reload
if 'app' in sys.modules:
    del sys.modules['app']
import app.app as appmod
importlib.reload(appmod)

# Clean all caches
appmod._MASTERY_TREE_CACHE = {}
appmod._COMPLETION_MAP_CACHE = None
appmod._KGCF_RECOMMEND_CACHE = {}
appmod._KGCF_RESOURCE_INDEX = None
appmod._KGCF_QUESTION_INDEX = None
appmod._KGCF_NAME_MAP = None

from app.app import kgcf_recommend_data, normalize_student_id, build_parent_maps, _kg_build_relationships, calculate_mastery_tree, _kgcf_classify_student

sid = normalize_student_id("3220602004")

# Check mastery for key KPs
score_map, detail_map, name_map, children = calculate_mastery_tree(sid)
print("=== Li Si Mastery for key KPs ===")
for kp in ["1.2", "1.3", "1.4", "1.5", "1.6.1", "1.6.2", "1.6.3", "1.6.4",
           "2.1.1", "2.3.4", "3.1.1", "3.1.2", "3.1.3", "3.1.4",
           "3.4.5", "3.4.8"]:
    m = score_map.get(kp, -1)
    status = "需巩固" if 0.4 <= m < 0.6 else ("薄弱" if 0.01 < m < 0.4 else ("未学习" if m <= 0.01 else "已掌握"))
    print("  {}: {:.3f} ({})".format(kp, m, status))

student_type, avg_m = _kgcf_classify_student(score_map)
print("\nStudent type: {} | Avg: {:.3f}".format(student_type, avg_m))

# Check all_kps filtering
catalog_names, _ = build_parent_maps()
all_kps_leaf = sorted([c for c in score_map
    if c in catalog_names
    and (c.count(".") >= 2 or (c.count(".") >= 1 and not children.get(c)))],
    key=lambda x: [int(p) if p.isdigit() else 99 for p in x.split(".")])

print("\n=== Need consolidate (0.40-0.59) ===")
need_consolidate = [c for c in all_kps_leaf if 0.40 <= score_map.get(c, 0) < 0.60]
need_consolidate.sort(key=lambda x: (int(x.split(".")[0]), score_map.get(x, 0)))
for c in need_consolidate:
    print("  {}: {:.3f}".format(c, score_map.get(c, 0)))

print("\n=== Weak (0.01-0.39) ===")
weak = [c for c in all_kps_leaf if 0.01 < score_map.get(c, 0) < 0.40]
weak.sort(key=lambda x: score_map.get(x, 0))
for c in weak[:10]:
    print("  {}: {:.3f}".format(c, score_map.get(c, 0)))

# Now run recommendation
data = kgcf_recommend_data(sid, max_targets=6)
print("\n=== Recommendation Result ===")
print("Type: {}".format(data.get("recommend_type")))
for t in data.get("targets", []):
    code = t.get("code", "")
    mastery = t.get("mastery", 0)
    resources = t.get("resources", [])
    questions = t.get("questions", [])
    print("  {} (m={:.3f}, status={}) | resources={}, questions={}".format(
        code, mastery, t.get("status",""), len(resources), len(questions)))
    for r in resources[:2]:
        print("    R [{rel}] kp={rkp} s={s:.3f}".format(
            rel=r.get("relation_label","?"), rkp=r.get("knowledge_id","?"), s=r.get("score",0)))

print("\nChecks:")
all_have_r = all(len(t.get("resources",[])) > 0 for t in data.get("targets", []))
all_have_q = all(len(t.get("questions",[])) > 0 for t in data.get("targets", []))
print("  All have resources: {}".format(all_have_r))
print("  All have questions: {}".format(all_have_q))
kps_in_res = set()
for t in data.get("targets", []):
    for r in t.get("resources", []):
        kps_in_res.add(r.get("knowledge_id", ""))
print("  3.1.3 in resources: {}".format("3.1.3" in kps_in_res and "3.1.3" not in [t.get("code") for t in data.get("targets", [])]))
print("  Target KPs: {}".format([t.get("code") for t in data.get("targets", [])]))