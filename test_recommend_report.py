# -*- coding: utf-8 -*-
"""
测试推荐算法，生成报告
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))

import app as app_module

kgcf_recommend_data = app_module.kgcf_recommend_data
load_questions_clean = app_module.load_questions_clean
_json_load = app_module._json_load
EXERCISE_SETS_FILE = app_module.EXERCISE_SETS_FILE
STUDENTS = app_module.STUDENTS
normalize_student_id = app_module.normalize_student_id

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
    print("推荐算法测试报告")
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
        
        student_type = result.get("student", {}).get("type", "medium")
        avg_mastery = result.get("avg_mastery", 0)
        targets = result.get("targets", [])
        
        print(f"\n学生类型: {student_type}")
        print(f"平均掌握度: {avg_mastery*100:.1f}%")
        print(f"推荐类型: {result.get('recommend_type', '')}")
        
        print(f"\n推荐知识点 ({len(targets)}个):")
        
        for i, target in enumerate(targets, 1):
            code = target.get("code", "")
            kp_name = target.get("name", "")
            mastery = target.get("mastery", 0)
            status = target.get("status", "")
            reason = target.get("reason", "")
            
            print(f"\n{i}. {code} {kp_name}")
            print(f"   掌握度: {mastery*100:.1f}% ({status})")
            print(f"   推荐理由: {reason[:60]}...")
            
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
                print(f"   目标知识点: {ex_analysis['target_kp']}")
                print(f"   题目总数: {ex_analysis['total_questions']}")
                print(f"   知识点分布:")
                
                for kp, count in sorted(ex_analysis["kp_distribution"].items(), key=lambda x: -x[1]):
                    pct = count / ex_analysis["total_questions"] * 100
                    is_target = "★" if kp == ex_analysis["target_kp"] else " "
                    print(f"     {is_target} {kp}: {count}题 ({pct:.1f}%)")
                
                print(f"   目标知识点匹配率: {ex_analysis['target_match_rate']:.1f}%")
                
                if ex_analysis["target_match_rate"] < 50:
                    print(f"   ⚠ 警告: 目标知识点题目占比过低!")
                    mismatch_found = True
                
                non_target_kps = [kp for kp in ex_analysis["kp_distribution"].keys() if kp != ex_analysis["target_kp"]]
                if non_target_kps:
                    print(f"   非目标知识点: {non_target_kps}")
    
    print("\n" + "=" * 60)
    print("总结报告")
    print("=" * 60)
    
    print("\n1. 刘大5个推荐知识点、资源难度、题目难度:")
    liuda = all_results.get("3220602001", {})
    print(f"   学生类型: {liuda.get('student', {}).get('type', '')}")
    for i, t in enumerate(liuda.get("targets", [])[:5], 1):
        print(f"   {i}. {t.get('code', '')} - 掌握度{t.get('mastery', 0)*100:.1f}%")
        res_diffs = [r.get("difficulty", "") for r in t.get("resources", [])]
        print(f"      资源难度: {res_diffs}")
    
    print("\n2. 李四5个推荐知识点、资源难度、题目难度:")
    lisi = all_results.get("3220602004", {})
    print(f"   学生类型: {lisi.get('student', {}).get('type', '')}")
    for i, t in enumerate(lisi.get("targets", [])[:5], 1):
        print(f"   {i}. {t.get('code', '')} - 掌握度{t.get('mastery', 0)*100:.1f}%")
        res_diffs = [r.get("difficulty", "") for r in t.get("resources", [])]
        print(f"      资源难度: {res_diffs}")
    
    print("\n3. 赵六5个推荐知识点、资源难度、题目难度:")
    zhaoliu = all_results.get("3220602006", {})
    print(f"   学生类型: {zhaoliu.get('student', {}).get('type', '')}")
    for i, t in enumerate(zhaoliu.get("targets", [])[:5], 1):
        print(f"   {i}. {t.get('code', '')} - 掌握度{t.get('mastery', 0)*100:.1f}%")
        res_diffs = [r.get("difficulty", "") for r in t.get("resources", [])]
        print(f"      资源难度: {res_diffs}")
    
    print("\n4. 每套练习的target_knowledge_id和题目knowledge_id分布:")
    for sid, name in test_students:
        result = all_results.get(sid, {})
        print(f"\n   {name}:")
        for t in result.get("targets", [])[:3]:
            ex_id = t.get("exercise_set_id", "")
            if ex_id:
                ex_analysis = analyze_exercise_set(ex_id)
                print(f"   - {t.get('code', '')}: 目标{ex_analysis['target_kp']}, 匹配率{ex_analysis['target_match_rate']:.1f}%")
    
    print(f"\n5. 是否还存在推荐知识点和练习题错配:")
    if mismatch_found:
        print("   ⚠ 是，存在错配问题")
    else:
        print("   ✓ 否，所有练习题与推荐知识点匹配良好")
    
    print("\n6. 修改了哪些推荐函数:")
    print("   - _kgcf_identify_targets: 修改目标选择逻辑")
    print("     * 薄弱学生: 优先推荐第1章和第2章基础知识")
    print("     * 中等学生: 优先推荐薄弱知识点和先修知识点")
    print("     * 优秀学生: 优先推荐局部未完全掌握的知识点和第3章难点")
    print("   - _kgcf_find_resources_for_kp: 修改资源排序分数")
    print("     * 添加难度适配分数 (0.15)")
    print("     * 资源总分 = 0.30*知识点匹配 + 0.20*掌握度需求 + 0.15*难度适配 + 0.15*教师偏好 + 0.10*相似学生效果 + 0.10*资源学习效果")
    print("   - generate_exercise_set: 修改练习题生成逻辑")
    print("     * 目标知识点题目占比从60%提升到70%")
    print("     * 添加难度偏好，根据学生类型选择题目难度")
    print("     * 添加difficulty_plan字段")

if __name__ == "__main__":
    main()
