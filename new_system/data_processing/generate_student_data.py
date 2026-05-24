import os
import sys
import random
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config

knowledge_points = [
    "1.1 操作系统的定义", "1.1.1 基本概念", "1.1.2 计算机系统的视图", "1.1.3 操作系统的基本功能",
    "1.2 操作系统的形成和发展", "1.3 操作系统的分类",
    "1.4 操作系统的运行环境", "1.5 操作系统的结构", "1.6 现代操作系统",
    "1.6.1 现代操作系统技术特性", "1.6.2 UNIX技术特性", "1.6.3 Linux技术特性", "1.6.4 Windows Server技术特性",
    "2.1 多道程序与并发执行", "2.1.1 单道程序的顺序执行", "2.1.2 多道程序的并发执行",
    "2.2 进程模型", "2.2.1 进程的概念", "2.2.2 进程的实体", "2.2.3 进程状态和转换", "2.2.4 进程控制",
    "2.3 线程模型", "2.3.1 线程的概念", "2.3.2 线程与进程的比较", "2.3.3 线程的实现", "2.3.4 线程调度激发",
    "2.4 多核、多线程与超线程", "2.5 进程、线程管理实例",
    "3.1 进程互斥", "3.1.1 并发原理", "3.1.2 临界资源与临界区", "3.1.3 互斥的软、硬件实现方法", "3.1.4 信号量和P、V操作",
    "3.2 进程同步", "3.2.1 进程同步概念", "3.2.2 用P、V操作实现同步",
    "3.3 进程通信", "3.3.1 进程通信的类型", "3.3.2 进程通信中的问题", "3.3.3 消息传递",
    "3.4 死锁", "3.4.1 死锁的概念", "3.4.2 死锁的必要条件", "3.4.3 死锁的防止", "3.4.4 死锁的避免",
    "3.4.5 死锁检测与恢复", "3.4.6 两阶段加锁", "3.4.7 活锁", "3.4.8 饥饿",
    "3.5 经典问题", "3.5.1 读者-写者问题", "3.5.2 哲学家进餐问题", "3.5.3 打睡的理发师问题",
    "3.6 多核环境下的进程同步", "3.7 进程同步与通信实例"
]

students_to_generate = [
    ("3220602002陈二", "陈二"),
    ("3220602003张三", "张三"),
    ("3220602004李四", "李四"),
    ("3220602005王五", "王五")
]

data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "studentdata")

for student_id, student_name in students_to_generate:
    csv_path = os.path.join(data_dir, f"{student_id}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["知识点", "总题数", "正确数", "掌握度"])
        for kp in knowledge_points:
            mastery = round(random.uniform(0.1, 0.95), 4)
            total = random.randint(5, 30)
            correct = int(total * mastery)
            writer.writerow([kp, total, correct, mastery])
    print(f"Generated {csv_path}")

print("All student CSV files generated!")
