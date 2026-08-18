# -*- coding: utf-8 -*-
import json
import os
import shutil
import random
from collections import defaultdict
from datetime import datetime, timedelta

BASE_DIR = r"c:\Users\zzlyx\Desktop\lunwen5.31\app\resources"
STUDENT_DATA_DIR = r"c:\Users\zzlyx\Desktop\lunwen5.31\studentdata"

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BASE_DIR, f"backup_before_rebuild_answer_records_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "answer_records.json",
        "wrong_book.json",
        "students_mastery.json",
        "exercise_sets.json"
    ]
    
    for fname in files_to_backup:
        src = os.path.join(BASE_DIR, fname)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, fname)
            shutil.copy2(src, dst)
            print(f"已备份: {fname}")
    
    if os.path.exists(STUDENT_DATA_DIR):
        student_backup = os.path.join(backup_dir, "studentdata")
        shutil.copytree(STUDENT_DATA_DIR, student_backup)
        print("已备份: studentdata")
    
    print(f"备份目录: {backup_dir}")
    return backup_dir

def load_questions():
    path = os.path.join(BASE_DIR, "questions.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", [])
    
    q_map = {}
    kp_map = defaultdict(list)
    for q in questions:
        qid = q.get("id") or q.get("question_id")
        kid = q.get("knowledge_id")
        if qid:
            q_map[qid] = q
            if kid:
                kp_map[kid].append(q)
    
    return questions, q_map, kp_map

def get_students():
    students = [
        {"id": "3220602001", "name": "刘大", "type": "优秀"},
        {"id": "3220602004", "name": "李四", "type": "中等"},
        {"id": "3220602006", "name": "赵六", "type": "冷启动"},
    ]
    
    other_students = [
        {"id": "3220602002", "name": "王二", "type": "优秀"},
        {"id": "3220602003", "name": "张三", "type": "良好"},
        {"id": "3220602005", "name": "王五", "type": "良好"},
        {"id": "3220602007", "name": "孙七", "type": "良好"},
        {"id": "3220602008", "name": "周八", "type": "中等"},
        {"id": "3220602009", "name": "吴九", "type": "中等"},
        {"id": "3220602010", "name": "郑十", "type": "中等"},
        {"id": "3220602011", "name": "钱十一", "type": "良好"},
        {"id": "3220602012", "name": "陈十二", "type": "优秀"},
        {"id": "3220602013", "name": "林十三", "type": "中等"},
        {"id": "3220602014", "name": "黄十四", "type": "良好"},
        {"id": "3220602015", "name": "赵十五", "type": "中等"},
        {"id": "3220602016", "name": "孙十六", "type": "薄弱"},
        {"id": "3220602017", "name": "周十七", "type": "良好"},
        {"id": "3220602018", "name": "吴十八", "type": "中等"},
        {"id": "3220602019", "name": "郑十九", "type": "优秀"},
        {"id": "3220602020", "name": "钱二十", "type": "良好"},
        {"id": "3220602021", "name": "陈二一", "type": "薄弱"},
        {"id": "3220602022", "name": "林二二", "type": "中等"},
        {"id": "3220602023", "name": "黄二三", "type": "良好"},
        {"id": "3220602024", "name": "赵二四", "type": "薄弱"},
        {"id": "3220602025", "name": "孙二五", "type": "中等"},
        {"id": "3220602026", "name": "周二六", "type": "良好"},
        {"id": "3220602027", "name": "吴二七", "type": "优秀"},
        {"id": "3220602028", "name": "郑二八", "type": "薄弱"},
        {"id": "3220602029", "name": "钱二九", "type": "中等"},
        {"id": "3220602030", "name": "陈三十", "type": "良好"},
    ]
    
    students.extend(other_students)
    return students

def get_student_profile(student_type):
    profiles = {
        "优秀": {"min_q": 200, "max_q": 280, "min_acc": 0.80, "max_acc": 0.92},
        "良好": {"min_q": 140, "max_q": 220, "min_acc": 0.68, "max_acc": 0.82},
        "中等": {"min_q": 80, "max_q": 160, "min_acc": 0.50, "max_acc": 0.68},
        "薄弱": {"min_q": 20, "max_q": 90, "min_acc": 0.30, "max_acc": 0.55},
        "冷启动": {"min_q": 10, "max_q": 35, "min_acc": 0.35, "max_acc": 0.55},
    }
    return profiles.get(student_type, profiles["中等"])

def generate_dates(start_date, end_date, count):
    if count <= 0:
        return []
    
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end - start).days + 1
    
    if count >= total_days:
        dates = []
        for i in range(total_days):
            dates.append(start + timedelta(days=i))
        extra = count - total_days
        for i in range(extra):
            dates.append(random.choice(dates[:total_days]))
    else:
        step = total_days / count
        dates = []
        for i in range(count):
            day_offset = int(i * step + random.uniform(0, step * 0.8))
            dates.append(start + timedelta(days=min(day_offset, total_days - 1)))
    
    random.shuffle(dates)
    return dates

def generate_time():
    hour = random.randint(8, 22)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f"{hour:02d}:{minute:02d}:{second:02d}"

def generate_answer_records():
    print("\n【第一步】创建备份...")
    create_backup()
    
    print("\n【第二步】加载题库...")
    questions, q_map, kp_map = load_questions()
    print(f"题库总数: {len(questions)}")
    
    students = get_students()
    print(f"学生总数: {len(students)}")
    
    print("\n【第三步】生成答题记录...")
    all_records = []
    wrong_records = defaultdict(lambda: {"wrong_count": 0, "correct_count": 0, "wrong_times": [], "correct_times": []})
    
    sources = ["recommend_practice", "wrong_book", "chapter_practice", "daily_practice"]
    
    for student in students:
        sid = student["id"]
        stype = student["type"]
        profile = get_student_profile(stype)
        
        target_q = random.randint(profile["min_q"], profile["max_q"])
        target_acc = random.uniform(profile["min_acc"], profile["max_acc"])
        
        if stype == "优秀":
            target_acc = min(target_acc, 0.93)
        elif stype == "中等":
            target_acc = max(0.58, min(target_acc, 0.72))
        elif stype == "冷启动":
            target_acc = max(0.35, min(target_acc, 0.55))
        
        available_questions = list(q_map.keys())
        
        if stype == "冷启动":
            ch1_questions = [qid for qid in available_questions if q_map[qid].get("chapter_id") == "1"]
            if len(ch1_questions) >= target_q:
                selected_questions = random.sample(ch1_questions, target_q)
            else:
                selected_questions = ch1_questions + random.sample(
                    [q for q in available_questions if q not in ch1_questions],
                    min(target_q - len(ch1_questions), len(available_questions) - len(ch1_questions))
                )
        elif stype == "中等" and student["name"] == "李四":
            weak_kps = ["3.1.1", "3.1.2", "3.2.1", "3.2.2", "3.3.1", "3.4.1", "3.4.2", "3.4.3", "3.4.4"]
            weak_questions = []
            strong_questions = []
            for qid in available_questions:
                kid = q_map[qid].get("knowledge_id", "")
                if any(kp in kid for kp in weak_kps):
                    weak_questions.append(qid)
                else:
                    strong_questions.append(qid)
            
            weak_count = int(target_q * 0.4)
            strong_count = target_q - weak_count
            
            selected_weak = random.sample(weak_questions, min(weak_count, len(weak_questions)))
            selected_strong = random.sample(strong_questions, min(strong_count, len(strong_questions)))
            selected_questions = selected_weak + selected_strong
        else:
            selected_questions = random.sample(available_questions, min(target_q, len(available_questions)))
        
        dates = generate_dates("2026-03-01", "2026-05-31", len(selected_questions))
        
        correct_count = int(len(selected_questions) * target_acc)
        correct_indices = set(random.sample(range(len(selected_questions)), correct_count))
        
        for i, qid in enumerate(selected_questions):
            q = q_map[qid]
            kid = q.get("knowledge_id", "")
            correct_answer = q.get("answer", "")
            
            is_correct = i in correct_indices
            
            if is_correct:
                student_answer = correct_answer
            else:
                options = ["A", "B", "C", "D"]
                wrong_options = [o for o in options if o != correct_answer]
                student_answer = random.choice(wrong_options) if wrong_options else "A"
            
            date = dates[i] if i < len(dates) else dates[-1]
            time_str = generate_time()
            answered_at = f"{date.strftime('%Y-%m-%d')} {time_str}"
            
            record = {
                "record_id": f"ar_{sid}_{i+1:05d}",
                "student_id": sid,
                "question_id": qid,
                "knowledge_id": kid,
                "student_answer": student_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "answered_at": answered_at,
                "source": random.choice(sources)
            }
            all_records.append(record)
            
            key = (sid, qid)
            if is_correct:
                wrong_records[key]["correct_count"] += 1
                wrong_records[key]["correct_times"].append(answered_at)
            else:
                wrong_records[key]["wrong_count"] += 1
                wrong_records[key]["wrong_times"].append(answered_at)
    
    print(f"总答题记录数: {len(all_records)}")
    
    print("\n【第四步】生成错题记录...")
    wrong_book = []
    for (sid, qid), data in wrong_records.items():
        if data["wrong_count"] > 0:
            q = q_map.get(qid, {})
            kid = q.get("knowledge_id", "")
            
            last_wrong = max(data["wrong_times"]) if data["wrong_times"] else None
            last_correct = max(data["correct_times"]) if data["correct_times"] else None
            
            if data["correct_count"] >= 2:
                status = "mastered"
            elif data["correct_count"] >= 1:
                status = "learning"
            else:
                status = "new"
            
            wrong_entry = {
                "student_id": sid,
                "question_id": qid,
                "knowledge_id": kid,
                "wrong_count": data["wrong_count"],
                "correct_count": data["correct_count"],
                "last_wrong_at": last_wrong,
                "last_correct_at": last_correct,
                "status": status
            }
            wrong_book.append(wrong_entry)
    
    print(f"错题记录数: {len(wrong_book)}")
    
    print("\n【第五步】保存数据...")
    
    answer_records_path = os.path.join(BASE_DIR, "answer_records.json")
    with open(answer_records_path, "w", encoding="utf-8") as f:
        json.dump({"records": all_records}, f, ensure_ascii=False, indent=2)
    print(f"已保存: answer_records.json")
    
    wrong_book_path = os.path.join(BASE_DIR, "wrong_book.json")
    with open(wrong_book_path, "w", encoding="utf-8") as f:
        json.dump({"wrong_book": wrong_book}, f, ensure_ascii=False, indent=2)
    print(f"已保存: wrong_book.json")
    
    print("\n" + "=" * 60)
    print("答题记录重建报告")
    print("=" * 60)
    
    print(f"\n1. questions.json 总题数: {len(questions)}")
    print(f"2. answer_records 总记录数: {len(all_records)}")
    
    student_stats = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in all_records:
        sid = r["student_id"]
        student_stats[sid]["total"] += 1
        if r["is_correct"]:
            student_stats[sid]["correct"] += 1
    
    for student in students:
        if student["name"] == "刘大":
            stats = student_stats[student["id"]]
            acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"\n3. 刘大做题数: {stats['total']}题, 正确率: {acc:.1f}%")
        elif student["name"] == "李四":
            stats = student_stats[student["id"]]
            acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"4. 李四做题数: {stats['total']}题, 正确率: {acc:.1f}%")
        elif student["name"] == "赵六":
            stats = student_stats[student["id"]]
            acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
            print(f"5. 赵六做题数: {stats['total']}题, 正确率: {acc:.1f}%")
    
    type_count = defaultdict(int)
    for student in students[3:]:
        type_count[student["type"]] += 1
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
    for r in all_records:
        if r["question_id"] not in q_map:
            missing_questions += 1
    print(f"8. 是否存在question_id找不到题目的答题记录: {'是' if missing_questions > 0 else '否'} (共{missing_questions}条)")
    
    print(f"\n9. wrong_book 总记录数: {len(wrong_book)}")
    
    print("\n" + "=" * 60)
    print("各学生做题统计")
    print("=" * 60)
    for student in students:
        stats = student_stats[student["id"]]
        acc = stats["correct"] / stats["total"] * 100 if stats["total"] > 0 else 0
        print(f"{student['name']} ({student['type']}): {stats['total']}题, 正确率{acc:.1f}%")

if __name__ == "__main__":
    random.seed(42)
    generate_answer_records()
