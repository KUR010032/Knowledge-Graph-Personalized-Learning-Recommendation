from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys
import json
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from data_processing.neo4j_manager import Neo4jManager
from recommendation.hybrid_recommender import HybridRecommender
from recommendation.mastery_based import MasteryCalculator

app = Flask(__name__, static_folder='../frontend')
app.secret_key = Config.SECRET_KEY
CORS(app)

neo4j = Neo4jManager()

RESOURCE_MAP = {
    "第1章": ["第1章 操作系统概述.pptx"],
    "第2章": ["第2章 进程与线程.pptx"],
    "第3章": ["第3章 同步与互斥-詹.pptx"],
    "第4章": ["第4章 处理机调度.pptx"],
    "第5章": ["第5章 内存管理.pptx"],
    "第6章": ["第6章 文件管理.pptx"],
    "第7章": ["第7章 设备管理.pptx"],
    "第8章": ["第8章 操作系统安全.pptx"],
    "第9章": ["第9章 新型操作系统简介.pptx"],
    "第10章": ["第10章 操作系统设计问题.pptx"],
}

VIDEO_MAP = {
    "2.2.3 进程状态和转换": ["2.2.3 进程状态和转换.mp4"],
    "2.2.1 进程的概念": ["2.2.1 进程的概念.mp4"],
    "3.1.4 信号量和P、V操作": ["3.1.4 信号量和PV操作.mp4"],
    "3.4.2 死锁的必要条件": ["3.4.2 死锁的必要条件.mp4"],
    "3.5.2 哲学家进餐问题": ["3.5.2 哲学家进餐问题.mp4"],
}


def _find_resources_for_kp(kp_name):
    resources = []
    ch_match = re.match(r'(\d+)\.', kp_name)
    if ch_match:
        ch_num = int(ch_match.group(1))
        ch_key = f"第{ch_num}章"
        if ch_key in RESOURCE_MAP:
            for f in RESOURCE_MAP[ch_key]:
                resources.append({"name": f, "type": "ppt", "url": f"/api/download/{f}"})
    if kp_name in VIDEO_MAP:
        for f in VIDEO_MAP[kp_name]:
            resources.append({"name": f, "type": "video", "url": f"/api/download/{f}"})
    return resources


@app.route('/')
def index():
    return send_from_directory('../frontend', 'index.html')


@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get('user_id')
    password = data.get('password')
    role = data.get('role')

    if role == 'teacher':
        if user_id in Config.TEACHERS and Config.TEACHERS[user_id]['password'] == password:
            return jsonify({
                'success': True,
                'role': 'teacher',
                'name': Config.TEACHERS[user_id]['name']
            })
    elif role == 'student':
        if user_id in Config.STUDENTS and Config.STUDENTS[user_id]['password'] == password:
            return jsonify({
                'success': True,
                'role': 'student',
                'name': Config.STUDENTS[user_id]['name'],
                'full_id': Config.STUDENTS[user_id]['full_id']
            })

    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401


@app.route('/api/knowledge-graph/<student_id>')
def get_knowledge_graph(student_id):
    nodes = []
    edges = []
    node_ids = set()

    chapter_query = """
    MATCH (c:Chapter)
    OPTIONAL MATCH (stu:Student {id: $sid})-[r:MASTERED]->(c)
    RETURN c.name AS name, r.mastery AS mastery
    """
    result = neo4j.run_query(chapter_query, {"sid": student_id})
    for r in result:
        name = r["name"]
        if name and name not in node_ids:
            nodes.append({
                "id": name,
                "label": name,
                "level": 0,
                "mastery": r["mastery"],
                "group": "chapter"
            })
            node_ids.add(name)

    section_query = """
    MATCH (c:Chapter)-[:包含]->(s:Knowledge)
    WHERE s.name =~ '\\d+\\.\\d+ .*' AND NOT s.name =~ '\\d+\\.\\d+\\.\\d+.*'
    OPTIONAL MATCH (stu:Student {id: $sid})-[r:MASTERED]->(s)
    RETURN c.name AS chapter, s.name AS name, r.mastery AS mastery
    """
    result = neo4j.run_query(section_query, {"sid": student_id})
    for r in result:
        name = r["name"]
        chapter = r["chapter"]
        if name and name not in node_ids:
            nodes.append({
                "id": name,
                "label": name,
                "level": 1,
                "mastery": r["mastery"],
                "group": "section"
            })
            node_ids.add(name)
            if chapter:
                edges.append({"from": chapter, "to": name, "type": "包含"})

    subsection_query = """
    MATCH (s:Knowledge)-[:包含]->(k:Knowledge)
    WHERE s.name =~ '\\d+\\.\\d+ .*' AND NOT s.name =~ '\\d+\\.\\d+\\.\\d+.*'
    AND k.name =~ '\\d+\\.\\d+\\.\\d+.*'
    OPTIONAL MATCH (stu:Student {id: $sid})-[r:MASTERED]->(k)
    RETURN s.name AS section, k.name AS name, r.mastery AS mastery
    """
    result = neo4j.run_query(subsection_query, {"sid": student_id})
    for r in result:
        name = r["name"]
        section = r["section"]
        if name and name not in node_ids:
            nodes.append({
                "id": name,
                "label": name,
                "level": 2,
                "mastery": r["mastery"],
                "group": "subsection"
            })
            node_ids.add(name)
            if section:
                edges.append({"from": section, "to": name, "type": "包含"})

    prereq_query = """
    MATCH (a)-[r:先修]->(b)
    RETURN a.name AS from_name, b.name AS to_name
    """
    result = neo4j.run_query(prereq_query)
    for r in result:
        if r["from_name"] in node_ids and r["to_name"] in node_ids:
            edges.append({"from": r["from_name"], "to": r["to_name"], "type": "先修"})

    rel_query = """
    MATCH (a)-[r:相关]->(b)
    RETURN a.name AS from_name, b.name AS to_name
    """
    result = neo4j.run_query(rel_query)
    for r in result:
        if r["from_name"] in node_ids and r["to_name"] in node_ids:
            edges.append({"from": r["from_name"], "to": r["to_name"], "type": "相关"})

    return jsonify({"nodes": nodes, "edges": edges})


@app.route('/api/recommendations/<student_id>')
def get_recommendations(student_id):
    try:
        recommender = HybridRecommender(
            alpha=0.7, beta=0.3,
            lambda1=0.25, lambda2=0.2, lambda3=0.2, lambda4=0.2, lambda5=0.15
        )
        recommendations = recommender.recommend(student_id, top_k=10)
        recommender.close()

        return jsonify({
            'success': True,
            'recommendations': recommendations
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/questions/<knowledge_point>')
def get_questions_by_kp(knowledge_point):
    query = """
    MATCH (q:Question)-[:属于]->(k:Knowledge {name: $kp})
    RETURN q.id AS id, q.content AS content, q.options AS options,
           q.answer AS answer, q.difficulty AS difficulty,
           q.importance AS importance
    LIMIT 10
    """
    result = neo4j.run_query(query, {"kp": knowledge_point})
    questions = []
    for r in result:
        questions.append({
            "id": r["id"],
            "content": r["content"],
            "options": r["options"],
            "answer": r["answer"],
            "difficulty": r.get("difficulty", "medium"),
            "importance": r.get("importance", "normal")
        })
    return jsonify({'success': True, 'questions': questions})


@app.route('/api/resources')
def get_resources():
    resources = []
    if os.path.exists(Config.RESOURCE_DIR):
        for f in os.listdir(Config.RESOURCE_DIR):
            if f == "questions.json":
                continue
            ext = os.path.splitext(f)[1].lower()
            rtype = "video" if ext == ".mp4" else "ppt" if ext == ".pptx" else "doc" if ext in [".docx", ".doc"] else "other"
            resources.append({
                "name": f,
                "type": rtype,
                "url": f"/api/download/{f}"
            })
    return jsonify({'success': True, 'resources': resources})


@app.route('/api/download/<filename>')
def download_file(filename):
    return send_from_directory(Config.RESOURCE_DIR, filename)


@app.route('/api/progress/<student_id>')
def get_progress(student_id):
    query = """
    MATCH (s:Student)-[r:MASTERED]->(k:Knowledge)
    WHERE (s.id = $sid OR s.id CONTAINS $sid) AND k.name =~ '\\d+\\..*'
    RETURN k.name AS name, r.mastery AS mastery, r.total_questions AS total,
           r.correct_questions AS correct, k.difficulty AS difficulty,
           k.importance AS importance
    ORDER BY k.name
    """
    result = neo4j.run_query(query, {"sid": student_id})

    chapters = {}
    for r in result:
        name = r["name"]
        ch_match = re.match(r'(\d+)\.', name)
        ch_num = int(ch_match.group(1)) if ch_match else 0
        ch_key = f"第{ch_num}章"
        if ch_key not in chapters:
            chapters[ch_key] = {"chapter": ch_key, "items": [], "total_mastery": 0, "count": 0}
        chapters[ch_key]["items"].append({
            "knowledge_point": name,
            "mastery": r["mastery"],
            "total_questions": r["total"],
            "correct_questions": r["correct"],
            "difficulty": r.get("difficulty", "medium"),
            "importance": r.get("importance", "normal")
        })
        chapters[ch_key]["total_mastery"] += r["mastery"]
        chapters[ch_key]["count"] += 1

    progress = []
    for ch_key in sorted(chapters.keys()):
        ch = chapters[ch_key]
        ch["avg_mastery"] = ch["total_mastery"] / ch["count"] if ch["count"] > 0 else 0
        progress.append(ch)

    return jsonify({'success': True, 'progress': progress})


@app.route('/api/students')
def get_students():
    students = []
    for sid, info in Config.STUDENTS.items():
        students.append({
            "id": info.get('full_id', sid),
            "name": info['name']
        })
    students.sort(key=lambda x: x['id'])
    return jsonify({'success': True, 'students': students})


@app.route('/api/upload', methods=['POST'])
def upload_resource():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    resource_type = request.form.get('type', 'doc')
    chapter = request.form.get('chapter', '')
    knowledge_point = request.form.get('knowledge_point', '')
    
    if not chapter:
        return jsonify({'success': False, 'error': 'Chapter is required'}), 400
    
    filename = file.filename
    filepath = os.path.join(Config.RESOURCE_DIR, filename)
    file.save(filepath)
    
    return jsonify({
        'success': True,
        'message': f'File {filename} uploaded successfully',
        'filename': filename,
        'chapter': chapter,
        'type': resource_type
    })


@app.route('/api/submit', methods=['POST'])
def submit_answer():
    data = request.get_json()
    student_id = data.get('student_id')
    knowledge_point = data.get('knowledge')
    is_correct = data.get('is_correct')

    if not all([student_id, knowledge_point, is_correct is not None]):
        return jsonify({'success': False, 'error': 'Missing parameters'}), 400

    query = """
    MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge {name: $kp})
    SET r.total_questions = r.total_questions + 1
    """
    if is_correct:
        query += ", r.correct_questions = r.correct_questions + 1"
    query += """
    RETURN r.correct_questions AS correct, r.total_questions AS total
    """
    result = neo4j.run_query(query, {"sid": student_id, "kp": knowledge_point})

    if result:
        calculator = MasteryCalculator(alpha=0.7, beta=0.3)
        new_mastery = calculator.update_mastery_in_db(student_id, knowledge_point)
        calculator.close()
        return jsonify({
            'success': True,
            'new_mastery': new_mastery,
            'correct': result[0]["correct"],
            'total': result[0]["total"]
        })

    return jsonify({'success': False, 'error': 'Update failed'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
