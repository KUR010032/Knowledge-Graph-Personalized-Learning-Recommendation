# -*- coding: utf-8 -*-
import sys, json, os, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Import from the app subdirectory
sys.path.insert(0, os.path.join(os.getcwd(), 'app'))

# Clear any cached module
for key in list(sys.modules.keys()):
    if key.startswith('app'):
        del sys.modules[key]

import importlib
spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.getcwd(), "app", "app.py"))
appmod = importlib.util.module_from_spec(spec)
sys.modules['app_module'] = appmod
spec.loader.exec_module(appmod)

# Clean caches
appmod._MASTERY_TREE_CACHE = {}
appmod._COMPLETION_MAP_CACHE = None
appmod._KGCF_RECOMMEND_CACHE = {}
appmod._KGCF_RESOURCE_INDEX = None
appmod._KGCF_QUESTION_INDEX = None
appmod._KGCF_NAME_MAP = None

kgcf_recommend_data = appmod.kgcf_recommend_data
normalize_student_id = appmod.normalize_student_id
build_parent_maps = appmod.build_parent_maps
calculate_mastery_tree = appmod.calculate_mastery_tree
_kgcf_classify_student = appmod._kgcf_classify_student

sid = normalize_student_id("3220602004")
score_map, detail_map, name_map, children = calculate_mastery_tree(sid)

print("=== Li Si Mastery for key KPs ===")
for kp in ["1.2", "1.3", "1.6.1", "1.6.2", "1.6.3",
           "2.3.4", "3.1.1", "3.1.2", "3.1.3", "3.1.4", "3.4.5", "3.4.8"]:
    m = score_map.get(kp, -1)
    if 0.4 <= m < 0.6:
        status = "需巩固"
    elif 0.01 < m < 0.4:
        status = "薄弱"
    elif m <= 0.01:
        status = "未学习"
    else:
        status = "已掌握"
    print("  {0}: {1:.3f} ({2})".format(kp, m, status))

student_type, avg_m = _kgcf_classify_student(score_map)
print("\nStudent type: {0} | Avg: {1:.3f}".format(student_type, avg_m))

catalog_names, _ = build_parent_maps()
all_kps_leaf = sorted([c for c in score_map
    if c in catalog_names
    and (c.count(".") >= 2 or (c.count(".") >= 1 and not children.get(c)))],
    key=lambda x: [int(p) if p.isdigit() else 99 for p in x.split(".")])

print("\n=== Need consolidate (0.40-0.59) leaf KPs ===")
need_consolidate = [c for c in all_kps_leaf if 0.40 <= score_map.get(c, 0) < 0.60]
need_consolidate.sort(key=lambda x: (int(x.split(".")[0]), score_map.get(x, 0)))
for c in need_consolidate:
    print("  {0}: {1:.3f}".format(c, score_map.get(c, 0)))

print("\n=== Weak (0.01-0.39) leaf KPs ===")
weak = [c for c in all_kps_leaf if 0.01 < score_map.get(c, 0) < 0.40]
weak.sort(key=lambda x: score_map.get(x, 0))
for c in weak[:10]:
    print("  {0}: {1:.3f}".format(c, score_map.get(c, 0)))

data = kgcf_recommend_data(sid, max_targets=6)
print("\n=== Recommendation Result ===")
print("Type: {0}".format(data.get("recommend_type")))
for t in data.get("targets", []):
    code = t.get("code", "")
    mastery = t.get("mastery", 0)
    resources = t.get("resources", [])
    questions = t.get("questions", [])
    print("  {0} (m={1:.3f}, {2}) | res={3}, q={4}".format(
        code, mastery, t.get("status",""), len(resources), len(questions)))
    for r in resources[:2]:
        print("    [{0}] kp={1} s={2:.3f}".format(
            r.get("relation_label","?"), r.get("knowledge_id","?"), r.get("score",0)))

all_have_r = all(len(t.get("resources",[])) > 0 for t in data.get("targets", []))
all_have_q = all(len(t.get("questions",[])) > 0 for t in data.get("targets", []))
print("\n  All have resources: {0}".format(all_have_r))
print("  All have questions: {0}".format(all_have_q))
print("  Target codes: {0}".format([t.get("code") for t in data.get("targets", [])]))