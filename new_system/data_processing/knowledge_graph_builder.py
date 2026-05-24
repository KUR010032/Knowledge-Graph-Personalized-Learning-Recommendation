import re
import random
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processing.neo4j_manager import Neo4jManager


KNOWLEDGE_LABELS = {
    "1.1 操作系统的定义": ("easy", "important"),
    "1.1.1 基本概念": ("easy", "important"),
    "1.1.2 计算机系统的视图": ("easy", "normal"),
    "1.1.3 操作系统的基本功能": ("easy", "important"),
    "1.2 操作系统的形成和发展": ("easy", "normal"),
    "1.3 操作系统的分类": ("easy", "normal"),
    "1.4 操作系统的运行环境": ("medium", "normal"),
    "1.5 操作系统的结构": ("medium", "important"),
    "1.6 现代操作系统": ("medium", "normal"),
    "1.6.1 现代操作系统技术特性": ("medium", "normal"),
    "1.6.2 UNIX技术特性": ("medium", "normal"),
    "1.6.3 Linux技术特性": ("medium", "normal"),
    "1.6.4 Windows Server技术特性": ("medium", "normal"),
    "2.1 多道程序与并发执行": ("medium", "important"),
    "2.1.1 单道程序的顺序执行": ("easy", "normal"),
    "2.1.2 多道程序的并发执行": ("medium", "important"),
    "2.2 进程模型": ("medium", "important"),
    "2.2.1 进程的概念": ("medium", "important"),
    "2.2.2 进程的实体": ("medium", "important"),
    "2.2.3 进程状态和转换": ("medium", "important"),
    "2.2.4 进程控制": ("medium", "important"),
    "2.3 线程模型": ("medium", "important"),
    "2.3.1 线程的概念": ("medium", "important"),
    "2.3.2 线程与进程的比较": ("medium", "important"),
    "2.3.3 线程的实现": ("hard", "normal"),
    "2.3.4 线程调度激发": ("hard", "normal"),
    "2.4 多核、多线程与超线程": ("hard", "normal"),
    "2.5 进程、线程管理实例": ("medium", "normal"),
    "3.1 进程互斥": ("hard", "important"),
    "3.1.1 并发原理": ("medium", "important"),
    "3.1.2 临界资源与临界区": ("medium", "important"),
    "3.1.3 互斥的软、硬件实现方法": ("hard", "important"),
    "3.1.4 信号量和P、V操作": ("hard", "important"),
    "3.2 进程同步": ("hard", "important"),
    "3.2.1 进程同步概念": ("medium", "important"),
    "3.2.2 用P、V操作实现同步": ("hard", "important"),
    "3.3 进程通信": ("medium", "important"),
    "3.3.1 进程通信的类型": ("medium", "normal"),
    "3.3.2 进程通信中的问题": ("medium", "normal"),
    "3.3.3 消息传递": ("medium", "important"),
    "3.4 死锁": ("hard", "important"),
    "3.4.1 死锁的概念": ("medium", "important"),
    "3.4.2 死锁的必要条件": ("medium", "important"),
    "3.4.3 死锁的防止": ("hard", "important"),
    "3.4.4 死锁的避免": ("hard", "important"),
    "3.4.5 死锁检测与恢复": ("hard", "important"),
    "3.4.6 两阶段加锁": ("hard", "normal"),
    "3.4.7 活锁": ("medium", "normal"),
    "3.4.8 饥饿": ("medium", "normal"),
    "3.5 经典问题": ("hard", "important"),
    "3.5.1 读者-写者问题": ("hard", "important"),
    "3.5.2 哲学家进餐问题": ("hard", "important"),
    "3.5.3 打瞌睡的理发师问题": ("hard", "normal"),
    "3.6 多核环境下的进程同步": ("hard", "normal"),
    "3.7 进程同步与通信实例": ("medium", "normal"),
}

PREREQUISITE_CHAPTERS = [
    ("第1章 操作系统概述", "第2章 进程与线程"),
    ("第2章 进程与线程", "第3章 互斥与同步"),
]

PREREQUISITE_SECTIONS = [
    ("1.1 操作系统的定义", "1.2 操作系统的形成和发展"),
    ("1.2 操作系统的形成和发展", "1.3 操作系统的分类"),
    ("1.3 操作系统的分类", "1.4 操作系统的运行环境"),
    ("1.4 操作系统的运行环境", "1.5 操作系统的结构"),
    ("1.5 操作系统的结构", "1.6 现代操作系统"),
    ("2.1 多道程序与并发执行", "2.2 进程模型"),
    ("2.2 进程模型", "2.3 线程模型"),
    ("2.3 线程模型", "2.4 多核、多线程与超线程"),
    ("2.4 多核、多线程与超线程", "2.5 进程、线程管理实例"),
    ("3.1 进程互斥", "3.2 进程同步"),
    ("3.2 进程同步", "3.3 进程通信"),
    ("3.3 进程通信", "3.4 死锁"),
    ("3.4 死锁", "3.5 经典问题"),
    ("3.5 经典问题", "3.6 多核环境下的进程同步"),
    ("3.6 多核环境下的进程同步", "3.7 进程同步与通信实例"),
]

PREREQUISITE_SUBSECTIONS = [
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
    ("3.4.5 死锁检测与恢复", "3.4.6 两阶段加锁"),
    ("3.4.6 两阶段加锁", "3.4.7 活锁"),
    ("3.4.7 活锁", "3.4.8 饥饿"),
    ("3.5.1 读者-写者问题", "3.5.2 哲学家进餐问题"),
    ("3.5.2 哲学家进餐问题", "3.5.3 打瞌睡的理发师问题"),
]

RELATED_PAIRS = [
    ("2.2.3 进程状态和转换", "3.1.4 信号量和P、V操作"),
    ("2.3.1 线程的概念", "2.2.1 进程的概念"),
    ("2.3.2 线程与进程的比较", "2.2.1 进程的概念"),
    ("3.1.4 信号量和P、V操作", "3.2.2 用P、V操作实现同步"),
    ("3.4.1 死锁的概念", "3.1.2 临界资源与临界区"),
    ("3.4.3 死锁的防止", "3.1.3 互斥的软、硬件实现方法"),
    ("3.5.1 读者-写者问题", "3.2.2 用P、V操作实现同步"),
    ("3.5.2 哲学家进餐问题", "3.5.1 读者-写者问题"),
    ("3.5.3 打瞌睡的理发师问题", "3.5.1 读者-写者问题"),
    ("1.1.3 操作系统的基本功能", "2.1.2 多道程序的并发执行"),
    ("2.1.2 多道程序的并发执行", "3.1.1 并发原理"),
    ("3.3.1 进程通信的类型", "3.3.3 消息传递"),
    ("3.4.4 死锁的避免", "3.4.2 死锁的必要条件"),
    ("3.4.5 死锁检测与恢复", "3.4.4 死锁的避免"),
]

SAMPLE_QUESTIONS = [
    {
        "content": "操作系统的主要功能是什么？",
        "options": ["A. 管理计算机硬件资源", "B. 提供用户界面", "C. 管理计算机软硬件资源并提供服务", "D. 运行应用程序"],
        "answer": "C"
    },
    {
        "content": "以下哪个不是操作系统的特征？",
        "options": ["A. 并发性", "B. 共享性", "C. 独立性", "D. 虚拟性"],
        "answer": "C"
    },
    {
        "content": "进程和程序的根本区别是什么？",
        "options": ["A. 进程是动态的，程序是静态的", "B. 进程占用内存，程序不占用", "C. 进程可以被调度，程序不能", "D. 以上都是"],
        "answer": "A"
    },
    {
        "content": "在操作系统中，临界区是指？",
        "options": ["A. 访问临界资源的代码段", "B. 内存的关键区域", "C. CPU的关键寄存器", "D. 系统核心代码"],
        "answer": "A"
    },
    {
        "content": "死锁的必要条件不包括以下哪项？",
        "options": ["A. 互斥条件", "B. 请求和保持条件", "C. 不可抢占条件", "D. 优先级条件"],
        "answer": "D"
    },
    {
        "content": "P、V操作是用于解决什么问题的？",
        "options": ["A. 进程同步与互斥", "B. 内存管理", "C. 文件管理", "D. 设备管理"],
        "answer": "A"
    },
    {
        "content": "线程与进程相比，以下哪个说法是正确的？",
        "options": ["A. 线程是资源分配的基本单位", "B. 线程切换的开销比进程大", "C. 同一进程的线程共享进程的资源", "D. 线程不能并发执行"],
        "answer": "C"
    },
    {
        "content": "信号量的物理意义是什么？",
        "options": ["A. 表示可用资源的数量", "B. 表示进程的数量", "C. 表示内存的大小", "D. 表示CPU的速度"],
        "answer": "A"
    },
    {
        "content": "哲学家进餐问题主要用来解释什么？",
        "options": ["A. 死锁问题", "B. 内存分配问题", "C. 文件共享问题", "D. 设备驱动问题"],
        "answer": "A"
    },
    {
        "content": "在并发环境下，以下哪种情况不会导致死锁？",
        "options": ["A. 多个进程竞争资源", "B. 进程推进顺序不当", "C. 资源充足且分配合理", "D. 资源分配策略不当"],
        "answer": "C"
    },
]


class KnowledgeGraphBuilder:
    def __init__(self):
        self.neo4j = Neo4jManager()

    def parse_catalog(self, catalog_text):
        lines = [l.strip() for l in catalog_text.split("\n") if l.strip()]
        parsed = []
        for line in lines:
            if line.startswith("第") and "章" in line:
                parsed.append(("chapter", line))
            elif re.match(r"^\d+\.\d+\.\d+", line):
                parsed.append(("subsection", line))
            elif re.match(r"^\d+\.\d+", line):
                parsed.append(("section", line))
            else:
                parsed.append(("skip", line))
        return parsed

    def build_graph(self, catalog_text):
        self.neo4j.clear_database()
        self.neo4j.create_indexes()
        parsed = self.parse_catalog(catalog_text)

        prev_chapter = None
        prev_section = None
        prev_subsection = None

        for t, line in parsed:
            if t == "chapter":
                self._create_chapter(line)
                prev_chapter = line
                prev_section = None
                prev_subsection = None
            elif t == "section":
                self._create_section(line, prev_chapter)
                prev_section = line
                prev_subsection = None
            elif t == "subsection":
                self._create_subsection(line, prev_section)
                prev_subsection = line

        self._add_chapter_prerequisites()
        self._add_section_prerequisites()
        self._add_subsection_prerequisites()
        self._add_related_relations()
        self._add_knowledge_labels()
        self._add_questions()
        print("Knowledge graph built successfully")

    def _create_chapter(self, name):
        self.neo4j.execute_write("MERGE (c:Chapter {name: $name})", {"name": name})

    def _create_section(self, name, chapter):
        self.neo4j.execute_write("MERGE (s:Knowledge {name: $name})", {"name": name})
        if chapter:
            self.neo4j.execute_write("""
                MATCH (c:Chapter {name: $c})
                MATCH (s:Knowledge {name: $s})
                MERGE (c)-[:包含]->(s)
            """, {"c": chapter, "s": name})

    def _create_subsection(self, name, section):
        self.neo4j.execute_write("MERGE (k:Knowledge {name: $name})", {"name": name})
        if section:
            self.neo4j.execute_write("""
                MATCH (s:Knowledge {name: $s})
                MATCH (k:Knowledge {name: $k})
                MERGE (s)-[:包含]->(k)
            """, {"s": section, "k": name})

    def _add_chapter_prerequisites(self):
        for a, b in PREREQUISITE_CHAPTERS:
            self.neo4j.execute_write("""
                MATCH (a:Chapter {name: $a})
                MATCH (b:Chapter {name: $b})
                MERGE (a)-[:先修]->(b)
            """, {"a": a, "b": b})

    def _add_section_prerequisites(self):
        for a, b in PREREQUISITE_SECTIONS:
            self.neo4j.execute_write("""
                MATCH (a:Knowledge {name: $a})
                MATCH (b:Knowledge {name: $b})
                MERGE (a)-[:先修]->(b)
            """, {"a": a, "b": b})

    def _add_subsection_prerequisites(self):
        for a, b in PREREQUISITE_SUBSECTIONS:
            self.neo4j.execute_write("""
                MATCH (a:Knowledge {name: $a})
                MATCH (b:Knowledge {name: $b})
                MERGE (a)-[:先修]->(b)
            """, {"a": a, "b": b})

    def _add_related_relations(self):
        for a, b in RELATED_PAIRS:
            self.neo4j.execute_write("""
                MATCH (a:Knowledge {name: $a})
                MATCH (b:Knowledge {name: $b})
                MERGE (a)-[:相关]->(b)
            """, {"a": a, "b": b})

    def _add_knowledge_labels(self):
        for kp_name, (difficulty, importance) in KNOWLEDGE_LABELS.items():
            self.neo4j.execute_write("""
                MATCH (k:Knowledge {name: $name})
                SET k.difficulty = $difficulty, k.importance = $importance
            """, {"name": kp_name, "difficulty": difficulty, "importance": importance})

    def _add_questions(self):
        knowledge_names = list(KNOWLEDGE_LABELS.keys())
        q_id = 1
        for kp_name in knowledge_names:
            num_questions = random.randint(2, 4)
            for _ in range(num_questions):
                template = random.choice(SAMPLE_QUESTIONS)
                difficulty, importance = KNOWLEDGE_LABELS.get(kp_name, ("medium", "normal"))
                self.neo4j.execute_write("""
                    MERGE (q:Question {id: $qid})
                    SET q.content = $content, q.options = $options,
                        q.answer = $answer, q.difficulty = $difficulty,
                        q.importance = $importance
                    WITH q
                    MATCH (k:Knowledge {name: $kp})
                    MERGE (q)-[:属于]->(k)
                """, {
                    "qid": str(q_id),
                    "content": template["content"],
                    "options": template["options"],
                    "answer": template["answer"],
                    "difficulty": difficulty,
                    "importance": importance,
                    "kp": kp_name
                })
                q_id += 1
        print(f"Added {q_id - 1} questions to knowledge graph")

    def close(self):
        self.neo4j.close()


if __name__ == "__main__":
    catalog_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "studentdata", "catalog.txt")
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog = f.read()
    builder = KnowledgeGraphBuilder()
    builder.build_graph(catalog)
    builder.close()
