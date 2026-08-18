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
    flow_kp_code, calculate_mastery_tree
)

print("=" * 70)
print("KG-CF推荐引擎 验证报告")
print("=" * 70)

# Test students
students = {
    "3220602004": "Li Si (李四)",
    "3220602001": "Liu Da (刘大)",
    "3220602003": "Zhao Liu (赵六)",
}

for sid, label in students.items():
    print("\n" + "=" * 70)
    print("学生: {} ({})".format(label, sid))
    print("-" * 70)

    t0 = time.time()
    sid_norm = normalize_student_id(sid)
    data = kgcf_recommend_data(sid_norm, max_targets=6)
    elapsed = time.time() - t0

    reco_type = data.get("recommend_type", "")
    avg_m = data.get("avg_mastery", 0)
    student_info = data.get("student", {})
    print("类型: {} | 平均掌握度: {:.3f} | 耗时: {:.0f}ms".format(
        reco_type, avg_m, elapsed * 1000
    ))

    # Verify KG relationships for a key target
    catalog_names, children = build_parent_maps()
    pre_map, rel_map, next_map = _kg_build_relationships(catalog_names, children)
    test_code = "1.6.2"
    print("\n  KG关系验证 (1.6.2):")
    print("    Pre: {}".format(pre_map.get(test_code, [])))
    print("    Rel: {}".format(rel_map.get(test_code, [])))
    print("    Next: {}".format(next_map.get(test_code, [])))

    targets = data.get("targets", [])
    print("\n  推荐目标: {} 个".format(len(targets)))

    has_313 = False
    for t in targets:
        code = t.get("code", "")
        mastery = t.get("mastery", 0)
        status = t.get("status", "")
        reason = t.get("reason", "")[:80]
        resources = t.get("resources", [])
        questions = t.get("questions", [])

        # Check if 3.1.3 appears
        for r in resources:
            r_kp = r.get("knowledge_id", "")
            if r_kp == "3.1.3":
                has_313 = True

        print("\n  [{0}] {1} ({2}) mastery={3:.3f}".format(
            code, catalog_names.get(code, code), status, mastery
        ))
        print("    reason: {}".format(reason))

        print("    资源 ({} 个):".format(len(resources)))
        for r in resources:
            print("      [{rl}] {kp} | {title} | {tp} | score={sc:.3f}".format(
                rl=r.get("relation_label", "?"),
                kp=r.get("knowledge_id", "?"),
                title=(r.get("title", ""))[:50],
                tp=r.get("type", "?"),
                sc=r.get("score", 0)
            ))

        print("    题目 ({} 个):".format(len(questions)))
        for q in questions:
            print("      [{reason}] {qid} kp={kp} | {diff}".format(
                reason=q.get("reason", ""),
                qid=q.get("question_id", ""),
                kp=q.get("knowledge_id", ""),
                diff=q.get("difficulty", "")
            ))

    print("\n  验收检查:")
    print("    包含无关3.1.3资源: {}".format("是" if has_313 else "否 (OK)"))
    all_have_resources = all(len(t.get("resources", [])) > 0 for t in targets)
    all_have_questions = all(len(t.get("questions", [])) > 0 for t in targets)
    print("    每个目标都有资源: {}".format("是" if all_have_resources else "否"))
    print("    每个目标都有题目: {}".format("是" if all_have_questions else "否"))
    print("    接口耗时: {:.0f}ms".format(elapsed * 1000))

print("\n" + "=" * 70)
print("验证完成")
print("=" * 70)