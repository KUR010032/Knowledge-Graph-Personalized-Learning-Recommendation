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
from app import kgcf_recommend_data, normalize_student_id, build_parent_maps, _kg_build_relationships, flow_kp_code

sid = normalize_student_id("3220602004")
catalog_names, children = build_parent_maps()
pre_map, rel_map, next_map = _kg_build_relationships(catalog_names, children)

data = kgcf_recommend_data(sid, max_targets=6)
reco_type = data.get("recommend_type", "")
avg_m = data.get("avg_mastery", 0)

print("Li Si (3220602004) | {} | AvgMastery={:.3f}".format(reco_type, avg_m))
print()

targets = data.get("targets", [])
for t in targets:
    code = t.get("code", "")
    mastery = t.get("mastery", 0)
    resources = t.get("resources", [])
    questions = t.get("questions", [])

    print("TARGET: {} (mastery={:.3f}, status={})".format(code, mastery, t.get("status","")))
    print("  reason: {}".format(t.get("reason","")))
    print("  Pre: {}".format(pre_map.get(code, [])))
    print("  Rel: {}".format(rel_map.get(code, [])))
    print("  Next: {}".format(next_map.get(code, [])))

    for i, r in enumerate(resources):
        if i >= 3:
            print("  ... +{} more resources".format(len(resources) - 3))
            break
        print("  R{} [{rel}] kp={rkp} | {title} | {tp} | s={s:.3f}".format(
            i+1,
            rel=r.get("relation_label","?"),
            rkp=r.get("knowledge_id","?"),
            title=r.get("title","")[:60],
            tp=r.get("type","?"),
            s=r.get("score",0)
        ))

    for i, q in enumerate(questions):
        print("  Q{} [{reason}] {qid} (kp={kp}) | {diff}".format(
            i+1,
            reason=q.get("reason",""),
            qid=q.get("question_id",""),
            kp=q.get("knowledge_id",""),
            diff=q.get("difficulty","")
        ))
    print()

# Summary checks
all_kps = set()
for t in targets:
    for r in t.get("resources", []):
        all_kps.add(r.get("knowledge_id", ""))

print("SUMMARY:")
print("  3.1.3 in any resource: {}".format("3.1.3" in all_kps))
print("  All unique resource KPs: {}".format(sorted(all_kps)))
all_have_res = all(len(t.get("resources",[])) > 0 for t in targets)
all_have_q = all(len(t.get("questions",[])) > 0 for t in targets)
print("  All targets have resources: {}".format(all_have_res))
print("  All targets have questions: {}".format(all_have_q))

# Check 1.6.2 specifically
for t in targets:
    if t["code"] == "1.6.2":
        print("\n1.6.2 RESOURCES:")
        for r in t["resources"]:
            print("  kp_id={} relation={}".format(r["knowledge_id"], r["relation_label"]))