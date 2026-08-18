# -*- coding: utf-8 -*-
"""Rebuild learning_records.json from resource_completion.json + clean existing."""
import json
import os
from datetime import datetime

RES_DIR = "app/resources"
TM_DIR = os.path.join(RES_DIR, "teaching_materials")
LR_FILE = os.path.join(RES_DIR, "learning_records.json")
RC_FILE = os.path.join(RES_DIR, "resource_completion.json")

def _json_load(path, default=None):
    if not os.path.exists(path):
        return default if default is not None else []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def _json_save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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

def normalize_resource_type(rt):
    rt = (rt or "").strip()
    type_map = {
        "mp4": "视频", "video": "视频", "视频": "视频",
        "doc": "文档", "docx": "文档", "文档": "文档",
        "ppt": "PPT", "pptx": "PPT", "PPT": "PPT",
        "习题": "习题", "练习": "习题", "exercise": "习题",
    }
    lower = rt.lower()
    for k, v in type_map.items():
        if k in lower or rt in [k, v]:
            return v
    ext = os.path.splitext(str(rt))[1].lower().lstrip(".")
    if ext in ("mp4", "avi", "mov", "mkv"):
        return "视频"
    if ext in ("doc", "docx", "pdf"):
        return "文档"
    if ext in ("ppt", "pptx"):
        return "PPT"
    return "未知"

def clean_resource_title(rid):
    if not rid:
        return "未知资源"
    basename = os.path.basename(str(rid).replace("\\", "/"))
    name_no_ext = os.path.splitext(basename)[0]
    return name_no_ext

def _now_iso():
    return datetime.now().isoformat()

def load_resource_manifest():
    p = os.path.join(RES_DIR, "resource_manifest.json")
    if os.path.exists(p):
        return _json_load(p, {})
    return {}

print("=== Reading existing learning_records.json ===")
existing = _json_load(LR_FILE, [])
print(f"Existing records: {len(existing)}")

print("=== Reading resource_completion.json ===")
rc = _json_load(RC_FILE, {})
print(f"Students with completions: {len(rc)}")

manifest = load_resource_manifest()
resources_by_rid = {}
if isinstance(manifest, list):
    for item in manifest:
        resources_by_rid[item.get("resource_id", "")] = item
elif isinstance(manifest, dict):
    for k, v in manifest.items():
        if isinstance(v, dict):
            resources_by_rid[k] = v

print(f"Manifest resources: {len(resources_by_rid)}")

# Phase 1: Collect all valid completed records from resource_completion
completion_records = []
for student_id, completions in rc.items():
    for resource_id, info in completions.items():
        if not is_valid_resource(resource_id):
            print(f"  SKIP (invalid): {student_id} -> {resource_id}")
            continue
        ri = resources_by_rid.get(resource_id, {})
        rtype = ri.get("type") or ""
        ext = os.path.splitext(str(resource_id))[1].lower()
        rtype = rtype or ext.lstrip(".")
        completion_records.append({
            "student_id": student_id,
            "resource_id": resource_id,
            "resource_title": ri.get("title") or clean_resource_title(resource_id),
            "resource_type": normalize_resource_type(rtype),
            "knowledge_id": ri.get("knowledge_id") or "",
            "knowledge_name": ri.get("knowledge_point") or ri.get("knowledge_name") or "",
            "teacher": ri.get("teacher_name") or "",
            "action_type": "complete",
            "started_at": info.get("completed_at") or _now_iso(),
            "completed_at": info.get("completed_at") or _now_iso(),
            "status": "completed",
            "source": "resource_library",
            "created_at": info.get("completed_at") or _now_iso(),
        })

print(f"Valid completed records from resource_completion: {len(completion_records)}")

# Phase 2: Keep existing "view" or "question_practice" records that are valid
existing_records = []
for item in existing:
    if item.get("action_type") == "complete":
        continue
    rid = str(item.get("resource_id") or "").replace("\\", "/")
    at = item.get("action_type") or ""
    if at != "question_practice" and not is_valid_resource(rid):
        continue
    rn = item.get("resource_name") or item.get("resource_title") or ""
    if "资源不存在" in rn or "资源已不存在" in rn:
        continue
    existing_records.append(item)

print(f"Valid non-complete records: {len(existing_records)}")

# Phase 3: Merge and deduplicate
all_records = existing_records + completion_records

seen = {}
final = []
for i, item in enumerate(all_records):
    sid = str(item.get("student_id") or "").strip()
    rid = str(item.get("resource_id") or "").replace("\\", "/")
    at = item.get("action_type") or ""
    key = (sid, rid, at)
    if key in seen:
        continue
    seen[key] = item
    
    ri = resources_by_rid.get(rid, {})
    rtype = item.get("resource_type") or ""
    ext = os.path.splitext(rid)[1].lower()
    rtype = rtype or ext.lstrip(".")
    
    final.append({
        "record_id": item.get("record_id") or f"lr_{int(datetime.now().timestamp()*1000)}_{i}",
        "student_id": sid,
        "resource_id": rid,
        "resource_title": item.get("resource_title") or clean_resource_title(rid),
        "resource_type": normalize_resource_type(rtype),
        "knowledge_id": item.get("knowledge_id") or ri.get("knowledge_id") or "",
        "knowledge_name": item.get("knowledge_name") or ri.get("knowledge_point") or "",
        "teacher": item.get("teacher") or ri.get("teacher_name") or "",
        "action_type": at,
        "started_at": item.get("started_at") or item.get("created_at") or _now_iso(),
        "completed_at": item.get("completed_at") or (item.get("created_at") if at == "complete" else None),
        "status": item.get("status") or ("completed" if at == "complete" else "learning"),
        "source": item.get("source") or "resource_library",
        "created_at": item.get("created_at") or _now_iso(),
    })

print(f"Final records: {len(final)}")
print(f"Duplicates removed: {len(all_records) - len(final)}")

_json_save(LR_FILE, final)
print("=== Done ===")

# Stats
video = sum(1 for r in final if normalize_resource_type(r.get("resource_type","")) == "视频")
doc = sum(1 for r in final if normalize_resource_type(r.get("resource_type","")) in ("文档", "PPT"))
exercise = sum(1 for r in final if normalize_resource_type(r.get("resource_type","")) in ("习题",))
print(f"Video: {video}, Document: {doc}, Exercise: {exercise}")

# Check for any remaining bad names
bad = [r for r in final if "资源不存在" in (r.get("resource_name","")+r.get("resource_title",""))]
print(f"Bad names: {len(bad)}")

# Check for invalid resources
invalid = []
for r in final:
    if r.get("action_type") != "question_practice" and not is_valid_resource(r.get("resource_id","")):
        invalid.append(r)
print(f"Invalid resources: {len(invalid)}")
for r in invalid[:5]:
    print(f"  {r.get('record_id')} -> {r.get('resource_id')}")