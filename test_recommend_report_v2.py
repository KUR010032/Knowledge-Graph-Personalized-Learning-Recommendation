# -*- coding: utf-8 -*-
"""
推荐算法测试报告（清除缓存版本）
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))

import json

RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "resources")
EXERCISE_SETS_FILE = os.path.join(RESOURCE_DIR, "exercise_sets.json")

import app as app_module

app_module._MASTERY_TREE_CACHE = {}
app_module._KGCF_RECOMMEND_CACHE = {}

kgcf_recommend_data = app_module.kgcf_recommend_data
normalize_student_id = app_module.normalize_student_id
load_questions_clean = app_module.load_questions_clean
STUDENTS = app_module.STUDENTS

def _json_load(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default if default is not None else {}

def get_student_name(sid):
    for uid, info in STUDENTS.items():
        if normalize_student_id(uid) == sid or info.get("full_id", "").startswith(sid):
            return info.get("name", "")
    return ""

def analyze_exercise_set(exercise_set_id):
    all_sets = _json_load(EXERCISE_SETS_FILE, {})
    ex_set = all_sets.get(exercise_set_id, {})
    
    target_kp = ex_set.get("target_knowledge_id", "")
    question_ids = ex_set.get("question_ids", [])
    
    all_questions = load_questions_clean().get("questions", [])
    q_map = {str(q.get("id")): q for q in all_questions}
    
    kp_distribution = {}
    for qid in question_ids:
        q = q_map.get(str(qid))
        if q:
            kp = q.get("knowledge_id", q.get("knowledge_point", ""))
            kp_code = kp.split()[0] if kp else ""
            kp_distribution[kp_code] = kp_distribution.get(kp_code, 0) + 1
    
    return {
        "target_kp": target_kp,
        "total_questions": len(question_ids),
        "kp_distribution": kp_distribution,
        "target_match_rate": kp_distribution.get(target_kp, 0) / len(question_ids) * 100 if question_ids else 0
    }

def main():
    print("=" * 60)
    print("推荐算法测试报告（清除缓存版本）")
    print("=" * 60)
    
    test_students = [
        ("3220602001", "刘大"),
        ("3220602004", "李四"),
        ("3220602006", "赵六")
    ]
    
    all_results = {}
    mismatch_found = False
    
    for sid, name in test_students:
        print(f"\n{'='*60}")
        print(f"学生: {name} ({sid})")
        print("=" * 60)
        
        result = kgcf_recommend_data(sid, max_targets=5)
        all_results[sid] = result
        
        student_type = result.get("student", {}).get("type", "")
        avg_mastery = result.get("avg_mastery", 0)
        
        print(f"\n学生类型: {student_type}")
        print(f"平均掌握度: {avg_mastery*100:.1f}%")
        
        targets = result.get("targets", [])
        
        for i, target in enumerate(targets, 1):
            code = target.get("code", "")
            kp_name = target.get("name", "")
            mastery = target.get("mastery", 0)
            status = target.get("status", "")
            reason = target.get("reason", "")
            
            print(f"\n{i}. {code} {kp_name}")
            print(f"   掌握度: {mastery*100:.1f}% ({status})")
            print(f"   推荐理由: {reason[:80]}...")
            
            resources = target.get("resources", [])
            print(f"\n   推荐资源 ({len(resources)}个):")
            
            resource_difficulties = []
            for j, res in enumerate(resources[:3], 1):
                res_kp = res.get("knowledge_id", "")
                res_kp_name = res.get("knowledge_name", "")
                res_type = res.get("type", "")
                res_diff = res.get("difficulty", "")
                res_teacher = res.get("teacher", "")
                res_relation = res.get("relation_label", "")
                
                resource_difficulties.append(res_diff)
                
                print(f"   {j}. {res_kp} {res_kp_name}")
                print(f"      类型: {res_type}, 难度: {res_diff}, 教师: {res_teacher}")
                print(f"      关系: {res_relation}")
            
            if student_type == "excellent":
                expected_diff = ["中等", "困难"]
            elif student_type == "medium":
                expected_diff = ["基础", "中等"]
            else:
                expected_diff = ["基础"]
            
            diff_match = any(d in expected_diff for d in resource_difficulties)
            print(f"\n   资源难度适配: {'✓' if diff_match else '✗'} (期望: {expected_diff}, 实际: {resource_difficulties})")
            
            exercise_set_id = target.get("exercise_set_id", "")
            if exercise_set_id:
                ex_analysis = analyze_exercise_set(exercise_set_id)
                
                print(f"\n   配套练习分析:")
                print(f"   练习集ID: {exercise_set_id}")
                print(f"   目标知识点: {ex_analysis['target_kp']}")
                print(f"   题目总数: {ex_analysis['total_questions']}")
                print(f"   知识点分布:")
                
                for kp, count in sorted(ex_analysis["kp_distribution"].items(), key=lambda x: -x[1]):
                    pct = count / ex_analysis["total_questions"] * 100 if ex_analysis["total_questions"] > 0 else 0
                    print(f"       {kp}: {count}题 ({pct:.1f}%)")
                
                print(f"   目标知识点匹配率: {ex_analysis['target_match_rate']:.1f}%")
                
                if ex_analysis["target_match_rate"] < 50:
                    print(f"   ⚠ 警告: 目标知识点题目占比过低!")
                    mismatch_found = True
                    non_target = [kp for kp in ex_analysis["kp_distribution"].keys() if kp != ex_analysis["target_kp"]]
                    if non_target:
                        print(f"   非目标知识点: {non_target}")

    print("\n" + "=" * 60)
    print("总结报告")
    print("=" * 60)
    
    print("\n1. 刘大5个推荐知识点、资源难度、题目难度:")
    for sid, name in test_students:
        if name == "刘大":
            result = all_results[sid]
            student_type = result.get("student", {}).get("type", "")
            print(f"   学生类型: {student_type}")
            for i, target in enumerate(result.get("targets", [])[:5], 1):
                code = target.get("code", "")
                resources = target.get("resources", [])
                difficulties = [r.get("difficulty", "") for r in resources]
                print(f"   {i}. {code} - 掌握度{target.get('mastery', 0)*100:.1f}%")
                print(f"      资源难度: {difficulties}")
    
    print("\n2. 李四5个推荐知识点、资源难度、题目难度:")
    for sid, name in test_students:
        if name == "李四":
            result = all_results[sid]
            student_type = result.get("student", {}).get("type", "")
            print(f"   学生类型: {student_type}")
            for i, target in enumerate(result.get("targets", [])[:5], 1):
                code = target.get("code", "")
                resources = target.get("resources", [])
                difficulties = [r.get("difficulty", "") for r in resources]
                print(f"   {i}. {code} - 掌握度{target.get('mastery', 0)*100:.1f}%")
                print(f"      资源难度: {difficulties}")
    
    print("\n3. 赵六5个推荐知识点、资源难度、题目难度:")
    for sid, name in test_students:
        if name == "赵六":
            result = all_results[sid]
            student_type = result.get("student", {}).get("type", "")
            print(f"   学生类型: {student_type}")
            for i, target in enumerate(result.get("targets", [])[:5], 1):
                code = target.get("code", "")
                resources = target.get("resources", [])
                difficulties = [r.get("difficulty", "") for r in resources]
                print(f"   {i}. {code} - 掌握度{target.get('mastery', 0)*100:.1f}%")
                print(f"      资源难度: {difficulties}")
    
    print("\n4. 每套练习的target_knowledge_id和题目knowledge_id分布:")
    for sid, name in test_students:
        print(f"\n   {name}:")
        result = all_results[sid]
        for target in result.get("targets", [])[:5]:
            code = target.get("code", "")
            exercise_set_id = target.get("exercise_set_id", "")
            if exercise_set_id:
                ex_analysis = analyze_exercise_set(exercise_set_id)
                print(f"   - {code}: 目标{ex_analysis['target_kp']}, 匹配率{ex_analysis['target_match_rate']:.1f}%")
    
    print("\n5. 是否还存在推荐知识点和练习题错配:")
    if mismatch_found:
        print("   ⚠ 是，存在错配问题")
    else:
        print("   ✓ 否，所有练习题与推荐知识点匹配")
    
    print("\n6. 修改了哪些推荐函数:")
    print("   - _kgcf_classify_student: 修改学生分类逻辑")
    print("     * 根据答题数量和掌握度综合判断学生类型")
    print("     * 优秀学生: practiced_count >= 25 and good_count >= 15")
    print("     * 中等学生: practiced_count >= 10 and good_count >= 5")
    print("   - _kgcf_find_resources_for_kp: 添加难度过滤")
    print("     * 薄弱学生过滤困难资源")
    print("   - generate_exercise_set: 修改题目知识点提取逻辑")
    print("     * 优先使用knowledge_id字段")

if __name__ == "__main__":
    main()
