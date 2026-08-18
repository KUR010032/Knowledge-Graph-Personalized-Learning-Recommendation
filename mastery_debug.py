# -*- coding: utf-8 -*-
import sys, json, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'app')

from app import (
    calculate_mastery_tree, normalize_student_id,
    load_question_history_clean, load_questions_clean,
    flow_kp_code, get_completion_map, all_resource_records,
    build_knowledge_catalog_names, build_parent_maps
)

sid = normalize_student_id("3220602004")
print(f"=== Mastery Debug for Student: {sid} ===")

# Clear cache
import app
app._MASTERY_TREE_CACHE = {}

score_map, detail_map, name_map, children = calculate_mastery_tree(sid)

targets = ["1.2", "1.3", "1.4", "1.5", "1.6.2", "1.6.3", "3.1.3"]

print("\n=== Catalog children check ===")
catalog_names, catalog_children = build_parent_maps()
for code in targets:
    child_codes = catalog_children.get(code, set())
    is_leaf = code.count(".") >= 2 or (code.count(".") >= 1 and not catalog_children.get(code))
    print(f"  {code}: is_leaf={is_leaf}, children={sorted(child_codes)}")

print("\n=== Mastery Results ===")
for code in targets:
    d = detail_map.get(code, {})
    s = score_map.get(code, None)
    print(f"\n  {code} ({name_map.get(code, code)}):")
    print(f"    mastery = {s}")
    print(f"    total_questions = {d.get('total_questions', 'N/A')}")
    print(f"    total_attempts = {d.get('total_attempts', 'N/A')}")
    print(f"    correct_questions = {d.get('correct_questions', 'N/A')}")
    print(f"    wrong_questions = {d.get('wrong_questions', 'N/A')}")
    print(f"    exercise_score = {d.get('exercise_score', 'N/A')}")
    print(f"    total_resources = {d.get('total_resources', 'N/A')}")
    print(f"    resource_completed = {d.get('resource_completed', 'N/A')}")
    print(f"    behavior_score = {d.get('behavior_score', 'N/A')}")
    print(f"    has_practice = {d.get('has_practice', 'N/A')}")
    print(f"    has_learning = {d.get('has_learning', 'N/A')}")

print("\n=== Question History for Li Si ===")
history = load_question_history_clean().get(sid, {})
print(f"  Total question records: {len(history)}")
for qid, h in sorted(history.items())[:20]:
    print(f"    question_id={qid}: total={h.get('total_attempts',0)}, correct={h.get('correct_count',0)}, wrong={h.get('wrong_count',0)}")

print("\n=== Completion Map for Li Si ===")
completion_map = get_completion_map(sid)
print(f"  Total completion records: {len(completion_map)}")
completed = [rid for rid, v in completion_map.items() if v.get('completed')]
print(f"  Completed resources: {len(completed)}")
for rid in completed[:20]:
    print(f"    {rid}")

print("\n=== All Resources with KP codes for 1.2-1.5, 1.6.2, 1.6.3, 3.1.3 ===")
all_res = all_resource_records()
for code in targets:
    kp_res = [r for r in all_res if flow_kp_code(r.get("knowledge_point")) == code]
    print(f"  {code}: {len(kp_res)} resources in all_resource_records")
    for r in kp_res:
        rid = r.get('resource_id', '')
        c = completion_map.get(rid, {})
        print(f"    -> {rid} | completed={c.get('completed', False)}")

print("\nDone.")