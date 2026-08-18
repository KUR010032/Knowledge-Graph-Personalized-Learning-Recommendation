# -*- coding: utf-8 -*-
import sys, json, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'app')
import app
app._MASTERY_TREE_CACHE = {}
app._COMPLETION_MAP_CACHE = None
from app import calculate_mastery_tree, normalize_student_id

sid = normalize_student_id("3220602004")
score_map, detail_map, name_map, children = calculate_mastery_tree(sid)

print("=== Li Si 3220602004 Mastery Results (After Fix) ===")
targets = ["1.2", "1.3", "1.4", "1.5", "1.6.2", "1.6.3", "3.1.3"]
for code in targets:
    d = detail_map.get(code, {})
    s = score_map.get(code, None)
    es = d.get("exercise_score", 0)
    bs = d.get("behavior_score", 0)
    print(f"\n{code} ({name_map.get(code, code)}):")
    print(f"  mastery = {s}")
    print(f"  total_questions = {d.get('total_questions')}")
    print(f"  total_attempts = {d.get('total_attempts')}")
    print(f"  correct_questions = {d.get('correct_questions')}")
    print(f"  wrong_questions = {d.get('wrong_questions')}")
    print(f"  exercise_score = {es:.3f}")
    print(f"  total_resources = {d.get('total_resources')}")
    print(f"  resource_completed = {d.get('resource_completed')}")
    print(f"  behavior_score = {bs:.3f}")
    print(f"  has_practice = {d.get('has_practice')}")
    print(f"  has_learning = {d.get('has_learning')}")
    print(f"  formula: M = 0.7 * {es:.3f} + 0.3 * {bs:.3f} = {0.7*es + 0.3*bs:.3f}")

print("\nDone.")