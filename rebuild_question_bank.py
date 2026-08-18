# -*- coding: utf-8 -*-
import json
import os
import shutil
import time
import random
import re
from collections import defaultdict
from datetime import datetime

BASE_DIR = r"c:\Users\zzlyx\Desktop\lunwen5.31\app\resources"

def create_backup():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(BASE_DIR, f"backup_before_rebuild_question_bank_{timestamp}")
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        "questions.json",
        "answer_records.json",
        "students_mastery.json",
        "wrong_book.json",
        "exercise_sets.json"
    ]
    
    for fname in files_to_backup:
        src = os.path.join(BASE_DIR, fname)
        if os.path.exists(src):
            dst = os.path.join(backup_dir, fname)
            shutil.copy2(src, dst)
            print(f"已备份: {fname}")
    
    print(f"备份目录: {backup_dir}")
    return backup_dir

def load_questions():
    path = os.path.join(BASE_DIR, "questions.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("questions", [])

def is_fake_question(q):
    options = q.get("options", [])
    fake_patterns = ["选项A", "选项B", "选项C", "选项D", "OptionA", "OptionB", "OptionC", "OptionD", "选项1", "选项2", "选项3", "选项4"]
    for opt in options:
        opt_text = opt.strip() if isinstance(opt, str) else str(opt).strip()
        for pattern in fake_patterns:
            if opt_text == pattern or opt_text.startswith(pattern + "。") or opt_text.startswith(pattern + " "):
                return True
        if len(opt_text) < 3:
            return True
    return False

def is_low_quality(q):
    stem = q.get("question", "") or q.get("stem", "") or q.get("title", "") or ""
    stem = stem.strip()
    
    if len(stem) < 10:
        return True
    
    vague_patterns = [
        r"^关于.*的是[（\(]\s*[）\)]$",
        r"^以下.*的是[（\(]\s*[）\)]$",
        r"^下列.*的是[（\(]\s*[）\)]$",
        r"^.*正确的是[（\(]\s*[）\)]$",
    ]
    for pattern in vague_patterns:
        if re.match(pattern, stem):
            if len(stem) < 25:
                return True
    
    explanation = q.get("explanation", "") or q.get("analysis", "") or ""
    explanation = explanation.strip()
    if not explanation or explanation in ["略", "无", "暂无", "待补充", "略。"]:
        return True
    
    return False

def is_duplicate(q, seen_stems):
    stem = q.get("question", "") or q.get("stem", "") or ""
    stem_normalized = re.sub(r'\s+', '', stem.lower())
    
    for seen in seen_stems:
        if stem_normalized == seen:
            return True
        if len(stem_normalized) > 20 and len(seen) > 20:
            if stem_normalized[:30] == seen[:30]:
                return True
    
    return False

def normalize_question(q, idx):
    kid = q.get("knowledge_id", "") or ""
    if not kid:
        kp = q.get("knowledge_point", "") or q.get("knowledge_name", "") or ""
        match = re.match(r'^([\d.]+)', kp)
        if match:
            kid = match.group(1)
    
    kname = q.get("knowledge_name", "") or q.get("knowledge_point", "") or ""
    kname = re.sub(r'^[\d.]+\s*', '', kname).strip()
    
    qtype = q.get("type", "") or q.get("question_type", "") or "single_choice"
    if qtype not in ["single_choice", "multiple_choice", "judge", "blank"]:
        qtype = "single_choice"
    
    diff = q.get("difficulty", "") or "中等"
    if diff not in ["基础", "中等", "困难"]:
        diff = "中等"
    
    stem = q.get("question", "") or q.get("stem", "") or q.get("title", "") or ""
    stem = stem.strip()
    
    options = q.get("options", [])
    normalized_opts = []
    for i, opt in enumerate(options):
        if isinstance(opt, str):
            opt = opt.strip()
            if not re.match(r'^[A-E][.、．]', opt):
                letters = ["A", "B", "C", "D", "E"]
                if i < len(letters):
                    opt = f"{letters[i]}. {opt}"
            normalized_opts.append(opt)
    
    answer = q.get("answer", "") or ""
    answer = answer.strip().upper()
    if "," in answer or "，" in answer:
        answer = answer.replace("，", ",").upper()
    
    explanation = q.get("explanation", "") or q.get("analysis", "") or ""
    explanation = explanation.strip()
    
    parts = kid.split(".") if kid else ["0"]
    ch_id = parts[0] if parts else "0"
    
    qid = q.get("id", "") or ""
    if not qid or not qid.startswith("q_"):
        kp_part = kid.replace(".", "_") if kid else "new"
        qid = f"q_{kp_part}_{idx:04d}"
    
    return {
        "question_id": qid,
        "id": qid,
        "knowledge_id": kid,
        "knowledge_name": f"{kid} {kname}" if kid and kname else kname or kid,
        "question_type": qtype,
        "type": qtype,
        "difficulty": diff,
        "stem": stem,
        "question": stem,
        "options": normalized_opts,
        "answer": answer,
        "explanation": explanation,
        "status": "enabled",
        "chapter_id": ch_id,
        "chapter_name": f"第{ch_id}章" if ch_id else "",
        "is_key": False,
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    }

def get_standard_knowledge_points():
    return {
        "1.1.1": "操作系统的概念",
        "1.1.2": "操作系统的发展历史",
        "1.1.3": "操作系统的基本功能",
        "1.1.4": "操作系统的特征",
        "1.2.1": "批处理系统",
        "1.2.2": "分时系统",
        "1.2.3": "实时系统",
        "1.3.1": "操作系统的接口",
        "1.4.1": "系统调用",
        "1.5.1": "操作系统的体系结构",
        "1.6.1": "Windows技术特性",
        "1.6.2": "Unix技术特性",
        "1.6.3": "Linux技术特性",
        "2.1.1": "单道程序的顺序执行",
        "2.1.2": "多道程序的并发执行",
        "2.2.1": "进程的概念",
        "2.2.2": "进程的状态与转换",
        "2.2.3": "进程控制块",
        "2.3.1": "进程控制",
        "2.3.2": "线程与进程的比较",
        "2.3.3": "线程的实现方式",
        "2.3.4": "线程调度激发",
        "2.4.1": "处理机调度层次",
        "2.4.2": "调度算法",
        "2.4.3": "调度算法评价",
        "3.1.1": "临界资源与临界区",
        "3.1.2": "互斥锁",
        "3.2.1": "信号量机制",
        "3.2.2": "用P、V操作实现同步",
        "3.3.1": "经典同步问题",
        "3.4.1": "死锁的概念",
        "3.4.2": "死锁产生条件",
        "3.4.3": "死锁处理策略",
        "3.4.4": "银行家算法",
        "3.4.5": "死锁检测与解除",
        "3.4.6": "死锁避免",
        "3.4.7": "活锁",
    }

def main():
    print("=" * 60)
    print("题库重建脚本")
    print("=" * 60)
    
    print("\n【第一步】创建备份...")
    backup_dir = create_backup()
    
    print("\n【第二步】加载现有题库...")
    all_questions = load_questions()
    print(f"原始题目总数: {len(all_questions)}")
    
    print("\n【第三步】分析知识点分布...")
    kp_count = defaultdict(int)
    for q in all_questions:
        kid = q.get("knowledge_id", "") or ""
        if not kid:
            kp = q.get("knowledge_point", "") or q.get("knowledge_name", "") or ""
            match = re.match(r'^([\d.]+)', kp)
            if match:
                kid = match.group(1)
        kp_count[kid] += 1
    
    print(f"原始知识点数量: {len(kp_count)}")
    
    standard_kps = get_standard_knowledge_points()
    print(f"标准知识点数量: {len(standard_kps)}")
    
    print("\n【第四步】筛选高质量题目...")
    seen_stems = set()
    filtered_questions = []
    fake_count = 0
    low_quality_count = 0
    duplicate_count = 0
    invalid_kp_count = 0
    
    for q in all_questions:
        if q.get("status") == "deleted":
            continue
        
        kid = q.get("knowledge_id", "") or ""
        if not kid:
            kp = q.get("knowledge_point", "") or q.get("knowledge_name", "") or ""
            match = re.match(r'^([\d.]+)', kp)
            if match:
                kid = match.group(1)
        
        if kid not in standard_kps:
            invalid_kp_count += 1
            continue
        
        if is_fake_question(q):
            fake_count += 1
            continue
        
        if is_low_quality(q):
            low_quality_count += 1
            continue
        
        stem = q.get("question", "") or q.get("stem", "") or ""
        stem_normalized = re.sub(r'\s+', '', stem.lower())
        if is_duplicate(q, seen_stems):
            duplicate_count += 1
            continue
        seen_stems.add(stem_normalized)
        
        filtered_questions.append(q)
    
    print(f"假题数量: {fake_count}")
    print(f"低质量题数量: {low_quality_count}")
    print(f"重复题数量: {duplicate_count}")
    print(f"无效知识点题数量: {invalid_kp_count}")
    print(f"筛选后题目数量: {len(filtered_questions)}")
    
    print("\n【第五步】按知识点和难度分布筛选...")
    questions_by_kp = defaultdict(list)
    for q in filtered_questions:
        kid = q.get("knowledge_id", "") or ""
        if not kid:
            kp = q.get("knowledge_point", "") or q.get("knowledge_name", "") or ""
            match = re.match(r'^([\d.]+)', kp)
            if match:
                kid = match.group(1)
        questions_by_kp[kid].append(q)
    
    target_per_kp = 30
    target_diff = {"基础": 11, "中等": 13, "困难": 5}
    
    final_questions = []
    kp_stats = {}
    
    for kid in standard_kps:
        kp_questions = questions_by_kp.get(kid, [])
        random.shuffle(kp_questions)
        
        by_diff = {"基础": [], "中等": [], "困难": []}
        for q in kp_questions:
            diff = q.get("difficulty", "") or "中等"
            if diff not in by_diff:
                diff = "中等"
            by_diff[diff].append(q)
        
        selected = []
        for diff, target in target_diff.items():
            available = by_diff.get(diff, [])
            count = min(len(available), target)
            selected.extend(available[:count])
        
        if len(selected) < target_per_kp:
            remaining = [q for q in kp_questions if q not in selected]
            need = target_per_kp - len(selected)
            selected.extend(remaining[:need])
        
        kp_stats[kid] = {
            "total": len(selected),
            "基础": len([q for q in selected if q.get("difficulty") == "基础"]),
            "中等": len([q for q in selected if q.get("difficulty") == "中等"]),
            "困难": len([q for q in selected if q.get("difficulty") == "困难"]),
            "single": len([q for q in selected if q.get("type") == "single_choice"]),
            "multiple": len([q for q in selected if q.get("type") == "multiple_choice"])
        }
        
        final_questions.extend(selected)
    
    print(f"最终题目数量: {len(final_questions)}")
    
    print("\n【第六步】统一字段格式...")
    normalized_questions = []
    for idx, q in enumerate(final_questions, 1):
        nq = normalize_question(q, idx)
        normalized_questions.append(nq)
    
    print("\n【第七步】保存新题库...")
    output_path = os.path.join(BASE_DIR, "questions.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"questions": normalized_questions}, f, ensure_ascii=False, indent=2)
    print(f"已保存: {output_path}")
    
    print("\n" + "=" * 60)
    print("题库重建报告")
    print("=" * 60)
    
    total = len(normalized_questions)
    print(f"\n1. 新题库总题数: {total}")
    print(f"2. 知识点数量: {len(standard_kps)}")
    
    print("\n3. 每个知识点题目数量统计:")
    print("-" * 50)
    for kid in sorted(standard_kps.keys()):
        stats = kp_stats.get(kid, {"total": 0})
        kname = standard_kps[kid]
        print(f"  {kid} {kname}: {stats['total']}题 (基础{stats['基础']}, 中等{stats['中等']}, 困难{stats['困难']})")
    
    base_count = sum(1 for q in normalized_questions if q["difficulty"] == "基础")
    mid_count = sum(1 for q in normalized_questions if q["difficulty"] == "中等")
    hard_count = sum(1 for q in normalized_questions if q["difficulty"] == "困难")
    
    print(f"\n4. 难度分布:")
    print(f"   基础: {base_count} ({base_count*100/total:.1f}%)")
    print(f"   中等: {mid_count} ({mid_count*100/total:.1f}%)")
    print(f"   困难: {hard_count} ({hard_count*100/total:.1f}%)")
    
    single_count = sum(1 for q in normalized_questions if q["question_type"] == "single_choice")
    multi_count = sum(1 for q in normalized_questions if q["question_type"] == "multiple_choice")
    other_count = total - single_count - multi_count
    
    print(f"\n5. 题型分布:")
    print(f"   单选: {single_count} ({single_count*100/total:.1f}%)")
    print(f"   多选: {multi_count} ({multi_count*100/total:.1f}%)")
    print(f"   其他: {other_count} ({other_count*100/total:.1f}%)")
    
    fake_remaining = 0
    for q in normalized_questions:
        if is_fake_question(q):
            fake_remaining += 1
    print(f"\n6. 是否还存在假题: {'是' if fake_remaining > 0 else '否'} (剩余{fake_remaining}道)")
    
    print(f"\n7. 随机5道题示例:")
    print("-" * 50)
    samples = random.sample(normalized_questions, min(5, len(normalized_questions)))
    for i, q in enumerate(samples, 1):
        print(f"\n【示例{i}】")
        print(f"  ID: {q['question_id']}")
        print(f"  知识点: {q['knowledge_id']} {q['knowledge_name']}")
        print(f"  题型: {q['question_type']} | 难度: {q['difficulty']}")
        print(f"  题干: {q['stem'][:80]}{'...' if len(q['stem']) > 80 else ''}")
        print(f"  选项: {', '.join(q['options'][:2])}...")
        print(f"  答案: {q['answer']}")
        print(f"  解析: {q['explanation'][:60]}{'...' if len(q['explanation']) > 60 else ''}")
    
    print("\n" + "=" * 60)
    print("题库重建完成!")
    print("=" * 60)

if __name__ == "__main__":
    random.seed(42)
    main()
