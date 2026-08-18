#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KG-CF 推荐算法离线评估脚本
==========================
功能：
1. 生成30名学生模拟数据
2. 划分训练集/测试集 (70%/30%)
3. 实现4种推荐方法对比：Random, Mastery, UserCF, KG-CF
4. 计算 Precision@5, Recall@5, HitRate@5, NDCG@5
5. 输出结果文件和推荐案例

用法: python tools/evaluate_kgcf.py
"""

import json, os, sys, random, math, itertools
from collections import defaultdict
from copy import deepcopy
from datetime import datetime, timedelta

random.seed(2026)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCE_DIR = os.path.join(BASE_DIR, "app", "resources")
TOOLS_DIR = os.path.join(BASE_DIR, "tools")
os.makedirs(RESOURCE_DIR, exist_ok=True)

# ============================================================
# 0. 加载真实资源数据和知识点信息
# ============================================================
def load_manifest():
    """加载资源清单，获取所有资源和知识点"""
    with open(os.path.join(RESOURCE_DIR, "resource_manifest.json"), "r", encoding="utf-8") as f:
        manifest = json.load(f)
    
    resources = []
    knowledge_points = {}
    
    for item in manifest.get("files", []):
        rid = "teaching_materials/" + item["filename"]
        kp_name = item["knowledge_point"]
        rtype = item["type"].lower()
        if rtype == "video":
            rtype = "video"
        elif rtype == "ppt":
            rtype = "ppt"
        else:
            rtype = "doc"
        
        resources.append({
            "resource_id": rid,
            "filename": rid,
            "knowledge_point": kp_name,
            "type": rtype,
            "teacher": item.get("teacher", ""),
        })
        
        # Extract knowledge point code
        parts = kp_name.split()
        kp_code = parts[0] if parts else kp_name
        
        if kp_code not in knowledge_points:
            knowledge_points[kp_code] = {
                "code": kp_code,
                "name": kp_name,
                "chapter": int(kp_code.split(".")[0]) if kp_code[0].isdigit() else 0,
            }
    
    return resources, knowledge_points


# ============================================================
# 1. 学生数据定义
# ============================================================

# 30名学生定义
STUDENT_DEFS = [
    # (student_num, name, class_name, gender, type, grade_level)
    ("3220602001", "刘大", "软件工程1班", "男", "excellent", 1),
    ("3220602002", "陈二", "软件工程1班", "男", "medium", 1),
    ("3220602003", "张三", "软件工程1班", "男", "excellent", 1),
    ("3220602004", "李四", "软件工程1班", "女", "medium", 1),
    ("3220602005", "王五", "软件工程1班", "男", "medium", 1),
    ("3220602006", "赵六", "软件工程1班", "男", "weak", 1),
    ("3220602007", "周七", "软件工程1班", "女", "video_pref", 1),
    ("3220602008", "吴八", "软件工程1班", "男", "excellent", 1),
    ("3220602009", "郑九", "软件工程1班", "女", "medium", 1),
    ("3220602010", "冯十", "软件工程1班", "男", "medium", 1),
    ("3220602011", "陈琳", "软件工程2班", "女", "weak", 1),
    ("3220602012", "黄明", "软件工程2班", "男", "doc_pref", 1),
    ("3220602013", "林芳", "软件工程2班", "女", "practice", 1),
    ("3220602014", "何强", "软件工程2班", "男", "excellent", 1),
    ("3220602015", "罗伟", "软件工程2班", "男", "medium", 1),
    ("3220602016", "梁静", "软件工程2班", "女", "video_pref", 1),
    ("3220602017", "宋涛", "软件工程2班", "男", "weak", 1),
    ("3220602018", "唐洁", "软件工程2班", "女", "medium", 1),
    ("3220602019", "韩冰", "软件工程2班", "男", "video_pref", 1),
    ("3220602020", "曹洋", "软件工程2班", "男", "doc_pref", 1),
    ("3220602021", "许晴", "软件工程3班", "女", "excellent", 1),
    ("3220602022", "邓超", "软件工程3班", "男", "practice", 1),
    ("3220602023", "彭飞", "软件工程3班", "男", "medium", 1),
    ("3220602024", "蒋丽", "软件工程3班", "女", "weak", 1),
    ("3220602025", "沈杰", "软件工程3班", "男", "video_pref", 1),
    ("3220602026", "姚远", "软件工程3班", "男", "cold_start", 1),
    ("3220602027", "姜悦", "软件工程3班", "女", "doc_pref", 1),
    ("3220602028", "范明", "软件工程3班", "男", "practice", 1),
    ("3220602029", "方芳", "软件工程3班", "女", "weak", 1),
    ("3220602030", "石磊", "软件工程3班", "男", "cold_start", 1),
]

# 学生类型与掌握度参数
STUDENT_TYPE_PARAMS = {
    "excellent":      {"mastery": (0.70, 0.95), "complete": (0.65, 0.90), "wrong": (0.02, 0.08),  "video_pref": 0.35, "ppt_pref": 0.40, "doc_pref": 0.25},
    "medium":         {"mastery": (0.40, 0.72), "complete": (0.35, 0.65), "wrong": (0.10, 0.25),  "video_pref": 0.40, "ppt_pref": 0.35, "doc_pref": 0.25},
    "weak":           {"mastery": (0.15, 0.42), "complete": (0.10, 0.35), "wrong": (0.25, 0.50),  "video_pref": 0.45, "ppt_pref": 0.30, "doc_pref": 0.25},
    "video_pref":     {"mastery": (0.35, 0.70), "complete": (0.30, 0.65), "wrong": (0.08, 0.20),  "video_pref": 0.55, "ppt_pref": 0.25, "doc_pref": 0.20},
    "doc_pref":       {"mastery": (0.35, 0.70), "complete": (0.30, 0.65), "wrong": (0.08, 0.20),  "video_pref": 0.20, "ppt_pref": 0.50, "doc_pref": 0.30},
    "practice":       {"mastery": (0.30, 0.65), "complete": (0.20, 0.50), "wrong": (0.15, 0.40),  "video_pref": 0.30, "ppt_pref": 0.30, "doc_pref": 0.40},
    "cold_start":     {"mastery": (0.10, 0.30), "complete": (0.03, 0.12), "wrong": (0.30, 0.60),  "video_pref": 0.33, "ppt_pref": 0.33, "doc_pref": 0.34},
}


def generate_student_data(resources, knowledge_points):
    """生成30名学生完整模拟数据"""
    kps = list(knowledge_points.values())
    kps.sort(key=lambda x: (x["chapter"], x["code"]))
    kp_codes = [k["code"] for k in kps]
    
    students = {}
    base_date = datetime(2025, 9, 1)
    
    for idx, (student_num, name, class_name, gender, stype, grade) in enumerate(STUDENT_DEFS):
        params = STUDENT_TYPE_PARAMS[stype]
        student_id = student_num + name  # full_id format
        rng = random.Random(2026 + idx)
        
        # --- 掌握度 ---
        mastery = {}
        # Base mastery depends on chapter: ch1 > ch2 > ch3
        chapter_decay = {1: (0, 0), 2: (0.05, 0.08), 3: (0.10, 0.15)}
        for kp in kps:
            ch = kp["chapter"]
            decay = chapter_decay.get(ch, (0, 0))
            base = rng.uniform(*params["mastery"])
            # More advanced chapters have slightly lower mastery
            adj = base - rng.uniform(*decay)
            mastery[kp["code"]] = round(max(0.0, min(1.0, adj)), 3)
        
        # --- 资源学习记录 + train/test split ---
        all_records = []
        
        # Select resources to "complete" based on mastery and type preference
        pref_map = {"video": params["video_pref"], "ppt": params["ppt_pref"], "doc": params["doc_pref"]}
        
        for res in resources:
            rid = res["resource_id"]
            kp_name = res["knowledge_point"]
            kp_code = kp_name.split()[0] if kp_name else ""
            rtype = res["type"]
            
            if kp_code not in mastery:
                continue
            
            kp_mastery = mastery[kp_code]
            
            # Probability of completing this resource depends on:
            # - Mastery of the knowledge point (lower mastery = higher chance to study)
            # - Resource type preference
            # - Cold start students complete very few
            if stype == "cold_start":
                base_prob = params["complete"][0]
            else:
                base_prob = params["complete"][0] + (params["complete"][1] - params["complete"][0]) * (1 - kp_mastery)
            
            type_mult = pref_map.get(rtype, 0.33) / 0.33
            prob = base_prob * type_mult
            prob = max(0.03, min(0.95, prob))
            
            if rng.random() < prob:
                # Assign a completion date (spread over the semester)
                days_offset = rng.randint(0, 110)
                comp_date = base_date + timedelta(days=days_offset)
                
                record = {
                    "resource_id": rid,
                    "knowledge_id": kp_code,
                    "knowledge_name": kp_name,
                    "type": rtype,
                    "teacher": res["teacher"],
                    "completed": True,
                    "completed_at": comp_date.strftime("%Y-%m-%d"),
                    "timestamp": comp_date.strftime("%Y-%m-%dT%H:%M:%S"),
                }
                all_records.append(record)
        
        # Sort by completion date
        all_records.sort(key=lambda r: r["completed_at"])
        
        # 70/30 split by time
        split_idx = int(len(all_records) * 0.7)
        if stype == "cold_start":
            # Ensure cold start students still have at least some test records
            split_idx = max(1, min(split_idx, len(all_records) - 1)) if len(all_records) > 1 else 0
        
        train_records = all_records[:split_idx]
        test_records = all_records[split_idx:]
        
        # --- 答题记录 ---
        answer_records = []
        wrong_questions = []
        questions_data = load_questions_clean()
        all_questions = questions_data.get("questions", [])
        
        # Assign questions based on mastered KPs
        for q in all_questions:
            qid = q.get("id", "")
            kp_name = q.get("knowledge_point", "")
            kp_code = kp_name.split()[0] if kp_name else ""
            if kp_code not in mastery:
                continue
            
            kp_mastery = mastery[kp_code]
            # Probability of answering correctly scales with mastery
            correct_prob = 0.2 + kp_mastery * 0.7
            
            # How many times to answer
            n_attempts = max(0, int(rng.gauss(3 * (1 - kp_mastery + 0.2), 1.5)))
            if stype == "practice":
                n_attempts = int(n_attempts * 1.8)  # Practice-oriented do more
            elif stype == "cold_start":
                n_attempts = max(0, int(n_attempts * 0.2))
            
            for _ in range(n_attempts):
                correct = rng.random() < correct_prob
                days_offset = rng.randint(0, 110)
                ans_date = base_date + timedelta(days=days_offset)
                answer_records.append({
                    "question_id": qid,
                    "knowledge_id": kp_code,
                    "correct": correct,
                    "timestamp": ans_date.strftime("%Y-%m-%dT%H:%M:%S"),
                })
            
            # Wrong questions tracking
            wrong_count = sum(1 for a in answer_records if a["question_id"] == qid and not a["correct"])
            if wrong_count > 0:
                wrong_questions.append({
                    "question_id": qid,
                    "knowledge_id": kp_code,
                    "knowledge_name": kp_name,
                    "wrong_count": wrong_count,
                })
        
        # --- 资源类型偏好 ---
        total_res = len(all_records)
        if total_res > 0:
            video_count = sum(1 for r in all_records if r["type"] == "video")
            ppt_count = sum(1 for r in all_records if r["type"] == "ppt")
            doc_count = sum(1 for r in all_records if r["type"] == "doc")
            resource_type_preference = {
                "video": round(video_count / total_res, 3),
                "ppt": round(ppt_count / total_res, 3),
                "doc": round(doc_count / total_res, 3),
            }
        else:
            resource_type_preference = {"video": 0.33, "ppt": 0.33, "doc": 0.34}
        
        students[student_id] = {
            "student_id": student_id,
            "student_num": student_num,
            "name": name,
            "class_name": class_name,
            "gender": gender,
            "type": stype,
            "password": "123456",
            "knowledge_mastery": mastery,
            "answer_records": answer_records,
            "resource_learning_records": all_records,
            "wrong_questions": wrong_questions,
            "resource_type_preference": resource_type_preference,
            "train_records": train_records,
            "test_records": test_records,
        }
    
    return students


def load_questions_clean():
    """加载题目数据"""
    try:
        with open(os.path.join(RESOURCE_DIR, "questions.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"questions": []}


# ============================================================
# 2. 生成资源学习效果事件
# ============================================================
def generate_resource_effects(students, resources):
    """生成资源学习效果事件"""
    effects = []
    for sid, stu in students.items():
        for rec in stu.get("resource_learning_records", []):
            rid = rec["resource_id"]
            kp_code = rec["knowledge_id"]
            mastery = stu["knowledge_mastery"].get(kp_code, 0.5)
            
            # Simulate mastery gain from completing a resource
            before = max(0.0, mastery - random.uniform(0.05, 0.15))
            gain = random.uniform(0.03, 0.25)
            after = min(1.0, before + gain)
            
            effects.append({
                "student_id": sid,
                "resource_id": rid,
                "teacher_name": rec.get("teacher", ""),
                "knowledge_id": kp_code,
                "before_mastery": round(before, 3),
                "after_mastery": round(after, 3),
                "mastery_gain": round(after - before, 3),
                "after_accuracy": round(random.uniform(0.6, 1.0), 3),
                "created_at": rec.get("completed_at", "") + "T12:00:00",
            })
    return effects


# ============================================================
# 3. 保存数据文件
# ============================================================
def save_data_files(students, resources, knowledge_points):
    """保存所有数据文件"""
    # kgcf_students_30.json
    with open(os.path.join(RESOURCE_DIR, "kgcf_students_30.json"), "w", encoding="utf-8") as f:
        json.dump(students, f, ensure_ascii=False, indent=2)
    
    # kgcf_train.json / kgcf_test.json
    train = {}
    test = {}
    for sid, stu in students.items():
        train[sid] = {
            "student_id": stu["student_id"],
            "student_num": stu["student_num"],
            "name": stu["name"],
            "type": stu["type"],
            "knowledge_mastery": stu["knowledge_mastery"],
            "train_records": stu["train_records"],
            "answer_records": stu["answer_records"],
            "wrong_questions": stu["wrong_questions"],
            "resource_type_preference": stu["resource_type_preference"],
        }
        test[sid] = {
            "student_id": stu["student_id"],
            "student_num": stu["student_num"],
            "name": stu["name"],
            "type": stu["type"],
            "test_records": stu["test_records"],
        }
    
    with open(os.path.join(RESOURCE_DIR, "kgcf_train.json"), "w", encoding="utf-8") as f:
        json.dump(train, f, ensure_ascii=False, indent=2)
    with open(os.path.join(RESOURCE_DIR, "kgcf_test.json"), "w", encoding="utf-8") as f:
        json.dump(test, f, ensure_ascii=False, indent=2)
    
    # resource_effect_events.json
    effects = generate_resource_effects(students, resources)
    with open(os.path.join(RESOURCE_DIR, "resource_effect_events.json"), "w", encoding="utf-8") as f:
        json.dump(effects, f, ensure_ascii=False, indent=2)
    
    print(f"[数据文件] 已生成:")
    print(f"  kgcf_students_30.json: {len(students)} 名学生")
    print(f"  kgcf_train.json: {sum(len(s['train_records']) for s in students.values())} 条训练记录")
    print(f"  kgcf_test.json: {sum(len(s['test_records']) for s in students.values())} 条测试记录")
    print(f"  resource_effect_events.json: {len(effects)} 条效果事件")


# ============================================================
# 4. 推荐算法实现
# ============================================================
def build_profile_vector(student_train, all_resources):
    """构建学生画像向量"""
    mastery = student_train.get("knowledge_mastery", {})
    train_recs = student_train.get("train_records", [])
    wrong = student_train.get("wrong_questions", [])
    type_pref = student_train.get("resource_type_preference", {})
    
    # M_u: knowledge mastery vector
    M_u = {k: v for k, v in mastery.items()}
    
    # R_u: resource completion vector
    completed_rids = set(r["resource_id"] for r in train_recs)
    R_u = {}
    for res in all_resources:
        rid = res["resource_id"]
        R_u[rid] = 1.0 if rid in completed_rids else 0.0
    
    # W_u: wrong question distribution
    W_u = {}
    for wq in wrong:
        kp = wq.get("knowledge_id", "")
        W_u[kp] = W_u.get(kp, 0) + wq.get("wrong_count", 0)
    
    # B_u: resource type preference
    B_u = dict(type_pref)
    
    return {"M_u": M_u, "R_u": R_u, "W_u": W_u, "B_u": B_u}


def cosine_sim(vec1, vec2):
    """计算余弦相似度"""
    keys = set(vec1.keys()) | set(vec2.keys())
    dot = sum(vec1.get(k, 0) * vec2.get(k, 0) for k in keys)
    norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
    norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


def student_similarity(prof1, prof2):
    """基于画像向量的学生相似度"""
    # Combine all sub-vectors
    def flatten(p):
        v = {}
        for k, val in p.get("M_u", {}).items():
            v["M_" + k] = val
        for k, val in p.get("W_u", {}).items():
            v["W_" + k] = min(1.0, val / 10.0)
        for k, val in p.get("B_u", {}).items():
            v["B_" + k] = val
        return v
    
    return cosine_sim(flatten(prof1), flatten(prof2))


def get_similar_students(sid, train_data, profiles, resources, top_k=5):
    """获取Top-K相似学生"""
    sims = []
    for other_sid in profiles:
        if other_sid == sid:
            continue
        sim = student_similarity(profiles[sid], profiles[other_sid])
        if sim > 0.01:
            sims.append((other_sid, sim))
    sims.sort(key=lambda x: x[1], reverse=True)
    return sims[:top_k]


# ============ 方法1: Random ============
def recommend_random(student_id, train_data, resources, kps, top_n=5):
    """随机推荐"""
    rid_list = [r["resource_id"] for r in resources]
    recs = random.sample(rid_list, min(top_n, len(rid_list)))
    return [{
        "resource_id": rid,
        "score": round(random.uniform(0.1, 0.5), 3),
        "method": "Random",
        "explain": "随机推荐",
    } for rid in recs]


# ============ 方法2: Mastery (仅薄弱知识点) ============
def recommend_mastery(student_id, train_data, resources, kps, top_n=5):
    """只根据薄弱知识点推荐，不使用协同过滤"""
    student = train_data.get(student_id, {})
    mastery = student.get("knowledge_mastery", {})
    
    # Find weakest KPs
    weak_kps = [(kp, score) for kp, score in mastery.items() if score < 0.6]
    weak_kps.sort(key=lambda x: x[1])
    
    recs = []
    seen_rids = set()
    
    for kp_code, _ in weak_kps:
        if len(recs) >= top_n:
            break
        # Find resources for this KP
        kp_resources = [r for r in resources if r["knowledge_point"].split()[0] == kp_code]
        for r in kp_resources:
            if r["resource_id"] not in seen_rids:
                recs.append({
                    "resource_id": r["resource_id"],
                    "score": round((1.0 - mastery.get(kp_code, 0.5)) * 0.9, 3),
                    "method": "Mastery",
                    "explain": f"薄弱知识点: {kp_code}",
                    "knowledge_id": kp_code,
                    "knowledge_name": r["knowledge_point"],
                })
                seen_rids.add(r["resource_id"])
                if len(recs) >= top_n:
                    break
    
    # Fill with random if not enough
    for r in resources:
        if len(recs) >= top_n:
            break
        if r["resource_id"] not in seen_rids:
            recs.append({
                "resource_id": r["resource_id"],
                "score": 0.1,
                "method": "Mastery",
                "explain": "兜底推荐",
            })
    
    return recs[:top_n]


# ============ 方法3: UserCF ============
def recommend_usercf(student_id, train_data, resources, kps, top_n=5):
    """只根据相似学生推荐，不使用知识图谱候选约束"""
    student = train_data.get(student_id, {})
    mastery = student.get("knowledge_mastery", {})
    
    profiles = {}
    for sid, stu in train_data.items():
        profiles[sid] = build_profile_vector(stu, resources)
    
    if student_id not in profiles:
        return recommend_mastery(student_id, train_data, resources, kps, top_n)
    
    similar = get_similar_students(student_id, train_data, profiles, resources, top_k=5)
    
    if not similar:
        return recommend_mastery(student_id, train_data, resources, kps, top_n)
    
    # Collect resources from similar students with scores
    scored_resources = {}
    sim_map = {s[0]: s[1] for s in similar}
    
    for other_sid, sim in similar:
        other_train = train_data.get(other_sid, {})
        other_recs = other_train.get("train_records", [])
        for rec in other_recs:
            rid = rec["resource_id"]
            if rid not in scored_resources:
                scored_resources[rid] = 0.0
            scored_resources[rid] += sim  # simple sum
    
    # Sort by score
    sorted_rids = sorted(scored_resources.items(), key=lambda x: x[1], reverse=True)
    
    recs = []
    for rid, cf_score in sorted_rids:
        if len(recs) >= top_n:
            break
        # Find resource info
        res_info = next((r for r in resources if r["resource_id"] == rid), None)
        kp_code = res_info["knowledge_point"].split()[0] if res_info else ""
        kp_mastery = mastery.get(kp_code, 0.5)
        
        recs.append({
            "resource_id": rid,
            "score": round(cf_score / len(similar), 3),
            "method": "UserCF",
            "explain": f"相似学生也学习了此资源",
            "knowledge_id": kp_code,
            "knowledge_name": res_info["knowledge_point"] if res_info else "",
        })
    
    # Fill with mastery-based if not enough
    if len(recs) < top_n:
        mastery_recs = recommend_mastery(student_id, train_data, resources, kps, top_n - len(recs))
        for r in mastery_recs:
            r["method"] = "UserCF+Mastery"
            recs.append(r)
    
    return recs[:top_n]


# ============ 方法4: KG-CF ============
def build_kg_relations(knowledge_points):
    """构建知识图谱关系（依赖关系）"""
    relations = {}
    kps_by_chapter = defaultdict(list)
    
    for kp in knowledge_points.values():
        code = kp["code"]
        ch = kp["chapter"]
        kps_by_chapter[ch].append(code)
        
        parts = code.split(".")
        
        # PREREQUISITE: section X -> chapter X+1
        if len(parts) == 2:
            major = parts[1]
            # Previous section in same chapter
            if int(major) > 1:
                prereq_code = f"{parts[0]}.{int(major) - 1}"
                if prereq_code in knowledge_points:
                    relations.setdefault(code, []).append({"code": prereq_code, "rel": "PREREQUISITE_OF"})
        
        if len(parts) == 3:
            # Subsection within section
            minor = parts[2]
            section_code = f"{parts[0]}.{parts[1]}"
            if minor == "1":
                if section_code in knowledge_points:
                    relations.setdefault(code, []).append({"code": section_code, "rel": "BELONGS_TO"})
            else:
                prev_sub = f"{parts[0]}.{parts[1]}.{int(minor) - 1}"
                if prev_sub in knowledge_points:
                    relations.setdefault(code, []).append({"code": prev_sub, "rel": "PREREQUISITE_OF"})
    
    # Chapter-level prerequisites
    for ch in sorted(kps_by_chapter.keys()):
        if ch > 1 and ch - 1 in kps_by_chapter:
            prev_ch = kps_by_chapter[ch - 1]
            curr_ch = kps_by_chapter[ch]
            for prev_kp in prev_ch[-2:]:
                for curr_kp in curr_ch[:2]:
                    relations.setdefault(curr_kp, []).append({"code": prev_kp, "rel": "PREREQUISITE_OF"})
    
    return relations


def get_prerequisites(kp_code, kg_relations, depth=2):
    """获取知识点的先修知识点"""
    prereqs = []
    visited = {kp_code}
    queue = [(kp_code, 0)]
    
    while queue:
        code, d = queue.pop(0)
        if d >= depth:
            continue
        for rel in kg_relations.get(code, []):
            if rel["code"] not in visited:
                visited.add(rel["code"])
                prereqs.append(rel["code"])
                queue.append((rel["code"], d + 1))
    
    return prereqs


def recommend_kgcf(student_id, train_data, resources, kps, top_n=5):
    """KG-CF: 知识图谱约束 + 协同过滤"""
    student = train_data.get(student_id, {})
    mastery = student.get("knowledge_mastery", {})
    kg_relations = build_kg_relations(kps)
    
    profiles = {}
    for sid, stu in train_data.items():
        profiles[sid] = build_profile_vector(stu, resources)
    
    # Step 1: Find weak knowledge points
    weak_kps = [(kp, score) for kp, score in mastery.items() if score < 0.6]
    weak_kps.sort(key=lambda x: x[1])
    
    # Step 2: KG candidate generation - weak KPs + their prerequisites
    candidate_kps = set()
    for kp_code, _ in weak_kps[:5]:
        candidate_kps.add(kp_code)
        prereqs = get_prerequisites(kp_code, kg_relations, depth=2)
        for pr in prereqs:
            pr_mastery = mastery.get(pr, 0.5)
            if pr_mastery < 0.6:
                candidate_kps.add(pr)
    
    # Find resources for candidate KPs
    candidate_resources = []
    for kp_code in candidate_kps:
        kp_resources = [r for r in resources if r["knowledge_point"].split()[0] == kp_code]
        for r in kp_resources:
            candidate_resources.append({
                **r,
                "knowledge_code": kp_code,
                "mastery": mastery.get(kp_code, 0.5),
                "candidate_reason": "薄弱知识点" if kp_code in dict(weak_kps) else "先修知识点",
            })
    
    if not candidate_resources:
        return recommend_mastery(student_id, train_data, resources, kps, top_n)
    
    # Step 3: CF ranking
    if student_id in profiles:
        similar = get_similar_students(student_id, train_data, profiles, resources, top_k=5)
        
        if similar:
            # Score by similar students
            scored = {}
            for other_sid, sim in similar:
                other_train = train_data.get(other_sid, {})
                other_recs = other_train.get("train_records", [])
                for rec in other_recs:
                    rid = rec["resource_id"]
                    scored[rid] = scored.get(rid, 0) + sim
            
            for cr in candidate_resources:
                cr["cf_score"] = scored.get(cr["resource_id"], 0) / max(len(similar), 1)
                kp_mastery = cr.get("mastery", 0.5)
                cr["kg_score"] = (1.0 - kp_mastery) * 0.5
                cr["final_score"] = 0.55 * cr["kg_score"] + 0.45 * cr["cf_score"]
            
            candidate_resources.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        else:
            # No similar students: use mastery
            for cr in candidate_resources:
                kp_mastery = cr.get("mastery", 0.5)
                cr["final_score"] = 1.0 - kp_mastery
            candidate_resources.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    else:
        for cr in candidate_resources:
            cr["final_score"] = 1.0 - cr.get("mastery", 0.5)
        candidate_resources.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    
    # Build results
    recs = []
    seen = set()
    for cr in candidate_resources:
        if len(recs) >= top_n:
            break
        rid = cr["resource_id"]
        if rid in seen:
            continue
        seen.add(rid)
        
        kp_code = cr.get("knowledge_code", "")
        kp_mastery = cr.get("mastery", 0.5)
        reason = cr.get("candidate_reason", "")
        
        explain_parts = []
        explain_parts.append(f"当前\"{kp_code}\"掌握度为{kp_mastery:.0%}")
        if "先修" in reason:
            explain_parts.append("该资源对应先修知识点，建议优先学习")
        elif reason == "薄弱知识点":
            explain_parts.append("属于薄弱知识点，需要加强学习")
        if cr.get("cf_score", 0) > 0.01:
            explain_parts.append("基于相似学生学习效果排序")
        
        recs.append({
            "resource_id": rid,
            "title": cr.get("filename", rid),
            "type": cr.get("type", "资源"),
            "score": round(cr.get("final_score", 0.5), 3),
            "method": "KG-CF",
            "explain": "；".join(explain_parts),
            "knowledge_id": kp_code,
            "knowledge_name": cr.get("knowledge_point", ""),
            "cf_score": round(cr.get("cf_score", 0), 3),
            "kg_score": round(cr.get("kg_score", 0), 3),
        })
    
    # Fill with mastery-based if not enough
    if len(recs) < top_n:
        mastery_recs = recommend_mastery(student_id, train_data, resources, kps, top_n - len(recs))
        for r in mastery_recs:
            r["method"] = "KG-CF+兜底"
            recs.append(r)
    
    return recs[:top_n]


# ============================================================
# 5. 评估指标
# ============================================================
def compute_metrics(recs_for_student, test_data, top_k=5):
    """
    计算 Precision@K, Recall@K, HitRate@K, NDCG@K
    
    recs_for_student: {student_id: [recommended_resource_ids]}
    test_data: {student_id: {"test_records": [...]}}
    """
    precisions = []
    recalls = []
    hit_rates = []
    ndcgs = []
    
    for sid, recs in recs_for_student.items():
        test_recs = test_data.get(sid, {}).get("test_records", [])
        test_rids = set(r["resource_id"] for r in test_recs)
        
        if not test_rids:
            continue
        
        rec_rids = [r["resource_id"] for r in recs[:top_k]]
        
        # Hit count
        hits = sum(1 for rid in rec_rids if rid in test_rids)
        
        # Precision@K
        prec = hits / len(rec_rids) if rec_rids else 0
        precisions.append(prec)
        
        # Recall@K
        rec = hits / len(test_rids) if test_rids else 0
        recalls.append(rec)
        
        # HitRate@K
        hit_rates.append(1.0 if hits > 0 else 0.0)
        
        # NDCG@K
        dcg = 0
        idcg = 0
        # Ideal: all test resources at top
        ideal_hits = min(len(test_rids), top_k)
        for i in range(ideal_hits):
            idcg += 1.0 / math.log2(i + 2)
        
        for i, rid in enumerate(rec_rids):
            if rid in test_rids:
                dcg += 1.0 / math.log2(i + 2)
        
        ndcg = dcg / idcg if idcg > 0 else 0
        ndcgs.append(ndcg)
    
    return {
        "Precision@{}".format(top_k): round(sum(precisions) / len(precisions), 4) if precisions else 0,
        "Recall@{}".format(top_k): round(sum(recalls) / len(recalls), 4) if recalls else 0,
        "HitRate@{}".format(top_k): round(sum(hit_rates) / len(hit_rates), 4) if hit_rates else 0,
        "NDCG@{}".format(top_k): round(sum(ndcgs) / len(ndcgs), 4) if ndcgs else 0,
    }


# ============================================================
# 6. 主评估流程
# ============================================================
def run_evaluation():
    print("=" * 60)
    print("  KG-CF 推荐算法离线评估")
    print("=" * 60)
    
    # Load resources
    print("\n[1/6] 加载资源清单...")
    resources, knowledge_points = load_manifest()
    print(f"  资源数: {len(resources)}")
    print(f"  知识点数: {len(knowledge_points)}")
    
    # Generate student data
    print("\n[2/6] 生成30名学生数据...")
    students = generate_student_data(resources, knowledge_points)
    type_counts = defaultdict(int)
    for s in students.values():
        type_counts[s["type"]] += 1
    print(f"  学生类型分布: {dict(type_counts)}")
    
    # Save data files
    print("\n[3/6] 保存数据文件...")
    save_data_files(students, resources, knowledge_points)
    
    # Load train/test split
    train_data = {}
    test_data = {}
    for sid, stu in students.items():
        train_data[sid] = {
            "student_id": stu["student_id"],
            "student_num": stu["student_num"],
            "name": stu["name"],
            "type": stu["type"],
            "knowledge_mastery": stu["knowledge_mastery"],
            "train_records": stu["train_records"],
            "answer_records": stu["answer_records"],
            "wrong_questions": stu["wrong_questions"],
            "resource_type_preference": stu["resource_type_preference"],
        }
        test_data[sid] = {
            "student_id": stu["student_id"],
            "student_num": stu["student_num"],
            "name": stu["name"],
            "type": stu["type"],
            "test_records": stu["test_records"],
        }
    
    # Run 4 methods
    print("\n[4/6] 运行4种推荐方法...")
    methods = {
        "Random": recommend_random,
        "Mastery": recommend_mastery,
        "UserCF": recommend_usercf,
        "KG-CF": recommend_kgcf,
    }
    
    all_recs = {}
    all_metrics = {}
    
    for method_name, method_fn in methods.items():
        print(f"  {method_name}...")
        recs_for_student = {}
        for sid in students:
            recs_for_student[sid] = method_fn(sid, train_data, resources, knowledge_points, top_n=5)
        all_recs[method_name] = recs_for_student
        
        metrics = compute_metrics(recs_for_student, test_data, top_k=5)
        all_metrics[method_name] = metrics
        print(f"    Precision@5={metrics['Precision@5']:.4f}  Recall@5={metrics['Recall@5']:.4f}  HitRate@5={metrics['HitRate@5']:.4f}  NDCG@5={metrics['NDCG@5']:.4f}")
    
    # Print comparison table
    print("\n[5/6] 对比结果表:")
    print("-" * 62)
    print(f"| {'Method':<10} | {'Precision@5':<12} | {'Recall@5':<10} | {'HitRate@5':<10} | {'NDCG@5':<8} |")
    print("|" + "-" * 11 + "|" + "-" * 14 + "|" + "-" * 12 + "|" + "-" * 12 + "|" + "-" * 10 + "|")
    for method_name in ["Random", "Mastery", "UserCF", "KG-CF"]:
        m = all_metrics[method_name]
        print(f"| {method_name:<10} | {m['Precision@5']:<12.4f} | {m['Recall@5']:<10.4f} | {m['HitRate@5']:<10.4f} | {m['NDCG@5']:<8.4f} |")
    print("-" * 62)
    
    # Save CSV results
    csv_path = os.path.join(RESOURCE_DIR, "kgcf_eval_results.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("Method,Precision@5,Recall@5,HitRate@5,NDCG@5\n")
        for method_name in ["Random", "Mastery", "UserCF", "KG-CF"]:
            m = all_metrics[method_name]
            f.write(f"{method_name},{m['Precision@5']},{m['Recall@5']},{m['HitRate@5']},{m['NDCG@5']}\n")
    print(f"\n  结果保存至: {csv_path}")
    
    # Generate recommendation cases
    print("\n[6/6] 生成推荐案例...")
    case_students = {
        "3220602001刘大": "优秀学生",
        "3220602004李四": "中等学生",
        "3220602006赵六": "薄弱学生",
    }
    
    cases = []
    for sid, s_type in case_students.items():
        stu = students.get(sid)
        if not stu:
            continue
        
        mastery = stu["knowledge_mastery"]
        weak_kps = [(k, v) for k, v in mastery.items() if v < 0.6]
        weak_kps.sort(key=lambda x: x[1])
        
        kgcf_recs = all_recs["KG-CF"].get(sid, [])
        test_rids = set(r["resource_id"] for r in stu.get("test_records", []))
        hit_rids = [r["resource_id"] for r in kgcf_recs if r["resource_id"] in test_rids]
        
        cases.append({
            "student_name": stu["name"],
            "student_type": s_type,
            "weak_knowledge_points": [{"code": k, "mastery": round(v, 3)} for k, v in weak_kps[:5]],
            "recommendations": kgcf_recs[:5],
            "hit_test_resources": hit_rids,
        })
    
    cases_path = os.path.join(RESOURCE_DIR, "kgcf_recommend_cases.json")
    with open(cases_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, ensure_ascii=False, indent=2)
    print(f"  案例保存至: {cases_path}")
    
    # Print cases
    for case in cases:
        print(f"\n  【{case['student_name']}】({case['student_type']})")
        wkps = [(k['code'], '{:.1%}'.format(k['mastery'])) for k in case['weak_knowledge_points'][:3]]
        print(f"    薄弱知识点: {wkps}")
        if case["hit_test_resources"]:
            print(f"    命中测试集资源: {case['hit_test_resources']}")
        else:
            print(f"    命中测试集资源: (无)")
        print(f"    KG-CF推荐Top-3:")
        for rec in case["recommendations"][:3]:
            reason = rec.get("explain", "").replace("；", "; ")
            print(f"      - {rec['resource_id'][:50]} (score={rec['score']}) [{reason}]")
    
    print("\n" + "=" * 60)
    print("  评估完成！")
    print("=" * 60)
    
    return all_metrics, all_recs


if __name__ == "__main__":
    run_evaluation()