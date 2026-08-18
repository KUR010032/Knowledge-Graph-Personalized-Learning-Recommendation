# -*- coding: utf-8 -*-
import sys, json, os, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'app')
import app
app._MASTERY_TREE_CACHE = {}
app._COMPLETION_MAP_CACHE = None
app._KGCF_RECOMMEND_CACHE = {}
app._KGCF_RESOURCE_INDEX = None
app._KGCF_QUESTION_INDEX = None
app._KGCF_NAME_MAP = None
from app import (
    kgcf_recommend_data, normalize_student_id,
    _kg_build_relationships, build_parent_maps,
    flow_kp_code, calculate_mastery_tree, _kgcf_classify_student
)

print("=" * 70)
print("KG-CF Recommendation Verification")
print("=" * 70)

students = [
    ("3220602001", "Liu Da"),
    ("3220602004", "Li Si"),
    ("3220602003", "Zhao Liu"),
]

for sid, name in students:
    sid_norm = normalize_student_id(sid)

    # Clear cache
    app._KGCF_RECOMMEND_CACHE = {}
    app._MASTERY_TREE_CACHE = {}

    t0 = time.time()
    data = kgcf_recommend_data(sid_norm, max_targets=6)
    elapsed = time.time() - t0

    reco_type = data.get("recommend_type", "")
    avg_m = data.get("avg_mastery", 0)
    student_info = data.get("student", {})

    print("\n" + "=" * 50)
    print("{} ({}) | Type={} | AvgMastery={:.3f} | Time={:.0f}ms".format(
        name, sid, reco_type, avg_m, elapsed * 1000
    ))
    print("-" * 50)

    targets = data.get("targets", [])
    all_kps_in_resources = set()

    for t in targets:
        code = t.get("code", "")
        mastery = t.get("mastery", 0)
        resources = t.get("resources", [])
        questions = t.get("questions", [])

        print("\nTARGET: {} (mastery={:.3f}, status={})".format(code, mastery, t.get("status","")))
        print("  reason: {}".format(t.get("reason","")[:100]))

        for r in resources:
            rkp = r.get("knowledge_id", "?")
            all_kps_in_resources.add(rkp)
            print("  RES [{rel}] kp={rkp} | {title} | {tp} | s={s:.3f}".format(
                rel=r.get("relation_label","?"),
                rkp=rkp,
                title=r.get("title","")[:55],
                tp=r.get("type","?"),
                s=r.get("score",0)
            ))

        for q in questions:
            print("  Q   [{reason}] {qid} (kp={kp}) | {diff}".format(
                reason=q.get("reason",""),
                qid=q.get("question_id",""),
                kp=q.get("knowledge_id",""),
                diff=q.get("difficulty","")
            ))

    # Checks
    has_313 = "3.1.3" in all_kps_in_resources
    all_res = all(len(t.get("resources",[])) > 0 for t in targets)
    all_q = all(len(t.get("questions",[])) > 0 for t in targets)
    print("\n  CHECKS:")
    print("    3.1.3 in resources: {}".format(has_313))
    print("    All have resources: {}".format(all_res))
    print("    All have questions: {}".format(all_q))

print("\n" + "=" * 70)
print("DONE")
print("=" * 70)