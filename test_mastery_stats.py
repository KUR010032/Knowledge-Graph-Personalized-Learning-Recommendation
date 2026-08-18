# -*- coding: utf-8 -*-
"""
知识点掌握度统计测试报告
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "app"))

import app as app_module

app_module._MASTERY_TREE_CACHE = {}
app_module._ANSWER_RECORDS_CACHE = None

calculate_mastery_tree = app_module.calculate_mastery_tree
normalize_student_id = app_module.normalize_student_id
get_mastery_status = app_module.get_mastery_status
STUDENTS = app_module.STUDENTS

def main():
    print("=" * 80)
    print("知识点掌握度统计测试报告")
    print("=" * 80)
    
    test_students = [
        ("3220602001", "刘大"),
        ("3220602004", "李四"),
        ("3220602006", "赵六")
    ]
    
    all_zero_count = 0
    
    for sid, name in test_students:
        print(f"\n{'='*80}")
        print(f"学生: {name} ({sid})")
        print("=" * 80)
        
        full_id = normalize_student_id(sid)
        score_map, detail_map, name_map, children = calculate_mastery_tree(full_id)
        
        leaf_codes = [code for code in name_map.keys() if code.count(".") >= 2]
        
        print(f"\n知识点统计 (共{len(leaf_codes)}个):")
        
        zero_count = 0
        for i, code in enumerate(sorted(leaf_codes), 1):
            detail = detail_map.get(code, {})
            mastery = detail.get("mastery", 0)
            total_questions = detail.get("total_questions", 0)
            answered_questions = detail.get("answered_questions", 0)
            correct_questions = detail.get("correct_questions", 0)
            
            status = get_mastery_status(mastery)
            stats_display = f"{status} · {correct_questions}/{answered_questions}/{total_questions} 题"
            
            if answered_questions == 0 and total_questions > 0:
                zero_count += 1
            
            if i <= 10 or name == "赵六":
                print(f"{i:2d}. {code:8s} {stats_display}")
        
        if zero_count > 0:
            print(f"\n⚠ 警告: {zero_count}个知识点未做题 (0/0/{total_questions})")
            all_zero_count += zero_count
        else:
            print(f"\n✓ 所有知识点都有做题记录")
    
    print("\n" + "=" * 80)
    print("总结报告")
    print("=" * 80)
    
    print("\n1. 刘大前10个知识点统计:")
    sid = normalize_student_id("3220602001")
    score_map, detail_map, name_map, children = calculate_mastery_tree(sid)
    leaf_codes = [code for code in name_map.keys() if code.count(".") >= 2]
    for i, code in enumerate(sorted(leaf_codes)[:10], 1):
        detail = detail_map.get(code, {})
        mastery = detail.get("mastery", 0)
        total_questions = detail.get("total_questions", 0)
        answered_questions = detail.get("answered_questions", 0)
        correct_questions = detail.get("correct_questions", 0)
        status = get_mastery_status(mastery)
        print(f"   {i:2d}. {code:8s} {status} · {correct_questions}/{answered_questions}/{total_questions} 题")
    
    print("\n2. 李四薄弱知识点统计:")
    sid = normalize_student_id("3220602004")
    score_map, detail_map, name_map, children = calculate_mastery_tree(sid)
    weak_points = [(code, detail_map.get(code, {})) for code in name_map.keys() 
                   if code.count(".") >= 2 and detail_map.get(code, {}).get("mastery", 0) < 0.6]
    weak_points.sort(key=lambda x: x[1].get("mastery", 0))
    for i, (code, detail) in enumerate(weak_points[:10], 1):
        mastery = detail.get("mastery", 0)
        total_questions = detail.get("total_questions", 0)
        answered_questions = detail.get("answered_questions", 0)
        correct_questions = detail.get("correct_questions", 0)
        status = get_mastery_status(mastery)
        print(f"   {i:2d}. {code:8s} {status} · {correct_questions}/{answered_questions}/{total_questions} 题 (掌握度{mastery*100:.1f}%)")
    
    print("\n3. 赵六基础知识点统计:")
    sid = normalize_student_id("3220602006")
    score_map, detail_map, name_map, children = calculate_mastery_tree(sid)
    basic_points = [(code, detail_map.get(code, {})) for code in name_map.keys() 
                    if code.count(".") >= 2 and code.startswith("1.")]
    basic_points.sort(key=lambda x: x[0])
    for i, (code, detail) in enumerate(basic_points[:10], 1):
        mastery = detail.get("mastery", 0)
        total_questions = detail.get("total_questions", 0)
        answered_questions = detail.get("answered_questions", 0)
        correct_questions = detail.get("correct_questions", 0)
        status = get_mastery_status(mastery)
        print(f"   {i:2d}. {code:8s} {status} · {correct_questions}/{answered_questions}/{total_questions} 题")
    
    print("\n4. 是否还有异常0/0:")
    if all_zero_count > 0:
        print(f"   ⚠ 是，共有{all_zero_count}个知识点未做题")
        print("   说明: 部分知识点题库中无题目或学生未做题")
    else:
        print("   ✓ 否，所有知识点都有做题记录")
    
    print("\n5. 修改了哪些函数:")
    print("   (1) load_answer_records: 新增函数")
    print("       * 从answer_records.json加载答题记录")
    print("       * 按学生ID和知识点ID统计已做题数和正确数")
    print("       * 使用缓存提高性能")
    print("")
    print("   (2) calculate_mastery_tree: 修改统计逻辑")
    print("       * 使用answer_records替代question_history")
    print("       * 添加total_questions字段（题库总数）")
    print("       * 添加answered_questions字段（已做题数）")
    print("       * 添加correct_questions字段（正确数）")
    print("       * 从题库获取knowledge_id字段")
    print("")
    print("   (3) fallback_flow_mastery_data: 修改显示逻辑")
    print("       * 调用calculate_mastery_tree获取统计数据")
    print("       * 生成stats_display字段：状态 · 正确数/已做题数/总题数 题")
    print("       * 添加total_questions、answered_questions、correct_questions字段")

if __name__ == "__main__":
    main()
