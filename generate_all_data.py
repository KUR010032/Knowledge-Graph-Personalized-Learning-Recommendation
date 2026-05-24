import json
import random
import math
from datetime import datetime, timedelta
from neo4j import GraphDatabase

# Load questions (already expanded with real variations)
with open('app/resources/questions.json', 'r', encoding='utf-8') as f:
    qdata = json.load(f)

all_questions = qdata['questions']

print(f"Total questions loaded: {len(all_questions)}")

q_by_id_all = {q['id']: q for q in all_questions}
q_by_kp_all = {}
for q in all_questions:
    kp = q['knowledge_point']
    if kp not in q_by_kp_all:
        q_by_kp_all[kp] = []
    q_by_kp_all[kp].append(q)

# Key knowledge points
key_kps = [
    "1.1.1 基本概念", "1.1.3 操作系统的基本功能", "1.2 操作系统的形成和发展",
    "1.3 操作系统的分类", "2.1.2 多道程序的并发执行", "2.2.1 进程的概念",
    "2.2.3 进程状态和转换", "2.3.1 线程的概念", "3.1.2 临界资源与临界区",
    "3.1.4 信号量和P、V操作", "3.2.2 用P、V操作实现同步",
    "3.4.2 死锁的必要条件", "3.4.4 死锁的避免", "3.5.1 读者-写者问题",
    "3.5.2 哲学家进餐问题",
]

# Knowledge graph relationships
prerequisite_chains = [
    ("1.1.1 基本概念", "1.1.2 计算机系统的视图"),
    ("1.1.2 计算机系统的视图", "1.1.3 操作系统的基本功能"),
    ("1.6.1 现代操作系统技术特性", "1.6.2 UNIX技术特性"),
    ("1.6.2 UNIX技术特性", "1.6.3 Linux技术特性"),
    ("1.6.3 Linux技术特性", "1.6.4 Windows Server技术特性"),
    ("2.1.1 单道程序的顺序执行", "2.1.2 多道程序的并发执行"),
    ("2.2.1 进程的概念", "2.2.2 进程的实体"),
    ("2.2.2 进程的实体", "2.2.3 进程状态和转换"),
    ("2.2.3 进程状态和转换", "2.2.4 进程控制"),
    ("2.3.1 线程的概念", "2.3.2 线程与进程的比较"),
    ("2.3.2 线程与进程的比较", "2.3.3 线程的实现"),
    ("2.3.3 线程的实现", "2.3.4 线程调度激发"),
    ("3.1.1 并发原理", "3.1.2 临界资源与临界区"),
    ("3.1.2 临界资源与临界区", "3.1.3 互斥的软、硬件实现方法"),
    ("3.1.3 互斥的软、硬件实现方法", "3.1.4 信号量和P、V操作"),
    ("3.2.1 进程同步概念", "3.2.2 用P、V操作实现同步"),
    ("3.3.1 进程通信的类型", "3.3.2 进程通信中的问题"),
    ("3.3.2 进程通信中的问题", "3.3.3 消息传递"),
    ("3.4.1 死锁的概念", "3.4.2 死锁的必要条件"),
    ("3.4.2 死锁的必要条件", "3.4.3 死锁的防止"),
    ("3.4.3 死锁的防止", "3.4.4 死锁的避免"),
    ("3.4.4 死锁的避免", "3.4.5 死锁检测与恢复"),
]

# 7 students, 7 different levels
students_config = {
    "3220602001刘大": {
        "target_total": 300, "target_correct": 295,  # 98.3% accuracy -> 优秀 ≥90%
        "level": "excellent", "video_rate": 0.95, "resource_views": 8,
        "target_mastery_avg": 0.95
    },
    "3220602002陈二": {
        "target_total": 280, "target_correct": 240,  # 85.7% accuracy -> 良好 75-89%
        "level": "good", "video_rate": 0.80, "resource_views": 6,
        "target_mastery_avg": 0.85
    },
    "3220602003张三": {
        "target_total": 260, "target_correct": 210,  # 80.8% accuracy -> 良好 75-89%
        "level": "good", "video_rate": 0.70, "resource_views": 5,
        "target_mastery_avg": 0.78
    },
    "3220602004李四": {
        "target_total": 200, "target_correct": 135,  # 67.5% accuracy -> 中等 60-74%
        "level": "medium", "video_rate": 0.50, "resource_views": 4,
        "target_mastery_avg": 0.65
    },
    "3220602005王五": {
        "target_total": 150, "target_correct": 75,   # 50% accuracy -> 薄弱 <60%
        "level": "weak", "video_rate": 0.30, "resource_views": 2,
        "target_mastery_avg": 0.48
    },
    "3220602006赵六": {
        # 学到一半：只学了第1章，第2、3章完全没学
        "target_total": 100, "target_correct": 70,   # 70% accuracy -> 中等
        "level": "half_learned", "video_rate": 0.40, "resource_views": 3,
        "target_mastery_avg": 0.60,
        "learned_chapters": [1]  # 只学了第1章
    },
    "3220602007周七": {
        # 一点没学：所有章节都没学，刚注册的新生
        "target_total": 0, "target_correct": 0,      # 0题 -> 无数据
        "level": "new_student", "video_rate": 0.0, "resource_views": 0,
        "target_mastery_avg": 0.0,
        "learned_chapters": []  # 什么都没学
    },
}

# Load existing history
try:
    with open('app/resources/question_history.json', 'r', encoding='utf-8') as f:
        history = json.load(f)
except:
    history = {}

neo4j_uri = "bolt://localhost:7687"
neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "12345678"))

def build_adjacency_list(session, valid_kps):
    adj = {kp: [] for kp in valid_kps}
    for from_kp, to_kp in prerequisite_chains:
        if from_kp in adj and to_kp in adj:
            adj[from_kp].append((to_kp, "先修", 0.8))
            adj[to_kp].append((from_kp, "相关", 0.5))
    for kp in valid_kps:
        ch_num = kp.split('.')[0]
        for other_kp in valid_kps:
            if other_kp != kp and other_kp.startswith(ch_num + '.'):
                if not any(n == other_kp for n, _, _ in adj[kp]):
                    adj[kp].append((other_kp, "相关", 0.3))
    return adj

def compute_base_mastery(correct, total, difficulty_factor):
    """
    基础掌握度计算：综合考虑正确率、做题量、难度
    Mastery = α × Accuracy + β × PracticeFactor + γ × DifficultyFactor
    α=0.6, β=0.25, γ=0.15
    n_max=7 (300题/45知识点≈6.7题/知识点，接近满分练习)
    """
    if total == 0:
        return 0.0
    accuracy = correct / total
    alpha = 0.6
    beta = 0.25
    gamma = 0.15
    n_max = 7  # 达到7题算充分练习（300题/45知识点≈6.7）
    practice_factor = min(total / n_max, 1.0)
    mastery = alpha * accuracy + beta * practice_factor + gamma * difficulty_factor
    return min(max(mastery, 0.0), 1.0)

def ripple_propagation(initial_mastery, adj_list, n_hops=2, decay=0.5):
    """RippleNet知识图谱传播"""
    propagated = dict(initial_mastery)
    for hop in range(1, n_hops + 1):
        decay_factor = decay ** hop
        updates = {}
        for kp, neighbors in adj_list.items():
            if kp not in propagated:
                continue
            current_score = propagated[kp]
            for neighbor, rel_type, rel_weight in neighbors:
                influence = current_score * rel_weight * decay_factor
                if neighbor not in propagated:
                    updates[neighbor] = influence
                else:
                    updates[neighbor] = max(propagated[neighbor], influence * 0.3)
        for kp, new_score in updates.items():
            propagated[kp] = max(propagated.get(kp, 0), new_score)
    return propagated

def collaborative_adjustment(student_id, kp_mastery, all_students_mastery, adj_list):
    """协同过滤调整"""
    similar_students = []
    for other_id, other_mastery in all_students_mastery.items():
        if other_id == student_id:
            continue
        common_kps = set(kp_mastery.keys()) & set(other_mastery.keys())
        if len(common_kps) < 3:
            continue
        dot_product = sum(kp_mastery[k] * other_mastery[k] for k in common_kps)
        norm_self = math.sqrt(sum(kp_mastery[k]**2 for k in common_kps))
        norm_other = math.sqrt(sum(other_mastery[k]**2 for k in common_kps))
        if norm_self > 0 and norm_other > 0:
            similarity = dot_product / (norm_self * norm_other)
            similar_students.append((other_id, similarity, other_mastery))
    similar_students.sort(key=lambda x: x[1], reverse=True)
    top_similar = similar_students[:3]
    adjusted = dict(kp_mastery)
    for kp in kp_mastery:
        if not top_similar:
            break
        cf_score = 0
        total_sim = 0
        for _, sim, other_mastery in top_similar:
            if kp in other_mastery:
                cf_score += sim * other_mastery[kp]
                total_sim += sim
        if total_sim > 0:
            cf_prediction = cf_score / total_sim
            adjusted[kp] = 0.7 * kp_mastery[kp] + 0.3 * cf_prediction
    return adjusted

def detect_avoidance_penalty(kp_mastery, kp_stats, behavior_profile):
    """逃避知识点检测"""
    penalized = dict(kp_mastery)
    for kp, mastery in kp_mastery.items():
        stats = kp_stats.get(kp, {"total": 0})
        engagement = behavior_profile.get(kp, 0)
        if mastery < 0.5 and stats["total"] < 3 and engagement < 2:
            penalty = (0.5 - mastery) * 0.2 * (1 - engagement / 3)
            penalized[kp] = max(mastery - penalty, 0.0)
    return penalized

def multi_behavior_adjustment(base_mastery, config, kp_name):
    """多行为建模调整"""
    video_rate = config.get("video_rate", 0.5)
    resource_views = config.get("resource_views", 2)
    seed = hash(config.get("id", "") + kp_name) % 100
    if seed < 60:
        kp_video_rate = video_rate + random.uniform(-0.1, 0.1)
    elif seed < 80:
        kp_video_rate = video_rate * 0.7
    else:
        kp_video_rate = video_rate * 0.4
    kp_video_rate = min(max(kp_video_rate, 0), 1)
    resource_factor = min(resource_views / 8.0, 1.0)
    behavior_score = 0.5 * kp_video_rate + 0.3 * resource_factor + 0.2 * 0.5
    adjusted = 0.75 * base_mastery + 0.25 * behavior_score
    return min(max(adjusted, 0.0), 1.0)

def compute_comprehensive_mastery(student_id, config, kp_stats, adj_list, all_students_mastery):
    """综合掌握度计算 - 基础掌握度为主(80%)，其他算法微调(20%)"""
    initial_mastery = {}
    for kp, stats in kp_stats.items():
        kp_questions = q_by_kp_all.get(kp, [])
        if kp_questions:
            diffs = [q.get('difficulty', 'medium') for q in kp_questions]
            diff_scores = {'easy': 1.0, 'medium': 0.8, 'hard': 0.6}
            difficulty_factor = sum(diff_scores.get(d, 0.8) for d in diffs) / len(diffs)
        else:
            difficulty_factor = 0.8
        base = compute_base_mastery(stats["correct"], stats["total"], difficulty_factor)
        initial_mastery[kp] = base
    
    behavior_profile = {}
    for kp in kp_stats:
        seed = hash(student_id + kp) % 100
        behavior_profile[kp] = seed % 5
    
    rippled_mastery = ripple_propagation(initial_mastery, adj_list, n_hops=2, decay=0.5)
    cf_adjusted = collaborative_adjustment(student_id, rippled_mastery, all_students_mastery, adj_list)
    avoidance_penalized = detect_avoidance_penalty(cf_adjusted, kp_stats, behavior_profile)
    
    final_mastery = {}
    for kp, mastery in avoidance_penalized.items():
        base_m = initial_mastery[kp]
        adjusted_m = multi_behavior_adjustment(mastery, config, kp)
        final_mastery[kp] = 0.85 * base_m + 0.15 * adjusted_m
    
    return final_mastery

with neo4j_driver.session() as session:
    print("\nGetting KPs from Neo4j...")
    r = session.run("MATCH (k:Knowledge) WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.' RETURN k.name AS name")
    neo4j_kps = set(x['name'] for x in r)
    print(f"KPs in Neo4j: {len(neo4j_kps)}")
    
    valid_kps = sorted([kp for kp in q_by_kp_all.keys() if kp in neo4j_kps])
    print(f"Valid KPs (in both): {len(valid_kps)}")
    
    adj_list = build_adjacency_list(session, valid_kps)
    print(f"Knowledge graph built with {len(adj_list)} nodes")
    
    print("\nSetting difficulty on Knowledge nodes...")
    for kp in valid_kps:
        kp_questions = q_by_kp_all.get(kp, [])
        if kp_questions:
            diffs = [q.get('difficulty', 'medium') for q in kp_questions]
            majority_diff = max(set(diffs), key=diffs.count)
        else:
            majority_diff = 'medium'
        
        session.run("""
        MATCH (k:Knowledge {name: $kp})
        SET k.difficulty = $diff
        """, kp=kp, diff=majority_diff)
    print("Difficulty set.")
    
    print("Setting is_key on Knowledge nodes...")
    for kp in valid_kps:
        is_key = kp in key_kps
        session.run("""
        MATCH (k:Knowledge {name: $kp})
        SET k.is_key = $is_key
        """, kp=kp, is_key=is_key)
    print("is_key set.")
    
    # Clear all old student data and related relationships
    print("\nClearing old student data...")
    session.run("MATCH (s:Student)-[r]->() DELETE r")
    session.run("MATCH ()-[r]->(s:Student) DELETE r")
    session.run("MATCH (s:Student) DELETE s")
    session.run("MATCH (v:Video) DELETE v")
    session.run("MATCH (r:Resource) DELETE r")
    print("Old data cleared.")
    
    all_students_mastery = {}
    
    for sid, config in students_config.items():
        print(f"\n{'='*60}")
        print(f"Generating data for {sid} ({config['level']})...")
        print(f"Target: {config['target_total']} total, {config['target_correct']} correct")
        print(f"Target mastery avg: {config['target_mastery_avg']*100:.0f}%")
        
        target_total = config["target_total"]
        target_correct = config["target_correct"]
        
        # 特殊处理：赵六只学了第1章，周七什么都没学
        learned_chapters = config.get("learned_chapters", [1, 2, 3])  # 默认学所有章节
        
        # 根据已学章节过滤知识点
        filtered_kps = []
        for kp in valid_kps:
            ch_num = int(kp.split('.')[0])
            if ch_num in learned_chapters:
                filtered_kps.append(kp)
        
        # 如果没学任何章节（周七），直接跳过题目生成
        if not filtered_kps:
            print(f"  [新学生] 未学习任何章节，无做题记录")
            kp_stats = {kp: {"total": 0, "correct": 0} for kp in valid_kps}
            student_history = {}
            actual_total = 0
            actual_correct = 0
            actual_wrong = 0
            print(f"  Actual: 0 total, 0 correct, 0 wrong")
            print(f"  Accuracy: N/A (no attempts)")
            print(f"  Unique questions: 0")
            history[sid] = student_history
            
            # 新学生所有知识点掌握度为0
            comprehensive_mastery = {kp: 0.0 for kp in valid_kps}
            all_students_mastery[sid] = comprehensive_mastery
            print(f"  Comprehensive mastery: avg=0.0%, min=0.0%, max=0.0%")
            
            # 保存学生节点
            session.run("""
            CREATE (s:Student {id: $sid, name: $name, level: $level})
            """, sid=sid, name=sid[9:], level=config['level'])
            
            # 创建MASTERED关系，掌握度全为0
            for kp in valid_kps:
                session.run("""
                MATCH (k:Knowledge {name: $kp})
                MATCH (s:Student {id: $sid})
                MERGE (s)-[r:MASTERED]->(k)
                SET r.mastery = 0.0,
                    r.total_questions = 0,
                    r.correct_questions = 0,
                    r.base_accuracy = 0.0,
                    r.practice_factor = 0.0,
                    r.difficulty_factor = 0.8
                """, sid=sid, kp=kp)
            
            # 新学生无视频观看和资源下载记录
            print(f"  [新学生] 无视频观看和资源下载记录")
            continue
        
        # 赵六：只分配已学章节的题目
        if config["level"] == "half_learned":
            # 重新分配题目到已学章节的知识点
            n_kps = len(filtered_kps)
            base_per_kp = target_total // n_kps
            remainder = target_total % n_kps
            
            kp_assignments = {}
            total_assigned = 0
            
            for i, kp in enumerate(filtered_kps):
                n_qs = base_per_kp + (1 if i < remainder else 0)
                n_qs = max(2, n_qs)
                kp_assignments[kp] = n_qs
                total_assigned += n_qs
            
            # 未学章节的知识点不分配题目
            for kp in valid_kps:
                if kp not in kp_assignments:
                    kp_assignments[kp] = 0
            
            print(f"  [学到一半] 只学了第{learned_chapters}章，共{n_kps}个知识点")
        else:
            # 正常学生：所有章节都学
            n_kps = len(valid_kps)
            base_per_kp = target_total // n_kps
            remainder = target_total % n_kps
            
            kp_assignments = {}
            total_assigned = 0
            
            for i, kp in enumerate(valid_kps):
                n_qs = base_per_kp + (1 if i < remainder else 0)
                n_qs = max(2, n_qs)
                kp_assignments[kp] = n_qs
                total_assigned += n_qs
        
        while total_assigned > target_total:
            max_kp = max(kp_assignments, key=kp_assignments.get)
            if kp_assignments[max_kp] > 2:
                kp_assignments[max_kp] -= 1
                total_assigned -= 1
            else:
                break
        
        while total_assigned < target_total:
            min_kp = min(kp_assignments, key=kp_assignments.get)
            kp_assignments[min_kp] += 1
            total_assigned += 1
        
        base_time = datetime(2026, 5, 1, 8, 0, 0)
        time_offset = 0
        
        kp_stats = {kp: {"total": 0, "correct": 0} for kp in valid_kps}
        
        # Calculate correct distribution based on difficulty
        kp_difficulty_distribution = {}
        for kp in valid_kps:
            kp_questions = q_by_kp_all.get(kp, [])
            if kp_questions:
                diffs = [q.get('difficulty', 'medium') for q in kp_questions]
                diff_scores = {'easy': 1.0, 'medium': 0.8, 'hard': 0.6}
                avg_diff_score = sum(diff_scores.get(d, 0.8) for d in diffs) / len(diffs)
                kp_difficulty_distribution[kp] = avg_diff_score
            else:
                kp_difficulty_distribution[kp] = 0.8
        
        kp_correct_targets = {}
        remaining_correct = target_correct
        
        total_weight = sum(kp_assignments[kp] * kp_difficulty_distribution[kp] for kp in valid_kps)
        
        for kp in valid_kps:
            n_attempts = kp_assignments[kp]
            if total_weight > 0:
                weight = n_attempts * kp_difficulty_distribution[kp]
                target_correct_for_kp = int(target_correct * weight / total_weight)
            else:
                target_correct_for_kp = 0
            kp_correct_targets[kp] = target_correct_for_kp
            remaining_correct -= target_correct_for_kp
        
        while remaining_correct > 0:
            for kp in valid_kps:
                if remaining_correct <= 0:
                    break
                if kp_correct_targets[kp] < kp_assignments[kp]:
                    kp_correct_targets[kp] += 1
                    remaining_correct -= 1
        
        # Generate question attempts
        student_history = {}
        
        for kp, n_attempts in kp_assignments.items():
            available_qs = q_by_kp_all.get(kp, [])
            if not available_qs:
                continue
            
            selected_qs = random.sample(available_qs, min(n_attempts, len(available_qs)))
            while len(selected_qs) < n_attempts:
                selected_qs.append(random.choice(available_qs))
            
            n_correct_needed = kp_correct_targets[kp]
            correct_indices = set(random.sample(range(n_attempts), min(n_correct_needed, n_attempts)))
            
            for i, q in enumerate(selected_qs):
                qid = q['id']
                is_correct = i in correct_indices
                time_offset += random.randint(60, 600)
                attempt_time = base_time + timedelta(seconds=time_offset)
                
                if qid not in student_history:
                    student_history[qid] = {
                        "correct_count": 0,
                        "wrong_count": 0,
                        "consecutive_correct": 0,
                        "last_result": None,
                        "total_attempts": 0,
                        "first_wrong_time": None,
                        "last_attempt_time": None
                    }
                
                entry = student_history[qid]
                entry["total_attempts"] += 1
                kp_stats[kp]["total"] += 1
                
                if is_correct:
                    entry["correct_count"] += 1
                    entry["consecutive_correct"] += 1
                    entry["last_result"] = "correct"
                    kp_stats[kp]["correct"] += 1
                else:
                    entry["wrong_count"] += 1
                    entry["consecutive_correct"] = 0
                    entry["last_result"] = "wrong"
                    if entry["first_wrong_time"] is None:
                        entry["first_wrong_time"] = attempt_time.isoformat()
                
                entry["last_attempt_time"] = attempt_time.isoformat()
        
        actual_total = sum(e["total_attempts"] for e in student_history.values())
        actual_correct = sum(e["correct_count"] for e in student_history.values())
        actual_wrong = sum(e["wrong_count"] for e in student_history.values())
        
        print(f"  Actual: {actual_total} total, {actual_correct} correct, {actual_wrong} wrong")
        print(f"  Accuracy: {actual_correct/actual_total*100:.1f}%")
        print(f"  Unique questions: {len(student_history)}")
        
        history[sid] = student_history
        
        # Compute comprehensive mastery
        config["id"] = sid
        comprehensive_mastery = compute_comprehensive_mastery(
            sid, config, kp_stats, adj_list, all_students_mastery
        )
        
        all_students_mastery[sid] = comprehensive_mastery
        
        mastery_values = list(comprehensive_mastery.values())
        avg_mastery = sum(mastery_values) / len(mastery_values) if mastery_values else 0
        min_mastery = min(mastery_values) if mastery_values else 0
        max_mastery = max(mastery_values) if mastery_values else 0
        
        print(f"  Comprehensive mastery: avg={avg_mastery*100:.1f}%, min={min_mastery*100:.1f}%, max={max_mastery*100:.1f}%")
        
        # Save to Neo4j
        session.run("""
        CREATE (s:Student {id: $sid, name: $name, level: $level})
        """, sid=sid, name=sid[9:], level=config['level'])
        
        for kp, mastery in comprehensive_mastery.items():
            stats = kp_stats.get(kp, {"total": 0, "correct": 0})
            base_acc = stats["correct"]/stats["total"] if stats["total"] > 0 else 0
            
            session.run("""
            MATCH (k:Knowledge {name: $kp})
            MATCH (s:Student {id: $sid})
            MERGE (s)-[r:MASTERED]->(k)
            SET r.mastery = $mastery,
                r.total_questions = $total,
                r.correct_questions = $correct,
                r.base_accuracy = $base_acc,
                r.practice_factor = $practice,
                r.difficulty_factor = $diff_factor
            """, sid=sid, kp=kp, mastery=round(mastery, 3),
                total=stats["total"], correct=stats["correct"],
                base_acc=round(base_acc, 3),
                practice=round(min(stats["total"]/15, 1.0), 3),
                diff_factor=round(kp_difficulty_distribution.get(kp, 0.8), 3))
        
        # Generate video watch records - 根据已学章节生成
        video_resources = []
        learned_chapters_for_videos = config.get("learned_chapters", [1, 2, 3])
        video_count = int(config["video_rate"] * 20)
        
        for i in range(video_count):
            ch_num = random.choice(learned_chapters_for_videos)
            sec_num = random.randint(1, 7)
            video_name = f"第{ch_num}章_第{sec_num}节_视频讲解.mp4"
            watch_duration = random.randint(600, 3600)
            completion_rate = config["video_rate"] + random.uniform(-0.1, 0.05)
            completion_rate = min(max(completion_rate, 0), 1)
            
            session.run("""
            MATCH (s:Student {id: $sid})
            MERGE (v:Video {name: $vname})
            MERGE (s)-[r:WATCHED]->(v)
            SET r.watch_duration = $duration,
                r.completion_rate = $completion,
                r.last_viewed = $wtime
            """, sid=sid, vname=video_name, 
                duration=watch_duration, 
                completion=round(completion_rate, 3),
                wtime=(base_time + timedelta(seconds=random.randint(0, 86400*30))).isoformat())
        
        # Generate resource view records - 根据已学章节生成
        resource_count = config["resource_views"] * 5
        for i in range(resource_count):
            ch_num = random.choice(learned_chapters_for_videos)
            res_name = f"第{ch_num}章_PPT课件_{i+1}.pptx"
            view_count = random.randint(1, 5)
            download = random.random() < 0.3
            download_count = random.randint(1, 3) if download else 0
            
            session.run("""
            MATCH (s:Student {id: $sid})
            MERGE (r:Resource {name: $rname})
            MERGE (s)-[rel:VIEWED]->(r)
            SET rel.view_count = $vc,
                rel.download_count = $dc,
                rel.downloaded = $dl,
                rel.last_viewed = $vtime,
                rel.resource_type = 'resource'
            """, sid=sid, rname=res_name,
                vc=view_count, dc=download_count, dl=download,
                vtime=(base_time + timedelta(seconds=random.randint(0, 86400*30))).isoformat())

# Save history
with open('app/resources/question_history.json', 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

neo4j_driver.close()
print("\n" + "="*60)
print("Done! Generated data with:")
print("- 3x expanded questions (363 total)")
print("- 5 students across 5 different levels")
print("- Comprehensive mastery calculation with:")
print("  * Base mastery (accuracy + practice + difficulty)")
print("  * RippleNet knowledge graph propagation")
print("  * Collaborative filtering adjustment")
print("  * Avoidance detection penalty")
print("  * Multi-behavior modeling")
print("- Real video watch and resource view records")
