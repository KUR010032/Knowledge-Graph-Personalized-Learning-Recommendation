import json
import os
import random
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCE_DIR = os.path.join(BASE_DIR, "resources", "teaching_materials")
STUDENTS_MASTERY_FILE = os.path.join(BASE_DIR, "resources", "students_mastery.json")
RESOURCE_MANIFEST_FILE = os.path.join(BASE_DIR, "resources", "teaching_materials", "resource_manifest.json")
KNOWLEDGE_GRAPH_FILE = os.path.join(BASE_DIR, "resources", "knowledge_graph.json")

valid_knowledge_points = [
    "1.1.1 基本概念",
    "1.1.2 计算机系统的视图",
    "1.1.3 操作系统的基本功能",
    "1.2 操作系统的形成和发展",
    "1.3 操作系统的分类",
    "1.4 操作系统的运行环境",
    "1.5 操作系统的结构",
    "1.6.1 现代操作系统技术特性",
    "1.6.2 UNIX技术特性",
    "1.6.3 Linux技术特性",
    "1.6.4 Windows Server技术特性",
    "2.1.1 单道程序的顺序执行",
    "2.1.2 多道程序的并发执行",
    "2.2.1 进程的概念",
    "2.2.2 进程的实体",
    "2.2.3 进程状态和转换",
    "2.2.4 进程控制",
    "2.3.1 线程的概念",
    "2.3.2 线程与进程的比较",
    "2.3.3 线程的实现",
    "2.3.4 线程调度激发",
    "2.4 多核、多线程与超线程",
    "2.5 进程、线程管理实例",
    "3.1.1 并发原理",
    "3.1.2 临界资源与临界区",
    "3.1.3 互斥的软、硬件实现方法",
    "3.1.4 信号量和P、V操作",
    "3.2.1 进程同步概念",
    "3.2.2 用P、V操作实现同步",
    "3.3.1 进程通信的类型",
    "3.3.2 进程通信中的问题",
    "3.3.3 消息传递",
    "3.4.1 死锁的概念",
    "3.4.2 死锁的必要条件",
    "3.4.3 死锁的防止",
    "3.4.4 死锁的避免",
    "3.4.5 死锁检测与恢复",
    "3.4.6 两阶段加锁",
    "3.4.7 活锁",
    "3.4.8 饥饿",
    "3.5.1 读者-写者问题",
    "3.5.2 哲学家进餐问题",
    "3.5.3 打瞌睡的理发师问题",
    "3.6 多核环境下的进程同步",
    "3.7 进程同步与通信实例",
]

def get_kp_code(kp_name):
    if not kp_name:
        return ""
    parts = kp_name.split()
    return parts[0] if parts else ""

def get_kp_chapter(kp_name):
    code = get_kp_code(kp_name)
    if code:
        return int(code.split('.')[0])
    return 0

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def get_student_type(student_id, mastery_data):
    if not mastery_data:
        return "cold_start"
    
    avg_mastery = sum(mastery_data.values()) / len(mastery_data) if mastery_data else 0
    
    mastered = sum(1 for v in mastery_data.values() if v >= 0.8)
    good = sum(1 for v in mastery_data.values() if 0.6 <= v < 0.8)
    learned = mastered + good
    
    if avg_mastery >= 0.65 or learned >= 30:
        return "excellent"
    elif avg_mastery >= 0.35 or learned >= 15:
        return "medium"
    else:
        return "weak"

def classify_knowledge_points(mastery_data):
    classified = {
        "mastered": [],
        "good": [],
        "need_practice": [],
        "not_learned": []
    }
    
    for kp in valid_knowledge_points:
        mastery = mastery_data.get(kp, 0)
        kp_info = {
            "name": kp,
            "code": get_kp_code(kp),
            "chapter": get_kp_chapter(kp),
            "mastery": mastery
        }
        
        if mastery == 0:
            classified["not_learned"].append(kp_info)
        elif mastery < 0.6:
            classified["need_practice"].append(kp_info)
        elif mastery < 0.8:
            classified["good"].append(kp_info)
        else:
            classified["mastered"].append(kp_info)
    
    for key in classified:
        classified[key].sort(key=lambda x: x["mastery"])
    
    return classified

def get_prerequisite_kps(kp_code):
    prereqs = []
    parts = kp_code.split('.')
    
    if len(parts) >= 3:
        parent_code = '.'.join(parts[:-1])
        for kp in valid_knowledge_points:
            if get_kp_code(kp) == parent_code:
                prereqs.append({"code": parent_code, "name": kp})
    
    if len(parts) >= 2:
        chapter = parts[0]
        section = parts[1]
        prev_section = str(int(section) - 1) if section.isdigit() and int(section) > 1 else None
        if prev_section:
            prev_code = f"{chapter}.{prev_section}"
            for kp in valid_knowledge_points:
                if get_kp_code(kp).startswith(prev_code):
                    prereqs.append({"code": get_kp_code(kp), "name": kp})
    
    return prereqs

def get_next_kps(kp_code):
    next_kps = []
    parts = kp_code.split('.')
    
    if len(parts) >= 2:
        chapter = parts[0]
        section = parts[1]
        next_section = str(int(section) + 1) if section.isdigit() else None
        if next_section:
            next_code = f"{chapter}.{next_section}"
            for kp in valid_knowledge_points:
                if get_kp_code(kp).startswith(next_code):
                    next_kps.append({"code": get_kp_code(kp), "name": kp})
    
    return next_kps

def get_related_kps(kp_code):
    related = []
    chapter = kp_code.split('.')[0] if kp_code else ""
    
    for kp in valid_knowledge_points:
        kp_c = get_kp_code(kp)
        if kp_c and kp_c != kp_code and kp_c.split('.')[0] == chapter:
            related.append({"code": kp_c, "name": kp})
    
    return related[:5]

def load_resources():
    manifest = load_json(RESOURCE_MANIFEST_FILE)
    resources = manifest.get('files', [])
    
    kp_resources = {}
    for res in resources:
        kp = res.get('knowledge_point', '')
        if kp not in kp_resources:
            kp_resources[kp] = []
        kp_resources[kp].append(res)
    
    return kp_resources

def recommend_for_excellent_student(student_id, mastery_data, classified, kp_resources):
    recommendations = []
    
    mastered_kps = classified["mastered"]
    good_kps = classified["good"]
    need_practice_kps = classified["need_practice"]
    
    target_kps = []
    
    for kp_info in need_practice_kps[:3]:
        target_kps.append({
            "kp": kp_info,
            "reason": "巩固提升",
            "priority": 1.0 - kp_info["mastery"]
        })
    
    for kp_info in good_kps[:2]:
        next_kps = get_next_kps(kp_info["code"])
        for next_kp in next_kps[:1]:
            next_mastery = mastery_data.get(next_kp["name"], 0)
            if next_mastery < 0.8:
                target_kps.append({
                    "kp": {"name": next_kp["name"], "code": next_kp["code"], "chapter": get_kp_chapter(next_kp["name"]), "mastery": next_mastery},
                    "reason": "进阶学习",
                    "priority": 0.8
                })
    
    for kp_info in mastered_kps[:2]:
        next_kps = get_next_kps(kp_info["code"])
        for next_kp in next_kps[:1]:
            next_mastery = mastery_data.get(next_kp["name"], 0)
            if next_mastery < 0.8:
                target_kps.append({
                    "kp": {"name": next_kp["name"], "code": next_kp["code"], "chapter": get_kp_chapter(next_kp["name"]), "mastery": next_mastery},
                    "reason": "后续知识点",
                    "priority": 0.7
                })
    
    target_kps.sort(key=lambda x: x["priority"], reverse=True)
    
    for target in target_kps[:5]:
        kp_name = target["kp"]["name"]
        kp_code = target["kp"]["code"]
        reason = target["reason"]
        
        resources = kp_resources.get(kp_name, [])
        if not resources:
            continue
        
        selected_resources = random.sample(resources, min(3, len(resources)))
        
        rec_resources = []
        for res in selected_resources:
            rec_resources.append({
                "resource_id": f"teaching_materials/{res['filename']}",
                "name": res['filename'],
                "type": res['type'],
                "teacher": res.get('teacher', ''),
                "knowledge_point": kp_name,
                "relation": "当前知识点" if reason == "巩固提升" else reason,
                "reason": f"该知识点掌握较好，建议学习后续内容或综合练习" if reason == "后续知识点" else f"该知识点已具备基础，建议通过相关资源巩固"
            })
        
        recommendations.append({
            "knowledge_point": kp_name,
            "knowledge_code": kp_code,
            "mastery": target["kp"]["mastery"],
            "status": "已掌握" if target["kp"]["mastery"] >= 0.8 else ("良好" if target["kp"]["mastery"] >= 0.6 else "需巩固"),
            "recommend_reason": f"该知识点掌握较好，建议学习后续内容或综合练习",
            "resources": rec_resources
        })
    
    return recommendations

def recommend_for_medium_student(student_id, mastery_data, classified, kp_resources):
    recommendations = []
    
    need_practice_kps = classified["need_practice"]
    not_learned_kps = classified["not_learned"]
    
    target_kps = []
    
    for kp_info in need_practice_kps:
        target_kps.append({
            "kp": kp_info,
            "reason": "查漏补缺",
            "priority": 1.0 - kp_info["mastery"]
        })
    
    for kp_info in not_learned_kps[:5]:
        prereqs = get_prerequisite_kps(kp_info["code"])
        prereq_mastered = all(mastery_data.get(p["name"], 0) >= 0.6 for p in prereqs)
        
        if prereq_mastered:
            target_kps.append({
                "kp": kp_info,
                "reason": "新知识点学习",
                "priority": 0.8
            })
        else:
            for prereq in prereqs:
                prereq_mastery = mastery_data.get(prereq["name"], 0)
                if prereq_mastery < 0.6:
                    target_kps.append({
                        "kp": {"name": prereq["name"], "code": prereq["code"], "chapter": get_kp_chapter(prereq["name"]), "mastery": prereq_mastery},
                        "reason": "先修补充",
                        "priority": 1.2 - prereq_mastery
                    })
    
    target_kps.sort(key=lambda x: x["priority"], reverse=True)
    
    for target in target_kps[:5]:
        kp_name = target["kp"]["name"]
        kp_code = target["kp"]["code"]
        reason = target["reason"]
        
        resources = kp_resources.get(kp_name, [])
        if not resources:
            continue
        
        selected_resources = random.sample(resources, min(3, len(resources)))
        
        rec_resources = []
        for res in selected_resources:
            rec_resources.append({
                "resource_id": f"teaching_materials/{res['filename']}",
                "name": res['filename'],
                "type": res['type'],
                "teacher": res.get('teacher', ''),
                "knowledge_point": kp_name,
                "relation": "当前知识点" if reason == "查漏补缺" else ("先修补充" if reason == "先修补充" else "新知识点"),
                "reason": f"该知识点掌握度较低，建议补充学习并练习"
            })
        
        recommendations.append({
            "knowledge_point": kp_name,
            "knowledge_code": kp_code,
            "mastery": target["kp"]["mastery"],
            "status": "需巩固" if target["kp"]["mastery"] > 0 else "未学习",
            "recommend_reason": f"该知识点掌握度较低，建议补充学习并练习",
            "resources": rec_resources
        })
    
    return recommendations

def recommend_for_weak_student(student_id, mastery_data, classified, kp_resources):
    recommendations = []
    
    need_practice_kps = classified["need_practice"]
    not_learned_kps = classified["not_learned"]
    
    target_kps = []
    
    chapter1_kps = [kp for kp in valid_knowledge_points if get_kp_chapter(kp) == 1]
    chapter2_kps = [kp for kp in valid_knowledge_points if get_kp_chapter(kp) == 2]
    
    for kp in chapter1_kps[:5]:
        mastery = mastery_data.get(kp, 0)
        if mastery < 0.6:
            target_kps.append({
                "kp": {"name": kp, "code": get_kp_code(kp), "chapter": 1, "mastery": mastery},
                "reason": "基础入门",
                "priority": 1.0 - mastery
            })
    
    for kp_info in need_practice_kps:
        if kp_info["chapter"] <= 2:
            target_kps.append({
                "kp": kp_info,
                "reason": "基础巩固",
                "priority": 0.9 - kp_info["mastery"]
            })
    
    target_kps.sort(key=lambda x: x["priority"], reverse=True)
    
    for target in target_kps[:5]:
        kp_name = target["kp"]["name"]
        kp_code = target["kp"]["code"]
        reason = target["reason"]
        
        resources = kp_resources.get(kp_name, [])
        if not resources:
            continue
        
        video_resources = [r for r in resources if r['type'] == 'Video']
        ppt_resources = [r for r in resources if r['type'] == 'PPT']
        
        selected_resources = []
        if video_resources:
            selected_resources.append(random.choice(video_resources))
        if ppt_resources:
            selected_resources.append(random.choice(ppt_resources))
        
        if len(selected_resources) < 2 and len(resources) > len(selected_resources):
            remaining = [r for r in resources if r not in selected_resources]
            selected_resources.extend(random.sample(remaining, min(2 - len(selected_resources), len(remaining))))
        
        rec_resources = []
        for res in selected_resources:
            rec_resources.append({
                "resource_id": f"teaching_materials/{res['filename']}",
                "name": res['filename'],
                "type": res['type'],
                "teacher": res.get('teacher', ''),
                "knowledge_point": kp_name,
                "relation": "当前知识点",
                "reason": f"该知识点尚未学习，建议先学习基础资源"
            })
        
        recommendations.append({
            "knowledge_point": kp_name,
            "knowledge_code": kp_code,
            "mastery": target["kp"]["mastery"],
            "status": "未学习" if target["kp"]["mastery"] == 0 else "需巩固",
            "recommend_reason": f"该知识点尚未学习，建议先学习基础资源",
            "resources": rec_resources
        })
    
    return recommendations

def new_recommend_system(student_id):
    student_num = student_id[:10] if len(student_id) >= 10 else student_id
    
    mastery_data = load_json(STUDENTS_MASTERY_FILE)
    student_mastery = mastery_data.get(student_num, {})
    
    student_type = get_student_type(student_num, student_mastery)
    classified = classify_knowledge_points(student_mastery)
    kp_resources = load_resources()
    
    if student_type == "excellent":
        recommendations = recommend_for_excellent_student(student_num, student_mastery, classified, kp_resources)
        recommend_type = "巩固提升型推荐"
        recommend_desc = "您已掌握大部分知识点，推荐后续进阶内容和综合练习"
    elif student_type == "medium":
        recommendations = recommend_for_medium_student(student_num, student_mastery, classified, kp_resources)
        recommend_type = "查漏补缺型推荐"
        recommend_desc = "针对薄弱知识点进行补充学习，查漏补缺"
    else:
        recommendations = recommend_for_weak_student(student_num, student_mastery, classified, kp_resources)
        recommend_type = "基础入门型推荐"
        recommend_desc = "建议从基础知识开始学习，打好基础"
    
    avg_mastery = sum(student_mastery.values()) / len(student_mastery) if student_mastery else 0
    
    return {
        "student_id": student_num,
        "student_type": student_type,
        "recommend_type": recommend_type,
        "recommend_desc": recommend_desc,
        "avg_mastery": avg_mastery,
        "recommendations": recommendations,
        "classified": {
            "mastered": len(classified["mastered"]),
            "good": len(classified["good"]),
            "need_practice": len(classified["need_practice"]),
            "not_learned": len(classified["not_learned"])
        }
    }

if __name__ == "__main__":
    for student_id in ["3220602001", "3220602004", "3220602006"]:
        result = new_recommend_system(student_id)
        print(f"\n{'='*60}")
        print(f"学生: {student_id}")
        print(f"类型: {result['student_type']}")
        print(f"推荐类型: {result['recommend_type']}")
        print(f"平均掌握度: {result['avg_mastery']*100:.1f}%")
        print(f"推荐数量: {len(result['recommendations'])}")
        
        for i, rec in enumerate(result['recommendations'], 1):
            print(f"\n{i}. {rec['knowledge_point']} ({rec['status']})")
            print(f"   掌握度: {rec['mastery']*100:.1f}%")
            print(f"   推荐理由: {rec['recommend_reason']}")
            print(f"   资源数量: {len(rec['resources'])}")
