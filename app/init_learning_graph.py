# -*- coding: utf-8 -*-
import json
import os
import re
from datetime import datetime

from neo4j import GraphDatabase

BASE_DIR = os.path.dirname(__file__)
RESOURCE_DIR = os.path.join(BASE_DIR, "resources")
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"), connection_timeout=3)

def load_json(path, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def kp_code(name):
    m = re.search(r"\d+(?:\.\d+)*", str(name or ""))
    return m.group(0) if m else ""

def normalize_question(q):
    q = dict(q or {})
    title = q.get("title") or q.get("question_text") or q.get("question") or ""
    knowledge = q.get("knowledge_name") or q.get("knowledge_point") or ""
    code = kp_code(knowledge)
    qtype = q.get("type") or "single_choice"
    if qtype == "choice":
        qtype = "single_choice"
    return {
        "id": str(q.get("id") or q.get("question_id")),
        "title": title,
        "type": qtype,
        "options": json.dumps(q.get("options") or [], ensure_ascii=False),
        "answer": ",".join(q.get("answer")) if isinstance(q.get("answer"), list) else str(q.get("answer") or ""),
        "analysis": q.get("analysis") if q.get("analysis") is not None else q.get("explanation", ""),
        "difficulty": q.get("difficulty") if q.get("difficulty") in ("easy", "medium", "hard") else "medium",
        "knowledge_id": q.get("knowledge_id") or code or knowledge,
        "knowledge_name": knowledge,
        "chapter_id": q.get("chapter_id") or (code.split(".")[0] if code else ""),
        "chapter_name": q.get("chapter_name") or ("第{}章".format(code.split(".")[0]) if code else "未分类"),
        "status": q.get("status") or "enabled",
    }

def load_resources():
    teaching_dir = os.path.join(RESOURCE_DIR, "teaching_materials")
    manifest = load_json(os.path.join(teaching_dir, "resource_manifest.json"), {}).get("files", []) if isinstance(load_json(os.path.join(teaching_dir, "resource_manifest.json"), {}), dict) else []
    manifest_map = {}
    for item in manifest:
        fn = item.get("filename")
        if fn:
            manifest_map[fn] = item

    resources = []
    if os.path.isdir(teaching_dir):
        for entry in os.scandir(teaching_dir):
            if not entry.is_file():
                continue
            filename = entry.name
            ext = os.path.splitext(filename)[1].lower()
            if ext not in (".mp4", ".ppt", ".pptx", ".doc", ".docx", ".pdf", ".txt", ".md"):
                continue
            if filename == "resource_manifest.json":
                continue

            meta = manifest_map.get(filename, {})
            kp_name = meta.get("knowledge_point") or ""
            code = kp_code(kp_name or filename)
            teacher = meta.get("teacher") or "未标注"
            rtype = meta.get("type") or os.path.splitext(filename)[1].lstrip(".")
            title_display = os.path.splitext(filename)[0]

            resources.append({
                "id": filename,
                "name": filename,
                "title": title_display,
                "filename": filename,
                "type": rtype,
                "teacher_name": teacher,
                "teacher_id": meta.get("teacher_id"),
                "knowledge_id": code or "",
                "knowledge_name": kp_name or title_display,
                "chapter_id": code.split(".")[0] if code else "",
                "chapter_name": "第{}章".format(code.split(".")[0]) if code else "待分类",
            })
    return resources

def create_constraints(tx):
    statements = [
        "CREATE CONSTRAINT student_id IF NOT EXISTS FOR (n:Student) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT teacher_id IF NOT EXISTS FOR (n:Teacher) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT resource_name IF NOT EXISTS FOR (n:Resource) REQUIRE n.name IS UNIQUE",
        "CREATE CONSTRAINT question_id IF NOT EXISTS FOR (n:Question) REQUIRE n.id IS UNIQUE",
        "CREATE INDEX knowledge_name IF NOT EXISTS FOR (n:Knowledge) ON (n.name)",
        "CREATE INDEX chapter_id IF NOT EXISTS FOR (n:Chapter) ON (n.id)",
    ]
    for stmt in statements:
        tx.run(stmt)

def import_questions(tx, questions):
    for q in questions:
        tx.run("""
        MERGE (ques:Question {id:$id})
        SET ques.title=$title, ques.question_text=$title, ques.type=$type,
            ques.options=$options, ques.answer=$answer, ques.analysis=$analysis,
            ques.difficulty=$difficulty, ques.knowledge_id=$knowledge_id,
            ques.knowledge_name=$knowledge_name, ques.chapter_id=$chapter_id,
            ques.chapter_name=$chapter_name, ques.status=$status,
            ques.updated_at=datetime()
        MERGE (k:Knowledge {name:$knowledge_name})
        SET k.id=COALESCE(k.id,$knowledge_id)
        MERGE (ques)-[:TESTS]->(k)
        MERGE (c:Chapter {id:$chapter_id})
        SET c.name=$chapter_name
        MERGE (ques)-[:BELONGS_TO]->(c)
        """, **q)

def import_resources(tx, resources):
    for r in resources:
        tx.run("""
        MERGE (res:Resource {name:$name})
        SET res.id=$id, res.title=$title, res.filename=$filename, res.type=$type,
            res.teacher_id=$teacher_id, res.teacher_name=$teacher_name,
            res.knowledge_id=$knowledge_id, res.knowledge_name=$knowledge_name,
            res.chapter_id=$chapter_id, res.chapter_name=$chapter_name,
            res.use_count=COALESCE(res.use_count,0), res.complete_count=COALESCE(res.complete_count,0),
            res.completion_rate=COALESCE(res.completion_rate,0),
            res.recommend_score=COALESCE(res.recommend_score,0),
            res.effectiveness_score=COALESCE(res.effectiveness_score,0),
            res.avg_score_gain=COALESCE(res.avg_score_gain,0),
            res.avg_mastery_gain=COALESCE(res.avg_mastery_gain,0),
            res.post_practice_count=COALESCE(res.post_practice_count,0),
            res.post_practice_correct_rate=COALESCE(res.post_practice_correct_rate,0)
        MERGE (k:Knowledge {name:$knowledge_name})
        SET k.id=COALESCE(k.id,$knowledge_id)
        MERGE (res)-[:TEACHES]->(k)
        MERGE (c:Chapter {id:$chapter_id})
        SET c.name=$chapter_name
        MERGE (res)-[:BELONGS_TO]->(c)
        MERGE (t:Teacher {id:COALESCE($teacher_id,$teacher_name)})
        SET t.name=$teacher_name
        MERGE (t)-[:PROVIDES]->(res)
        """, **r)

def main():
    questions = [normalize_question(q) for q in load_json(os.path.join(RESOURCE_DIR, "questions.json"), {"questions": []}).get("questions", [])]
    resources = load_resources()
    history = load_json(os.path.join(RESOURCE_DIR, "question_history.json"), {})
    completions = load_json(os.path.join(RESOURCE_DIR, "resource_completion.json"), {})
    with driver.session() as session:
        session.execute_write(create_constraints)
        session.execute_write(import_questions, questions)
        session.execute_write(import_resources, resources)
        counts = session.run("""
        MATCH (k:Knowledge) WITH count(k) AS k
        MATCH (q:Question) WITH k, count(q) AS q
        MATCH (r:Resource) WITH k,q,count(r) AS r
        MATCH (s:Student) RETURN k AS knowledge_points, q AS questions, r AS resources, count(s) AS students
        """).single()
    wrong_count = sum(1 for h in history.values() for v in h.values() if v.get("wrong_count", 0) > 0 and not v.get("removed"))
    answer_count = sum(len(h) for h in history.values() if isinstance(h, dict))
    complete_count = sum(len(v) for v in completions.values() if isinstance(v, dict))
    print("初始化完成 {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print("知识点数量:", counts["knowledge_points"])
    print("题目数量:", counts["questions"])
    print("资源数量:", counts["resources"])
    print("学生数量:", counts["students"])
    print("答题记录数量:", answer_count)
    print("错题数量:", wrong_count)
    print("资源完成记录数量:", complete_count)

if __name__ == "__main__":
    main()
