# -*- coding: utf-8 -*-
import json
import os
from collections import defaultdict

BASE_DIR = r"c:\Users\zzlyx\Desktop\lunwen5.31\app\resources"

def main():
    questions_path = os.path.join(BASE_DIR, "questions.json")
    with open(questions_path, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    questions = questions_data.get("questions", [])
    q_map = {q.get("id") or q.get("question_id"): q for q in questions}
    
    answer_records_path = os.path.join(BASE_DIR, "answer_records.json")
    with open(answer_records_path, "r", encoding="utf-8") as f:
        records_data = json.load(f)
    records = records_data.get("records", [])
    
    wrong_book_path = os.path.join(BASE_DIR, "wrong_book.json")
    with open(wrong_book_path, "r", encoding="utf-8") as f:
        wrong_data = json.load(f)
    wrong_book = wrong_data.get("wrong_book", [])
    
    student_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in records:
        sid = r["student_id"]
        student_stats[sid]["total"] += 1
        if r.get("is_correct"):
            student_stats[sid]["correct"] += 1
    
    print("=" * 60)
    print("答题记录重建验证报告")
    print("=" * 60)
    
    print(f"\n1. questions.json 总题数: {len(questions)}")
    print(f"2. answer_records 总记录数: {len(records)}")
    
    students_info = {
        "3220602001": "刘大",
        "3220602004": "李四",
        "3220602006": "赵六"
    }
    
    for sid, name in students_info.items():
        stats = student_stats[sid]
        if stats["total"] > 0:
            acc = stats["correct"] / stats["total"] * 100
        else:
            acc = 0
        print(f"\n{name}做题数: {stats['total']}题, 正确率: {acc:.1f}%")
    
    type_count = defaultdict(int)
    other_students = [
        ("3220602002", "王二", "优秀"),
        ("3220602003", "张三", "良好"),
        ("3220602005", "王五", "良好"),
        ("3220602007", "孙七", "良好"),
        ("3220602008", "周八", "中等"),
        ("3220602009", "吴九", "中等"),
        ("3220602010", "郑十", "中等"),
        ("3220602011", "钱十一", "良好"),
        ("3220602012", "陈十二", "优秀"),
        ("3220602013", "林十三", "中等"),
        ("3220602014", "黄十四", "良好"),
        ("3220602015", "赵十五", "中等"),
        ("3220602016", "孙十六", "薄弱"),
        ("3220602017", "周十七", "良好"),
        ("3220602018", "吴十八", "中等"),
        ("3220602019", "郑十九", "优秀"),
        ("3220602020", "钱二十", "良好"),
        ("3220602021", "陈二一", "薄弱"),
        ("3220602022", "林二二", "中等"),
        ("3220602023", "黄二三", "良好"),
        ("3220602024", "赵二四", "薄弱"),
        ("3220602025", "孙二五", "中等"),
        ("3220602026", "周二六", "良好"),
        ("3220602027", "吴二七", "优秀"),
        ("3220602028", "郑二八", "薄弱"),
        ("3220602029", "钱二九", "中等"),
        ("3220602030", "陈三十", "良好"),
    ]
    
    for sid, name, stype in other_students:
        type_count[stype] += 1
    
    print(f"\n6. 其他27名学生等级分布:")
    print(f"   优秀: {type_count['优秀']}人")
    print(f"   良好: {type_count['良好']}人")
    print(f"   中等: {type_count['中等']}人")
    print(f"   薄弱: {type_count['薄弱']}人")
    
    half_questions = len(questions) * 0.5
    abnormal = False
    for sid, stats in student_stats.items():
        if stats["total"] > half_questions:
            abnormal = True
            break
    print(f"\n7. 是否存在学生做题数超过题库总数50%的异常: {'是' if abnormal else '否'}")
    
    missing_questions = 0
    for r in records:
        if r["question_id"] not in q_map:
            missing_questions += 1
    print(f"8. 是否存在question_id找不到题目的答题记录: {'是' if missing_questions > 0 else '否'} (共{missing_questions}条)")
    
    print(f"\n9. wrong_book 总记录数: {len(wrong_book)}")
    
    print("\n" + "=" * 60)
    print("各学生详细统计")
    print("=" * 60)
    
    all_students = [
        ("3220602001", "刘大", "优秀"),
        ("3220602004", "李四", "中等"),
        ("3220602006", "赵六", "冷启动"),
    ] + other_students
    
    for sid, name, stype in all_students:
        stats = student_stats[sid]
        if stats["total"] > 0:
            acc = stats["correct"] / stats["total"] * 100
        else:
            acc = 0
        print(f"{name} ({stype}): {stats['total']}题, 正确率{acc:.1f}%")
    
    print("\n" + "=" * 60)
    print("数据一致性检查")
    print("=" * 60)
    
    max_questions = max(stats["total"] for stats in student_stats.values())
    min_questions = min(stats["total"] for stats in student_stats.values())
    print(f"最多做题数: {max_questions}题")
    print(f"最少做题数: {min_questions}题")
    print(f"平均做题数: {sum(stats['total'] for stats in student_stats.values()) / len(student_stats):.1f}题")
    
    print("\n时间分布检查:")
    dates = defaultdict(int)
    for r in records:
        date = r.get("answered_at", "")[:10]
        dates[date] += 1
    
    sorted_dates = sorted(dates.items())
    print(f"答题日期范围: {sorted_dates[0][0]} 到 {sorted_dates[-1][0]}")
    print(f"涉及天数: {len(dates)}天")
    print(f"平均每天做题: {len(records) / len(dates):.1f}题")

if __name__ == "__main__":
    main()
