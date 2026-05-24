import re
import random
import pandas as pd
import os

# 获取当前脚本所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CATALOG_PATH = os.path.join(BASE_DIR, "catalog.txt")

# 读取目录
with open(CATALOG_PATH, "r", encoding="utf-8") as f:
    lines = [l.strip() for l in f.readlines() if l.strip()]

# 提取所有 x.x 和 x.x.x 格式的节点
nodes = []
for line in lines:
    # 排除章标题、小结、习题等
    if line.startswith("第") and "章" in line:
        continue
    if "本章小结" in line or "习题" in line or line == "目录":
        continue
    # 匹配 1.1 或 1.1.1 (开头是数字编号)
    if re.match(r"^\d+\.\d+(\.\d+)?", line):
        nodes.append(line)

# 找出所有作为父节点的节点（即存在子节点的节点）
# 例如 1.1 是 1.1.1 的父节点，我们需要排除 1.1，只保留叶子节点
parents = set()
for n in nodes:
    # 如果 n 是 x.x 格式，检查是否有 x.x.y 存在
    if n.count('.') == 1:
        prefix = n + "."
        for other in nodes:
            if other.startswith(prefix):
                parents.add(n)
                break

# 目标节点：所有叶子节点
# 1. 所有的 x.x.x (小节)
# 2. 没有子节点的 x.x (大节)
target_nodes = []
for n in nodes:
    if n not in parents:
        target_nodes.append(n)

# 定义学生名单
students = [
    "3220602001刘大",
    "3220602002陈二",
    "3220602003张三",
    "3220602004李四",
    "3220602005王五"
]

# 生成数据
print(f"Found {len(target_nodes)} leaf knowledge points.")

for student_name in students:
    data = []
    skill = random.uniform(0.3, 0.9) 
    
    for node in target_nodes:
        total = random.randint(10, 30)
        correct_rate = min(max(random.normalvariate(skill, 0.12), 0.1), 0.99)
        done = int(total * random.uniform(0.5, 1.0))
        mastery = round(min(correct_rate * (done / total * 0.8 + 0.2), 1.0), 4)
        
        data.append({
            "knowledge_point": node,
            "questions_done": done,
            "total_questions": total,
            "correct_rate": round(correct_rate, 4),
            "mastery": mastery
        })
    
    df = pd.DataFrame(data)
    filename = f"{student_name}.csv"
    filepath = os.path.join(BASE_DIR, filename)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"Generated: {filename} | Contains {len(data)} points | Skill: {skill:.2f}")

print("\nAll done! Please run load_student_data.py to import data.")
