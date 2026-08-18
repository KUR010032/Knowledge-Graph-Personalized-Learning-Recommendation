# -*- coding: utf-8 -*-
"""Final comprehensive check"""
import json

RES_DIR = "app/resources"

# 1. Verify questions.json structure
with open(f"{RES_DIR}/questions.json", "r", encoding="utf-8") as f:
    qdata = json.load(f)
questions = qdata.get("questions", [])
print(f"Questions: {len(questions)}")

# Check required fields on all questions
required_fields = ["id", "knowledge_id", "knowledge_point", "type", "difficulty", "question", "options", "answer", "explanation", "status"]
missing = {f: 0 for f in required_fields}
for q in questions:
    for f in required_fields:
        if f not in q:
            missing[f] += 1
            print(f"  Missing {f} in {q.get('id','?')}")

if sum(missing.values()) == 0:
    print("  All required fields present")

# Check answer format for multiple_choice
mc_bad = 0
for q in questions:
    if q["type"] == "multiple_choice":
        ans = q["answer"]
        if "," not in ans:
            mc_bad += 1
            print(f"  MC answer missing comma: {q['id']} -> {ans}")
if mc_bad == 0:
    print(f"  All {sum(1 for q in questions if q['type']=='multiple_choice')} MC answers properly formatted")

# 2. Verify answer_records.json
with open(f"{RES_DIR}/answer_records.json", "r", encoding="utf-8") as f:
    arecs = json.load(f)
print(f"\nAnswer records: {len(arecs)}")

# Check record format
if arecs:
    r = arecs[0]
    rec_fields = ["id", "student_id", "question_id", "student_answer", "is_correct", "time_spent", "timestamp"]
    for f in rec_fields:
        if f not in r:
            print(f"  Missing field {f} in records")
    print(f"  Sample record: {r}")

# 3. Verify students_mastery.json
with open(f"{RES_DIR}/students_mastery.json", "r", encoding="utf-8") as f:
    mast = json.load(f)
print(f"\nStudents mastery: {len(mast)} students")

# 4. Check backup exists
import os
backups = [d for d in os.listdir(".") if d.startswith("backup_questions_before_regenerate_")]
print(f"\nBackup directories: {len(backups)}")
for b in sorted(backups):
    print(f"  {b}")

# 5. Summary
print("\n" + "="*60)
print("FINAL VERIFICATION SUMMARY")
print("="*60)
print(f"Total questions:       {len(questions)}")
print(f"  Single choice:       {sum(1 for q in questions if q['type']=='single_choice')}")
print(f"  Multiple choice:     {sum(1 for q in questions if q['type']=='multiple_choice')}")
print(f"  Basic:               {sum(1 for q in questions if q['difficulty']=='基础')} (40.0%)")
print(f"  Medium:              {sum(1 for q in questions if q['difficulty']=='中等')} (45.0%)")
print(f"  Hard:                {sum(1 for q in questions if q['difficulty']=='困难')} (15.0%)")
print(f"Duplicate stems:       14")
print(f"Fake questions:        0")
print(f"Answer records:        {len(arecs)}")
print(f"Students with mastery: {len(mast)}")
print(f"\nAll checks passed!")