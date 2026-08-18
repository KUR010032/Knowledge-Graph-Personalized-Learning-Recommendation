# -*- coding: utf-8 -*-
"""Verify current state of learning_records.json for验收 output."""
import json
import os
from collections import Counter

RES_DIR = "app/resources"
TM_DIR = os.path.join(RES_DIR, "teaching_materials")
LR_FILE = os.path.join(RES_DIR, "learning_records.json")
RC_FILE = os.path.join(RES_DIR, "resource_completion.json")

def _json_load(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def is_valid_resource(resource_id):
    if not resource_id:
        return False
    safe_rel = str(resource_id).replace("\\", "/").lstrip("/")
    basename = os.path.basename(safe_rel)
    abs_path_tm = os.path.normpath(os.path.join(TM_DIR, basename))
    if os.path.isfile(abs_path_tm):
        return True
    abs_path = os.path.normpath(os.path.join(RES_DIR, safe_rel))
    if abs_path.startswith(os.path.normpath(RES_DIR)) and os.path.isfile(abs_path):
        return True
    return False

records = _json_load(LR_FILE, [])
print("=" * 60)
print("学习记录验收报告")
print("=" * 60)

# Total
print(f"\n1. 学习记录总数: {len(records)}")

# Check for "资源不存在"
bad_names = [r for r in records if "资源不存在" in (r.get("resource_name","")+r.get("resource_title","")+r.get("knowledge_point",""))]
print(f"\n2. 包含\"资源不存在\"的记录数: {len(bad_names)}")
if bad_names:
    for r in bad_names:
        print(f"   - {r.get('record_id')}: {r.get('resource_title')} | {r.get('resource_name')}")

# Check for invalid resources
invalid = []
for r in records:
    at = r.get("action_type") or ""
    rid = str(r.get("resource_id") or "").replace("\\", "/")
    if at != "question_practice" and not is_valid_resource(rid):
        invalid.append(r)
print(f"\n3. resource_id无效的记录数: {len(invalid)}")
for r in invalid[:10]:
    print(f"   - {r.get('record_id')} -> {r.get('resource_id')}")

# Check for duplicates
dup_keys = {}
dups = 0
for r in records:
    sid = str(r.get("student_id") or "").strip()
    rid = str(r.get("resource_id") or "").replace("\\", "/")
    at = r.get("action_type") or ""
    key = (sid, rid, at)
    if key in dup_keys:
        dups += 1
    dup_keys[key] = r
print(f"\n4. 重复记录数: {dups}")

# Resource types
type_counter = Counter()
for r in records:
    rt = r.get("resource_type") or "未知"
    type_counter[rt] += 1
print(f"\n5. 资源类型分布:")
for t, c in sorted(type_counter.items()):
    print(f"   {t}: {c}")

# Video count
video = sum(1 for r in records if r.get("resource_type") == "视频")
print(f"\n6. 视频学习 = {video}")

# Document count (文档 + PPT)
doc = sum(1 for r in records if r.get("resource_type") in ("文档", "PPT"))
print(f"7. 文档学习(文档+PPT) = {doc}")

# Exercise count
exercise = sum(1 for r in records if r.get("resource_type") == "习题")
print(f"8. 练习 = {exercise}")

# Source distribution
src_counter = Counter()
for r in records:
    src_counter[r.get("source") or "unknown"] += 1
print(f"\n9. 来源分布:")
for s, c in sorted(src_counter.items()):
    print(f"   {s}: {c}")

# Status distribution
status_counter = Counter()
for r in records:
    status_counter[r.get("status") or "unknown"] += 1
print(f"\n10. 状态分布:")
for s, c in sorted(status_counter.items()):
    print(f"   {s}: {c}")

# Check required fields
required_fields = ["record_id","student_id","resource_id","resource_title","resource_type","knowledge_id","knowledge_name","teacher","started_at","completed_at","status","source"]
missing = 0
for r in records:
    for f in required_fields:
        if f not in r:
            missing += 1
            print(f"  MISSING FIELD: {r.get('record_id')} missing {f}")
print(f"\n11. 缺少必填字段的记录数: {missing}")

# Students
students = set()
for r in records:
    students.add(str(r.get("student_id") or "").strip())
print(f"\n12. 涉及学生数: {len(students)}")

# Sample record
if records:
    print(f"\n13. 样例记录:")
    sample = records[0]
    for k, v in sample.items():
        print(f"   {k}: {v}")

# Resource_completion stats
rc = _json_load(RC_FILE, {})
print(f"\n14. resource_completion.json 学生数: {len(rc)}")
total_completions = sum(len(v) for v in rc.values())
print(f"   完成记录数: {total_completions}")

print("\n" + "=" * 60)
print("验收通过!" if len(bad_names)==0 and len(invalid)==0 and dups==0 else "验收未通过!")
print("=" * 60)