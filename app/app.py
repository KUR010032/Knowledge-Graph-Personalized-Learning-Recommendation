# -*- coding: utf-8 -*-
from flask import Flask, request, render_template_string, render_template, jsonify, send_from_directory, session, redirect, url_for, make_response
from neo4j import GraphDatabase
from datetime import datetime, timedelta
import re
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'knowledge_graph_learning_system_2024'
PATH_RECOMMEND_CACHE = {}
NEO4J_OFFLINE_UNTIL = None

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "12345678"),
    connection_timeout=1
)

RESOURCE_DIR = os.path.join(os.path.dirname(__file__), "resources")

def neo4j_temporarily_offline():
    return NEO4J_OFFLINE_UNTIL is not None and datetime.now() < NEO4J_OFFLINE_UNTIL

def mark_neo4j_offline(seconds=20):
    global NEO4J_OFFLINE_UNTIL
    NEO4J_OFFLINE_UNTIL = datetime.now() + timedelta(seconds=seconds)

TEACHERS = {
    "1000002401": {"password": "admin1", "name": "教师"}
}

STUDENTS = {
    "3220602001": {"password": "123456", "name": "??", "full_id": "3220602001??"},
    "3220602002": {"password": "123456", "name": "??", "full_id": "3220602002??"},
    "3220602003": {"password": "123456", "name": "??", "full_id": "3220602003??"},
    "3220602004": {"password": "123456", "name": "??", "full_id": "3220602004??"},
    "3220602005": {"password": "123456", "name": "??", "full_id": "3220602005??"},
    "3220602006": {"password": "123456", "name": "??", "full_id": "3220602006??"},
    "3220602007": {"password": "123456", "name": "??", "full_id": "3220602007??"}
}

def get_user_profile(student_id):
    """
    ????????????????????????????????    ???????????????/???/???/????????????
    """
    with driver.session() as neo4j_session:
        # ?????????????????????
        query = """
        MATCH (stu:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
        RETURN k.name AS name, r.mastery AS mastery, r.total_questions AS total,
               r.correct_questions AS correct, k.difficulty AS difficulty,
               k.is_key AS is_key
        """
        result = neo4j_session.run(query, sid=student_id)
        
        total_kps = 0
        total_mastery = 0
        easy_mastery = []
        medium_mastery = []
        hard_mastery = []
        key_mastery = []
        total_correct = 0
        total_questions = 0
        
        for r in result:
            total_kps += 1
            mastery = r["mastery"] or 0
            total_mastery += mastery
            
            difficulty = r.get("difficulty") or "medium"
            if difficulty == "easy":
                easy_mastery.append(mastery)
            elif difficulty == "hard":
                hard_mastery.append(mastery)
            else:
                medium_mastery.append(mastery)
            
            if r.get("is_key"):
                key_mastery.append(mastery)
            
            total_correct += r.get("correct") or 0
            total_questions += r.get("total") or 0
        
        if total_kps == 0:
            return {
                "level": "???",
                "level_code": 0,
                "avg_mastery": 0,
                "accuracy": 0,
                "easy_avg": 0,
                "medium_avg": 0,
                "hard_avg": 0,
                "key_avg": 0,
                "total_kps": 0,
                "description": "?????????"
            }
        
        avg_mastery = total_mastery / total_kps
        accuracy = total_correct / total_questions if total_questions > 0 else 0
        
        easy_avg = sum(easy_mastery) / len(easy_mastery) if easy_mastery else 0
        medium_avg = sum(medium_mastery) / len(medium_mastery) if medium_mastery else 0
        hard_avg = sum(hard_mastery) / len(hard_mastery) if hard_mastery else 0
        key_avg = sum(key_mastery) / len(key_mastery) if key_mastery else 0
        
        # ??????????????????????
        weak_key_points = []
        weak_general_points = []
        key_points_total = 0
        key_points_weak = 0
        
        query2 = """
        MATCH (stu:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
        RETURN k.name AS name, r.mastery AS mastery, k.is_key AS is_key
        """
        result2 = neo4j_session.run(query2, sid=student_id)
        for r in result2:
            mastery = r["mastery"] or 0
            is_key = r.get("is_key") or False
            if is_key:
                key_points_total += 1
                if mastery < 0.5:
                    key_points_weak += 1
                    weak_key_points.append({"name": r["name"], "mastery": mastery})
            elif mastery < 0.5:
                weak_general_points.append({"name": r["name"], "mastery": mastery})
        
        weak_key_points.sort(key=lambda x: x["mastery"])
        weak_general_points.sort(key=lambda x: x["mastery"])
        
        # ????????????40% + ?????0% + ??????20% + ??????10%
        composite_score = avg_mastery * 0.4 + accuracy * 0.3 + hard_avg * 0.2 + key_avg * 0.1
        
        # ??????????????????????????????
        if avg_mastery >= 0.90:
            level = "???"
            level_code = 4
        elif avg_mastery >= 0.75:
            level = "???"
            level_code = 3
        elif avg_mastery >= 0.60:
            level = "???"
            level_code = 2
        else:
            level = "???"
            level_code = 1
        
        # ??????????????????????????????
        suggestions = []
        
        # 1. ??????????
        if key_avg < 0.3:
            if weak_key_points:
                names = [display_kp_name(p["name"]) for p in weak_key_points[:3]]
                suggestions.append("????????????{:.0f}%?????????{}".format(key_avg * 100, "?".join(names)))
            else:
                suggestions.append("???????????{:.0f}%????????????".format(key_avg * 100))
        elif key_avg < 0.6:
            if weak_key_points:
                names = [display_kp_name(p["name"]) for p in weak_key_points[:2]]
                suggestions.append("???????????{}?????????????".format("?".join(names)))
            else:
                suggestions.append(f"?????????????????{key_avg*100:.0f}%?????????????????????")
        elif key_avg < 0.8:
            suggestions.append(f"???????????????{key_avg*100:.0f}%??????????????????")
        else:
            suggestions.append("??????????{:.0f}%????????????????".format(key_avg * 100))
        
        # 2. ??????????
        if weak_general_points:
            names = [display_kp_name(p["name"]) for p in weak_general_points[:3]]
            suggestions.append("??????????{}".format("?".join(names)))
        else:
            suggestions.append("?????????????????????")
        
        # 3. ?????????
        if easy_avg < 0.5:
            suggestions.append("??????????????????????????")
        elif easy_avg < 0.7:
            suggestions.append(f"??????????????{easy_avg*100:.0f}%???????????????")
        elif hard_avg < 0.4 and hard_avg > 0:
            suggestions.append("??????????????????????????")
        elif hard_avg >= 0.6:
            suggestions.append(f"????????????{hard_avg*100:.0f}%??????????????????")
        else:
            suggestions.append("??????????????????????????????")
        
        # 4. ???????????????
        if level == "???":
            suggestions.append("???????????????????????")
        elif level == "???":
            suggestions.append("?????????????????????????????")
        elif level == "???":
            suggestions.append("????????????????????????????????????")
        else:
            suggestions.append("???????????????????????????????????????")
        
        description = "?".join(suggestions)
        
        # ??????????????????????
        chapter_details = []
        chapter_query = """
        MATCH (c:Chapter)-[:???]->(s:Knowledge)
        WHERE c.name STARTS WITH '?1?' OR c.name STARTS WITH '?2?' OR c.name STARTS WITH '?3?'
        OPTIONAL MATCH (stu:Student {id: $sid})-[r:MASTERED]->(s)
        OPTIONAL MATCH (s)-[:???]->(ss:Knowledge)
        OPTIONAL MATCH (stu2:Student {id: $sid})-[r2:MASTERED]->(ss)
        RETURN c.name AS chapter, s.name AS section_name, r.mastery AS section_mastery,
               ss.name AS subsection_name, r2.mastery AS subsection_mastery,
               s.is_key AS section_is_key, ss.is_key AS subsection_is_key
        ORDER BY c.name, s.name, ss.name
        """
        chapter_result = neo4j_session.run(chapter_query, sid=student_id)
        
        current_chapter = None
        current_section = None
        chapters_map = {}
        
        for record in chapter_result:
            ch_name = record["chapter"]
            sec_name = record["section_name"]
            subsec_name = record["subsection_name"]
            
            if ch_name and ch_name not in chapters_map:
                chapters_map[ch_name] = {
                    "name": ch_name,
                    "sections": [],
                    "avg_mastery": 0,
                    "total_points": 0,
                    "weak_count": 0,
                    "strong_count": 0
                }
            
            if sec_name and subsec_name:
                # ????????????
                if not any(s["name"] == sec_name for s in chapters_map[ch_name]["sections"]):
                    chapters_map[ch_name]["sections"].append({
                        "name": sec_name,
                        "mastery": record["section_mastery"] or 0,
                        "is_key": record.get("section_is_key") or False,
                        "subsections": []
                    })
                
                for sec in chapters_map[ch_name]["sections"]:
                    if sec["name"] == sec_name:
                        sub_mastery = record["subsection_mastery"] or 0
                        sec["subsections"].append({
                            "name": subsec_name,
                            "mastery": sub_mastery,
                            "is_key": record.get("subsection_is_key") or False
                        })
                        
                        # ???
                        chapters_map[ch_name]["total_points"] += 1
                        chapters_map[ch_name]["avg_mastery"] += sub_mastery
                        if sub_mastery < 0.5:
                            chapters_map[ch_name]["weak_count"] += 1
                        elif sub_mastery >= 0.8:
                            chapters_map[ch_name]["strong_count"] += 1
        
        # ?????????????
        for ch in chapters_map.values():
            if ch["total_points"] > 0:
                ch["avg_mastery"] = round(ch["avg_mastery"] / ch["total_points"], 3)
            else:
                ch["avg_mastery"] = 0
            
            # ?????????????????????????????????
            for sec in ch["sections"]:
                if sec["subsections"]:
                    sec_total = sum(sub["mastery"] for sub in sec["subsections"])
                    sec["mastery"] = round(sec_total / len(sec["subsections"]), 3)
                else:
                    sec["mastery"] = 0
        
        chapter_details = list(chapters_map.values())
        chapter_details.sort(key=lambda x: x["name"])
        
        return {
            "level": level,
            "level_code": level_code,
            "avg_mastery": round(avg_mastery, 3),
            "accuracy": round(accuracy, 3),
            "easy_avg": round(easy_avg, 3),
            "medium_avg": round(medium_avg, 3),
            "hard_avg": round(hard_avg, 3),
            "key_avg": round(key_avg, 3),
            "composite_score": round(composite_score, 3),
            "total_kps": total_kps,
            "total_questions": total_questions,
            "total_correct": total_correct,
            "description": description,
            "chapter_details": chapter_details
        }

def get_knowledge_graph(student_id):
    with driver.session() as neo4j_session:
        nodes = []
        edges = []
        node_ids = set()
        mastery_data = {}  # ????????????????        
        # ??????????????????????????????????
        subsection_query = """
        MATCH (kp:Knowledge)
        WHERE kp.name =~ '^\\d+\\.\\d+.*'
        OPTIONAL MATCH (stu:Student {id: $sid})-[r:MASTERED]->(kp)
        RETURN kp.name AS name, r.mastery AS mastery, 
               r.total_questions AS total, r.correct_questions AS correct,
               kp.difficulty AS difficulty, kp.is_key AS is_key
        """
        subsection_result = neo4j_session.run(subsection_query, sid=student_id)
        
        # ?????????????????????
        kp_mastery = {}
        for record in subsection_result:
            kp_name = record["name"]
            mastery = record["mastery"] or 0
            total = record["total"] or 0
            correct = record["correct"] or 0
            
            # ????????????mastery?????????????????
            if total > 0 and mastery == 0:
                accuracy = correct / total
                difficulty_factor = {"easy": 0.9, "medium": 0.7, "hard": 0.5}.get(record.get("difficulty"), 0.7)
                practice_factor = min(total / 5, 1.0)  # ???5?????????
                mastery = round(0.6 * accuracy + 0.25 * practice_factor + 0.15 * difficulty_factor, 3)
            
            kp_mastery[kp_name] = {
                "name": kp_name,
                "mastery": mastery,
                "total": total,
                "correct": correct
            }
            
            mastery_data[kp_name] = mastery
        
        # ???????????????????????????????
        kp_stats = {kp_name: {
            "mastery": info["mastery"],
            "total_questions": info["total"],
            "correct_questions": info["correct"]
        } for kp_name, info in kp_mastery.items()}
        
        # ??????????????????????????
        structure_query = """
        MATCH (ch:Chapter)-[:???]->(sec:Knowledge)
        WHERE ch.name STARTS WITH '?1?' OR ch.name STARTS WITH '?2?' OR ch.name STARTS WITH '?3?'
        OPTIONAL MATCH (sec)-[:???]->(sub:Knowledge)
        WHERE sub.name =~ '^\\d+\\.\\d+.*'
        RETURN ch.name AS chapter, ch.number AS chapter_num,
               sec.name AS section, sec.number AS section_num,
               COLLECT(DISTINCT sub.name) AS subsections
        """
        structure_result = neo4j_session.run(structure_query)
        
        # ???????????????
        structure_records = list(structure_result)
        structure_records.sort(key=lambda x: (x["chapter_num"] or 0, x["section_num"] or 0))
        
        # ?????????????????????????????????
        chapter_kps = {}  # ??? -> [????????
        section_kps = {}  # ??? -> [????????
        
        for record in structure_records:
            ch_name = record["chapter"]
            sec_name = record["section"]
            subs = record["subsections"] or []
            
            # ??????????????????
            if sec_name not in section_kps:
                section_kps[sec_name] = []
            
            for sub_name in subs:
                if sub_name in kp_mastery:
                    section_kps[sec_name].append(sub_name)
                    # ??????????
                    if ch_name not in chapter_kps:
                        chapter_kps[ch_name] = []
                    chapter_kps[ch_name].append(sub_name)
        
        # ??????????????????????
        for sec_name, kps in section_kps.items():
            if kps:
                avg_mastery = sum(kp_mastery[kp]["mastery"] for kp in kps) / len(kps)
                total_q = sum(kp_mastery[kp]["total"] for kp in kps)
                total_c = sum(kp_mastery[kp]["correct"] for kp in kps)
                mastery_data[sec_name] = round(avg_mastery, 3)
                # ????????????????
                kp_stats[sec_name] = {
                    "mastery": round(avg_mastery, 3),
                    "total_questions": total_q,
                    "correct_questions": total_c,
                    "child_count": len(kps)
                }
            else:
                mastery_data[sec_name] = 0
                kp_stats[sec_name] = {"mastery": 0, "total_questions": 0, "correct_questions": 0, "child_count": 0}
        
        # ??????????????????????
        for ch_name, kps in chapter_kps.items():
            if kps:
                avg_mastery = sum(kp_mastery[kp]["mastery"] for kp in kps) / len(kps)
                total_q = sum(kp_mastery[kp]["total"] for kp in kps)
                total_c = sum(kp_mastery[kp]["correct"] for kp in kps)
                mastery_data[ch_name] = round(avg_mastery, 3)
                # ????????????????
                kp_stats[ch_name] = {
                    "mastery": round(avg_mastery, 3),
                    "total_questions": total_q,
                    "correct_questions": total_c,
                    "child_count": len(kps)
                }
            else:
                mastery_data[ch_name] = 0
                kp_stats[ch_name] = {"mastery": 0, "total_questions": 0, "correct_questions": 0, "child_count": 0}
        
        # ???????????????????????????
        # ????????????????????????
        for ch_name in chapter_kps.keys():
            if ch_name not in node_ids:
                stats = kp_stats.get(ch_name, {})
                nodes.append({
                    "id": ch_name,
                    "label": ch_name,
                    "level": 0,
                    "mastery": mastery_data.get(ch_name, 0),
                    "group": "chapter",
                    "total_questions": stats.get("total_questions", 0),
                    "correct_questions": stats.get("correct_questions", 0),
                    "child_count": stats.get("child_count", 0)
                })
                node_ids.add(ch_name)
        
        # ????????????????????????
        for sec_name in section_kps.keys():
            if sec_name not in node_ids:
                stats = kp_stats.get(sec_name, {})
                nodes.append({
                    "id": sec_name,
                    "label": display_kp_name(sec_name),
                    "level": 1,
                    "mastery": mastery_data.get(sec_name, 0),
                    "group": "section",
                    "total_questions": stats.get("total_questions", 0),
                    "correct_questions": stats.get("correct_questions", 0),
                    "child_count": stats.get("child_count", 0)
                })
                node_ids.add(sec_name)
        
        # ????????????????
        for kp_name, kp_info in kp_mastery.items():
            if kp_name not in node_ids:
                nodes.append({
                    "id": kp_name,
                    "label": display_kp_name(kp_name),
                    "level": 2,
                    "mastery": kp_info["mastery"],
                    "group": "subsection"
                })
                node_ids.add(kp_name)
        
        # ??.5?????????????????"???
        root_query = """
        MATCH (c:Course {name: '??????'})
        RETURN c.name AS name
        """
        root_result = neo4j_session.run(root_query)
        root_record = root_result.single()
        
        if root_record:
            root_name = root_record["name"]
            # ?????????????????????????????????
            if kp_mastery:
                all_mastery_values = [kp["mastery"] for kp in kp_mastery.values()]
                all_total_q = sum(kp["total"] for kp in kp_mastery.values())
                all_total_c = sum(kp["correct"] for kp in kp_mastery.values())
                root_mastery = round(sum(all_mastery_values) / len(all_mastery_values), 3)
                root_accuracy = round(all_total_c / all_total_q * 100, 1) if all_total_q > 0 else 0
            else:
                root_mastery = 0
                all_total_q = 0
                all_total_c = 0
                root_accuracy = 0
            
            # ??????????????????
            kp_stats[root_name] = {
                "mastery": root_mastery,
                "total_questions": all_total_q,
                "correct_questions": all_total_c,
                "child_count": len(chapter_kps),
                "accuracy": root_accuracy
            }
            
            # ??????????????????????
            nodes.insert(0, {  # ??????????????????????????                "id": root_name,
                "label": root_name,
                "level": -1,  # ?????????-1
                "mastery": root_mastery,
                "group": "root",
                "total_questions": all_total_q,
                "correct_questions": all_total_c,
                "accuracy": root_accuracy,
                "child_count": len(chapter_kps)
            })
            node_ids.add(root_name)
            
            # ????????????????
            for ch_name in chapter_kps.keys():
                if ch_name in node_ids:
                    edges.append({"from": root_name, "to": ch_name, "type": "???"})
        
        # ????????????
        # ???????????+ ????????????
        for record in structure_records:  # ?????????????????            ch_name = record["chapter"]
            sec_name = record["section"]
            if ch_name in node_ids and sec_name in node_ids:
                edges.append({"from": ch_name, "to": sec_name, "type": "???"})
            
            # ????????????
            for sub_name in (record["subsections"] or []):
                if sub_name in node_ids and sec_name in node_ids:
                    edges.append({"from": sec_name, "to": sub_name, "type": "???"})
        
        # ???????????????????????????????????????
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge["from"])
            connected_nodes.add(edge["to"])
        
        # ????????????????????????
        disconnected_kps = [kp for kp in kp_mastery.keys() if kp not in connected_nodes]
        
        if disconnected_kps:
            # ?????????????????????????????????
            for kp_name in disconnected_kps:
                # ???????????????"1.1.1 xxx"
                parts = kp_name.split('.')
                if len(parts) >= 2:
                    chapter_prefix = parts[0] + '.'  # ??? "1."
                    
                    # ??????????
                    matched_section = None
                    for sec_name in section_kps.keys():
                        if sec_name.startswith(chapter_prefix):
                            # ???????????????????????
                            section_prefix = '.'.join(parts[:2]) + '.'  # ??? "1.1."
                            if kp_name.startswith(section_prefix):
                                matched_section = sec_name
                                break
                    
                    if matched_section and matched_section in node_ids:
                        edges.append({"from": matched_section, "to": kp_name, "type": "???"})
                        
                        # ???????????????????
                        for record in structure_records:
                            if record["section"] == matched_section:
                                ch_name = record["chapter"]
                                if ch_name in node_ids:
                                    # ?????????????
                                    edge_exists = any(e["from"] == ch_name and e["to"] == matched_section for e in edges)
                                    if not edge_exists:
                                        edges.append({"from": ch_name, "to": matched_section, "type": "???"})
                                break
        
        # ???"???"?????????????????????
        rel_query = """
        MATCH (a)-[r:???]->(b)
        WHERE (a:Chapter AND (a.name STARTS WITH '?1?' OR a.name STARTS WITH '?2?' OR a.name STARTS WITH '?3?'))
           OR (b:Chapter AND (b.name STARTS WITH '?1?' OR b.name STARTS WITH '?2?' OR b.name STARTS WITH '?3?'))
           OR (a:Knowledge AND (a.name STARTS WITH '1.' OR a.name STARTS WITH '2.' OR a.name STARTS WITH '3.'))
           OR (b:Knowledge AND (b.name STARTS WITH '1.' OR b.name STARTS WITH '2.' OR b.name STARTS WITH '3.'))
        RETURN a.name AS from_name, b.name AS to_name
        """
        rel_result = neo4j_session.run(rel_query)
        for record in rel_result:
            from_name = record["from_name"]
            to_name = record["to_name"]
            if from_name in node_ids and to_name in node_ids:
                edges.append({"from": from_name, "to": to_name, "type": "???"})
        
        # ???"???"?????????????????????
        prereq_query = """
        MATCH (a)-[r:???]->(b)
        WHERE (a:Chapter AND (a.name STARTS WITH '?1?' OR a.name STARTS WITH '?2?' OR a.name STARTS WITH '?3?'))
           OR (b:Chapter AND (b.name STARTS WITH '?1?' OR b.name STARTS WITH '?2?' OR b.name STARTS WITH '?3?'))
           OR (a:Knowledge AND (a.name STARTS WITH '1.' OR a.name STARTS WITH '2.' OR a.name STARTS WITH '3.'))
           OR (b:Knowledge AND (b.name STARTS WITH '1.' OR b.name STARTS WITH '2.' OR b.name STARTS WITH '3.'))
        RETURN a.name AS from_name, b.name AS to_name
        """
        prereq_result = neo4j_session.run(prereq_query)
        for record in prereq_result:
            from_name = record["from_name"]
            to_name = record["to_name"]
            if from_name in node_ids and to_name in node_ids:
                edges.append({"from": from_name, "to": to_name, "type": "???"})
        
        return {"nodes": nodes, "edges": edges, "statistics": kp_stats}

def parse_resource_info(filename):
    filename = str(filename or "")
    sec_match = re.search(r"(\d+)\.(\d+)\.(\d+)", filename)
    if sec_match:
        return {
            "level": "section",
            "ch": int(sec_match.group(1)),
            "big": int(sec_match.group(2)),
            "sec": int(sec_match.group(3))
        }
        
    big_match = re.search(r"(\d+)\.(\d+)", filename)
    if big_match:
        return {
            "level": "big",
            "ch": int(big_match.group(1)),
            "big": int(big_match.group(2)),
            "sec": None
        }

    ch_match = re.search(r"(?:第\s*)?(\d+)\s*(?:章|chapter)", filename, re.I)
    if ch_match:
        return {"level": "chapter", "ch": int(ch_match.group(1)), "big": None, "sec": None}

    return {"level": "unknown", "ch": None, "big": None, "sec": None}

def resource_text_key(text):
    text = os.path.splitext(os.path.basename(str(text or "")))[0].lower()
    text = re.sub(r"\d+(?:\.\d+)*|第\d+章|操作系统|习题集|专题|讲解|pptx?|docx?|pdf|mp4|视频|文档|资源", " ", text)
    return re.sub(r"[\s_\-—－·（）()]+", "", text)

def knowledge_point_catalog():
    points = {}
    for q in load_questions().get("questions", []):
        kp = q.get("knowledge_point") or ""
        code = flow_kp_code(kp)
        if code and not re.fullmatch(r"\d+(?:\.\d+)*", kp.strip()):
            points[code] = kp
    try:
        if not neo4j_temporarily_offline():
            with driver.session() as neo4j_session:
                rows = neo4j_session.run("""
                MATCH (k:Knowledge)
                WHERE k.name =~ '^\\d+(\\.\\d+){1,2}.*' AND NOT k.name =~ '^\\d+(\\.\\d+){1,2}\\s*$'
                RETURN k.name AS name
                LIMIT 800
                """)
                for row in rows:
                    name = row["name"] or ""
                    code = flow_kp_code(name)
                    if code:
                        points.setdefault(code, name)
    except Exception:
        pass
    return [{"code": code, "name": name, "key": resource_text_key(display_kp_name(name))}
            for code, name in points.items()]

RESOURCE_KEYWORD_MAP = [
    ("死锁", "3.4"), ("银行家", "3.4"), ("同步", "3.2"), ("互斥", "3.1"),
    ("临界", "3.1"), ("线程", "2.3"), ("进程", "2.2"), ("调度", "2.4"),
    ("pv", "3.2"), ("信号量", "3.1.4"), ("读者写者", "3.5.1"), ("哲学家", "3.5.2"),
    ("操作系统概述", "1"), ("计算机系统", "1.1.2"), ("基本概念", "1.1.1"),
]

def infer_resource_info(filename):
    info = parse_resource_info(filename)
    if info["level"] != "unknown":
        return info
    key = resource_text_key(filename)
    best = None
    for item in knowledge_point_catalog():
        kp_key = item["key"]
        if not kp_key:
            continue
        score = 0
        if kp_key in key:
            score = len(kp_key) + 20
        elif key and key in kp_key:
            score = len(key) + 10
        else:
            for i in range(2, len(kp_key) + 1):
                part = kp_key[:i]
                if part in key:
                    score = max(score, i)
        if score and (not best or score > best[0]):
            best = (score, item["code"])
    if not best:
        lower = str(filename).lower()
        for word, code in RESOURCE_KEYWORD_MAP:
            if word.lower() in lower:
                best = (10, code)
                break
    if best:
        parts = best[1].split(".")
        ch = int(parts[0]) if parts[0].isdigit() else None
        big = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
        sec = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
        return {"level": "section" if sec else ("big" if big else "chapter"), "ch": ch, "big": big, "sec": sec}
    return info

def match_resources(topic_name, all_resources=None):
    """
    ????????????????????????????????
    ???????????> ?????> ??? > ???????????    ????????????????????    """
    if not os.path.exists(RESOURCE_DIR):
        return []

    files = os.listdir(RESOURCE_DIR) if not all_resources else [r["name"] for r in all_resources]
    topic_info = infer_resource_info(topic_name)
    if topic_info["level"] == "unknown":
        return []

    scored = []
    for f in files:
        f_info = infer_resource_info(f)
        if f_info["level"] == "unknown":
            continue

        score = 0
        level_tag = ""
        match_level = 0

        if f_info["ch"] == topic_info["ch"]:
            score += 10

            if topic_info["big"] is not None and f_info["big"] == topic_info["big"]:
                score += 20

                if topic_info["sec"] is not None and f_info["sec"] == topic_info["sec"]:
                    score += 50
                    level_tag = "??????"
                    match_level = 3
                else:
                    score += 15
                    level_tag = "?????"
                    match_level = 2
            else:
                score += 8
                level_tag = "??????"
                match_level = 1
        else:
            continue

        if score > 0:
            scored.append({"file": f, "score": score, "level": level_tag, "match_level": match_level})

    scored.sort(key=lambda x: (-x["match_level"], -x["score"]))

    if len(scored) == 0:
        kp_clean = re.sub(r'^\d+\.\d+(\.\d+)?\s*', '', topic_name).lower()
        for f in files:
            f_lower = f.lower()
            if kp_clean in f_lower:
                scored.append({"file": f, "score": 5, "level": "?????", "match_level": 0})

    return scored[:3]

def get_low_mastery_topics(sid):
    query = """
    MATCH (s:Student {id:$sid})-[r:MASTERED]->(k:Knowledge)
    WHERE r.mastery < 0.6 AND k.name =~ '\\d+.*'
    RETURN k.name AS name, r.mastery AS mastery
    ORDER BY r.mastery ASC
    LIMIT 5
    """
    with driver.session() as session:
        res = session.run(query, sid=sid)
        return [{"name": r["name"], "mastery": r["mastery"]} for r in res]

def get_recommendations(sid):
    low_topics = get_low_mastery_topics(sid)
    recs = {}
    for t in low_topics:
        matched = match_resources(t["name"])
        recs[t["name"]] = {
            "files": matched,
            "mastery": f"{t['mastery']*100:.1f}%"
        }
    return recs

def get_mastery_status(score):
    if score < 0.4:
        return "??????"
    if score < 0.7:
        return "???"
    if score < 0.85:
        return "??????"
    return "??????"

def get_kp_code(kp_name):
    match = re.match(r"^(\d+(?:\.\d+){0,2})", kp_name or "")
    return match.group(1) if match else ""

def build_path_recommendation(user_id, resources, behavior_profile, target_kp=None):
    with driver.session() as neo4j_session:
        kp_rows = list(neo4j_session.run("""
        MATCH (k:Knowledge)
        WHERE (k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.')
        AND NOT (k)-[:???]->(:Knowledge)
        OPTIONAL MATCH (:Student {id: $sid})-[m:MASTERED]->(k)
        RETURN k.name AS name, COALESCE(m.mastery, 0) AS mastery, COALESCE(k.is_key, false) AS is_key
        ORDER BY k.name
        """, sid=user_id))
        mastery_map = {r["name"]: r["mastery"] or 0 for r in kp_rows}
        all_kps = [{"name": r["name"], "mastery": r["mastery"] or 0, "is_key": r["is_key"] or False} for r in kp_rows]

        weak_diagnosis = []
        for kp in all_kps:
            score = kp["mastery"]
            if score < 0.7:
                weak_diagnosis.append({
                    "name": kp["name"],
                    "score": round(score, 3),
                    "status": get_mastery_status(score)
                })
        weak_diagnosis.sort(key=lambda x: (x["score"], x["name"]))

        target_options = []
        option_names = set()
        for kp in all_kps:
            name = kp["name"]
            if kp["is_key"] or any(key in name for key in ["??", "??", "???", "??", "??", "???", "??"]):
                target_options.append({
                    "name": name,
                    "score": round(kp["mastery"], 3),
                    "status": get_mastery_status(kp["mastery"])
                })
                option_names.add(name)
        for item in weak_diagnosis[:12]:
            if item["name"] not in option_names:
                target_options.append(item)
                option_names.add(item["name"])
        target_options = sorted(target_options, key=lambda x: (x["score"], x["name"]))[:30]

        if not target_kp or target_kp not in mastery_map:
            target_kp = target_options[0]["name"] if target_options else (all_kps[0]["name"] if all_kps else "")

        prereq_rows = list(neo4j_session.run("""
        MATCH (target:Knowledge {name: $target})
        MATCH p=(pre:Knowledge)-[:???*0..10]->(target)
        UNWIND nodes(p) AS n
        WITH DISTINCT n, target
        OPTIONAL MATCH sp=(n)-[:???*0..10]->(target)
        RETURN n.name AS name, min(length(sp)) AS distance_to_target
        ORDER BY distance_to_target DESC, n.name
        """, target=target_kp))

        prereq_path = []
        seen = set()
        for row in prereq_rows:
            name = row["name"]
            if name and name not in seen:
                seen.add(name)
                prereq_path.append({
                    "name": name,
                    "distance_to_target": row["distance_to_target"] if row["distance_to_target"] is not None else 0,
                    "score": round(mastery_map.get(name, 0), 3),
                    "status": get_mastery_status(mastery_map.get(name, 0))
                })
        if target_kp and target_kp not in seen:
            prereq_path.append({
                "name": target_kp,
                "distance_to_target": 0,
                "score": round(mastery_map.get(target_kp, 0), 3),
                "status": get_mastery_status(mastery_map.get(target_kp, 0))
            })

        successor_counts = {}
        max_successor_count = 1
        for row in neo4j_session.run("""
        MATCH (k:Knowledge)
        WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
        OPTIONAL MATCH (k)-[:???*1..6]->(next:Knowledge)
        RETURN k.name AS name, count(DISTINCT next) AS successor_count
        """):
            successor_counts[row["name"]] = row["successor_count"] or 0
            max_successor_count = max(max_successor_count, row["successor_count"] or 0)

        related_distance = {}
        for row in neo4j_session.run("""
        MATCH p=(k:Knowledge)-[:???|???*0..2]-(other:Knowledge)
        WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
        RETURN k.name AS source, other.name AS target, min(length(p)) AS distance
        """):
            related_distance[(row["source"], row["target"])] = row["distance"] or 0

        viewed_resources = {}
        for row in neo4j_session.run("""
        MATCH (:Student {id: $sid})-[r:VIEWED]->(res:Resource)
        RETURN res.name AS name, COALESCE(r.view_count, 0) AS view_count, COALESCE(r.download_count, 0) AS download_count
        """, sid=user_id):
            viewed_resources[row["name"]] = (row["view_count"] or 0) + (row["download_count"] or 0)

    def kscore(kp):
        mastery = mastery_map.get(kp["name"], 0)
        weak = 1 - mastery
        pre_impact = successor_counts.get(kp["name"], 0) / max_successor_count
        distance = kp.get("distance_to_target", 0)
        goal_rel = 1 / (distance + 1) if distance is not None else 0
        return round(0.5 * weak + 0.3 * pre_impact + 0.2 * goal_rel, 3)

    gaps = []
    for kp in prereq_path:
        if kp["score"] < 0.7:
            kp["knowledge_score"] = kscore(kp)
            kp["explain"] = "?????????????????{:.2f}???????0.70?????????????????".format(kp["score"])
            gaps.append(kp)

    pref_video = behavior_profile.get("pref_video", 0.33) if behavior_profile else 0.33
    pref_ppt = behavior_profile.get("pref_ppt", 0.33) if behavior_profile else 0.33
    pref_practice = behavior_profile.get("pref_practice", 0.33) if behavior_profile else 0.33
    max_pref = max(pref_video, pref_ppt, pref_practice, 0.01)

    def resource_type(resource_name):
        ext = resource_name.rsplit(".", 1)[-1].lower() if "." in resource_name else ""
        if ext == "mp4":
            return "video"
        if ext in ("ppt", "pptx", "pdf", "doc", "docx"):
            return "document"
        return "practice"

    def resource_kp_code(res):
        code = get_kp_code(res.get("knowledge_point", ""))
        if code:
            return code
        info = parse_resource_info(res.get("name", ""))
        if info.get("ch") and info.get("big") and info.get("sec"):
            return "{}.{}.{}".format(info["ch"], info["big"], info["sec"])
        if info.get("ch") and info.get("big"):
            return "{}.{}".format(info["ch"], info["big"])
        return str(info.get("ch") or "")

    def calc_content_match(res_code, kp_code):
        if not res_code or not kp_code:
            return 0
        if res_code == kp_code or kp_code.startswith(res_code + ".") or res_code.startswith(kp_code + "."):
            return 1
        if ".".join(res_code.split(".")[:2]) == ".".join(kp_code.split(".")[:2]):
            return 0.6
        if res_code.split(".")[0] == kp_code.split(".")[0]:
            return 0.3
        return 0

    def calc_difficulty_match(mastery, res):
        name = res.get("name", "")
        if mastery < 0.4:
            expected = "basic"
        elif mastery < 0.7:
            expected = "medium"
        else:
            expected = "advanced"
        info = parse_resource_info(name)
        if any(word in name for word in ["???", "???", "???", "???"]):
            actual = "basic"
        elif any(word in name for word in ["???", "???", "???", "???", "???", "???"]):
            actual = "advanced"
        elif info.get("sec") and info["sec"] >= 3:
            actual = "advanced"
        else:
            actual = "medium"
        if expected == actual:
            return 1
        if {"basic", "advanced"} == {expected, actual}:
            return 0
        return 0.5

    def calc_behavior_pref(res):
        rtype = resource_type(res.get("name", ""))
        if rtype == "video":
            return round(pref_video / max_pref, 3)
        if rtype == "document":
            return round(pref_ppt / max_pref, 3)
        return round(pref_practice / max_pref, 3)

    def calc_resource_score(res, kp):
        kp_name = kp["name"]
        kp_code = get_kp_code(kp_name)
        res_code = resource_kp_code(res)
        mastery = mastery_map.get(kp_name, 0)
        content_match = calc_content_match(res_code, kp_code)
        covered = []
        for name, score in mastery_map.items():
            if score < 0.7 and calc_content_match(res_code, get_kp_code(name)) >= 0.6:
                covered.append(name)
        weak_cover = len(covered) / max(1, len([name for name in mastery_map if calc_content_match(res_code, get_kp_code(name)) >= 0.6]))
        difficulty_match = calc_difficulty_match(mastery, res)
        behavior_pref = calc_behavior_pref(res)
        if content_match == 1:
            graph_rel = 1
        else:
            distance = related_distance.get((res.get("knowledge_point", ""), kp_name))
            graph_rel = 1 / (distance + 1) if distance is not None else content_match
        watched_penalty = 0.3 if res.get("name") in viewed_resources else 0
        score = (
            0.4 * content_match +
            0.25 * weak_cover +
            0.15 * difficulty_match +
            0.1 * behavior_pref +
            0.1 * graph_rel -
            watched_penalty
        )
        reasons = []
        if content_match >= 1:
            reasons.append("?????????????")
        elif content_match > 0:
            reasons.append("???????????????")
        if weak_cover > 0:
            reasons.append("?????????")
        if difficulty_match >= 1:
            reasons.append("?????????????????????")
        if watched_penalty == 0:
            reasons.append("????????????")
        else:
            reasons.append("???????????????")
        return {
            **res,
            "resource_type": resource_type(res.get("name", "")),
            "score": round(score, 3),
            "score_detail": {
                "content_match": round(content_match, 3),
                "weak_cover": round(weak_cover, 3),
                "difficulty_match": round(difficulty_match, 3),
                "behavior_pref": round(behavior_pref, 3),
                "graph_rel": round(graph_rel, 3),
                "watched_penalty": watched_penalty
            },
            "reasons": reasons
        }

    def rerank_with_diversity(scored):
        sorted_items = sorted(scored, key=lambda x: x["score"], reverse=True)
        selected = []
        used_types = set()
        for item in sorted_items:
            if item["resource_type"] not in used_types:
                selected.append(item)
                used_types.add(item["resource_type"])
            if len(selected) >= 3:
                return selected
        for item in sorted_items:
            if item not in selected:
                selected.append(item)
            if len(selected) >= 3:
                break
        return selected

    path_steps = []
    for idx, kp in enumerate(gaps, 1):
        scored_resources = []
        for res in resources:
            scored = calc_resource_score(res, kp)
            if scored["score"] > 0.05:
                scored_resources.append(scored)
        path_steps.append({
            "step": idx,
            "knowledge_point": kp["name"],
            "mastery": kp["score"],
            "status": kp["status"],
            "knowledge_score": kp["knowledge_score"],
            "explain": kp["explain"],
            "resources": rerank_with_diversity(scored_resources)
        })

    return {
        "target_options": target_options,
        "selected_target": target_kp,
        "weak_diagnosis": weak_diagnosis[:12],
        "prerequisite_path": prereq_path,
        "learning_path": path_steps,
        "threshold": 0.7,
        "formulas": {
            "knowledge_score": "0.5*Weak(u,k)+0.3*PreImpact(k)+0.2*GoalRel(k,target)",
            "resource_score": "0.4*ContentMatch+0.25*WeakCover+0.15*DifficultyMatch+0.1*BehaviorPref+0.1*GraphRel-WatchedPenalty"
        }
    }

def flow_status(score):
    score = float(score or 0)
    if score < 0.4:
        return "严重薄弱"
    if score < 0.7:
        return "薄弱"
    if score < 0.85:
        return "基本掌握"
    return "已掌握"

def flow_resource_type(filename):
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")
    if ext == "mp4":
        return "视频"
    if ext in ("ppt", "pptx", "pdf", "doc", "docx"):
        return "文档"
    return "资源"

def flow_resource_difficulty(filename):
    name = filename or ""
    if any(word in name for word in ["基础", "概述", "入门", "简单"]):
        return "简单"
    if any(word in name for word in ["专题", "死锁", "PV", "P、V", "同步", "互斥", "银行家"]):
        return "困难"
    info = infer_resource_info(name)
    if info.get("sec") and info["sec"] >= 3:
        return "困难"
    return "中等"

def flow_kp_code(name):
    match = re.match(r"^(\d+(?:\.\d+){0,2})", name or "")
    return match.group(1) if match else ""

def flow_resource_code(resource_name):
    info = infer_resource_info(resource_name or "")
    if info.get("ch") and info.get("big") and info.get("sec"):
        return "{}.{}.{}".format(info["ch"], info["big"], info["sec"])
    if info.get("ch") and info.get("big"):
        return "{}.{}".format(info["ch"], info["big"])
    return str(info.get("ch") or "")

def flow_content_match(resource_code, kp_code):
    if not resource_code or not kp_code:
        return 0
    if resource_code == kp_code or resource_code.startswith(kp_code + ".") or kp_code.startswith(resource_code + "."):
        return 1
    if ".".join(resource_code.split(".")[:2]) == ".".join(kp_code.split(".")[:2]):
        return 0.6
    return 0

def display_kp_name(name):
    return re.sub(r"^\s*\d+(?:\.\d+)+\s*", "", str(name or "")).strip() or str(name or "")

def fallback_students():
    students = []
    for info in STUDENTS.values():
        sid = info.get("full_id") or ""
        students.append({"id": sid, "num": re.sub(r"\D.*$", "", sid), "name": info.get("name", "")})
    return students

def fallback_flow_mastery_data():
    codes = set()
    if os.path.exists(RESOURCE_DIR):
        for filename in os.listdir(RESOURCE_DIR):
            if not os.path.isfile(os.path.join(RESOURCE_DIR, filename)):
                continue
            code = flow_resource_code(filename)
            if code and code[0] in {"1", "2", "3"}:
                codes.add(code)
    if not codes:
        codes = {"1.1.1", "1.1.2", "2.1.1", "3.1.1"}
    points = []
    chapters = {}
    for code in sorted(codes, key=lambda x: [int(p) if p.isdigit() else 99 for p in x.split(".")]):
        chapter = code.split(".")[0]
        item = {
            "kp_id": code,
            "name": code,
            "full_name": code,
            "chapter": chapter,
            "score": 0,
            "base_score": 0,
            "mastery_formula": "Neo4j ???????????????????",
            "components": {"exercise": 0, "accuracy": 0, "volume": 0, "video": 0, "resource": 0, "discussion": 0},
            "status": flow_status(0)
        }
        points.append(item)
        chapters.setdefault(chapter, {"chapter": chapter, "title": "?{}?".format(chapter), "knowledge_points": []})
        chapters[chapter]["knowledge_points"].append(item)
    return {
        "points": points,
        "chapters": [chapters[k] for k in sorted(chapters.keys(), key=lambda x: int(x) if str(x).isdigit() else 99)],
        "stats": {
            "total": len(points),
            "mastered": 0,
            "weak": 0,
            "severe": len(points)
        },
        "offline": True
    }

def get_flow_mastery_data(user_id):
    if neo4j_temporarily_offline():
        return fallback_flow_mastery_data()
    try:
        with driver.session() as neo4j_session:
            rows = list(neo4j_session.run("""
            MATCH (k:Knowledge)
            WHERE (k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.')
              AND NOT (k)-[:???]->(:Knowledge)
            OPTIONAL MATCH (:Student {id: $sid})-[m:MASTERED]->(k)
            RETURN k.name AS name, COALESCE(m.mastery, 0) AS score,
                   COALESCE(m.total_questions, 0) AS total_questions,
                   COALESCE(m.correct_questions, 0) AS correct_questions
            ORDER BY k.name
            """, sid=user_id))
    except Exception:
        mark_neo4j_offline()
        return fallback_flow_mastery_data()
    chapters = {}
    points = []
    activity_scores = {}
    try:
        resources = get_flow_resources(user_id)
        name_to_code = {r["name"]: r["knowledge_point"] for r in resources}
        with driver.session() as neo4j_session:
            act_rows = neo4j_session.run("""
            MATCH (:Student {id:$sid})-[r:VIEWED|WATCHED]->(res)
            RETURN res.name AS name, type(r) AS rel_type,
                   coalesce(r.view_count,0) AS view_count,
                   coalesce(r.download_count,0) AS download_count,
                   coalesce(r.play_count,0) AS play_count
            """, sid=user_id)
            for ar in act_rows:
                code = name_to_code.get(ar["name"] or "")
                if not code:
                    continue
                bucket = activity_scores.setdefault(code, {"video": 0.0, "resource": 0.0, "discussion": 0.0})
                if ar["rel_type"] == "WATCHED":
                    bucket["video"] = max(bucket["video"], min(1.0, (ar["play_count"] or 1) / 3))
                else:
                    views = ar["view_count"] or 0
                    downloads = ar["download_count"] or 0
                    bucket["resource"] = max(bucket["resource"], min(1.0, (views + downloads * 2) / 4))
            solved_rows = neo4j_session.run("""
            MATCH (p:DiscussionPost {author:$author, status:'?????})
            WHERE p.knowledge_tag IS NOT NULL AND p.knowledge_tag <> ''
            RETURN p.knowledge_tag AS tag, count(p) AS c
            """, author=session.get("user_name", ""))
            for sr in solved_rows:
                tag = sr["tag"]
                bucket = activity_scores.setdefault(tag, {"video": 0.0, "resource": 0.0, "discussion": 0.0})
                bucket["discussion"] = max(bucket["discussion"], min(1.0, (sr["c"] or 0) / 2))
    except Exception:
        if not neo4j_temporarily_offline():
            mark_neo4j_offline()
        pass
    for row in rows:
        name = row["name"]
        base_score = float(row["score"] or 0)
        code = flow_kp_code(name)
        total_q = int(row["total_questions"] or 0)
        correct_q = int(row["correct_questions"] or 0)
        if total_q > 0:
            accuracy = correct_q / total_q
            volume_score = min(1.0, total_q / 10)
            exercise_score = 0.6 * accuracy + 0.4 * volume_score
        else:
            accuracy = 0
            volume_score = 0
            exercise_score = base_score
        video_score = 0.0
        resource_score = 0.0
        discussion_score = 0.0
        for b_code, value in activity_scores.items():
            if b_code and (code.startswith(b_code) or b_code.startswith(code)):
                video_score = max(video_score, value.get("video", 0.0))
                resource_score = max(resource_score, value.get("resource", 0.0))
                discussion_score = max(discussion_score, value.get("discussion", 0.0))
        score = min(1.0, 0.70 * exercise_score + 0.12 * video_score + 0.08 * resource_score + 0.10 * discussion_score)
        chapter = (flow_kp_code(name).split(".")[0] if flow_kp_code(name) else "???")
        item = {
            "kp_id": name,
            "name": display_kp_name(name),
            "full_name": name,
            "chapter": chapter,
            "score": round(score, 3),
            "base_score": round(base_score, 3),
            "mastery_formula": "????????= ??????70%??????60%+???40%??+ ???12% + ???8% + ????????0%",
            "components": {
                "exercise": round(exercise_score, 3),
                "accuracy": round(accuracy, 3),
                "volume": round(volume_score, 3),
                "video": round(video_score, 3),
                "resource": round(resource_score, 3),
                "discussion": round(discussion_score, 3)
            },
            "status": flow_status(score)
        }
        points.append(item)
        chapters.setdefault(chapter, {"chapter": chapter, "title": "?{}?".format(chapter), "knowledge_points": []})
        chapters[chapter]["knowledge_points"].append(item)
    stats = {
        "total": len(points),
        "mastered": sum(1 for p in points if p["score"] >= 0.85),
        "weak": sum(1 for p in points if 0.4 <= p["score"] < 0.7),
        "severe": sum(1 for p in points if p["score"] < 0.4)
    }
    return {
        "points": points,
        "chapters": [chapters[k] for k in sorted(chapters.keys(), key=lambda x: int(x) if str(x).isdigit() else 99)],
        "stats": stats
    }

def get_flow_resources(user_id=None):
    resources = []
    watched_names = set()
    if user_id and not neo4j_temporarily_offline():
        try:
            with driver.session() as neo4j_session:
                rows = neo4j_session.run("""
                MATCH (:Student {id: $sid})-[r:VIEWED|WATCHED]->(res)
                RETURN DISTINCT res.name AS name
                """, sid=user_id)
                watched_names = {row["name"] for row in rows if row["name"]}
        except Exception:
            mark_neo4j_offline()
            watched_names = set()
    if not os.path.exists(RESOURCE_DIR):
        return resources
    excluded = {"questions.json", "question_history.json"}
    for filename in os.listdir(RESOURCE_DIR):
        if filename in excluded or not os.path.isfile(os.path.join(RESOURCE_DIR, filename)):
            continue
        info = infer_resource_info(filename)
        if info.get("ch") and info["ch"] > 3:
            continue
        code = flow_resource_code(filename)
        resources.append({
            "resource_id": filename,
            "name": filename,
            "title": os.path.splitext(filename)[0],
            "type": flow_resource_type(filename),
            "difficulty": flow_resource_difficulty(filename),
            "chapter": str(info.get("ch") or ""),
            "chapter_label": "第{}章".format(info.get("ch")) if info.get("ch") else "未分类",
            "section_label": "{}.{}".format(info.get("ch"), info.get("big")) if info.get("ch") and info.get("big") else ("整章" if info.get("ch") else "未分类"),
            "knowledge_point": code,
            "watched": filename in watched_names
        })
    resources.sort(key=lambda r: (int(r["chapter"]) if r["chapter"].isdigit() else 99, r["name"]))
    return resources

def get_flow_pref(user_id):
    if neo4j_temporarily_offline():
        return None
    profile = compute_behavior_profile(user_id) if user_id else {}
    prefs = {
        "???": profile.get("pref_video", 0.33),
        "???": profile.get("pref_ppt", 0.33),
        "???": profile.get("pref_practice", 0.33)
    }
    max_pref = max(prefs.values()) if prefs else 0
    if max_pref <= 0.01:
        return None
    return prefs

def explainKnowledgePoint(userId, kpId, targetKpId):
    mastery_data = get_flow_mastery_data(userId)
    score_map = {p["kp_id"]: p["score"] for p in mastery_data["points"]}
    score = score_map.get(kpId, 0)
    if neo4j_temporarily_offline():
        is_prereq = None
    else:
        try:
            with driver.session() as neo4j_session:
                is_prereq = neo4j_session.run("""
                MATCH (kp:Knowledge {name: $kp}), (target:Knowledge {name: $target})
                RETURN EXISTS((kp)-[:???*1..10]->(target)) AS ok
                """, kp=kpId, target=targetKpId).single()
        except Exception:
            mark_neo4j_offline()
            is_prereq = None
    prereq_text = "???????????" if (is_prereq and is_prereq["ok"]) else "????????"
    return {
        "score": round(score, 3),
        "status": flow_status(score),
        "below_threshold": score < 0.7,
        "is_prerequisite": bool(is_prereq and is_prereq["ok"]),
        "reason": "????????{:.2f}???????0.70??{}?".format(score, prereq_text)
    }

def generateLearningPath(userId, targetKpId):
    mastery_data = get_flow_mastery_data(userId)
    score_map = {p["kp_id"]: p["score"] for p in mastery_data["points"]}
    if neo4j_temporarily_offline():
        rows = [{"name": targetKpId, "distance": 0}]
    else:
        try:
            with driver.session() as neo4j_session:
                rows = list(neo4j_session.run("""
                MATCH (target:Knowledge {name: $target})
                MATCH p=(pre:Knowledge)-[:???*0..10]->(target)
                UNWIND nodes(p) AS n
                WITH DISTINCT n, target
                OPTIONAL MATCH sp=(n)-[:???*0..10]->(target)
                RETURN n.name AS name, min(length(sp)) AS distance
                ORDER BY distance DESC, n.name
                """, target=targetKpId))
        except Exception:
            mark_neo4j_offline()
            rows = [{"name": targetKpId, "distance": 0}]
    path = []
    seen = set()
    for row in rows:
        name = row["name"]
        if not name or name in seen:
            continue
        seen.add(name)
        score = score_map.get(name, 0)
        if score < 0.7:
            exp = explainKnowledgePoint(userId, name, targetKpId)
            path.append({
                "kp_id": name,
                "name": display_kp_name(name),
                "full_name": name,
                "score": round(score, 3),
                "status": flow_status(score),
                "reason": exp["reason"]
            })
    if targetKpId and targetKpId not in seen and score_map.get(targetKpId, 0) < 0.7:
        exp = explainKnowledgePoint(userId, targetKpId, targetKpId)
        path.append({
            "kp_id": targetKpId,
            "name": display_kp_name(targetKpId),
            "full_name": targetKpId,
            "score": round(score_map.get(targetKpId, 0), 3),
            "status": flow_status(score_map.get(targetKpId, 0)),
            "reason": exp["reason"]
        })
    return path

def explainResource(userId, resourceId, kpId):
    mastery_data = get_flow_mastery_data(userId)
    score_map = {p["kp_id"]: p["score"] for p in mastery_data["points"]}
    res_code = flow_resource_code(resourceId)
    kp_code = flow_kp_code(kpId)
    content = flow_content_match(res_code, kp_code)
    score = score_map.get(kpId, 0)
    expected = "???" if score < 0.4 else ("???" if score < 0.7 else "???")
    difficulty = flow_resource_difficulty(resourceId)
    with driver.session() as neo4j_session:
        watched = neo4j_session.run("""
        MATCH (:Student {id: $sid})-[r:VIEWED|WATCHED]->(res {name: $resource})
        RETURN count(r) AS c
        """, sid=userId, resource=resourceId).single()["c"] > 0
    reasons = []
    if content == 1:
        reasons.append("????????????")
    elif content > 0:
        reasons.append("???????????????")
    if score < 0.7:
        reasons.append("???????{}".format(flow_status(score)))
    if difficulty == expected:
        reasons.append("?????{}?????????".format(difficulty))
    else:
        reasons.append("?????{}????{}???????".format(difficulty, expected))
    reasons.append("????????" if not watched else "??????????????")
    return reasons

def recommendResourcesForKnowledgePoint(userId, kpId, limit=3):
    mastery_data = get_flow_mastery_data(userId)
    score_map = {p["kp_id"]: p["score"] for p in mastery_data["points"]}
    resources = get_flow_resources(userId)
    watched_names = {r["name"] for r in resources if r.get("watched")}
    try:
        prefs = get_flow_pref(userId)
    except Exception:
        prefs = None
    pref_type = None
    if prefs:
        pref_type = max(prefs.items(), key=lambda x: x[1])[0]
    kp_score = score_map.get(kpId, 0)
    kp_code = flow_kp_code(kpId)
    scored = []
    for res in resources:
        if res["name"] in watched_names:
            continue
        res_code = res["knowledge_point"]
        content = flow_content_match(res_code, kp_code)
        covered = [name for name, score in score_map.items() if score < 0.7 and flow_content_match(res_code, flow_kp_code(name)) >= 0.6]
        covered_total = [name for name in score_map if flow_content_match(res_code, flow_kp_code(name)) >= 0.6]
        weak_cover = len(covered) / max(1, len(covered_total))
        expected = "???" if kp_score < 0.4 else ("???" if kp_score < 0.7 else "???")
        diff_order = {"???": 0, "???": 1, "???": 2}
        diff_gap = abs(diff_order.get(res["difficulty"], 1) - diff_order.get(expected, 1))
        difficulty_match = 1 if diff_gap == 0 else (0.5 if diff_gap == 1 else 0)
        behavior_pref = 0.5 if not pref_type else (1 if res["type"] == pref_type else 0.5)
        if content == 1:
            graph_rel = 1
        elif content == 0.6:
            graph_rel = 0.5
        else:
            graph_rel = 0
        watched_penalty = 0.3 if res["watched"] else 0
        final_score = (
            0.4 * content +
            0.25 * weak_cover +
            0.15 * difficulty_match +
            0.1 * behavior_pref +
            0.1 * graph_rel -
            watched_penalty
        )
        if final_score <= 0 and content <= 0:
            continue
        scored.append({
            "resource_id": res["resource_id"],
            "title": res["title"],
            "name": res["name"],
            "type": res["type"],
            "difficulty": res["difficulty"],
            "score": round(final_score, 3),
            "watched": res["watched"],
            "reason": [
                "????????????????" if content > 0 else "??????????",
                "?????????????" if difficulty_match >= 1 else "?????????",
                "?????????????"
            ],
            "score_detail": {
                "ContentMatch": round(content, 3),
                "WeakCover": round(weak_cover, 3),
                "DifficultyMatch": round(difficulty_match, 3),
                "BehaviorPref": round(behavior_pref, 3),
                "GraphRel": round(graph_rel, 3),
                "WatchedPenalty": watched_penalty
            }
        })
    scored.sort(key=lambda x: x["score"], reverse=True)
    selected = []
    used_types = set()
    for item in scored:
        if item["type"] not in used_types:
            selected.append(item)
            used_types.add(item["type"])
        if len(selected) >= limit:
            return selected
    for item in scored:
        if item not in selected:
            selected.append(item)
        if len(selected) >= limit:
            break
    return selected

def completeResourceLearning(userId, resourceId, accuracy=None, kpId=None):
    rtype = flow_resource_type(resourceId)
    if rtype == "???":
        if accuracy is None:
            delta = 0.05
        elif accuracy >= 0.8:
            delta = 0.15
        elif accuracy >= 0.6:
            delta = 0.08
        else:
            delta = 0.02
    else:
        delta = 0.05
    kp_name = kpId
    if not kp_name:
        res_code = flow_resource_code(resourceId)
        with driver.session() as neo4j_session:
            row = neo4j_session.run("""
            MATCH (k:Knowledge)
            WHERE k.name STARTS WITH $code
            RETURN k.name AS name
            ORDER BY size(k.name)
            LIMIT 1
            """, code=res_code).single()
            kp_name = row["name"] if row else None
    if not kp_name:
        return {"success": False, "error": "???????????????"}
    record_resource_activity(userId, resourceId, "view")
    with driver.session() as neo4j_session:
        row = neo4j_session.run("""
        MERGE (s:Student {id: $sid})
        MERGE (k:Knowledge {name: $kp})
        MERGE (s)-[m:MASTERED]->(k)
        WITH m, COALESCE(m.mastery, 0) AS before
        SET m.mastery = CASE WHEN before + $delta > 1.0 THEN 1.0 ELSE before + $delta END,
            m.last_learned_resource = $resource,
            m.last_updated = datetime()
        RETURN before AS before_score, m.mastery AS after_score
        """, sid=userId, kp=kp_name, delta=delta, resource=resourceId).single()
    return {
        "success": True,
        "resource_id": resourceId,
        "kp_id": kp_name,
        "delta": round(delta, 3),
        "before_score": round(row["before_score"] or 0, 3),
        "after_score": round(row["after_score"] or 0, 3),
        "status": flow_status(row["after_score"] or 0)
    }

STUDENT_FLOW_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ page_title }} - ???????????????</title>
<style>
:root{--primary:#1f6feb;--primary-dark:#174ea6;--ink:#1f2937;--muted:#667085;--line:#d9e2ef;--soft:#f4f7fb;--panel:#fff;--green:#16a34a;--orange:#d97706;--red:#dc2626;--nav:#18324a}
*{box-sizing:border-box}body{margin:0;font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif;background:#eef3f8;color:var(--ink);font-size:14px}.layout{display:flex;min-height:100vh}.side{width:238px;background:var(--nav);color:#fff;display:flex;flex-direction:column;box-shadow:4px 0 16px rgba(24,50,74,.16);position:sticky;top:0;height:100vh}.brand{padding:22px 20px 18px;border-bottom:1px solid rgba(255,255,255,.12)}.brand-mark{width:42px;height:42px;border-radius:8px;background:#fff;color:var(--primary-dark);display:grid;place-items:center;font-weight:800;margin-bottom:12px}.brand h1{font-size:17px;margin:0 0 6px;line-height:1.35}.brand p{margin:0;color:#c7d4e5;font-size:12px}.course-pill{margin-top:12px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.12);border-radius:8px;padding:10px 12px;color:#e9f1fb}.nav{padding:12px 10px;flex:1}.nav a{display:flex;align-items:center;gap:10px;color:#d7e2f0;text-decoration:none;padding:12px 12px;border-radius:8px;margin:4px 0;font-size:14px}.nav a:hover,.nav a.active{background:#244966;color:#fff}.nav .ico{width:22px;text-align:center}.logout{padding:16px 18px;border-top:1px solid rgba(255,255,255,.1)}.logout a{display:block;text-align:center;background:#eaf2ff;color:#174ea6;text-decoration:none;padding:9px;border-radius:8px;font-weight:600}.main{flex:1;min-width:0}.top{height:66px;background:rgba(255,255,255,.92);border-bottom:1px solid #dde5f0;display:flex;align-items:center;justify-content:space-between;padding:0 28px;position:sticky;top:0;z-index:5;backdrop-filter:blur(10px)}.top h2{margin:0;font-size:20px}.top-meta{display:flex;align-items:center;gap:16px;color:var(--muted)}.avatar{width:34px;height:34px;border-radius:50%;background:#dbeafe;color:#174ea6;display:grid;place-items:center;font-weight:700}.content{padding:24px 28px 40px;max-width:1360px}.hero{background:#fff;border:1px solid var(--line);border-radius:10px;padding:22px 24px;margin-bottom:18px;display:flex;align-items:center;justify-content:space-between;gap:20px;box-shadow:0 8px 24px rgba(30,64,104,.06)}.hero h3{font-size:22px;margin:0 0 8px}.hero p{margin:0;color:var(--muted);line-height:1.7}.hero-actions{display:flex;gap:10px;flex-wrap:wrap}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:14px}.card{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:18px;margin-bottom:16px;box-shadow:0 6px 18px rgba(30,64,104,.045)}.card h3{font-size:16px;margin:0 0 14px}.stat-card{position:relative;overflow:hidden}.stat-label{color:var(--muted);font-size:13px}.stat{font-size:34px;font-weight:800;margin:8px 0 2px}.stat-sub{font-size:12px;color:var(--muted)}.muted{color:var(--muted);font-size:13px}.btn{border:0;border-radius:7px;background:var(--primary);color:#fff;padding:9px 14px;cursor:pointer;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;gap:6px;font-weight:600}.btn:hover{background:var(--primary-dark)}.btn.secondary{background:#eef4ff;color:#174ea6;border:1px solid #c7d8f5}.btn.green{background:var(--green)}.btn:disabled{background:#94a3b8;cursor:not-allowed}.toolbar,.filters{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}.filters button,.select,input{border:1px solid #cad5e5;background:#fff;border-radius:7px;padding:9px 11px;min-height:38px}.filters button{cursor:pointer}.filters button.active{background:#1f6feb;color:#fff;border-color:#1f6feb}.search{min-width:320px}.kp-row,.res-row{display:flex;align-items:center;gap:14px;justify-content:space-between;border-top:1px solid #edf2f7;padding:13px 0}.kp-title{font-weight:700}.tag{font-size:12px;padding:4px 9px;border-radius:999px;background:#eef2ff;color:#3730a3;white-space:nowrap}.tag.bad{background:#fee2e2;color:#b91c1c}.tag.warn{background:#fff7ed;color:#b45309}.tag.ok{background:#dcfce7;color:#166534}.progress{height:7px;background:#e5ecf5;border-radius:99px;overflow:hidden;width:150px;margin-top:7px}.bar{height:100%;background:#1f6feb}.path-layout{display:grid;grid-template-columns:minmax(0,1fr) 300px;gap:16px}.path-step{position:relative;padding-left:28px}.path-step:before{content:"";position:absolute;left:8px;top:24px;bottom:-18px;width:2px;background:#c7d8f5}.path-step:last-child:before{display:none}.step-dot{position:absolute;left:0;top:18px;width:18px;height:18px;border-radius:50%;background:#1f6feb;border:4px solid #dbeafe}.resource-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(255px,1fr));gap:12px;margin-top:12px}.resource{background:#f8fbff;border:1px solid #d9e5f6;border-radius:9px;padding:14px}.resource h4{margin:0 0 8px;font-size:15px;line-height:1.45}.resource-meta{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:8px}.reason{margin:9px 0 12px;padding-left:18px;color:#475569;font-size:13px;line-height:1.55}.empty{padding:34px;text-align:center;color:#64748b;background:#fff;border:1px dashed #b8c7d9;border-radius:10px}.score{font-weight:800}.after{font-size:13px;color:#166534;margin-top:8px}.section-title{display:flex;align-items:center;justify-content:space-between;margin:18px 0 10px}.chapter-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(310px,1fr));gap:14px}.goal-card{border:1px solid #e1e8f2;border-radius:9px;padding:14px;background:#fff}.goal-card:hover{border-color:#8db6f4;box-shadow:0 8px 20px rgba(31,111,235,.08)}.side-panel{position:sticky;top:86px}.formula{font-size:12px;line-height:1.7;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;color:#475569}@media(max-width:920px){.layout{display:block}.side{position:relative;width:100%;height:auto}.nav{display:grid;grid-template-columns:repeat(2,1fr)}.top{position:relative}.path-layout{grid-template-columns:1fr}.side-panel{position:relative;top:auto}.search{min-width:100%}}
</style>
<style>
.compact-hero{padding:16px 18px}.compact-hero h3{font-size:18px}.path-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px}.mini-stat{background:#fff;border:1px solid var(--line);border-radius:9px;padding:13px}.mini-stat b{display:block;font-size:20px;margin-top:5px}.path-step.compact{padding-top:16px;padding-bottom:16px}.reason-collapsed{display:none}.resource-actions{display:flex;gap:8px;flex-wrap:wrap;align-items:center}.link-btn{border:0;background:transparent;color:#1f6feb;cursor:pointer;padding:0;font-weight:600}.details-panel summary{cursor:pointer;font-weight:700;color:#1f2937}.details-panel[open] summary{margin-bottom:10px}@media(max-width:920px){.path-summary{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="layout">
  <aside class="side">
    <div class="brand">
      <div class="brand-mark">OS</div>
      <h1>???????????????</h1>
      <p>??????????????????</p>
      <div class="course-pill">????????{ student_name }}</div>
    </div>
    <nav class="nav">
      <a href="/student/dashboard" class="{% if active_page=='dashboard' %}active{% endif %}"><span class="ico">??/span>???</a>
      <a href="/student/mastery" class="{% if active_page=='mastery' %}active{% endif %}"><span class="ico">??/span>?????????</a>
      <a href="/student/goals" class="{% if active_page=='goals' %}active{% endif %}"><span class="ico">??/span>?????????</a>
      <a href="/student/path" class="{% if active_page=='path' %}active{% endif %}"><span class="ico">??/span>???????????</a>
      <a href="/student/resources" class="{% if active_page=='resources' %}active{% endif %}"><span class="ico">??/span>????????/a>
      <a href="/student/records" class="{% if active_page=='records' %}active{% endif %}"><span class="ico">??/span>??????</a>
    </nav>
    <div class="logout"><a href="/logout">???????/a></div>
  </aside>
  <main class="main">
    <header class="top">
      <h2>{{ page_title }}</h2>
      <div class="top-meta"><span>???????????/span><span>????????/span><div class="avatar">??/div></div>
    </header>
    <section class="content" id="app"></section>
  </main>
</div>
<script>
const PAGE = "{{ active_page }}";
const TARGET = new URLSearchParams(location.search).get("target_kp") || "";
const app = document.getElementById("app");
const statusClass = s => s === "??????" ? "bad" : (s === "???" ? "warn" : "ok");
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function getJson(url){ const r = await fetch(url); return await r.json(); }
function pct(v){ return Math.round((Number(v)||0)*100) + "%"; }
function bar(score){ return `<div class="progress"><div class="bar" style="width:${Math.max(0, Math.min(100, score*100))}%"></div></div>`; }

async function dashboard(){
  const data = await getJson("/student/dashboard/data");
  app.innerHTML = `<div class="hero">
    <div><h3>?????????????????????</h3><p>????????????????????????????????????????????????????????????????????/p></div>
    <div class="hero-actions"><a class="btn" href="/student/goals">?????????</a><a class="btn secondary" href="/student/mastery">????????/a></div>
  </div>
  <div class="grid">
    <div class="card stat-card"><div class="stat-label">??????</div><div class="stat">??????</div><div class="stat-sub">?????????/div></div>
    <div class="card stat-card"><div class="stat-label">???????????/div><div class="stat">${data.stats.mastered}</div><div class="stat-sub">????????? 0.85</div></div>
    <div class="card stat-card"><div class="stat-label">????????/div><div class="stat">${data.stats.weak}</div><div class="stat-sub">0.40 ??0.70 ???</div></div>
    <div class="card stat-card"><div class="stat-label">???????????/div><div class="stat">${data.stats.severe}</div><div class="stat-sub">????????0.40</div></div>
  </div>
  <div class="card"><h3>??????</h3><div class="kp-row"><div><div class="kp-title">??????????/div><div class="muted">${esc(data.recent_target || "?????????????????????????????????)}</div></div><a class="btn" href="/student/goals">?????????</a></div></div>`;
}

async function mastery(){
  const data = await getJson("/student/mastery/data");
  let filter = "???";
  function render(){
    const chapters = data.chapters.map(ch => {
      const rows = ch.knowledge_points.filter(k => filter==="???" || k.status===filter).map(k =>
        `<div class="kp-row"><div><div class="kp-title">${esc(k.name)}</div><div class="muted">??{esc(k.chapter)}??? ?????${k.score.toFixed(2)}</div>${bar(k.score)}</div><div><span class="tag ${statusClass(k.status)}">${k.status}</span></div></div>`
      ).join("");
      return rows ? `<div class="card"><h3>${esc(ch.title)}</h3>${rows}</div>` : "";
    }).join("");
    app.innerHTML = `<div class="hero"><div><h3>?????????</h3><p>?????????1??????????????????????????0.70?????????????????????/p></div></div><div class="filters">${["???","??????","???","??????","??????"].map(x=>`<button class="${x===filter?'active':''}" onclick="window.setMasteryFilter('${x}')">${x}</button>`).join("")}</div>${chapters || '<div class="empty">???????????????????/div>'}`;
  }
  window.setMasteryFilter = x => { filter = x; render(); };
  render();
}

async function goals(){
  const data = await getJson("/student/mastery/data");
  let q = "";
  function render(){
    const cards = data.chapters.map(ch => {
      const rows = ch.knowledge_points.filter(k => !q || k.name.includes(q)).map(k =>
        `<div class="goal-card"><div class="kp-title">${esc(k.name)}</div><div class="muted">?????${k.score.toFixed(2)} ? <span class="tag ${statusClass(k.status)}">${k.status}</span></div>${bar(k.score)}<div style="margin-top:12px"><button class="btn" onclick="location.href='/student/path?target_kp=${encodeURIComponent(k.kp_id)}'">?????????</button></div></div>`
      ).join("");
      return rows ? `<div class="card"><h3>${esc(ch.title)}</h3><div class="chapter-grid">${rows}</div></div>` : "";
    }).join("");
    app.innerHTML = `<div class="hero"><div><h3>?????????</h3><p>???????????????????????????????????????????????????????????????/p></div></div><div class="toolbar"><input class="select search" placeholder="???????????????????????????? value="${esc(q)}" oninput="window.goalSearch(this.value)"></div>${cards || '<div class="empty">???????????/div>'}`;
  }
  window.goalSearch = v => { q = v; render(); };
  render();
}

async function pathPage(){
  if(!TARGET){ app.innerHTML = `<div class="empty">??????????????br><br><a class="btn" href="/student/goals">???????????</a></div>`; return; }
  const data = await getJson("/student/path/data?target_kp=" + encodeURIComponent(TARGET));
  const steps = data.learning_path.length ? data.learning_path : data.fallback_path;
  const html = steps.map((step, i) => `<div class="card path-step compact"><span class="step-dot"></span>
    <h3>??{i+1}???${esc(step.name)}</h3>
    <p><span class="score">?????${step.score.toFixed(2)}</span> <span class="tag ${statusClass(step.status)}">${step.status}</span></p>${bar(step.score)}
    <p class="muted">${esc(step.reason)}</p>
    <div class="section-title"><b>??????</b><span class="muted">??????????????/span></div>
    <div class="resource-list">${step.resources.map(r => `<div class="resource">
      <h4>${esc(r.title)}</h4>
      <div class="resource-meta"><span class="tag">${r.type}</span><span class="tag">${r.difficulty}</span><span class="tag">?????${r.score.toFixed(2)}</span><span class="tag ${r.watched?'warn':'ok'}">${r.watched ? "????? : "?????}</span></div>
      <ul class="reason reason-collapsed">${r.reason.map(x=>`<li>${esc(x)}</li>`).join("")}</ul>
      <div class="resource-actions">
        <button class="btn green" disabled>\\u5b8c\\u6210</button>
        <a class="btn secondary" href="${r.type==='???'?'/video/':'/download/'}${encodeURIComponent(r.resource_id)}" target="_blank">${r.type==='???'?'???':'???'}</a>
        <button class="link-btn" onclick="toggleReason(this)">??????</button>
      </div>
      <div class="after"></div>
    </div>`).join("")}</div>
  </div>`).join("");
  app.innerHTML = `<div class="hero compact-hero"><div><h3>????????{esc(data.target_kp)}</h3><p>${data.learning_path.length ? "???????????????????????????? : "???????????????????????????????????}</p></div><a class="btn secondary" href="/student/goals">??????</a></div>
  <div class="path-summary"><div class="mini-stat">??????<b>${steps.length}</b></div><div class="mini-stat">???????b>0.70</b></div><div class="mini-stat">??????<b>Top 3</b></div></div>
  <div class="path-layout"><div>${html}</div><aside class="side-panel"><details class="card details-panel"><summary>??????</summary><div class="formula">??????????????????????????mastered.score????????0.70 ????????????????????????????????????????????????????????????????????????????????/div></details></aside></div>`;
}

async function completeResource(resourceId, kpId, btn){
  btn.disabled = true;
  const box = btn.parentElement.querySelector(".after");
  const data = await fetch("/student/resource/complete", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({resource_id:decodeURIComponent(resourceId), kp_id:decodeURIComponent(kpId)})}).then(r=>r.json());
  if(data.success){ box.textContent = `????????${data.before_score.toFixed(2)} ?????${data.after_score.toFixed(2)}??${data.delta.toFixed(2)}??; }
  else { box.textContent = data.error || "??????"; btn.disabled = false; }
}

function toggleReason(btn){
  const reason = btn.closest(".resource").querySelector(".reason");
  reason.classList.toggle("reason-collapsed");
  btn.textContent = reason.classList.contains("reason-collapsed") ? "??????" : "??????";
}

async function resourcesPage(){
  const data = await getJson("/student/resources/data");
  let type = "???", ch = "???", q = "";
  function render(){
    const list = data.resources.filter(r => (type==="???"||r.type===type) && (ch==="???"||String(r.chapter_num||r.chapter)===ch) && (!q || r.name.includes(q) || String(r.knowledge_point||"").includes(q)));
    app.innerHTML = `<div class="hero"><div><h3>????????/h3><p>??????????????????????????????????????????????/p></div></div><div class="toolbar"><select class="select" onchange="window.resCh(this.value)"><option>???</option><option value="1">????/option><option value="2">????/option><option value="3">????/option></select><select class="select" onchange="window.resType(this.value)"><option>???</option><option>???</option><option>???</option><option>???</option></select><input class="select search" placeholder="????????????" oninput="window.resSearch(this.value)"></div><div class="card">${list.map(r=>`<div class="res-row"><div><div class="kp-title">${esc(r.title || r.name)}</div><div class="muted">${r.type || "???"} ? ${r.difficulty || "???"} ? ${esc(r.knowledge_point || "")}</div></div><div><a class="btn secondary" target="_blank" href="${(r.type==='???'||String(r.name).endsWith('.mp4'))?'/video/':'/download/'}${encodeURIComponent(r.name)}">${(r.type==='???'||String(r.name).endsWith('.mp4'))?'???':'???'}</a></div></div>`).join("") || '<div class="empty">??????????????/div>'}</div>`;
  }
  window.resType = v => { type = v; render(); };
  window.resCh = v => { ch = v.replace("??,"").replace("??,""); render(); };
  window.resSearch = v => { q = v; render(); };
  render();
}

async function records(){
  const data = await getJson("/student/records/data");
  app.innerHTML = `<div class="hero"><div><h3>??????</h3><p>??????????????????????????????????????????????????????????/p></div></div><div class="card"><h3>????????/h3>${data.records.map(r=>`<div class="res-row"><div><div class="kp-title">${esc(r.name)}</div><div class="muted">${r.type} ? ${esc(r.knowledge_point || "?????????")} ? ${esc(r.time || "")}</div></div><span class="tag ok">?????/span></div>`).join("") || '<div class="empty">?????????</div>'}</div>`;
}

if(PAGE==="dashboard") dashboard();
if(PAGE==="mastery") mastery();
if(PAGE==="goals") goals();
if(PAGE==="path") pathPage();
if(PAGE==="resources") resourcesPage();
if(PAGE==="records") records();
</script>
</body>
</html>
"""

def render_flow_page(title, active):
    title_map = {
        "dashboard": "\u9996\u9875",
        "path": "\u667a\u80fd\u5b66\u4e60\u8def\u5f84",
        "resources": "\u5b66\u4e60\u8d44\u6e90\u5e93",
        "mastery": "\u77e5\u8bc6\u70b9\u638c\u63e1\u5ea6",
        "graph": "\u77e5\u8bc6\u56fe\u8c31",
        "discuss": "\u95ee\u9898\u8ba8\u8bba",
        "my_discuss": "\u6211\u7684\u8ba8\u8bba",
        "records": "\u5b66\u4e60\u8bb0\u5f55",
    }
    return make_response(render_template_string(
        STUDENT_FLOW_HTML,
        page_title=title_map.get(active, title),
        active_page=active,
        student_name=session.get("user_name", "")
    ))

STUDENT_FLOW_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ page_title }} - ????????????</title>
<style>
:root{--blue:#3b82f6;--ink:#1f2937;--muted:#7b8494;--bg:#f3f5f8;--line:#e3e8f0;--nav:#fff;--soft:#f7f9fc;--green:#22c55e;--orange:#f59e0b;--red:#ef4444}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:"Microsoft YaHei","PingFang SC",Arial,sans-serif}.layout{display:grid;grid-template-columns:216px 1fr;min-height:100vh}.side{background:var(--nav);border-right:1px solid var(--line);padding:18px 0;position:sticky;top:0;height:100vh}.logo{display:flex;align-items:center;gap:10px;padding:0 24px 20px}.logo-mark{width:34px;height:34px;border-radius:7px;background:#e43d4f;color:#fff;display:grid;place-items:center;font-weight:800}.course-cover{height:92px;margin:8px 24px 14px;border-radius:7px;background:linear-gradient(135deg,#81d4fa,#7cb342);position:relative;overflow:hidden}.course-cover:after{content:"??????";position:absolute;left:12px;bottom:10px;color:#fff;font-size:13px}.course-name{font-size:18px;text-align:center;margin:0 0 22px}.nav a{display:flex;align-items:center;gap:13px;padding:13px 28px;text-decoration:none;color:#5f6b7a;border-left:3px solid transparent}.nav a:hover,.nav a.active{background:#edf4ff;color:#2563eb;border-left-color:#60a5fa}.logout{position:absolute;bottom:18px;left:20px;right:20px}.logout a{display:block;text-align:center;background:#edf4ff;color:#2563eb;border-radius:7px;padding:10px;text-decoration:none;font-weight:700}.main{min-width:0}.top{height:64px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 34px;position:sticky;top:0;z-index:4}.top h1{margin:0;font-size:22px}.user{display:flex;align-items:center;gap:10px;color:#64748b}.avatar{width:34px;height:34px;border-radius:50%;background:#dbeafe;color:#2563eb;display:grid;place-items:center;font-weight:800}.content{padding:28px 36px;max-width:1320px}.panel{background:#fff;border:1px solid var(--line);border-radius:9px;margin-bottom:18px;box-shadow:0 8px 24px rgba(18,38,63,.04)}.panel-pad{padding:22px 24px}.section-head{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:16px}.section-head h2,.panel h2{margin:0;font-size:20px}.muted{color:var(--muted);font-size:13px;line-height:1.7}.btn{border:0;border-radius:7px;background:#4f83ff;color:#fff;padding:9px 15px;text-decoration:none;cursor:pointer;font-weight:700;display:inline-flex;align-items:center;justify-content:center;gap:6px}.btn:hover{background:#2563eb}.btn.light{background:#eef4ff;color:#2563eb;border:1px solid #d6e4ff}.btn.green{background:#16a34a}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.stat{padding:18px;background:#fff;border:1px solid var(--line);border-radius:9px}.stat b{display:block;font-size:32px;margin:8px 0}.task-grid{display:grid;grid-template-columns:2fr 1fr 1fr;gap:16px}.task-card{background:#fff;border:1px solid var(--line);border-radius:9px;padding:22px}.progress{height:8px;background:#e8edf4;border-radius:99px;overflow:hidden}.bar{height:100%;background:#60a5fa}.toolbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:16px}.select,.search,input,textarea{border:1px solid #d5dde8;border-radius:7px;background:#fff;padding:10px 12px;min-height:40px}.search{min-width:300px}.resource-layout{display:grid;grid-template-columns:260px 1fr;gap:16px}.tree{padding:14px}.tree button{display:block;width:100%;text-align:left;border:0;background:transparent;padding:10px;border-radius:7px;cursor:pointer;color:#4b5563}.tree button.active,.tree button:hover{background:#edf4ff;color:#2563eb}.res-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px}.res-card{border:1px solid var(--line);border-radius:8px;padding:14px;background:#fff}.res-title{font-weight:700;margin-bottom:8px;line-height:1.45}.tag{display:inline-flex;border-radius:999px;background:#eef2ff;color:#3730a3;font-size:12px;padding:4px 9px;margin:0 6px 6px 0}.tag.video{background:#fef3c7;color:#92400e}.tag.doc{background:#dcfce7;color:#166534}.tag.bad{background:#fee2e2;color:#b91c1c}.record-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.record-list details{border-top:1px solid #eef2f7;padding:13px 0}.record-list summary{cursor:pointer;font-weight:700}.record-row{display:flex;justify-content:space-between;color:#64748b;font-size:13px;margin-top:8px}.path-item{display:grid;grid-template-columns:38px 1fr;gap:12px;padding:16px 0;border-top:1px solid #eef2f7}.step-no{width:30px;height:30px;border-radius:50%;background:#ffb454;color:#fff;display:grid;place-items:center;font-weight:800}.resource-strip{display:flex;gap:10px;overflow:auto;padding-top:10px}.mini-res{min-width:220px;border:1px solid #dce7f5;background:#f8fbff;border-radius:8px;padding:12px}.discuss-layout{display:grid;grid-template-columns:1fr 290px;gap:16px}.post{border-top:1px solid #eef2f7;padding:16px 0}.post-title{font-weight:800}.graph-form{display:grid;grid-template-columns:1fr 1fr 160px 100px;gap:10px}.graph-list{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px;margin-top:14px}.graph-edge{background:#f8fafc;border:1px solid var(--line);border-radius:8px;padding:12px}.empty{padding:46px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px;background:#fff}@media(max-width:980px){.layout{grid-template-columns:1fr}.side{position:relative;height:auto}.logout{position:relative;left:auto;right:auto}.task-grid,.resource-layout,.discuss-layout{grid-template-columns:1fr}.record-summary{grid-template-columns:1fr 1fr}.graph-form{grid-template-columns:1fr}.search{min-width:100%}}
</style>
</head>
<body>
<div class="layout">
<aside class="side">
  <div class="logo"><div class="logo-mark">OS</div><b>??????</b></div>
  <div class="course-cover"></div>
  <h2 class="course-name">??????A</h2>
  <nav class="nav">
    <a href="/student/dashboard" class="{% if active_page=='dashboard' %}active{% endif %}">?????</a>
    <a href="/student/path" class="{% if active_page=='path' %}active{% endif %}">???????????</a>
    <a href="/student/resources" class="{% if active_page=='resources' %}active{% endif %}">?????</a>
    <a href="/student/mastery" class="{% if active_page=='mastery' %}active{% endif %}">???????/a>
    <a href="/student/discuss" class="{% if active_page=='discuss' %}active{% endif %}">?????</a>
    <a href="/student/graph-builder" class="{% if active_page=='graph_builder' %}active{% endif %}">????????</a>
    <a href="/student/records" class="{% if active_page=='records' %}active{% endif %}">????????</a>
  </nav>
  <div class="logout"><a href="/logout">???????/a></div>
</aside>
<main class="main">
  <header class="top"><h1>{{ page_title }}</h1><div class="user"><span>{{ student_name }}</span><div class="avatar">??/div></div></header>
  <section class="content" id="app"></section>
</main>
</div>
<script>
const PAGE="{{ active_page }}";
const TARGET=new URLSearchParams(location.search).get("target_kp")||"";
const app=document.getElementById("app");
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const cls=s=>s==="??????"?"bad":(s==="???"?"video":"doc");
async function getJson(url){const r=await fetch(url);return await r.json();}
function bar(v){return `<div class="progress"><div class="bar" style="width:${Math.max(2,Math.min(100,(Number(v)||0)*100))}%"></div></div>`}
function resAction(r){return r.type==="???"?`/student/watch/${encodeURIComponent(r.name)}`:`/student/view/${encodeURIComponent(r.name)}`}

async function dashboard(){
 const data=await getJson("/student/dashboard/data");
 app.innerHTML=`<div class="panel panel-pad"><div class="section-head"><div><h2>?????????</h2><div class="muted">?????????????????????????????????????????????????/div></div><a class="btn" href="/student/path">??????????/a></div></div>
 <div class="task-grid"><div class="task-card"><h2>????????/h2><p><b>${data.stats.mastered}</b> / ${data.stats.total} ?????????</p>${bar(data.stats.total?data.stats.mastered/data.stats.total:0)}<div class="muted">??? ${data.stats.weak} ????????? ${data.stats.severe} ??/div></div><div class="task-card"><h2>??????</h2><p><b>${data.recent_count||0}</b> ??/p><div class="muted">?????????????????/div></div><div class="task-card"><h2>??????</h2><p>${esc(data.latest_message||"?????????")}</p></div></div>
 <div class="panel panel-pad"><h2>??????</h2><div class="grid"><a class="stat" href="/student/path"><span>?????????</span><b>AI</b><span class="muted">????????????</span></a><a class="stat" href="/student/resources"><span>??????</span><b>???</b><span class="muted">????????????</span></a><a class="stat" href="/student/discuss"><span>?????/span><b>???</b><span class="muted">???????????/span></a><a class="stat" href="/student/graph-builder"><span>??????</span><b>???</b><span class="muted">????????????</span></a></div></div>`;
}

async function pathPage(){
 const data=await getJson("/student/path/data"+(TARGET?"?target_kp="+encodeURIComponent(TARGET):""));
 const steps=(data.learning_path.length?data.learning_path:data.fallback_path);
 app.innerHTML=`<div class="panel panel-pad"><div class="section-head"><div><h2>????????????</h2><div class="muted">?????{esc(data.target_kp)}????????????????????????????/div></div><button class="btn light" onclick="location.reload()">??????</button></div></div>
 <div class="panel panel-pad">${steps.map((step,i)=>`<div class="path-item"><div class="step-no">${i+1}</div><div><h3>${esc(step.name)}</h3><div><span class="tag ${cls(step.status)}">${step.status}</span><span class="tag">?????${step.score.toFixed(2)}</span></div>${bar(step.score)}<div class="muted">${esc(step.reason)}</div><div class="resource-strip">${step.resources.map(r=>`<div class="mini-res"><div class="res-title">${esc(r.title)}</div><span class="tag ${r.type==='???'?'video':'doc'}">${r.type}</span><span class="tag">${r.difficulty}</span><div class="muted">?????${r.score.toFixed(2)}</div><a class="btn light" href="${resAction(r)}">?????/a><button class="btn green" disabled>\\u5b8c\\u6210</button><div class="muted after"></div></div>`).join("")}</div></div></div>`).join("")}</div>`;
}
async function completeResource(r,k,btn){btn.disabled=true;const box=btn.parentElement.querySelector(".after");const data=await fetch("/student/resource/complete",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({resource_id:decodeURIComponent(r),kp_id:decodeURIComponent(k)})}).then(x=>x.json());box.textContent=data.success?`?????? ${data.after_score.toFixed(2)}`:(data.error||"??????");}

async function resourcesPage(){
 const data=await getJson("/student/resources/data"); let ch="???",type="???",q="",section="???";
 function render(){const all=data.resources||[]; const chapters=[...new Set(all.map(r=>r.chapter_label||"?????))]; const sections=[...new Set(all.filter(r=>ch==="???"||(r.chapter_label||"?????)===ch).map(r=>r.section_label||"?????))]; const list=all.filter(r=>(ch==="???"||(r.chapter_label||"?????)===ch)&&(section==="???"||(r.section_label||"?????)===section)&&(type==="???"||r.type===type)&&(!q||r.name.includes(q)||String(r.knowledge_point||"").includes(q))); app.innerHTML=`<div class="panel panel-pad"><div class="section-head"><div><h2>????????/h2><div class="muted">????????????????????????????????????????/div></div></div><div class="toolbar"><select class="select" onchange="ch=this.value;section='???';render()"><option>???</option>${chapters.map(x=>`<option ${x===ch?'selected':''}>${x}</option>`).join("")}</select><select class="select" onchange="section=this.value;render()"><option>???</option>${sections.map(x=>`<option ${x===section?'selected':''}>${x}</option>`).join("")}</select><select class="select" onchange="type=this.value;render()"><option>???</option><option>???</option><option>???</option><option>???</option></select><input class="search" placeholder="????????/ ???????? value="${esc(q)}" oninput="q=this.value;render()"></div></div><div class="resource-layout"><div class="panel tree"><button class="${type==='???'?'active':''}" onclick="type='???';render()">??????</button><button class="${type==='???'?'active':''}" onclick="type='???';render()">???</button><button class="${type==='???'?'active':''}" onclick="type='???';render()">PPT / ???</button><button class="${type==='???'?'active':''}" onclick="type='???';render()">???</button></div><div class="panel panel-pad"><div class="res-grid">${list.map(r=>`<div class="res-card"><div class="res-title">${esc(r.title||r.name)}</div><span class="tag ${r.type==='???'?'video':'doc'}">${r.type}</span><span class="tag">${r.chapter_label}</span><span class="tag">${r.section_label}</span><div class="muted">${esc(r.knowledge_point||"?????????")}</div><a class="btn light" href="${resAction(r)}">??????</a><a class="btn light" href="/download/${encodeURIComponent(r.name)}">???</a></div>`).join("")||'<div class="empty">??????????????/div>'}</div></div></div>`}
 window.render=render; render();
}

async function records(){
 const data=await getJson("/student/records/data"); const s=data.summary||{};
 app.innerHTML=`<div class="record-summary"><div class="stat"><span>??????</span><b>${s.video||0}</b></div><div class="stat"><span>??????</span><b>${s.document||0}</b></div><div class="stat"><span>??????/span><b>${s.week||0}</b></div><div class="stat"><span>?????/span><b>${s.total||0}</b></div></div><div class="panel panel-pad record-list"><h2>??????</h2>${(data.groups||[]).map(g=>`<details><summary>${esc(g.date)} ? ${g.items.length} ??/summary>${g.items.map(r=>`<div class="record-row"><span>${esc(r.name)}</span><span>${r.type} ? ${esc(r.knowledge_point||"") } ? ${esc(r.time)}</span></div>`).join("")}</details>`).join("")||'<div class="empty">?????????</div>'}</div>`;
}

async function discuss(){
 const data=await getJson("/student/discuss/data");
 app.innerHTML=`<div class="discuss-layout"><div class="panel panel-pad"><div class="section-head"><h2>????????/h2><button class="btn" onclick="postTopic()">???</button></div><input id="topicTitle" class="search" placeholder="??????????????????????????????"><textarea id="topicBody" style="width:100%;margin-top:10px" rows="4" placeholder="??????"></textarea>${data.posts.map(p=>`<div class="post"><div class="post-title">${esc(p.title)}</div><div class="muted">${esc(p.author)} ? ${esc(p.time)}</div><p>${esc(p.body)}</p></div>`).join("")||'<div class="empty">??????????????????</div>'}</div><div class="panel panel-pad"><h2>??????</h2><p class="muted">????????????????????????????????????/p></div></div>`;
}
async function postTopic(){await fetch("/student/discuss/post",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({title:document.getElementById("topicTitle").value,body:document.getElementById("topicBody").value})});discuss();}

async function graphBuilder(){
 const data=await getJson("/student/graph-builder/data");
 app.innerHTML=`<div class="panel panel-pad"><h2>?????????</h2><p class="muted">?????????????????????????????????????????/p><div class="graph-form"><input id="fromK" placeholder="????????><input id="toK" placeholder="????????><select id="relK" class="select"><option>???</option><option>???</option><option>???</option></select><button class="btn" onclick="addEdge()">???</button></div><div class="graph-list">${data.edges.map(e=>`<div class="graph-edge"><b>${esc(e.from)}</b><div class="muted">${esc(e.rel)}</div><b>${esc(e.to)}</b></div>`).join("")||'<div class="empty">??????????????/div>'}</div></div>`;
}
async function addEdge(){await fetch("/student/graph-builder/add",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({from:fromK.value,to:toK.value,rel:relK.value})});graphBuilder();}

async function mastery(){const data=await getJson("/student/mastery/data");app.innerHTML=`<div class="panel panel-pad"><h2>?????????</h2>${data.chapters.map(ch=>`<h3>${esc(ch.title)}</h3>${ch.knowledge_points.map(k=>`<div class="record-row"><span>${esc(k.name)}</span><span>${k.score.toFixed(2)} ? ${k.status}</span></div>`).join("")}`).join("")}</div>`}
if(PAGE==="dashboard")dashboard();if(PAGE==="path")pathPage();if(PAGE==="resources")resourcesPage();if(PAGE==="records")records();if(PAGE==="discuss")discuss();if(PAGE==="graph_builder")graphBuilder();if(PAGE==="mastery")mastery();
</script>
</body>
</html>
"""

@app.route("/student/dashboard")
def student_dashboard():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("??", "dashboard")

@app.route("/student/dashboard/data")
def student_dashboard_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    user_id = session.get("full_id")
    data = get_flow_mastery_data(user_id)
    recent_count = 0
    latest_message = ""
    try:
        if neo4j_temporarily_offline():
            raise RuntimeError("neo4j offline")
        with driver.session() as neo4j_session:
            row = neo4j_session.run("""
            MATCH (:Student {id:$sid})-[r:VIEWED|WATCHED]->()
            RETURN count(r) AS c
            """, sid=user_id).single()
            recent_count = row["c"] if row else 0
            msg = neo4j_session.run("""
            MATCH (:Student {id:$sid})<-[:TO_STUDENT]-(m:TeacherMessage)
            RETURN m.body AS body
            ORDER BY m.created_ts DESC
            LIMIT 1
            """, sid=user_id).single()
            latest_message = msg["body"] if msg else ""
    except Exception:
        pass
    return jsonify({"success": True, "stats": data["stats"], "recent_target": session.get("recent_target_kp"), "recent_count": recent_count, "latest_message": latest_message})

@app.route("/student/mastery")
def student_mastery():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("??????", "mastery")

@app.route("/student/mastery/data")
def student_mastery_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    return jsonify({"success": True, **get_flow_mastery_data(session.get("full_id"))})

@app.route("/student/goals")
def student_goals():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("??????", "goals")

@app.route("/student/path")
def student_path():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("??????", "path")

@app.route("/student/path/data")
def student_path_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    user_id = session.get("full_id")
    target_kp = request.args.get("target_kp", "").strip()
    if not target_kp:
        mastery = get_flow_mastery_data(user_id)
        weak_points = [p for p in mastery["points"] if p["score"] < 0.7]
        weak_points.sort(key=lambda x: (x["score"], x["kp_id"]))
        target_kp = weak_points[0]["kp_id"] if weak_points else (mastery["points"][0]["kp_id"] if mastery["points"] else "")
    if not target_kp:
        return jsonify({"success": False, "error": "????????????"})
    session["recent_target_kp"] = target_kp
    cache_key = (user_id, target_kp)
    cached = PATH_RECOMMEND_CACHE.get(cache_key)
    if cached and (datetime.now() - cached["time"]).total_seconds() < 300:
        return jsonify(cached["data"])
    learning_path = generateLearningPath(user_id, target_kp)
    target_score = {p["kp_id"]: p["score"] for p in get_flow_mastery_data(user_id)["points"]}.get(target_kp, 0)
    fallback_path = []
    if not learning_path:
        fallback_path = [{
            "kp_id": target_kp,
            "name": target_kp,
            "score": round(target_score, 3),
            "status": flow_status(target_score),
            "reason": "??????????????????????????",
            "resources": recommendResourcesForKnowledgePoint(user_id, target_kp, 3)
        }]
    for step in learning_path:
        step["resources"] = recommendResourcesForKnowledgePoint(user_id, step["kp_id"], 3)
    payload = {
        "success": True,
        "target_kp": target_kp,
        "learning_path": learning_path,
        "fallback_path": fallback_path,
        "threshold": 0.7
    }
    PATH_RECOMMEND_CACHE[cache_key] = {"time": datetime.now(), "data": payload}
    return jsonify(payload)

@app.route("/student/records")
def student_records():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("????", "records")

@app.route("/student/records/data")
def student_records_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    user_id = session.get("full_id")
    records = []
    try:
        if neo4j_temporarily_offline():
            raise RuntimeError("neo4j offline")
        with driver.session() as neo4j_session:
            rows = neo4j_session.run("""
            MATCH (:Student {id: $sid})-[r:VIEWED|WATCHED]->(res)
            RETURN res.name AS name, type(r) AS rel_type,
                   coalesce(r.last_viewed, r.last_downloaded) AS t
            ORDER BY t DESC
            LIMIT 80
            """, sid=user_id)
            for row in rows:
                name = row["name"] or ""
                records.append({
                    "name": name,
                    "type": "???" if row["rel_type"] == "WATCHED" or name.endswith(".mp4") else "???",
                    "knowledge_point": flow_resource_code(name),
                    "time": str(row["t"]) if row["t"] else ""
                })
    except Exception:
        if not neo4j_temporarily_offline():
            mark_neo4j_offline()
        records = []
    normalized = []
    for idx, record in enumerate(records):
        display_dt = datetime.now() - timedelta(days=idx // 5, hours=(idx * 3) % 24, minutes=(idx * 7) % 60)
        name = record.get("name", "")
        rtype = "???" if name.endswith(".mp4") else ("???" if flow_resource_type(name) == "???" else "???")
        normalized.append({
            **record,
            "type": rtype,
            "time": display_dt.strftime("%H:%M"),
            "date": display_dt.strftime("%Y-%m-%d")
        })
    groups_map = {}
    for record in normalized:
        groups_map.setdefault(record["date"], []).append(record)
    groups = [{"date": key, "items": value} for key, value in groups_map.items()]
    summary = {
        "total": len(normalized),
        "video": sum(1 for r in normalized if r["type"] == "???"),
        "document": sum(1 for r in normalized if r["type"] == "???"),
        "week": sum(1 for r in normalized if (datetime.now() - datetime.strptime(r["date"], "%Y-%m-%d")).days < 7)
    }
    return jsonify({"success": True, "records": normalized, "groups": groups, "summary": summary})

@app.route("/student/resource/complete", methods=["POST"])
def student_resource_complete():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    resource_id = data.get("resource_id", "")
    kp_id = data.get("kp_id")
    accuracy = data.get("accuracy")
    if accuracy is not None:
        try:
            accuracy = float(accuracy)
            if accuracy > 1:
                accuracy = accuracy / 100
        except Exception:
            accuracy = None
    if not resource_id:
        return jsonify({"success": False, "error": "??????ID"})
    return jsonify(completeResourceLearning(session.get("full_id"), resource_id, accuracy, kp_id))

@app.route("/student/discuss")
def student_discuss():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("????", "discuss")

@app.route("/student/discuss/mine")
def student_discuss_mine_page():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("????", "my_discuss")

@app.route("/student/discuss/data")
def student_discuss_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    try:
        with driver.session() as neo4j_session:
            rows = neo4j_session.run("""
            MATCH (p:DiscussionPost)
            RETURN p.title AS title, p.body AS body, p.author AS author, p.created_at AS created_at
            ORDER BY p.created_ts DESC
            LIMIT 30
            """)
            posts = [{"title": row["title"], "body": row["body"], "author": row["author"] or "???", "time": str(row["created_at"])[:16] if row["created_at"] else ""} for row in rows]
    except Exception:
        posts = []
    return jsonify({"success": True, "posts": posts})

@app.route("/student/discuss/post", methods=["POST"])
def student_discuss_post():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    knowledge_tag = (data.get("knowledge_tag") or data.get("tag") or "").strip()
    if not title:
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        neo4j_session.run("""
        CREATE (p:DiscussionPost {title:$title, body:$body, author:$author, knowledge_tag:$knowledge_tag,
                                  status:'?????, created_at:datetime(), created_ts:datetime().epochSeconds})
        """, title=title, body=body, knowledge_tag=knowledge_tag, author=session.get("user_name", "???"))
    return jsonify({"success": True})

@app.route("/student/graph-builder")
def student_graph_builder():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return redirect(url_for("student_graph"))

@app.route("/student/graph-builder/data")
def student_graph_builder_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    sid = session.get("full_id")
    try:
        if neo4j_temporarily_offline():
            raise RuntimeError("neo4j offline")
        with driver.session() as neo4j_session:
            rows = neo4j_session.run("""
            MATCH (:Student {id:$sid})-[:OWNS_PERSONAL_GRAPH]->(a:PersonalKnowledge)-[r:PERSONAL_REL]->(b:PersonalKnowledge)
            RETURN a.name AS from_name, b.name AS to_name, r.rel AS rel
            ORDER BY a.name, b.name
            """, sid=sid)
            edges = [{"from": row["from_name"], "to": row["to_name"], "rel": row["rel"]} for row in rows]
    except Exception:
        if not neo4j_temporarily_offline():
            mark_neo4j_offline()
        edges = []
    return jsonify({"success": True, "edges": edges})

@app.route("/student/graph-builder/add", methods=["POST"])
def student_graph_builder_add():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    from_name = (data.get("from") or "").strip()
    to_name = (data.get("to") or "").strip()
    rel = (data.get("rel") or "???").strip()
    if not from_name or not to_name:
        return jsonify({"success": False, "error": "????????????"})
    sid = session.get("full_id")
    with driver.session() as neo4j_session:
        neo4j_session.run("""
        MERGE (s:Student {id:$sid})
        MERGE (a:PersonalKnowledge {owner:$sid, name:$from_name})
        MERGE (b:PersonalKnowledge {owner:$sid, name:$to_name})
        MERGE (s)-[:OWNS_PERSONAL_GRAPH]->(a)
        MERGE (s)-[:OWNS_PERSONAL_GRAPH]->(b)
        MERGE (a)-[r:PERSONAL_REL]->(b)
        SET r.rel=$rel, r.updated_at=datetime()
        """, sid=sid, from_name=from_name, to_name=to_name, rel=rel)
    return jsonify({"success": True})

@app.route("/student/file/<path:filename>")
def inline_file(filename):
    return send_from_directory(RESOURCE_DIR, filename, as_attachment=False)

@app.route("/student/view/<path:filename>")
def student_view_file(filename):
    if session.get("role") != "student":
        return redirect(url_for("login"))
    record_resource_activity(session.get("full_id"), filename, "view")
    html = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>??????</title>
    <style>body{margin:0;font-family:Microsoft YaHei,Arial;background:#f3f5f8}.top{height:58px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 22px}.wrap{display:grid;grid-template-columns:1fr 300px;gap:18px;padding:18px}.viewer{height:calc(100vh - 94px);background:#fff;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden}.side{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:16px}.btn{background:#3b82f6;color:#fff;text-decoration:none;padding:8px 12px;border-radius:6px}</style>
    <div class="top"><b>{{ filename }}</b><a class="btn" href="/download/{{ filename }}">???</a></div><div class="wrap"><div class="viewer"><iframe src="/student/file/{{ filename }}" style="width:100%;height:100%;border:0"></iframe></div><div class="side"><h3>??????</h3><p>PDF ?????????PPT/Word ???????????????????????????????????????????/p><p><a class="btn" href="/student/resources">????????/a></p></div></div></html>"""
    return render_template_string(html, filename=filename)

@app.route("/student/watch/<path:filename>")
def student_watch_video(filename):
    if session.get("role") != "student":
        return redirect(url_for("login"))
    record_video_activity(session.get("full_id"), filename)
    resources = [r for r in get_flow_resources(session.get("full_id")) if r["name"] != filename][:8]
    html = """<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>??????</title>
    <style>body{margin:0;font-family:Microsoft YaHei,Arial;background:#f3f5f8}.top{height:58px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;padding:0 22px}.wrap{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px;padding:18px}.player,.side{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:16px}video{width:100%;max-height:72vh;background:#000}.item{border-top:1px solid #eef2f7;padding:12px 0}.btn{background:#eef4ff;color:#2563eb;text-decoration:none;padding:7px 10px;border-radius:6px;display:inline-block}</style>
    <div class="top"><b>{{ filename }}</b></div><div class="wrap"><div class="player"><video src="/video/{{ filename }}" controls autoplay></video><p><a class="btn" href="/student/resources">????????/a></p></div><aside class="side"><h3>??????</h3>{% for r in resources %}<div class="item"><b>{{ r.title }}</b><p>{{ r.type }} ? {{ r.difficulty }}</p><a class="btn" href="{{ '/student/watch/' + r.name if r.type == '???' else '/student/view/' + r.name }}">???</a></div>{% endfor %}</aside></div></html>"""
    return render_template_string(html, filename=filename, resources=resources)

@app.route("/teacher/message/send", methods=["POST"])
def teacher_send_message():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or request.form
    sid = (data.get("student_id") or "").strip()
    body = (data.get("body") or "").strip()
    if not sid or not body:
        return jsonify({"success": False, "error": "????"})
    try:
        with driver.session() as neo4j_session:
            neo4j_session.run("""
            MATCH (s:Student {id:$sid})
            CREATE (m:TeacherMessage {body:$body, teacher:$teacher, created_at:datetime(), created_ts:datetime().epochSeconds})
            CREATE (m)-[:TO_STUDENT]->(s)
            """, sid=sid, body=body, teacher=session.get("user_name", "???"))
        return jsonify({"success": True})
    except Exception:
        return jsonify({"success": False, "error": "Neo4j ??????????????????"})

@app.route("/teacher/public-graph/add", methods=["POST"])
def teacher_public_graph_add():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or request.form
    from_name = (data.get("from") or "").strip()
    to_name = (data.get("to") or "").strip()
    rel = (data.get("rel") or "???").strip()
    if not from_name or not to_name:
        return jsonify({"success": False, "error": "?????????"})
    try:
        with driver.session() as neo4j_session:
            neo4j_session.run("""
            MERGE (a:Knowledge {name:$from_name})
            MERGE (b:Knowledge {name:$to_name})
            MERGE (a)-[r:PUBLIC_REL]->(b)
            SET r.rel=$rel, r.teacher=$teacher, r.updated_at=datetime()
            """, from_name=from_name, to_name=to_name, rel=rel, teacher=session.get("user_name", "???"))
        return jsonify({"success": True})
    except Exception:
        return jsonify({"success": False, "error": "Neo4j ?????????????????????"})

def get_all_students():
    if neo4j_temporarily_offline():
        return fallback_students()
    query = """
    MATCH (s:Student)
    RETURN s.id AS id
    ORDER BY s.id
    """
    try:
        with driver.session() as session:
            result = session.run(query)
            students = []
            for r in result:
                sid = r["id"]
                match = re.match(r"(\d+)(.*)", sid)
                if match:
                    num = match.group(1)
                    name = match.group(2)
                    students.append({"id": sid, "num": num, "name": name})
                else:
                    students.append({"id": sid, "num": sid, "name": ""})
            return students
    except Exception:
        mark_neo4j_offline()
        return fallback_students()

def update_mastery(old_mastery, is_correct):
    """
    ????????    - ??????????????????1
    - ??????????????????0
    """
    if is_correct:
        new_mastery = old_mastery + 0.2 * (1 - old_mastery)
    else:
        new_mastery = old_mastery - 0.2 * old_mastery
    return max(0.0, min(1.0, new_mastery))

def update_student_mastery(student_id, knowledge_name, is_correct):
    """
    ????????????????????????????????????
    """
    with driver.session() as session:
        # 1. ??????????
        result = session.run("""
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge {name: $kname})
        RETURN r.mastery AS current_mastery
        """, sid=student_id, kname=knowledge_name)
        
        current_mastery = 0.5
        for record in result:
            current_mastery = record["current_mastery"] or 0.5
        
        # 2. ??????????
        new_mastery = update_mastery(current_mastery, is_correct)
        
        # 3. ????????????
        session.run("""
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge {name: $kname})
        SET r.mastery = $new_m
        """, sid=student_id, kname=knowledge_name, new_m=new_mastery)
        
        # 4. ???????????ection??????
        session.run("""
        MATCH (s:Student {id: $sid})
        MATCH (sec:Section)-[:???]->(k:Knowledge {name: $kname})
        MATCH (s)-[r_sec:MASTERED]->(sec)
        WITH sec, r_sec
        MATCH (sec)-[:???]->(child:Knowledge)
        MATCH (s)-[r_child:MASTERED]->(child)
        WITH r_sec, avg(r_child.mastery) AS avg_m
        SET r_sec.mastery = avg_m
        """, sid=student_id, kname=knowledge_name)
        
        # 5. ???????????hapter??????
        session.run("""
        MATCH (s:Student {id: $sid})
        MATCH (ch:Chapter)-[:???]->(sec:Section)
        MATCH (sec)-[:???]->(k:Knowledge {name: $kname})
        MATCH (s)-[r_ch:MASTERED]->(ch)
        WITH ch, r_ch
        MATCH (ch)-[:???]->(child)
        WHERE child:Section OR child:Knowledge
        MATCH (s)-[r_child:MASTERED]->(child)
        WITH r_ch, avg(r_child.mastery) AS avg_m
        SET r_ch.mastery = avg_m
        """, sid=student_id, kname=knowledge_name)
        
        return new_mastery

def load_questions():
    """
    Load questions from the questions.json file
    """
    questions_path = os.path.join(RESOURCE_DIR, "questions.json")
    if os.path.exists(questions_path):
        with open(questions_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"questions": []}

def question_id_prefix(knowledge_point):
    code = flow_kp_code(knowledge_point)
    return "q" + code.replace(".", "_") if code else "q_other"

def next_question_id(questions, knowledge_point):
    prefix = question_id_prefix(knowledge_point)
    max_no = 0
    pattern = re.compile(r"^" + re.escape(prefix) + r"_(\d+)(?:_v\d+)?$")
    for q in questions:
        match = pattern.match(str(q.get("id", "")))
        if match:
            max_no = max(max_no, int(match.group(1)))
    return "{}_{}".format(prefix, max_no + 1)

def get_knowledge_points_for_practice(student_id):
    """
    ???????????????????????????????????????
    """
    with driver.session() as session:
        query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE k.name =~ '\\d+\\.\\d+\\.\\d+.*'
        AND (k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.')
        RETURN k.name AS name, r.mastery AS mastery, k.is_key AS is_key
        ORDER BY r.mastery ASC
        """
        result = session.run(query, sid=student_id)
        return [{"name": r["name"], "mastery": r["mastery"], "is_key": r.get("is_key", False)} for r in result]

def record_resource_activity(student_id, resource_name, action="view"):
    if not student_id or not resource_name:
        return

    now_ts = int(datetime.now().timestamp())
    last_key = "last_resource_record"
    last_record = session.get(last_key, {})
    is_duplicate = (
        last_record.get("name") == resource_name and
        last_record.get("action") == action and
        now_ts - int(last_record.get("time", 0)) < 10
    )
    session[last_key] = {"name": resource_name, "action": action, "time": now_ts}
    session.modified = True
    if is_duplicate:
        return

    is_download = action == "download"
    weight = 2 if is_download else 1
    with driver.session() as neo4j_session:
        neo4j_session.run("""
        MERGE (s:Student {id: $sid})
        MERGE (res:Resource {name: $resource_name})
        MERGE (s)-[v:VIEWED]->(res)
        SET v.view_count = COALESCE(v.view_count, 0) + 1,
            v.last_viewed = datetime(),
            v.download_count = COALESCE(v.download_count, 0) + CASE WHEN $is_download THEN 1 ELSE 0 END,
            v.downloaded = COALESCE(v.downloaded, false) OR $is_download,
            v.last_downloaded = CASE WHEN $is_download THEN datetime() ELSE v.last_downloaded END
        MERGE (s)-[i:INTERACTED_WITH]->(res)
        SET i.count = COALESCE(i.count, 0) + 1,
            i.last_action = $action,
            i.total_weight = COALESCE(i.total_weight, 0) + $weight,
            i.last_time = datetime().epochSeconds
        """, sid=student_id, resource_name=resource_name,
             is_download=is_download, action=action, weight=weight)

def record_video_activity(student_id, video_name):
    if not student_id or not video_name:
        return

    now_ts = int(datetime.now().timestamp())
    last_key = "last_video_record"
    last_record = session.get(last_key, {})
    is_duplicate = (
        last_record.get("name") == video_name and
        now_ts - int(last_record.get("time", 0)) < 10
    )
    session[last_key] = {"name": video_name, "time": now_ts}
    session.modified = True

    play_increment = 0 if is_duplicate else 1
    with driver.session() as neo4j_session:
        neo4j_session.run("""
        MERGE (s:Student {id: $sid})
        MERGE (v:Video {name: $video_name})
        MERGE (s)-[w:WATCHED]->(v)
        SET w.play_count = COALESCE(w.play_count, 0) + $play_increment,
            w.last_viewed = datetime(),
            w.completion_rate = CASE
                WHEN w.completion_rate IS NULL THEN 0.1
                ELSE w.completion_rate
            END
        MERGE (res:Resource {name: $video_name})
        MERGE (s)-[i:INTERACTED_WITH]->(res)
        SET i.count = COALESCE(i.count, 0) + $play_increment,
            i.last_action = 'video_play',
            i.total_weight = COALESCE(i.total_weight, 0) + $play_increment * 3,
            i.last_time = datetime().epochSeconds
        """, sid=student_id, video_name=video_name, play_increment=play_increment)

@app.route("/download/<path:filename>")
def download_file(filename):
    if session.get("role") == "student":
        try:
            record_resource_activity(session.get("full_id"), filename, "download")
        except Exception as e:
            print("[resource download record] {}".format(str(e)))
    return send_from_directory(RESOURCE_DIR, filename, as_attachment=True)

# =========================
# ??????
# =========================
LOGIN_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>?? - ?????????</title>
<style>
    * { box-sizing: border-box; }
    body { font-family: "Microsoft YaHei", Arial, sans-serif; background: #f3f5f8; min-height: 100vh; display: grid; place-items: center; margin: 0; color: #1f2937; }
    body:before { content: ""; position: fixed; inset: 0 0 auto 0; height: 42vh; background: linear-gradient(180deg, #eaf2ff 0%, rgba(234,242,255,0) 100%); pointer-events: none; }
    .login-card { position: relative; background: white; padding: 34px 36px; border-radius: 10px; border: 1px solid #e5e7eb; box-shadow: 0 18px 45px rgba(15,23,42,.10); width: 420px; max-width: calc(100vw - 32px); }
    h2 { color: #1f2937; margin: 0; text-align: center; font-size: 24px; }
    .subtitle { text-align: center; color: #64748b; margin: 10px 0 28px; font-size: 14px; }
    .form-group { margin-bottom: 18px; }
    label { display: block; margin-bottom: 8px; color: #334155; font-weight: 700; font-size: 14px; }
    input { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 15px; background: #f8fafc; }
    input:focus { outline: none; border-color: #3b82f6; background: #fff; box-shadow: 0 0 0 3px rgba(59,130,246,.12); }
    .btn { width: 100%; padding: 12px; background: #2563eb; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: 700; }
    .btn:hover { background: #1d4ed8; }
    .error { color: #dc2626; text-align: center; margin-bottom: 15px; background: #fee2e2; padding: 10px; border-radius: 6px; }
    .role-switch { display: grid; grid-template-columns: 1fr 1fr; gap: 4px; margin-bottom: 24px; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 7px; padding: 5px; }
    .role-btn { padding: 11px; text-align: center; border-radius: 6px; cursor: pointer; color: #64748b; font-weight: 700; }
    .role-btn.active { background: #2563eb; color: white; box-shadow: 0 8px 18px rgba(37,99,235,.20); }
</style>
</head>
<body>
<div class="login-card">
    <h2>?????????</h2>
    <p class="subtitle">????????????????</p>
    <div class="role-switch">
        <div class="role-btn active" onclick="switchRole('student')" id="studentBtn">????</div>
        <div class="role-btn" onclick="switchRole('teacher')" id="teacherBtn">????</div>
    </div>
    <form method="POST" id="loginForm">
        <input type="hidden" name="role" id="roleInput" value="student">
        <div class="form-group">
            <label id="idLabel">??</label>
            <input name="user_id" id="userIdInput" placeholder="?????????3220602001?" required>
        </div>
        <div class="form-group">
            <label>??</label>
            <input type="password" name="password" placeholder="?????" required>
        </div>
        <button type="submit" class="btn">??</button>
    </form>
    {% if error %}
    <div class="error" style="margin-top:15px;">{{ error }}</div>
    {% endif %}
</div>
<script>
function switchRole(role) {
    document.getElementById('roleInput').value = role;
    document.getElementById('studentBtn').classList.toggle('active', role === 'student');
    document.getElementById('teacherBtn').classList.toggle('active', role === 'teacher');
    if (role === 'student') {
        document.getElementById('idLabel').textContent = '??';
        document.getElementById('userIdInput').placeholder = '?????????3220602001?';
    } else {
        document.getElementById('idLabel').textContent = '??';
        document.getElementById('userIdInput').placeholder = '?????????1000002401?';
    }
}
</script>
</body>
</html>
"""
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        role = request.form.get("role")
        user_id = request.form.get("user_id")
        password = request.form.get("password")
        
        if role == "teacher":
            if user_id in TEACHERS and TEACHERS[user_id]["password"] == password:
                session["role"] = "teacher"
                session["user_id"] = user_id
                session["user_name"] = TEACHERS[user_id]["name"]
                return redirect(url_for("teacher_tools"))
            else:
                error = "???????"
        else:
            if user_id in STUDENTS and STUDENTS[user_id]["password"] == password:
                session["role"] = "student"
                session["user_id"] = user_id
                session["user_name"] = STUDENTS[user_id]["name"]
                session["full_id"] = STUDENTS[user_id]["full_id"]
                return redirect(url_for("student_dashboard"))
            else:
                error = "???????"
    
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/student/graph")
def student_graph():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    response = render_flow_page("????", "graph")
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/student/progress")
def student_progress():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    
    full_id = session.get("full_id")
    student_name = session.get("user_name")

    response = make_response(render_template('student_progress.html',
                                 student_name=student_name,
                                 page_title="??????", active_page="progress"))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/student/progress/data")
def get_progress_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    
    with driver.session() as neo4j_session:
        progress_data = {
            "chapters": [],
            "videos_watched": [],
            "resources_viewed": [],
            "questions_practiced": [],
            "statistics": {
                "total_chapters": 0,
                "learned_chapters": 0,
                "total_videos": 0,
                "watched_videos": 0,
                "total_resources": 0,
                "viewed_resources": 0,
                "total_questions": 0,
                "practiced_questions": 0,
                "overall_completion": 0
            }
        }
        
        # 1. ?????????????????????
        chapter_query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE k.name =~ '^\\d+\\.\\d+.*'
        WITH k, r
        MATCH (k)-[:BELONGS_TO]->(sec:Section)-[:BELONGS_TO]->(ch:Chapter)
        RETURN ch.name AS chapter_name, ch.number AS chapter_num,
               sec.name AS section_name, sec.number AS section_num,
               COLLECT({name: k.name, mastery: r.mastery, 
                        total: r.total_questions, correct: r.correct_questions}) AS knowledge_points
        ORDER BY chapter_num, section_num
        """
        chapters_result = neo4j_session.run(chapter_query, sid=full_id)
        
        chapters_dict = {}
        for record in chapters_result:
            ch_name = record["chapter_name"]
            ch_num = record["chapter_num"]
            sec_name = record["section_name"]
            sec_num = record["section_num"]
            kps = record["knowledge_points"]
            
            if ch_name not in chapters_dict:
                chapters_dict[ch_name] = {
                    "name": ch_name,
                    "number": ch_num,
                    "sections": [],
                    "avg_mastery": 0,
                    "total_kps": 0,
                    "learned_kps": 0
                }
            
            # ???????????????
            sec_avg = sum(kp["mastery"] for kp in kps) / len(kps) if kps else 0
            learned_count = sum(1 for kp in kps if kp["mastery"] >= 0.6)
            
            chapters_dict[ch_name]["sections"].append({
                "name": sec_name,
                "number": sec_num,
                "knowledge_points": kps,
                "avg_mastery": round(sec_avg, 3),
                "learned_count": learned_count,
                "total_count": len(kps),
                "status": "completed" if sec_avg >= 0.8 else ("learning" if sec_avg >= 0.4 else "not_started")
            })
            
            chapters_dict[ch_name]["total_kps"] += len(kps)
            chapters_dict[ch_name]["learned_kps"] += learned_count
        
        # ??????????????????
        for ch in chapters_dict.values():
            if ch["sections"]:
                total_mastery = sum(sec["avg_mastery"] for sec in ch["sections"])
                ch["avg_mastery"] = round(total_mastery / len(ch["sections"]), 3)
                ch["status"] = "completed" if ch["avg_mastery"] >= 0.8 else ("learning" if ch["avg_mastery"] >= 0.4 else "not_started")
        
        if not chapters_dict:
            fallback_query = """
            MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
            WHERE k.name =~ '^\\d+\\.\\d+.*'
            RETURN k.name AS name, r.mastery AS mastery,
                   r.total_questions AS total, r.correct_questions AS correct
            ORDER BY k.name
            """
            fallback_result = neo4j_session.run(fallback_query, sid=full_id)
            chapter_titles = {
                "1": "?1? ??????",
                "2": "?2? ?????",
                "3": "?3? ?????"
            }
            section_groups = {}
            for record in fallback_result:
                name = record["name"] or ""
                match = re.match(r"^(\d+)\.(\d+)", name)
                if not match:
                    continue
                chapter_num, section_num = match.group(1), match.group(2)
                section_key = "{}.{}".format(chapter_num, section_num)
                section_groups.setdefault((chapter_num, section_key), []).append({
                    "name": name,
                    "mastery": record["mastery"] or 0,
                    "total": record["total"] or 0,
                    "correct": record["correct"] or 0
                })

            for (chapter_num, section_key), kps in section_groups.items():
                chapter_name = chapter_titles.get(chapter_num, "?{}?".format(chapter_num))
                if chapter_name not in chapters_dict:
                    chapters_dict[chapter_name] = {
                        "name": chapter_name,
                        "number": int(chapter_num),
                        "sections": [],
                        "avg_mastery": 0,
                        "total_kps": 0,
                        "learned_kps": 0
                    }
                sec_avg = sum(kp["mastery"] for kp in kps) / len(kps) if kps else 0
                learned_count = sum(1 for kp in kps if kp["mastery"] >= 0.6)
                chapters_dict[chapter_name]["sections"].append({
                    "name": section_key,
                    "number": section_key,
                    "knowledge_points": kps,
                    "avg_mastery": round(sec_avg, 3),
                    "learned_count": learned_count,
                    "total_count": len(kps),
                    "status": "completed" if sec_avg >= 0.8 else ("learning" if sec_avg >= 0.4 else "not_started")
                })
                chapters_dict[chapter_name]["total_kps"] += len(kps)
                chapters_dict[chapter_name]["learned_kps"] += learned_count

            for ch in chapters_dict.values():
                if ch["sections"]:
                    ch["sections"] = sorted(ch["sections"], key=lambda sec: str(sec["number"]))
                    total_mastery = sum(sec["avg_mastery"] for sec in ch["sections"])
                    ch["avg_mastery"] = round(total_mastery / len(ch["sections"]), 3)
                    ch["status"] = "completed" if ch["avg_mastery"] >= 0.8 else ("learning" if ch["avg_mastery"] >= 0.4 else "not_started")

        progress_data["chapters"] = sorted(chapters_dict.values(), key=lambda x: x["number"])
        progress_data["statistics"]["total_chapters"] = len(progress_data["chapters"])
        progress_data["statistics"]["learned_chapters"] = sum(1 for ch in progress_data["chapters"] if ch["status"] == "completed")
        
        # 2. ????????????
        video_query = """
        MATCH (s:Student {id: $sid})-[r:WATCHED]->(v:Video)
        RETURN v.name AS video_name, r.watch_duration AS duration,
               r.completion_rate AS completion, r.last_viewed AS last_viewed,
               r.play_count AS play_count
        ORDER BY r.last_viewed DESC
        """
        videos_result = neo4j_session.run(video_query, sid=full_id)
        for record in videos_result:
            completion = record["completion"] or 0
            progress_data["videos_watched"].append({
                "name": record["video_name"],
                "duration": record["duration"] or 0,
                "completion_rate": round(completion * 100, 1),
                "last_viewed": record["last_viewed"],
                "play_count": record["play_count"] or 1,
                "status": "completed" if completion >= 0.8 else ("watching" if completion > 0 else "not_started")
            })
        
        total_video_files = len([f for f in os.listdir(RESOURCE_DIR) if f.lower().endswith(".mp4")]) if os.path.exists(RESOURCE_DIR) else 0
        progress_data["statistics"]["watched_videos"] = sum(1 for v in progress_data["videos_watched"] if v["status"] in ["completed", "watching"])
        progress_data["statistics"]["total_videos"] = max(total_video_files, progress_data["statistics"]["watched_videos"])
        
        # 3. ????????????
        resource_query = """
        MATCH (s:Student {id: $sid})-[r:VIEWED]->(res:Resource)
        RETURN res.name AS resource_name, r.view_count AS view_count,
               r.download_count AS download_count, r.downloaded AS downloaded,
               r.last_viewed AS last_viewed
        ORDER BY r.last_viewed DESC
        """
        resources_result = neo4j_session.run(resource_query, sid=full_id)
        for record in resources_result:
            progress_data["resources_viewed"].append({
                "name": record["resource_name"],
                "view_count": record["view_count"] or 0,
                "download_count": record["download_count"] or 0,
                "downloaded": record["downloaded"] or False,
                "last_viewed": record["last_viewed"],
                "status": "downloaded" if record["downloaded"] else ("viewed" if (record["view_count"] or 0) > 0 else "not_viewed")
            })
        
        resource_files = []
        if os.path.exists(RESOURCE_DIR):
            excluded_files = {"questions.json", "question_history.json"}
            resource_files = [
                f for f in os.listdir(RESOURCE_DIR)
                if os.path.isfile(os.path.join(RESOURCE_DIR, f)) and f not in excluded_files
            ]
        progress_data["statistics"]["viewed_resources"] = sum(1 for r in progress_data["resources_viewed"] if r["status"] in ["viewed", "downloaded"])
        progress_data["statistics"]["total_resources"] = max(len(resource_files), progress_data["statistics"]["viewed_resources"])
        
        # 4. ????????????
        question_query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        RETURN SUM(r.total_questions) AS total_practiced,
               SUM(r.correct_questions) AS total_correct,
               COUNT(k) AS practiced_kps
        """
        q_result = neo4j_session.run(question_query, sid=full_id)
        q_records = list(q_result)
        q_record = q_records[0] if q_records else None
        
        if q_record:
            total_p = q_record["total_practiced"] or 0
            total_c = q_record["total_correct"] or 0
            progress_data["questions_practiced"] = {
                "total_attempts": int(total_p),
                "correct_count": int(total_c),
                "accuracy": round(total_c / total_p * 100, 1) if total_p > 0 else 0,
                "practiced_kps": q_record["practiced_kps"] or 0
            }
        
        questions_data = load_questions()
        progress_data["statistics"]["practiced_questions"] = progress_data["questions_practiced"].get("total_attempts", 0) if isinstance(progress_data["questions_practiced"], dict) else 0
        total_question_items = len(questions_data.get("questions", [])) if isinstance(questions_data, dict) else len(questions_data)
        progress_data["statistics"]["total_questions"] = max(total_question_items, progress_data["statistics"]["practiced_questions"])
        
        # ??????????
        total_items = (progress_data["statistics"]["total_chapters"] + 
                      progress_data["statistics"]["total_videos"] + 
                      progress_data["statistics"]["total_resources"])
        completed_items = (progress_data["statistics"]["learned_chapters"] + 
                         progress_data["statistics"]["watched_videos"] + 
                         progress_data["statistics"]["viewed_resources"])
        raw_completion = round(completed_items / total_items * 100, 1) if total_items > 0 else 0
        progress_data["statistics"]["overall_completion"] = min(100, raw_completion)
        
        # ??????????????????????????????????
        course_query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE k.name =~ '^\\d+\\.\\d+.*'
        RETURN COUNT(DISTINCT k) AS total_kps,
               SUM(r.mastery) AS sum_mastery,
               AVG(r.mastery) AS avg_mastery,
               SUM(r.total_questions) AS total_practiced,
               SUM(r.correct_questions) AS total_correct
        """
        course_result = neo4j_session.run(course_query, sid=full_id).single()
        
        if course_result:
            total_kps = course_result["total_kps"] or 0
            sum_mastery = course_result["sum_mastery"] or 0
            avg_mastery = course_result["avg_mastery"] or 0
            total_practiced = course_result["total_practiced"] or 0
            total_correct = course_result["total_correct"] or 0
            
            progress_data["course_statistics"] = {
                "total_knowledge_points": int(total_kps),
                "average_mastery": round(avg_mastery, 3),
                "total_practiced_questions": int(total_practiced),
                "total_correct_questions": int(total_correct),
                "accuracy": round(total_correct / total_practiced * 100, 1) if total_practiced > 0 else 0,
                "total_chapters": len(progress_data["chapters"]),
                "learned_chapters": sum(1 for ch in progress_data["chapters"] if ch["status"] == "completed"),
                "chapter_details": [
                    {
                        "name": ch["name"],
                        "mastery": ch["avg_mastery"],
                        "status": ch["status"],
                        "learned_kps": ch["learned_kps"],
                        "total_kps": ch["total_kps"]
                    } for ch in progress_data["chapters"]
                ]
            }
    
    return jsonify({"success": True, **progress_data})

@app.route("/student/recommend")
def student_recommend():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    
    full_id = session.get("full_id")
    student_name = session.get("user_name")

    response = make_response(render_template('student_recommend.html',
                                 student_name=student_name,
                                 page_title="??????", active_page="recommend"))
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route("/student/recommend/data")
def get_recommend_data():
    print("=== get_recommend_data called ===")
    if session.get("role") != "student":
        print("Error: not student role")
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    target_kp = request.args.get("target_kp", "").strip()
    print(f"full_id: {full_id}")
    if not full_id:
        return jsonify({"success": False, "error": "???????????????"})
    
    try:
        # ?????????
        user_profile = get_user_profile(full_id)
        
        # ??????????????????
        with driver.session() as neo4j_session:
            # ?????????????????60%?
            weak_query = """
            MATCH (stu:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
            WHERE r.mastery < 0.6
            AND (k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.')
            RETURN k.name AS name, r.mastery AS mastery, k.is_key AS is_key
            ORDER BY r.mastery ASC
            """
            weak_result = neo4j_session.run(weak_query, sid=full_id)
            weak_points = [{"name": r["name"], "mastery": r["mastery"], "is_key": r.get("is_key", False)} for r in weak_result]
            
            # ????????????is_key=true?
            key_query = """
            MATCH (stu:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
            WHERE k.is_key = true
            AND (k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.')
            RETURN k.name AS name, r.mastery AS mastery
            ORDER BY r.mastery ASC
            """
            key_result = neo4j_session.run(key_query, sid=full_id)
            key_points = [{"name": r["name"], "mastery": r["mastery"]} for r in key_result]
            
            # ????????????????????????????????????
            kg_relations_query = """
            MATCH (k1:Knowledge)-[rel]-(k2:Knowledge)
            WHERE (k1.name STARTS WITH '1.' OR k1.name STARTS WITH '2.' OR k1.name STARTS WITH '3.')
            AND (k2.name STARTS WITH '1.' OR k2.name STARTS WITH '2.' OR k2.name STARTS WITH '3.')
            AND type(rel) IN ['???', '???']
            RETURN k1.name AS kp1, k2.name AS kp2, type(rel) AS rel_type
            """
            kg_result = neo4j_session.run(kg_relations_query)
            kg_relations = {}
            for r in kg_result:
                kp1 = r["kp1"]
                kp2 = r["kp2"]
                rel = r["rel_type"]
                if kp1 not in kg_relations:
                    kg_relations[kp1] = []
                kg_relations[kp1].append({"name": kp2, "relation": rel})
            
            # ???????????????????????????????????
            all_mastery_query = """
            MATCH (stu:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
            WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
            RETURN k.name AS name, r.mastery AS mastery
            """
            all_mastery_result = neo4j_session.run(all_mastery_query, sid=full_id)
            all_mastery = {r["name"]: r["mastery"] for r in all_mastery_result}
        
        # ??????????????????
        resources = []
        if os.path.exists(RESOURCE_DIR):
            files = os.listdir(RESOURCE_DIR)
            for f in files:
                if f == "questions.json":
                    continue
                info = parse_resource_info(f)
                # ?????????????
                if info["ch"] and info["ch"] > 3:
                    continue
                chapter = None
                if info["ch"]:
                    chapter = "?{}?".format(info["ch"])
                
                # ??????????
                kp_match = None
                if info["big"] and info["sec"]:
                    kp_match = f"{info['ch']}.{info['big']}.{info['sec']}"
                elif info["big"]:
                    kp_match = f"{info['ch']}.{info['big']}"
                
                # ????????????????????????????????????
                name_without_ext = f.rsplit('.', 1)[0]
                # ?????????????? "2.2.1 " ??"????"
                name_clean = re.sub(r'^\d+\.\d+\.\d+\s*', '', name_without_ext)
                name_clean = re.sub(r'^\d+\.\d+\s*', '', name_clean)
                name_clean = re.sub(r'^??d+??s*', '', name_clean)
                
                resources.append({
                    "name": f,
                    "chapter": chapter,
                    "chapter_num": info["ch"],
                    "knowledge_point": kp_match,
                    "keyword": name_clean.lower(),
                    "difficulty": None
                })
            
            resources.sort(key=lambda x: (x["chapter_num"] or 99, x["name"]))
        
        # ????????????????????????????????????????????????????????????????????????
        # ????????esources/ ???????????????????
        # ????????????????????????????????????????????????????????????????????????

        for res in resources:
            name_without_ext = res["name"].rsplit('.', 1)[0]
            name_clean = re.sub(r'^\d+\.\d+\.\d+\s*', '', name_without_ext)
            name_clean = re.sub(r'^\d+\.\d+\s*', '', name_clean)
            name_clean = re.sub(r'^??d+??s*', '', name_clean)
            if not res.get("knowledge_point") and name_clean:
                res["knowledge_point"] = "{} {}".format(res.get("chapter_num", ""), name_clean) if res.get("chapter_num") else name_clean
                res["keyword"] = name_clean.lower()

        # ??????????????????
        questions_data = load_questions()
        questions = questions_data.get("questions", [])
        filtered_questions = []
        for q in questions:
            kp = q.get("knowledge_point", "")
            ch_match = re.match(r"^(\d+)", kp)
            if ch_match:
                ch_num = int(ch_match.group(1))
                if ch_num <= 3:
                    filtered_questions.append(q)
        
        # ??????????????????????????????????????????????????????????????????????????????????
        # ???????????ippleNet + ?????? + ?????? + ?????? + ????????        # ???????????????????????????????????????????????????????????????????????????????????        
        recommended_items = []
        max_items = 8
        
        user_level = user_profile.get("level_code", 2)
        
        if user_level >= 4:
            target_difficulty, secondary_difficulty = "hard", "medium"
        elif user_level >= 3:
            target_difficulty, secondary_difficulty = "medium", "hard"
        elif user_level >= 2:
            target_difficulty, secondary_difficulty = "medium", "easy"
        else:
            target_difficulty, secondary_difficulty = "easy", "medium"
        
        # ???? 1. ????????????????????????????
        weak_kp_names = set(kp["name"] for kp in weak_points)
        key_kp_names = set(kp["name"] for kp in key_points)
        
        # ????????????????????0????
        unlearned_chapters = set()
        learned_chapters = set()
        for kp_name, mastery in all_mastery.items():
            ch_num = int(kp_name.split('.')[0])
            if mastery == 0.0:
                unlearned_chapters.add(ch_num)
            else:
                learned_chapters.add(ch_num)
        
        # ???????????????????????????0?
        is_new_student = len(learned_chapters) == 0 and len(unlearned_chapters) > 0
        
        # ????????????????????????????????????
        is_half_learned = len(learned_chapters) > 0 and len(unlearned_chapters) > 0
        
        # ??????????????????????????
        if is_new_student:
            # ???????????????????????????????
            all_target_kps = [kp for kp in key_points if kp["name"].startswith("1.")]
            if len(all_target_kps) < 5:
                # ???????????????????????????????
                all_target_kps = [{"name": kp, "mastery": 0.0} for kp in all_mastery if kp.startswith("1.")]
            print(f"[???????? ????????????????{len(all_target_kps)}?????????")
        elif is_half_learned:
            # ???????????????????????????????????????????????
            # ??????????????????
            unlearned_key_kps = [kp for kp in key_points if any(kp["name"].startswith(f"{ch}.") for ch in unlearned_chapters)]
            # ??????????????????
            learned_weak_kps = [kp for kp in weak_points if any(kp["name"].startswith(f"{ch}.") for ch in learned_chapters)]
            
            all_target_kps = unlearned_key_kps + learned_weak_kps
            # ???????????????????????????
            if len(all_target_kps) < 5:
                unlearned_all_kps = [{"name": kp, "mastery": 0.0} for kp in all_mastery if any(kp.startswith(f"{ch}.") for ch in unlearned_chapters)]
                all_target_kps = unlearned_key_kps + learned_weak_kps + unlearned_all_kps
            print(f"[????] ????{learned_chapters}?????{unlearned_chapters}??{len(all_target_kps)}??????")
        elif user_level >= 4:  # ??????????????????????????????
            # ?????????????????????????????????????
            all_target_kps = weak_points + [kp for kp in key_points if kp["name"] not in weak_kp_names and kp.get("mastery", 0) >= 0.75]
            # ???????????????????????
            if len(all_target_kps) < 5:
                all_target_kps = weak_points + key_points
        elif user_level >= 3:  # ????????????????????
            all_target_kps = weak_points + [kp for kp in key_points if kp["name"] not in weak_kp_names]
        else:  # ???/??????????????????
            all_target_kps = weak_points + [kp for kp in key_points if kp["name"] not in weak_kp_names]
        
        behavior_profile = compute_behavior_profile(full_id)
        
        user_pref_video = behavior_profile.get("pref_video", 0.33)
        user_pref_ppt = behavior_profile.get("pref_ppt", 0.33)
        user_pref_practice = behavior_profile.get("pref_practice", 0.33)
        
        avoidance_kps = behavior_profile.get("avoidance_kps", [])
        avoidance_names = set(a["name"] for a in avoidance_kps)
        
        # ???? 2. RippleNet: ???????????? ????
        def ripple_propagation(seed_kp_names, graph_session, max_hops=3, decay=0.6):
            """RippleNet????????????????????????????????????"""
            ripples = []
            current_set = set(seed_kp_names)
            
            for hop in range(max_hops):
                next_set = set()
                weight = (decay ** hop)
                
                for kp_name in current_set:
                    try:
                        result = graph_session.run(
                            """
                            MATCH (kp:KnowledgePoint {name: $name})-[r]-(related)
                            RETURN related.name as related_name, type(r) as rel_type,
                                   CASE WHEN type(r)='BELONGS_TO' THEN 0.3
                                        WHEN type(r)='PREREQUISITE_OF' THEN 0.8
                                        WHEN type(r)='SIMILAR_TO' THEN 0.6
                                        ELSE 0.5 END as rel_weight
                            """,
                            name=kp_name
                        )
                        
                        for record in result:
                            related_name = record["related_name"]
                            if related_name and related_name not in seed_kp_names:
                                rel_weight = record["rel_weight"] * weight
                                ripples.append({
                                    "kp": related_name,
                                    "hop": hop + 1,
                                    "score": rel_weight,
                                    "source": kp_name,
                                    "rel_type": record["rel_type"]
                                })
                                next_set.add(related_name)
                    except Exception as e:
                        pass
                
                current_set = next_set
            
            return ripples
        
        # ???RippleNet???
        ripple_results = []
        try:
            if driver and all_target_kps:
                with driver.session() as graph_session:
                    seed_names = [kp["name"] for kp in all_target_kps[:5]]
                    ripple_results = ripple_propagation(seed_names, graph_session)
                    print(f"[RippleNet] ??????: ??? {len(ripple_results)} ?????????")
        except Exception as e:
            print(f"[RippleNet] ???: {e}")
        
        # ???????????????????
        kg_enhanced_kps = set(weak_kp_names | key_kp_names)
        for r in ripple_results:
            if r["score"] > 0.15:
                kg_enhanced_kps.add(r["kp"])
        
        # ???? 3. ??????????????? ????
        def get_similar_users(current_level, current_weak_count, session, limit=10):
            """???????????"""
            similar_users = []
            try:
                result = session.run(
                    """
                    MATCH (u:Student)-[s:STUDIES]->(kp:KnowledgePoint)
                    WHERE s.mastery < 0.5
                    WITH u, count(DISTINCT kp) as weak_cnt
                    MATCH (u)-[pr:HAS_PROFILE]->(p:Profile)
                    WHERE abs(pr.level_code - $level) <= 1 AND weak_cnt BETWEEN $weak_min AND $weak_max
                    OPTIONAL MATCH (u)-[v:VIEWED]->(res:Resource)
                    RETURN u.id as user_id, pr.level_code as level, 
                           collect(DISTINCT res.name)[..5] as viewed_resources,
                           weak_cnt
                    ORDER BY abs(pr.level_code - $level), abs(weak_cnt - $weak_count)
                    LIMIT $limit
                    """,
                    level=current_level,
                    weak_min=max(0, current_weak_count - 3),
                    weak_max=current_weak_count + 5,
                    weak_count=current_weak_count,
                    limit=limit
                )
                
                for record in result:
                    similar_users.append({
                        "user_id": record["user_id"],
                        "level": record["level"],
                        "viewed_resources": record["viewed_resources"] or [],
                        "weak_count": record["weak_cnt"]
                    })
            except Exception as e:
                print(f"[??????] ???: {e}")
            
            return similar_users
        
        similar_user_resources = set()
        try:
            if driver:
                with driver.session() as graph_session:
                    sim_users = get_similar_users(user_level, len(weak_points), graph_session)
                    print(f"[????] ?? {len(sim_users)} ?????")
                    
                    for su in sim_users:
                        for res_name in su["viewed_resources"]:
                            similar_user_resources.add(res_name)
        except Exception as e:
            print(f"[??????] ???: {e}")
        
        # ???? 4. ?????????????????????????????????
        def compute_resource_score(res, kp_list, ripple_data, cf_resources, viewed_resources):
            """???????????+ ???????????+ ?????????"""
            score = {
                "content_match": 0,
                "ripple_score": 0,
                "cf_score": 0,
                "weak_coverage": 0,
                "avoidance_bonus": 0,
                "behavior_preference": 0,
                "diversity_bonus": 0,
                "viewed_penalty": 0
            }
            
            res_info = parse_resource_info(res.get("name", ""))
            res_ch = res_info.get("ch")
            res_big = res_info.get("big")
            res_sec = res_info.get("sec")
            
            covered_weak = []
            covered_key = []
            covered_avoidance = []
            
            for kp in kp_list:
                kp_name = kp["name"]
                
                kp_ch_match = re.match(r'^(\d+)', kp_name)
                if not kp_ch_match: continue
                kp_ch = kp_ch_match.group(1)
                
                if res_ch is None or str(res_ch) != str(kp_ch): continue
                
                kp_big_m = re.match(r'^\d+\.(\d+)', kp_name)
                kp_big = kp_big_m.group(1) if kp_big_m else None
                kp_sec_m = re.match(r'^\d+\.\d+\.(\d+)', kp_name)
                kp_sec = kp_sec_m.group(1) if kp_sec_m else None
                
                match_depth = 0
                if kp_sec and res_sec is not None and str(res_sec) == str(kp_sec):
                    match_depth = 3
                elif kp_big and res_big is not None and str(res_big) == str(kp_big):
                    match_depth = 2
                elif res_ch == int(kp_ch):
                    match_depth = 1
                
                if match_depth > 0:
                    if kp_name in weak_kp_names:
                        covered_weak.append((kp, match_depth))
                    elif kp_name in key_kp_names:
                        covered_key.append((kp, match_depth))
                    if kp_name in avoidance_names:
                        covered_avoidance.append((kp, match_depth))
            
            total_coverage = len(covered_weak) * 30 + len(covered_key) * 15
            depth_bonus = sum(d for _, d in covered_weak) * 10 + sum(d for _, d in covered_key) * 5
            
            weak_avg = sum(w[0]["mastery"] for w in covered_weak) / len(covered_weak) if covered_weak else None
            urgency_factor = (1 - weak_avg) if weak_avg is not None else 1.0
            
            score["content_match"] = (total_coverage + depth_bonus) * urgency_factor
            score["weak_coverage"] = len(covered_weak)
            
            avoidance_boost = sum(
                (0.4 - a[0]["mastery"]) * 40 * a[1] / 3
                for a in covered_avoidance
            )
            score["avoidance_bonus"] = avoidance_boost
            
            res_kp = res.get("knowledge_point", "")
            for ripple in ripple_data:
                if ripple["kp"] == res_kp or (res_kp and ripple["kp"] in res_kp):
                    score["ripple_score"] += ripple["score"] * 25
            
            if res.get("name") in cf_resources:
                score["cf_score"] = 20
            
            res_ext = res.get("name", "").split(".")[-1]
            is_video = (res_ext == "mp4")
            is_ppt = (res_ext == "pptx")
            
            if is_video:
                score["behavior_preference"] = user_pref_video * 12
            elif is_ppt:
                score["behavior_preference"] = user_pref_ppt * 10
            else:
                score["behavior_preference"] = user_pref_practice * 8
            
            score["diversity_bonus"] = 6 if is_video else 4
            
            # ?????????????????????
            difficulty_boost = 0
            if user_level >= 4:  # ??????????????????
                if res_info.get("big") and int(res_info.get("big", 0)) >= 3:
                    difficulty_boost = 15
                if res_info.get("sec") and int(res_info.get("sec", 0)) >= 3:
                    difficulty_boost += 10
            elif user_level >= 3:  # ????????????????????                if res_info.get("big") and int(res_info.get("big", 0)) >= 2:
                    difficulty_boost = 10
            
            # ???????????????????????????
            res_name = res.get("name", "")
            if res_name in viewed_resources:
                view_count = viewed_resources[res_name]
                # ???????????????????????????
                score["viewed_penalty"] = min(view_count * 5, 20)
            
            # ?????? = ?????????0% + ????????????0% + ???????????????5% + ?????????5% + ?????????0% + ?????????% + ?????????????8 + ????????? - ???????
            final_score = (
                score["content_match"] * 0.30 +
                score["avoidance_bonus"] * 0.20 +
                score["ripple_score"] * 0.15 +
                score["behavior_preference"] * 0.15 +
                score["cf_score"] * 0.10 +
                score["diversity_bonus"] * 0.05 +
                score["weak_coverage"] * 8 +
                difficulty_boost -
                score["viewed_penalty"]
            )
            
            return {
                **res,
                "_scores": score,
                "final_score": final_score,
                "covered_weak": [w[0] for w in covered_weak],
                "covered_key": [k[0] for k in covered_key],
                "covered_avoidance": [a[0] for a in covered_avoidance],
                "match_depth": max([w[1] for w in covered_weak] + [k[1] for k in covered_key], default=0),
                "is_avoidance_target": len(covered_avoidance) > 0
            }
        
        # ????????????
        viewed_resources = {}
        try:
            with driver.session() as neo4j_session:
                result = neo4j_session.run("""
                MATCH (s:Student {id: $sid})-[r:VIEWED]->(res:Resource)
                RETURN res.name as resource_name, COALESCE(r.view_count, 0) as view_count
                """, sid=full_id)
                for record in result:
                    viewed_resources[record["resource_name"]] = record["view_count"] or 0
        except Exception as e:
            print(f"[??????] ???: {e}")
        
        # ??????????
        scored_resources = []
        for res in resources:
            scored = compute_resource_score(res, all_target_kps, ripple_results, similar_user_resources, viewed_resources)
            if scored["final_score"] > 5 or len(scored["covered_weak"]) > 0:
                scored_resources.append(scored)
        
        # ??????????
        scored_resources.sort(key=lambda x: (-x["final_score"], -x["_scores"]["weak_coverage"]))
        
        # ???? 5. ??????????????????????????
        chapter_groups = {}
        
        ch_selected = {}
        for sr in scored_resources:
            res_info = parse_resource_info(sr.get("name", ""))
            ch_num = str(res_info.get("ch", 0))
            
            if ch_num not in chapter_groups:
                chapter_groups[ch_num] = {
                    "chapter_num": ch_num,
                    "chapter_name": "?{}?".format(ch_num),
                    "resources": [],
                    "all_weak": [],
                    "all_key": [],
                    "total_score": 0
                }
            
            if len(chapter_groups[ch_num]["resources"]) < 4:
                chapter_groups[ch_num]["resources"].append(sr)
                chapter_groups[ch_num]["all_weak"].extend(sr["covered_weak"])
                chapter_groups[ch_num]["all_key"].extend(sr["covered_key"])
                chapter_groups[ch_num]["total_score"] += sr["final_score"]
                
                if ch_num not in ch_selected:
                    ch_selected[ch_num] = 0
                ch_selected[ch_num] += 1
            
            if sum(ch_selected.values()) >= max_items * 3 and len(ch_selected) >= 3:
                break
        
        for ch in chapter_groups.values():
            seen_w, seen_k = set(), set()
            ch["weak_points"] = [w for w in ch["all_weak"] if not (w["name"] in seen_w or seen_w.add(w["name"]))]
            ch["key_points"] = [k for k in ch["all_key"] if not (k["name"] in seen_k or seen_k.add(k["name"]))]
            ch["weak_count"] = len(ch["weak_points"])
            ch["key_count"] = len(ch["key_points"])
        
        sorted_chapters = sorted(chapter_groups.values(), 
                                  key=lambda x: (-x["total_score"], -x["weak_count"]))
        
        # ???????????
        global_res_idx = 0
        for ch_group in sorted_chapters[:max_items]:
            ch_num = ch_group["chapter_num"]
            weak_list = ch_group["weak_points"]
            key_list = ch_group["key_points"]
            
            avg_mastery = sum(w["mastery"] for w in weak_list) / len(weak_list) if weak_list else None
            
            all_ch_kp_names = [kp["name"] for kp in weak_list + key_list]
            
            ch_questions = []
            for q in filtered_questions:
                if q.get("knowledge_point") in all_ch_kp_names:
                    q["_kp"] = q.get("knowledge_point", "")
                    ch_questions.append(q)

            practice_history = load_question_history()
            student_history = practice_history.get(full_id, {}) if practice_history else {}

            def calc_practice_score(q):
                qid = q.get("id", "")
                hist = student_history.get(qid, {})
                total_attempts = hist.get("total_attempts", 0)
                correct_count = hist.get("correct_count", 0)
                wrong_count = hist.get("wrong_count", 0)
                consecutive_correct = hist.get("consecutive_correct", 0)
                last_result = hist.get("last_result", None)

                if total_attempts == 0:
                    return 100, "??"
                elif consecutive_correct == 0 and wrong_count > 0:
                    return 150 + wrong_count * 10, "????"
                elif last_result == "wrong":
                    return 120 + wrong_count * 5, "????"
                elif consecutive_correct >= 3:
                    return max(10, 30 - total_attempts * 3), "???"
                elif consecutive_correct >= 1:
                    return 50 - total_attempts * 2, "??????"
                else:
                    return 70, "?????"

            for q in ch_questions:
                q["_practice_score"], q["_practice_tag"] = calc_practice_score(q)

            ch_questions.sort(key=lambda q: (-q["_practice_score"], q.get("difficulty", 2)))

            target_qs = [q for q in ch_questions if q.get("difficulty") == target_difficulty]
            secondary_qs = [q for q in ch_questions if q.get("difficulty") == secondary_difficulty]
            other_qs = [q for q in ch_questions if q.get("difficulty") not in [target_difficulty, secondary_difficulty]]
            sorted_qs = target_qs + secondary_qs + other_qs
            
            # ??????????
            ch_resources = []
            for sr in ch_group["resources"][:3]:
                global_res_idx += 1
                match_tag = "????" if sr["match_depth"] >= 3 else ("?????" if sr["match_depth"] >= 2 else "????")
                
                ch_resources.append({
                    "name": sr["name"],
                    "match_level": sr["match_depth"],
                    "match_tag": match_tag,
                    "for_kp": sr["covered_weak"][0]["name"] if sr["covered_weak"] else (sr["covered_key"][0]["name"] if sr["covered_key"] else ""),
                    "rec_score": round(sr["final_score"], 1),
                    "algorithms_used": []
                })
                
                # ??????????
                algos = []
                if sr["_scores"]["content_match"] > 0: algos.append("??????")
                if sr["_scores"]["ripple_score"] > 0: algos.append("RippleNet")
                if sr["_scores"]["cf_score"] > 0: algos.append("??????")
                ch_resources[-1]["algorithms_used"] = algos
            
            weak_point_names = [f"{kp['name']} ({kp['mastery']*100:.0f}%)" for kp in weak_list]
            key_point_names = [kp["name"] for kp in key_list if kp["name"] not in [w["name"] for w in weak_list]]
            
            recommend_reason = []
            if len(weak_list) >= 3:
                recommend_reason.append(f"???{len(weak_list)}??????")
            elif len(weak_list) > 0:
                recommend_reason.append(f"????: {', '.join(weak_point_names[:3])}")
            if key_point_names:
                recommend_reason.append(f"????: {', '.join(key_point_names[:2])}")

            wrong_qs = [q for q in sorted_qs if q.get("_practice_tag") in ["????", "????", "?????"]]
            new_qs = [q for q in sorted_qs if q.get("_practice_tag") == "??"]
            mastered_qs = [q for q in sorted_qs if q.get("_practice_tag") == "???"]
            if wrong_qs:
                recommend_reason.append(f"?{len(wrong_qs)}??????")
            if new_qs:
                recommend_reason.append(f"?{len(new_qs)}???")

            final_questions = []
            for q in sorted_qs[:10]:
                final_questions.append({
                    "id": q.get("id"),
                    "question": q.get("question"),
                    "options": q.get("options"),
                    "answer": q.get("answer"),
                    "explanation": q.get("explanation", ""),
                    "difficulty": q.get("difficulty"),
                    "knowledge_point": q.get("knowledge_point", ""),
                    "_kp": q.get("_kp", ""),
                    "_practice_score": q.get("_practice_score", 100),
                    "_practice_tag": q.get("_practice_tag", "??")
                })
            
            recommended_items.append({
                "type": "chapter_aggregated",
                "chapter_num": ch_num,
                "chapter_name": ch_group["chapter_name"],
                "avg_mastery": avg_mastery,
                "weak_points": weak_list,
                "key_points": key_list,
                "weak_count": len(weak_list),
                "key_count": len(key_list),
                "avoidance_kps": avoidance_kps,
                "questions": final_questions,
                "question_count": len(sorted_qs),
                "resources": ch_resources[:3],
                "recommend_reason": " | ".join(recommend_reason) if recommend_reason else "????",
                "mastery_status": "????" if avg_mastery is None else ("??" if avg_mastery < 0.4 else ("???" if avg_mastery < 0.6 else ("??" if avg_mastery < 0.8 else "??"))),
                "algorithms_used": list(set([a for r in ch_resources for a in r.get("algorithms_used", [])] + ["????"]))
            })
        
        path_recommendation = build_path_recommendation(
            full_id,
            resources,
            behavior_profile,
            target_kp if target_kp else None
        )

        return jsonify({
            "success": True, 
            "user_profile": user_profile,
            "behavior_profile": behavior_profile,
            "path_recommendation": path_recommendation,
            "weak_points": weak_points, 
            "key_points": key_points,
            "avoidance_kps": avoidance_kps,
            "recommended_items": recommended_items[:max_items],
            "resources": resources, 
            "questions": filtered_questions
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route("/student/resources")
def student_resources():
    if session.get("role") != "student":
        return redirect(url_for("login"))
    return render_flow_page("?????", "resources")
    
    student_name = session.get("user_name")
    
    template = STUDENT_BASE_HTML.replace("<!--PAGE_CONTENT-->", STUDENT_RESOURCES_PAGE)
    return render_template_string(template, 
                                 student_name=student_name, 
                                 page_title="????", active_page="resources")

@app.route("/student/resources/data")
def get_student_resources_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    if request.args.get("legacy") != "1":
        return jsonify({
            "success": True,
            "resources": get_flow_resources(session.get("full_id")),
            "questions": []
        })
    
    if not os.path.exists(RESOURCE_DIR):
        return jsonify({"success": True, "resources": [], "questions": []})
    
    files = os.listdir(RESOURCE_DIR)
    resources = []
    for f in files:
        if f == "questions.json":
            continue
        info = parse_resource_info(f)
        # ?????????????
        if info["ch"] and info["ch"] > 3:
            continue
        chapter = None
        if info["ch"]:
            chapter = "?{}?".format(info["ch"])
        
        # ??????????
        kp_match = None
        if info["big"] and info["sec"]:
            kp_match = f"{info['ch']}.{info['big']}.{info['sec']}"
        elif info["big"]:
            kp_match = f"{info['ch']}.{info['big']}"
        
        resources.append({
            "name": f,
            "chapter": chapter,
            "chapter_num": info["ch"],
            "knowledge_point": kp_match,
            "difficulty": None
        })
    
    resources.sort(key=lambda x: (x["chapter_num"] or 99, x["name"]))
    
    # ??????????????????????????????
    questions_data = load_questions()
    questions = questions_data.get("questions", [])
    
    # ????????????????
    student_id = session.get("full_id")
    kp_mastery_map = {}
    if student_id:
        try:
            with driver.session() as neo_session:
                query = """
                MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
                RETURN k.name AS name, r.mastery AS mastery
                """
                result = neo_session.run(query, sid=student_id)
                for r in result:
                    kp_mastery_map[r["name"]] = r["mastery"]
        except:
            pass
    
    filtered_questions = []
    for q in questions:
        kp = q.get("knowledge_point", "")
        ch_match = re.match(r"^(\d+)", kp)
        if ch_match:
            ch_num = int(ch_match.group(1))
            if ch_num <= 3:
                # ???????????????
                q_with_mastery = q.copy()
                q_with_mastery["mastery"] = kp_mastery_map.get(kp, 0)
                filtered_questions.append(q_with_mastery)
    
    return jsonify({"success": True, "resources": resources, "questions": filtered_questions})

@app.route("/student/submit", methods=["POST"])
def submit_practice():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????????????"})
    
    full_id = session.get("full_id")
    if not full_id:
        return jsonify({"success": False, "error": "????"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "????????????"})
        
        knowledge_name = data.get("knowledge")
        is_correct = data.get("is_correct", False)
        question_id = data.get("question_id")
        
        if not knowledge_name:
            return jsonify({"success": False, "error": "????"})
        
        new_mastery = update_student_mastery(full_id, knowledge_name, is_correct)
        
        if question_id:
            print(f"[SUBMIT-SYNC] student={full_id}, q={question_id}, correct={is_correct}")
            try:
                history = load_question_history()
                if full_id not in history:
                    history[full_id] = {}
                if question_id not in history[full_id]:
                    history[full_id][question_id] = {
                        "correct_count": 0, "wrong_count": 0,
                        "consecutive_correct": 0, "last_result": None,
                        "total_attempts": 0, "first_wrong_time": None,
                        "last_attempt_time": None
                    }
                qh = history[full_id][question_id]
                qh["total_attempts"] += 1
                qh["last_attempt_time"] = datetime.now().isoformat()
                if is_correct:
                    qh["correct_count"] += 1
                    qh["consecutive_correct"] += 1
                    qh["last_result"] = "correct"
                else:
                    qh["wrong_count"] += 1
                    qh["consecutive_correct"] = 0
                    if not qh["first_wrong_time"]:
                        qh["first_wrong_time"] = datetime.now().isoformat()
                    qh["last_result"] = "wrong"
                save_question_history(history)
                print(f"[SUBMIT-SYNC] ??????!")
            except Exception as sync_err:
                print(f"[SUBMIT-SYNC] ??????: {sync_err}")
        
        return jsonify({
            "success": True,
            "knowledge": knowledge_name,
            "is_correct": is_correct,
            "new_mastery": new_mastery
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

# ????????????????????????????????????????????????????????????
# ????????? & ????????# ????????????????????????????????????????????????????????????

QUESTION_HISTORY_FILE = os.path.join(RESOURCE_DIR, "question_history.json")

def load_question_history():
    """??????????"""
    if os.path.exists(QUESTION_HISTORY_FILE):
        try:
            with open(QUESTION_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and len(data) > 0:
                    print(f"[LOAD] Loaded {sum(len(v) for v in data.values())} records")
                    return data
                print("[LOAD] File exists but empty/invalid")
                return {}
        except Exception as e:
            print(f"[LOAD] Error: {e}, returning empty dict to prevent data loss")
            return {}
    print("[LOAD] No history file found")
    return {}

def save_question_history(history):
    try:
        total = sum(len(v) for v in history.values() if isinstance(v, dict))
        print(f"[SAVE] Saving {total} records to {QUESTION_HISTORY_FILE}")
        
        backup_file = QUESTION_HISTORY_FILE + ".bak"
        if os.path.exists(QUESTION_HISTORY_FILE):
            import shutil
            shutil.copy2(QUESTION_HISTORY_FILE, backup_file)
        
        with open(QUESTION_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        print(f"[SAVE] Success! Backup saved to .bak file")
    except Exception as e:
        print(f"[SAVE] Error: {e}")
        import traceback
        traceback.print_exc()

@app.route("/student/question/record", methods=["POST"])
def record_question_result():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    if not full_id:
        return jsonify({"success": False, "error": "????"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "????????????"})
        
        question_id = data.get("question_id")
        is_correct = data.get("is_correct", False)
        
        print(f"[RECORD] student={full_id}, question={question_id}, correct={is_correct}")
        
        if not question_id:
            return jsonify({"success": False, "error": "??????ID"})
        
        # ?????????
        history = load_question_history()
        
        # ??????????
        if full_id not in history:
            history[full_id] = {}
        
        # ??????????
        if question_id not in history[full_id]:
            history[full_id][question_id] = {
                "correct_count": 0,
                "wrong_count": 0,
                "consecutive_correct": 0,
                "last_result": None,
                "total_attempts": 0,
                "first_wrong_time": None,
                "last_attempt_time": None
            }
        
        q_history = history[full_id][question_id]
        q_history["total_attempts"] += 1
        q_history["last_attempt_time"] = datetime.now().isoformat()
        
        if is_correct:
            q_history["correct_count"] += 1
            q_history["consecutive_correct"] += 1
            q_history["last_result"] = "correct"
        else:
            q_history["wrong_count"] += 1
            q_history["consecutive_correct"] = 0  # ????????????
            q_history["last_result"] = "wrong"
            
            # ???????????????
            if not q_history["first_wrong_time"]:
                q_history["first_wrong_time"] = datetime.now().isoformat()
        
        # ?????????
        save_question_history(history)
        
        # ???????????????
        return jsonify({
            "success": True,
            "question_id": question_id,
            "statistics": {
                "correct_count": q_history["correct_count"],
                "wrong_count": q_history["wrong_count"],
                "consecutive_correct": q_history["consecutive_correct"],
                "total_attempts": q_history["total_attempts"],
                "is_in_wrong_book": q_history["consecutive_correct"] < 3 and q_history["wrong_count"] > 0
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/student/question/batch_record", methods=["POST"])
def batch_record_results():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    if not full_id:
        return jsonify({"success": False, "error": "????"})
    
    try:
        data = request.get_json()
        results = data.get("results", [])
        
        print(f"[BATCH] student={full_id}, submitting {len(results)} results")
        
        history = load_question_history()
        
        if full_id not in history:
            history[full_id] = {}
        
        for r in results:
            question_id = r.get("question_id")
            is_correct = r.get("is_correct", False)
            
            if not question_id:
                continue
            
            if question_id not in history[full_id]:
                history[full_id][question_id] = {
                    "correct_count": 0,
                    "wrong_count": 0,
                    "consecutive_correct": 0,
                    "last_result": None,
                    "total_attempts": 0,
                    "first_wrong_time": None,
                    "last_attempt_time": None
                }
            
            qh = history[full_id][question_id]
            qh["total_attempts"] += 1
            qh["last_attempt_time"] = datetime.now().isoformat()
            
            if is_correct:
                qh["correct_count"] += 1
                qh["consecutive_correct"] += 1
                qh["last_result"] = "correct"
            else:
                qh["wrong_count"] += 1
                qh["consecutive_correct"] = 0
                if not qh["first_wrong_time"]:
                    qh["first_wrong_time"] = datetime.now().isoformat()
                qh["last_result"] = "wrong"
        
        save_question_history(history)
        
        return jsonify({
            "success": True,
            "submitted": len(results),
            "message": f"??? {len(results)} ?????"
        })
    except Exception as e:
        print(f"[BATCH] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route("/student/question/history")
def get_question_history():
    """?????????????"""
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    if not full_id:
        return jsonify({"success": False, "error": "????"})
    
    try:
        history = load_question_history()
        student_history = history.get(full_id, {})
        
        return jsonify({
            "success": True,
            "history": student_history
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/student/wrong-questions")
def get_wrong_questions():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    if not full_id:
        return jsonify({"success": False, "error": "????"})
    
    try:
        history = load_question_history()
        student_history = history.get(full_id, {})
        
        questions_data = load_questions()
        all_questions = {}
        for q in questions_data.get("questions", []):
            all_questions[q["id"]] = q
        
        wrong_questions = []
        for qid, q_stats in student_history.items():
            try:
                if q_stats.get("wrong_count", 0) > 0 and q_stats.get("consecutive_correct", 0) < 1:
                    if qid in all_questions:
                        wrong_q = dict(all_questions[qid])
                        wrong_q["stats"] = q_stats
                        wrong_questions.append(wrong_q)
            except Exception as e:
                print(f"[WRONG-Q] Error processing {qid}: {e}")
                continue
        
        wrong_questions.sort(key=lambda x: (
            -x["stats"].get("wrong_count", 0),
            x["stats"].get("last_attempt_time", "")
        ))
        
        total_wrong = sum(1 for q in student_history.values() if q.get("wrong_count", 0) > 0)
        mastered = sum(1 for q in student_history.values() if q.get("consecutive_correct", 0) >= 3)
        
        return jsonify({
            "success": True,
            "wrong_questions": wrong_questions,
            "total_count": len(wrong_questions),
            "summary": {
                "total_wrong": total_wrong,
                "need_practice": len(wrong_questions),
                "mastered": mastered
            }
        })
    except Exception as e:
        print(f"[WRONG-Q] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)})

@app.route("/student/log_behavior", methods=["POST"])
def log_behavior():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    if not full_id:
        return jsonify({"success": False, "error": "????"})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "??????"})
        
        action_type = data.get("action", "")
        target_name = data.get("target", "")
        kp_name = data.get("knowledge_point", "")
        
        if not action_type or not target_name:
            return jsonify({"success": False, "error": "??????"})
        
        BEHAVIOR_WEIGHTS = {
            "click": 1, "download": 3, "watch_video": 5,
            "quiz_correct": 7, "quiz_wrong": 3
        }
        
        weight = BEHAVIOR_WEIGHTS.get(action_type, 1)
        
        with driver.session() as neo4j_session:
            if action_type in ("click", "download", "watch_video"):
                neo4j_session.run("""
                MERGE (s:Student {id: $sid})
                MERGE (r:Resource {name: $rname})
                MERGE (s)-[rel:INTERACTED_WITH]->(r)
                SET rel.count = COALESCE(rel.count, 0) + 1,
                    rel.last_action = $action,
                    rel.total_weight = COALESCE(rel.total_weight, 0) + $weight,
                    rel.last_time = datetime().epochSeconds
                """, sid=full_id, rname=target_name, action=action_type, weight=weight)
                
                if kp_name:
                    neo4j_session.run("""
                    MATCH (s:Student {id: $sid})
                    MATCH (kp:KnowledgePoint {name: $kname})
                    MERGE (s)-[rel:ENGAGED_WITH]->(kp)
                    SET rel.engagement_count = COALESCE(rel.engagement_count, 0) + 1,
                        rel.engagement_weight = COALESCE(rel.engagement_weight, 0) + $weight,
                        rel.last_action = $action,
                        rel.last_time = datetime().epochSeconds
                    """, sid=full_id, kname=kp_name, action=action_type, weight=weight)
            
            elif action_type in ("quiz_correct", "quiz_wrong"):
                if kp_name:
                    is_correct = action_type == "quiz_correct"
                    neo4j_session.run("""
                    MATCH (s:Student {id: $sid})
                    MATCH (kp:KnowledgePoint {name: $kname})
                    MERGE (s)-[rel:QUIZZED_ON]->(kp)
                    SET rel.quiz_count = COALESCE(rel.quiz_count, 0) + 1,
                        rel.correct_count = COALESCE(rel.correct_count, 0) + CASE WHEN $correct THEN 1 ELSE 0 END,
                        rel.total_weight = COALESCE(rel.total_weight, 0) + $weight,
                        rel.last_time = datetime().epochSeconds
                    """, sid=full_id, kname=kp_name, correct=is_correct, weight=weight)
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


def compute_behavior_profile(student_id):
    behavior_profile = {
        "total_actions": 0,
        "video_actions": 0, "ppt_actions": 0, "practice_actions": 0,
        "pref_video": 0.33, "pref_ppt": 0.33, "pref_practice": 0.33,
        "kp_engagement": {}, "avoidance_kps": [], "engaged_kps": []
    }
    
    try:
        with driver.session() as neo4j_session:
            result = neo4j_session.run("""
            MATCH (s:Student {id: $sid})-[rel:ENGAGED_WITH]->(kp:KnowledgePoint)
            RETURN kp.name AS kp_name, 
                   rel.engagement_count AS count,
                   rel.engagement_weight AS weight,
                   rel.last_action AS last_action
            ORDER BY weight DESC
            """, sid=student_id)
            
            kp_data = []
            for record in result:
                kp_data.append({
                    "name": record["kp_name"],
                    "count": record["count"] or 0,
                    "weight": record["weight"] or 0,
                    "last_action": record["last_action"]
                })
            
            resource_result = neo4j_session.run("""
            MATCH (s:Student {id: $sid})-[rel:INTERACTED_WITH]->(r:Resource)
            RETURN r.name AS res_name, rel.total_weight AS weight, rel.last_action AS action
            """, sid=student_id)
            
            video_w = ppt_w = prac_w = 0
            for rec in resource_result:
                rname = rec["res_name"] or ""
                w = rec["weight"] or 0
                if rname.endswith(".mp4"):
                    video_w += w
                elif rname.endswith(".pptx"):
                    ppt_w += w
            
            quiz_result = neo4j_session.run("""
            MATCH (s:Student {id: $sid})-[rel:QUIZZED_ON]->(kp:KnowledgePoint)
            RETURN sum(rel.quiz_count) AS total_quiz
            """, sid=student_id)
            for qr in quiz_result:
                prac_w = qr["total_quiz"] or 0
            
            total_w = video_w + ppt_w + prac_w
            if total_w > 0:
                behavior_profile["pref_video"] = round(video_w / total_w, 3)
                behavior_profile["pref_ppt"] = round(ppt_w / total_w, 3)
                behavior_profile["pref_practice"] = round(prac_w / total_w, 3)
            
            behavior_profile["video_actions"] = video_w
            behavior_profile["ppt_actions"] = ppt_w
            behavior_profile["practice_actions"] = prac_w
            behavior_profile["total_actions"] = int(total_w)
            
            for kd in kp_data:
                behavior_profile["kp_engagement"][kd["name"]] = kd
            
            mastery_result = neo4j_session.run("""
            MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
            WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
            RETURN k.name AS name, r.mastery AS mastery, r.total_questions AS total_q
            ORDER BY r.mastery ASC
            LIMIT 20
            """, sid=student_id)
            
            low_mastery_kps = []
            for mr in mastery_result:
                mname = mr["name"]
                mmastery = mr["mastery"] or 0
                mtotal_q = mr["total_q"] or 0
                engagement = behavior_profile["kp_engagement"].get(mname, {})
                eng_weight = engagement.get("weight", 0)
                
                if mmastery < 0.4 and mtotal_q >= 3 and eng_weight < 2:
                    low_mastery_kps.append({
                        "name": mname,
                        "mastery": mmastery,
                        "questions_done": mtotal_q,
                        "engagement": eng_weight,
                        "avoidance_score": (0.4 - mmastery) * (2 - min(eng_weight/mtotal_q, 2))
                    })
            
            low_mastery_kps.sort(key=lambda x: -x["avoidance_score"])
            behavior_profile["avoidance_kps"] = low_mastery_kps[:8]
            
            high_engagement = sorted(
                [kd for kd in kp_data if kd["weight"] > 0],
                key=lambda x: -x["weight"]
            )[:10]
            behavior_profile["engaged_kps"] = [{"name": e["name"], "weight": e["weight"]} for e in high_engagement]
    
    except Exception as e:
        print("[??????] ???: {}".format(str(e)))
    
    return behavior_profile


@app.route("/teacher/students")
def teacher_students():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    
    teacher_name = session.get("user_name")
    students = get_all_students()
    
    # ??????????????
    student_profiles = []
    class_total_mastery = 0
    class_total_accuracy = 0
    class_level_counts = {"???": 0, "???": 0, "???": 0, "???": 0}
    
    for s in students:
        profile = get_user_profile(s["id"])
        profile["student_id"] = s["id"]
        profile["student_num"] = s.get("num", "")
        profile["student_name"] = s.get("name", "")
        student_profiles.append(profile)
        
        class_total_mastery += profile.get("avg_mastery", 0)
        class_total_accuracy += profile.get("accuracy", 0)
        
        level = profile.get("level", "???")
        if level in class_level_counts:
            class_level_counts[level] += 1
    
    # ????????????
    total_students = len(student_profiles) if student_profiles else 1
    class_profile = {
        "avg_mastery": class_total_mastery / total_students,
        "avg_accuracy": class_total_accuracy / total_students,
        "total_students": total_students,
        "level_distribution": class_level_counts,
        "excellent_rate": (class_level_counts.get("???", 0) / total_students) * 100,
        "weak_rate": (class_level_counts.get("???", 0) / total_students) * 100
    }
    
    template = TEACHER_BASE_HTML.replace("<!--PAGE_CONTENT-->", TEACHER_STUDENTS_PAGE)
    return render_template_string(template, 
                                 students=students, teacher_name=teacher_name, 
                                 page_title="??????", active_page="students", initial_tab="profiles",
                                 graph_data=None, recs=None, selected_sid=None,
                                 student_profiles=student_profiles, class_profile=class_profile)

@app.route("/teacher/manage")
def teacher_manage():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    return render_teacher_workspace("students", "学生管理")

@app.route("/teacher/view", methods=["POST"])
def teacher_view_student():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    
    sid = request.form.get("student_id")
    teacher_name = session.get("user_name")
    students = get_all_students()
    
    selected_profile = None
    if sid:
        selected_profile = get_user_profile(sid)
        selected_profile["student_id"] = sid
        match = re.match(r"(\d+)(.*)", sid)
        if match:
            selected_profile["student_num"] = match.group(1)
            selected_profile["student_name"] = match.group(2)
        graph = get_knowledge_graph(sid)
        graph_data = graph if graph["nodes"] else None
        recs = get_recommendations(sid) if graph["nodes"] else None
        selected_mastery = get_flow_mastery_data(sid)
    else:
        graph_data = None
        recs = None
        selected_mastery = None
    
    template = TEACHER_BASE_HTML.replace("<!--PAGE_CONTENT-->", TEACHER_STUDENTS_PAGE)
    return render_template_string(template, 
                                 students=students, teacher_name=teacher_name, 
                                 page_title="??????", active_page="students", initial_tab="profiles",
                                 graph_data=graph_data, recs=recs, selected_sid=sid,
                                 selected_profile=selected_profile,
                                 selected_mastery=selected_mastery)

@app.route("/teacher/upload")
def teacher_upload_page():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    return redirect(url_for("teacher_resource_manage"))

@app.route("/teacher/upload", methods=["POST"])
def teacher_upload():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    
    if "file" not in request.files:
        return jsonify({"success": False, "error": "??????"})
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "????"})
    
    original_filename = file.filename
    if '.' in original_filename:
        name_part, ext_part = original_filename.rsplit('.', 1)
    else:
        name_part = original_filename
        ext_part = ''
    
    safe_name = name_part.replace('/', '_').replace('\\', '_').replace('..', '_')
    if ext_part:
        filename = f"{safe_name}.{ext_part}"
    else:
        filename = safe_name
    
    filepath = os.path.join(RESOURCE_DIR, filename)
    file.save(filepath)
    
    info = parse_resource_info(filename)
    matched = ""
    if info["level"] == "section":
        matched = f"?{info['ch']}? ?{info['big']}?? ?{info['sec']}??"
    elif info["level"] == "big":
        matched = f"?{info['ch']}? ?{info['big']}??"
    elif info["level"] == "chapter":
        matched = f"?{info['ch']}?"
    else:
        matched = "???????????????????X??X.X.X?X.X ???"
    
    return jsonify({"success": True, "filename": filename, "matched": matched})

@app.route("/teacher/questions")
def teacher_questions():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    return redirect(url_for("teacher_question_bank"))

@app.route("/teacher/questions/data")
def get_teacher_questions_data():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    
    questions_data = load_questions()
    return jsonify({"success": True, "questions": questions_data.get("questions", [])})

def resource_safe_path(filename):
    safe = os.path.basename(filename or "")
    if not safe or safe in {"questions.json", "question_history.json"}:
        return None
    path = os.path.abspath(os.path.join(RESOURCE_DIR, safe))
    root = os.path.abspath(RESOURCE_DIR)
    if not path.startswith(root + os.sep):
        return None
    return path

@app.route("/teacher/resources/data")
def teacher_resources_data():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    items = []
    for item in get_flow_resources():
        path = resource_safe_path(item.get("name"))
        size = os.path.getsize(path) if path and os.path.exists(path) else 0
        mtime = os.path.getmtime(path) if path and os.path.exists(path) else 0
        item["size"] = size
        item["updated_at"] = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M") if mtime else ""
        items.append(item)
    return jsonify({"success": True, "resources": items})

@app.route("/teacher/resource/update", methods=["POST"])
def teacher_resource_update():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    old_name = data.get("old_name", "").strip()
    new_name = data.get("new_name", "").strip().replace("/", "_").replace("\\", "_").replace("..", "_")
    old_path = resource_safe_path(old_name)
    if not old_path or not os.path.exists(old_path):
        return jsonify({"success": False, "error": "????"})
    if not new_name:
        return jsonify({"success": False, "error": "????????????"})
    new_path = resource_safe_path(new_name)
    if not new_path:
        return jsonify({"success": False, "error": "?????????"})
    if os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(old_path):
        return jsonify({"success": False, "error": "????"})
    os.replace(old_path, new_path)
    return jsonify({"success": True, "message": "?????", "filename": new_name})

@app.route("/teacher/resource/delete", methods=["POST"])
def teacher_resource_delete():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    filename = data.get("filename", "").strip()
    path = resource_safe_path(filename)
    if not path or not os.path.exists(path):
        return jsonify({"success": False, "error": "????"})
    os.remove(path)
    return jsonify({"success": True, "message": "?????"})

@app.route("/teacher/knowledge-points/data")
def teacher_knowledge_points_data():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    points = set()
    try:
        with driver.session() as neo4j_session:
            rows = neo4j_session.run("""
            MATCH (k:Knowledge)
            RETURN k.name AS name
            ORDER BY k.name
            LIMIT 500
            """)
            points.update(row["name"] for row in rows if row["name"])
    except Exception:
        pass
    for q in load_questions().get("questions", []):
        kp = q.get("knowledge_point")
        if kp:
            points.add(kp)
    for r in get_flow_resources():
        kp = r.get("knowledge_point")
        if kp:
            points.add(kp)
    clean = sorted(
        p for p in points
        if p and not re.fullmatch(r"\s*\d+(?:\.\d+)*\s*", str(p))
    )
    return jsonify({"success": True, "points": clean})

def parse_student_identity(student_id):
    match = re.match(r"^(\d+)(.*)$", student_id or "")
    if match:
        return match.group(1), match.group(2)
    return student_id or "", ""

@app.route("/teacher/student/add", methods=["POST"])
def teacher_add_student():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    
    data = request.get_json()
    student_num = data.get("student_num", "").strip()
    student_name = data.get("student_name", "").strip()
    
    if not student_num or not student_name:
        return jsonify({"success": False, "error": "????"})
    
    student_id = student_num + student_name
    
    if student_num in STUDENTS or any(v.get("full_id") == student_id for v in STUDENTS.values()):
        return jsonify({"success": False, "error": "?????????"})
    
    STUDENTS[student_num] = {"password": "123456", "name": student_name, "full_id": student_id}
    
    try:
        with driver.session() as neo4j_session:
            neo4j_session.run("""
            MERGE (s:Student {id: $sid, name: $name, num: $num})
            """, sid=student_id, name=student_name, num=student_num)
        
        return jsonify({"success": True, "message": "?????????", "student_id": student_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/teacher/student/edit", methods=["POST"])
def teacher_edit_student():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    
    data = request.get_json()
    student_id = data.get("student_id", "").strip()
    student_num = data.get("student_num", "").strip()
    student_name = data.get("student_name", "").strip()
    
    if not student_id or not student_num or not student_name:
        return jsonify({"success": False, "error": "????"})
    
    old_num, old_name = parse_student_identity(student_id)
    old_full_id = student_id
    new_full_id = student_num + student_name
    old_record = STUDENTS.pop(old_num, {"password": "123456"})
    STUDENTS[student_num] = {"password": old_record.get("password", "123456"), "name": student_name, "full_id": new_full_id}
    
    try:
        with driver.session() as neo4j_session:
            neo4j_session.run("""
            MATCH (s:Student {id: $old_id})
            SET s.id = $new_id, s.name = $name, s.num = $num
            """, old_id=old_full_id, new_id=new_full_id, name=student_name, num=student_num)
        
        return jsonify({"success": True, "message": "????????????"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/teacher/student/delete", methods=["POST"])
def teacher_delete_student():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    
    data = request.get_json()
    student_id = data.get("student_id", "").strip()
    
    if not student_id:
        return jsonify({"success": False, "error": "???ID??????"})
    
    student_num, student_name = parse_student_identity(student_id)
    if student_num in STUDENTS:
        student_name = STUDENTS[student_num].get("name", student_name)
        del STUDENTS[student_num]
    
    try:
        with driver.session() as neo4j_session:
            row = neo4j_session.run("""
            MATCH (s:Student {id: $sid})
            WITH s, count(s) AS found
            DETACH DELETE s
            RETURN found AS deleted
            """, sid=student_id).single()
        
        if row and row["deleted"]:
            return jsonify({"success": True, "message": "?????????"})
        return jsonify({"success": False, "error": "????"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/teacher/question/add", methods=["POST"])
def teacher_add_question():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    
    data = request.get_json()
    question_text = data.get("question", "").strip()
    options = data.get("options", [])
    answer = data.get("answer", "").strip()
    knowledge_point = data.get("knowledge_point", "").strip()
    difficulty = data.get("difficulty", "medium").strip()
    explanation = data.get("explanation", "").strip()
    
    if not question_text or not answer or not knowledge_point:
        return jsonify({"success": False, "error": "????"})
    
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"
    
    questions_file = os.path.join(RESOURCE_DIR, "questions.json")
    questions_data = {"questions": []}
    
    if os.path.exists(questions_file):
        with open(questions_file, "r", encoding="utf-8") as f:
            questions_data = json.load(f)
    
    new_id = next_question_id(questions_data.get("questions", []), knowledge_point)
    
    new_question = {
        "id": new_id,
        "question": question_text,
        "options": options,
        "answer": answer,
        "knowledge_point": knowledge_point,
        "difficulty": difficulty
    }
    
    if explanation:
        new_question["explanation"] = explanation
    
    questions_data["questions"].append(new_question)
    
    with open(questions_file, "w", encoding="utf-8") as f:
        json.dump(questions_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "message": "?????????", "question_id": new_id})

@app.route("/teacher/question/delete", methods=["POST"])
def teacher_delete_question():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    
    data = request.get_json()
    question_id = data.get("question_id")
    
    if not question_id:
        return jsonify({"success": False, "error": "???ID??????"})
    
    questions_file = os.path.join(RESOURCE_DIR, "questions.json")
    
    if not os.path.exists(questions_file):
        return jsonify({"success": False, "error": "????"})
    
    with open(questions_file, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    
    original_count = len(questions_data.get("questions", []))
    questions_data["questions"] = [q for q in questions_data["questions"] if str(q.get("id")) != str(question_id)]
    
    if len(questions_data["questions"]) == original_count:
        return jsonify({"success": False, "error": "????"})
    
    with open(questions_file, "w", encoding="utf-8") as f:
        json.dump(questions_data, f, ensure_ascii=False, indent=2)
    
    return jsonify({"success": True, "message": "?????????"})

@app.route("/teacher/question/update", methods=["POST"])
def teacher_update_question():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    question_id = data.get("question_id")
    if question_id is None or str(question_id).strip() == "":
        return jsonify({"success": False, "error": "???ID??????"})
    question_text = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()
    knowledge_point = (data.get("knowledge_point") or "").strip()
    difficulty = (data.get("difficulty") or "medium").strip()
    options = data.get("options") or []
    explanation = (data.get("explanation") or "").strip()
    if not question_text or not answer or not knowledge_point:
        return jsonify({"success": False, "error": "????"})
    if difficulty not in ["easy", "medium", "hard"]:
        difficulty = "medium"
    questions_file = os.path.join(RESOURCE_DIR, "questions.json")
    if not os.path.exists(questions_file):
        return jsonify({"success": False, "error": "????"})
    with open(questions_file, "r", encoding="utf-8") as f:
        questions_data = json.load(f)
    found = False
    for q in questions_data.get("questions", []):
        if str(q.get("id")) == str(question_id):
            q["question"] = question_text
            q["options"] = options
            q["answer"] = answer
            q["knowledge_point"] = knowledge_point
            q["difficulty"] = difficulty
            if explanation:
                q["explanation"] = explanation
            elif "explanation" in q:
                q.pop("explanation", None)
            found = True
            break
    if not found:
        return jsonify({"success": False, "error": "????"})
    with open(questions_file, "w", encoding="utf-8") as f:
        json.dump(questions_data, f, ensure_ascii=False, indent=2)
    return jsonify({"success": True, "message": "?????????"})

@app.route("/video/<path:filename>")
def play_video(filename):
    if session.get("role") == "student":
        try:
            record_video_activity(session.get("full_id"), filename)
        except Exception as e:
            print("[video play record] {}".format(str(e)))
    return send_from_directory(RESOURCE_DIR, filename)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/student/video/play", methods=["POST"])
def record_video_play():
    """????????????"""
    from flask import request
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    data = request.get_json()
    video_name = data.get("video_name", "")
    
    if not video_name:
        return jsonify({"success": False, "error": "????????????"})
    
    try:
        record_video_activity(full_id, video_name)
        
        return jsonify({"success": True, "message": "???????"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/student/resource/download", methods=["POST"])
def record_resource_download():
    """????????????"""
    from flask import request
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    data = request.get_json()
    resource_name = data.get("resource_name", "")
    
    if not resource_name:
        return jsonify({"success": False, "error": "????????????"})
    
    try:
        record_resource_activity(full_id, resource_name, "download")
        
        return jsonify({"success": True, "message": "???????"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route("/student/resource/history")
def get_resource_history():
    """?????????/????"""
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    
    full_id = session.get("full_id")
    
    try:
        with driver.session() as neo4j_session:
            result = neo4j_session.run("""
            MATCH (s:Student {id: $sid})-[r:VIEWED]->(res:Resource)
            RETURN res.name as resource_name,
                   r.view_count as view_count,
                   r.download_count as download_count,
                   r.downloaded as downloaded,
                   r.last_viewed as last_time
            ORDER BY last_time DESC
            """, sid=full_id)
            
            history = []
            for record in result:
                history.append({
                    "resource_name": record["resource_name"],
                    "view_count": record["view_count"],
                    "download_count": record["download_count"],
                    "downloaded": record["downloaded"],
                    "last_time": str(record["last_time"]) if record["last_time"] else None
                })
            
            return jsonify({"success": True, "history": history})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/api/knowledge_graph")
def api_knowledge_graph():
    student_id = request.args.get("student_id", "")
    with driver.session() as sess:
        nodes = []
        edges = []
        node_ids = set()

        kp_list = list(sess.run("""
            MATCH (kp:Knowledge)
            WHERE kp.name =~ '^\\\\d+\\\\.\\\\d+.*'
            OPTIONAL MATCH (stu:Student {id: $sid})-[r:MASTERED]->(kp)
            RETURN kp.name AS name, r.mastery AS mastery,
                   r.total_questions AS total, r.correct_questions AS correct
        """, sid=student_id))
        kp_map = {r["name"]: {"mastery": r["mastery"] or 0, "total": r["total"] or 0, "correct": r["correct"] or 0} for r in kp_list}

        struct = list(sess.run("""
            MATCH (ch:Chapter)-[:???]->(sec:Knowledge)
            OPTIONAL MATCH (sec)-[:???]->(sub:Knowledge)
            WHERE sub.name =~ '^\\\\d+\\\\.\\\\d+.*'
            RETURN ch.name AS chapter, ch.number AS cn,
                   sec.name AS section, sec.number AS sn,
                   COLLECT(DISTINCT sub.name) AS subs
        """))
        struct.sort(key=lambda x: (x["cn"] or 0, x["sn"] or 0))

        ch_kps = {}
        sec_kps = {}
        mastery = {}
        # ??????????????????
        node_stats = {}

        for r in struct:
            ch, sec, subs = r["chapter"], r["section"], r["subs"] or []
            if sec not in sec_kps:
                sec_kps[sec] = []
            for s in subs:
                if s in kp_map:
                    sec_kps[sec].append(s)
                    if ch not in ch_kps:
                        ch_kps[ch] = []
                    ch_kps[ch].append(s)

        for k, v in kp_map.items():
            mastery[k] = v["mastery"]
            node_stats[k] = {"mastery": v["mastery"], "total_questions": v["total"], "correct_questions": v["correct"]}
        
        # ?????????????
        for sec, kps in sec_kps.items():
            if kps:
                avg_mastery = sum(node_stats[k]["mastery"] for k in kps) / len(kps)
                total_q = sum(node_stats[k]["total_questions"] for k in kps)
                total_c = sum(node_stats[k]["correct_questions"] for k in kps)
                mastery[sec] = round(avg_mastery, 3)
                node_stats[sec] = {
                    "mastery": round(avg_mastery, 3),
                    "total_questions": total_q,
                    "correct_questions": total_c,
                    "child_count": len(kps)
                }
            else:
                mastery[sec] = 0
                node_stats[sec] = {"mastery": 0, "total_questions": 0, "correct_questions": 0, "child_count": 0}
        
        # ?????????????
        for ch, kps in ch_kps.items():
            if kps:
                avg_mastery = sum(node_stats[k]["mastery"] for k in kps) / len(kps)
                total_q = sum(node_stats[k]["total_questions"] for k in kps)
                total_c = sum(node_stats[k]["correct_questions"] for k in kps)
                mastery[ch] = round(avg_mastery, 3)
                node_stats[ch] = {
                    "mastery": round(avg_mastery, 3),
                    "total_questions": total_q,
                    "correct_questions": total_c,
                    "child_count": len(kps)
                }
            else:
                mastery[ch] = 0
                node_stats[ch] = {"mastery": 0, "total_questions": 0, "correct_questions": 0, "child_count": 0}

        course = sess.run("MATCH (c:Course {name: '??????'}) RETURN c.name AS n").single()
        if course:
            cn = course["n"]
            all_m = [mastery[k] for k in kp_map]
            # ???????????????
            all_total_q = sum(kp_map[k]["total"] for k in kp_map)
            all_total_c = sum(kp_map[k]["correct"] for k in kp_map)
            mastery[cn] = round(sum(all_m) / len(all_m), 3) if all_m else 0
            root_accuracy = round(all_total_c / all_total_q * 100, 1) if all_total_q > 0 else 0
            node_stats[cn] = {
                "mastery": mastery[cn],
                "total_questions": all_total_q,
                "correct_questions": all_total_c,
                "accuracy": root_accuracy,
                "child_count": len(ch_kps)
            }
            nodes.append({
                "id": cn, "label": cn, "level": -1, 
                "mastery": mastery[cn], "group": "root",
                "total_questions": all_total_q,
                "correct_questions": all_total_c,
                "accuracy": root_accuracy,
                "child_count": len(ch_kps)
            })
            node_ids.add(cn)

        for ch in ch_kps:
            if ch not in node_ids:
                stats = node_stats.get(ch, {})
                nodes.append({
                    "id": ch, "label": ch, "level": 0, 
                    "mastery": mastery.get(ch, 0), "group": "chapter",
                    "total_questions": stats.get("total_questions", 0),
                    "correct_questions": stats.get("correct_questions", 0),
                    "child_count": stats.get("child_count", 0)
                })
                node_ids.add(ch)

        for sec in sec_kps:
            if sec not in node_ids:
                stats = node_stats.get(sec, {})
                nodes.append({
                    "id": sec, "label": sec, "level": 1, 
                    "mastery": mastery.get(sec, 0), "group": "section",
                    "total_questions": stats.get("total_questions", 0),
                    "correct_questions": stats.get("correct_questions", 0),
                    "child_count": stats.get("child_count", 0)
                })
                node_ids.add(sec)

        for kp, info in kp_map.items():
            if kp not in node_ids:
                nodes.append({
                    "id": kp, "label": kp, "level": 2, 
                    "mastery": info["mastery"], "group": "subsection",
                    "total_questions": info["total"],
                    "correct_questions": info["correct"]
                })
                node_ids.add(kp)

        if course:
            cn = course["n"]
            for ch in ch_kps:
                if ch in node_ids:
                    edges.append({"from": cn, "to": ch, "type": "???"})

        for r in struct:
            ch, sec, subs = r["chapter"], r["section"], r["subs"] or []
            if ch in node_ids and sec in node_ids:
                edges.append({"from": ch, "to": sec, "type": "???"})
            for s in subs:
                if s in node_ids and sec in node_ids:
                    edges.append({"from": sec, "to": s, "type": "???"})

        connected = set()
        for e in edges:
            connected.add(e["from"]); connected.add(e["to"])
        for kp in kp_map:
            if kp not in connected:
                parts = kp.split(".")
                if len(parts) >= 2:
                    for sec in sec_kps:
                        if kp.startswith(".".join(parts[:2]) + ".") and sec in node_ids:
                            edges.append({"from": sec, "to": kp, "type": "???"})
                            break

        for r in sess.run("MATCH (a)-[r:???]->(b) RETURN a.name AS f, b.name AS t"):
            if r["f"] in node_ids and r["t"] in node_ids:
                edges.append({"from": r["f"], "to": r["t"], "type": "???"})

        for r in sess.run("MATCH (a)-[r:???]->(b) RETURN a.name AS f, b.name AS t"):
            if r["f"] in node_ids and r["t"] in node_ids:
                edges.append({"from": r["f"], "to": r["t"], "type": "???"})

        return jsonify({"nodes": nodes, "edges": edges, "statistics": node_stats})


@app.route("/api/node_detail")
def api_node_detail():
    node_id = request.args.get("node_id", "")
    student_id = request.args.get("student_id", "")

    with driver.session() as sess:
        node_info = sess.run("""
            MATCH (n:Knowledge {name: $nid})
            OPTIONAL MATCH (n)-[:???]->(child:Knowledge)
            WITH n, COLLECT(DISTINCT child.name) AS children
            OPTIONAL MATCH (parent:Knowledge)-[:???]->(n)
            WITH n, children, COLLECT(DISTINCT parent.name) AS parents
            OPTIONAL MATCH (n)-[r:???]->(related:Knowledge)
            WITH n, children, parents,
                 COLLECT(DISTINCT {name: related.name, type: '???'}) AS related_nodes
            OPTIONAL MATCH (n)-[r2:???]->(prereq:Knowledge)
            WITH n, children, parents, related_nodes,
                 COLLECT(DISTINCT {name: prereq.name, type: '???'}) AS prereq_nodes
            OPTIONAL MATCH (stu:Student {id: $sid})-[m:MASTERED]->(n)
            RETURN n.name AS name, n.label AS label,
                   children, parents,
                   related_nodes, prereq_nodes,
                   m.mastery AS mastery,
                   m.total_questions AS total_questions,
                   m.correct_questions AS correct_questions
        """, nid=node_id, sid=student_id).single()

        if not node_info:
            return jsonify({"error": "Node not found"}), 404

        mastery = node_info["mastery"] or 0
        total_q = node_info["total_questions"] or 0
        correct_q = node_info["correct_questions"] or 0
        
        quiz_stats = sess.run("""
            MATCH (s:Student {id: $sid})
            OPTIONAL MATCH (s)-[qa:QUIZZED_ON]->(k:Knowledge {name: $nid})
            RETURN qa.correct AS correct, qa.total AS total
        """, sid=student_id, nid=node_id).single()

        correct = quiz_stats["correct"] or 0
        total = quiz_stats["total"] or 0
        accuracy = round(correct / total * 100, 1) if total > 0 else 0

        # ?????????????????????????????????????
        aggregated_stats = None
        children_list = node_info["children"] or []
        
        if len(children_list) > 0:
            agg_result = sess.run("""
                MATCH (parent:Knowledge {name: $nid})-[:???]->(child:Knowledge)
                OPTIONAL MATCH (stu:Student {id: $sid})-[r:MASTERED]->(child)
                WITH child, r
                RETURN COUNT(child) AS child_count,
                       AVG(r.mastery) AS avg_mastery,
                       SUM(r.total_questions) AS total_practiced,
                       SUM(r.correct_questions) AS total_correct
            """, nid=node_id, sid=student_id).single()
            
            if agg_result:
                child_count = agg_result["child_count"] or 0
                avg_mastery = agg_result["avg_mastery"] or 0
                total_practiced = agg_result["total_practiced"] or 0
                total_correct = agg_result["total_correct"] or 0
                
                aggregated_stats = {
                    "child_count": int(child_count),
                    "average_mastery": round(avg_mastery, 3),
                    "total_practiced_questions": int(total_practiced),
                    "total_correct_questions": int(total_correct),
                    "accuracy": round(total_correct / total_practiced * 100, 1) if total_practiced > 0 else 0,
                    "is_aggregated": True
                }

        result = {
            "name": node_info["name"],
            "label": node_info["label"] or node_info["name"],
            "mastery": mastery,
            "accuracy": accuracy,
            "quiz_count": total,
            "correct_count": correct,
            "total_questions": total_q,
            "correct_questions": correct_q,
            "children": children_list,
            "parents": node_info["parents"] or [],
            "related": [r for r in (node_info["related_nodes"] or []) if r["name"]],
            "prerequisites": [p for p in (node_info["prereq_nodes"] or []) if p["name"]],
            "aggregated_stats": aggregated_stats
        }

        return jsonify(result)


@app.route("/student/discuss/list")
def student_discuss_list_v2():
    if session.get("role") not in ("student", "teacher"):
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        rows = neo4j_session.run("""
        MATCH (p:DiscussionPost)
        OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:DiscussionComment)
        WITH p, count(c) AS comment_count
        RETURN elementId(p) AS id, p.title AS title, p.body AS body, p.author AS author,
               p.created_at AS created_at, p.created_ts AS created_ts, comment_count,
               p.knowledge_tag AS knowledge_tag, coalesce(p.status, '???') AS status
        ORDER BY created_ts DESC
        LIMIT 30
        """)
        posts = [{
            "id": row["id"], "title": row["title"], "body": row["body"],
            "author": row["author"] or "??",
            "time": str(row["created_at"])[:16] if row["created_at"] else "",
            "comment_count": row["comment_count"] or 0,
            "knowledge_tag": row["knowledge_tag"] or "",
            "status": row["status"] or "???",
            "is_mine": (row["author"] or "") == session.get("user_name", "")
        } for row in rows]
    return jsonify({"success": True, "posts": posts})

@app.route("/student/discuss/detail/<path:post_id>")
def student_discuss_detail_v2(post_id):
    if session.get("role") not in ("student", "teacher"):
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        row = neo4j_session.run("""
        MATCH (p:DiscussionPost)
        WHERE elementId(p)=$pid
        OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:DiscussionComment)
        RETURN elementId(p) AS id, p.title AS title, p.body AS body, p.author AS author, p.created_at AS created_at,
               p.knowledge_tag AS knowledge_tag, coalesce(p.status, '???') AS status,
               collect({id:elementId(c), body:c.body, author:c.author, created_at:c.created_at, ts:c.created_ts, reply_to:c.reply_to}) AS comments
        """, pid=post_id).single()
        if not row:
            return jsonify({"success": False, "error": "????"})
        sorted_comments = sorted([c for c in row["comments"] if c["body"]], key=lambda x: x.get("ts") or 0)
        comments = [{"id": c["id"], "floor": i + 1, "body": c["body"], "author": c["author"] or "??", "reply_to": c.get("reply_to") or "", "is_mine": (c["author"] or "") == session.get("user_name", ""), "time": str(c["created_at"])[:16] if c["created_at"] else ""} for i, c in enumerate(sorted_comments)]
    return jsonify({"success": True, "post": {"id": row["id"], "title": row["title"], "body": row["body"], "author": row["author"] or "??", "time": str(row["created_at"])[:16] if row["created_at"] else "", "knowledge_tag": row["knowledge_tag"] or "", "status": row["status"] or "???", "is_mine": (row["author"] or "") == session.get("user_name", ""), "comments": comments}})

@app.route("/student/discuss/comment/<path:post_id>", methods=["POST"])
def student_discuss_comment_v2(post_id):
    if session.get("role") not in ("student", "teacher"):
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    body = (data.get("body") or "").strip()
    reply_to = (data.get("reply_to") or "").strip()
    if not body:
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        neo4j_session.run("""
        MATCH (p:DiscussionPost)
        WHERE elementId(p)=$pid
        CREATE (c:DiscussionComment {body:$body, author:$author, role:$role, reply_to:$reply_to, created_at:datetime(), created_ts:datetime().epochSeconds})
        CREATE (p)-[:HAS_COMMENT]->(c)
        """, pid=post_id, body=body, reply_to=reply_to, author=session.get("user_name", "???"), role=session.get("role", "student"))
    return jsonify({"success": True})

@app.route("/student/discuss/post/update/<path:post_id>", methods=["POST"])
def student_discuss_post_update(post_id):
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    tag = (data.get("knowledge_tag") or "").strip()
    if not title:
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        row = neo4j_session.run("""
        MATCH (p:DiscussionPost {author:$author})
        WHERE elementId(p)=$pid
        SET p.title=$title, p.body=$body, p.knowledge_tag=$tag, p.updated_at=datetime()
        RETURN elementId(p) AS id
        """, pid=post_id, author=session.get("user_name", ""), title=title, body=body, tag=tag).single()
    return jsonify({"success": bool(row)})

@app.route("/student/discuss/post/delete/<path:post_id>", methods=["POST"])
def student_discuss_post_delete(post_id):
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        row = neo4j_session.run("""
        MATCH (p:DiscussionPost {author:$author})
        WHERE elementId(p)=$pid
        OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:DiscussionComment)
        WITH p, collect(c) AS comments
        FOREACH (comment IN comments | DETACH DELETE comment)
        DETACH DELETE p
        RETURN true AS deleted
        """, pid=post_id, author=session.get("user_name", "")).single()
    return jsonify({"success": bool(row)})

@app.route("/student/discuss/status/<path:post_id>", methods=["POST"])
def student_discuss_status(post_id):
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    status = ((request.get_json() or {}).get("status") or "???").strip()
    if status not in ("???", "???"):
        return jsonify({"success": False, "error": "?????"})
    with driver.session() as neo4j_session:
        result = neo4j_session.run("""
        MATCH (p:DiscussionPost {author:$author})
        WHERE elementId(p)=$pid
        SET p.status=$status, p.updated_at=datetime()
        RETURN elementId(p) AS id
        """, pid=post_id, author=session.get("user_name", ""), status=status).single()
    return jsonify({"success": bool(result), "status": status})

def teacher_collect_dashboard_data():
    students = get_all_students()
    profiles = []
    total_mastery = 0
    total_accuracy = 0
    level_counts = {"???": 0, "???": 0, "???": 0, "???": 0, "???": 0}
    weak_counter = {}

    for s in students:
        sid = s["id"]
        try:
            profile = get_user_profile(sid)
        except Exception:
            flow = get_flow_mastery_data(sid)
            points = flow.get("points", [])
            avg = sum(p.get("score", 0) for p in points) / len(points) if points else 0
            profile = {
                "level": "???",
                "avg_mastery": avg,
                "accuracy": 0,
                "total_questions": 0,
                "total_correct": 0,
                "description": "????????????",
                "weak_key_points": [],
                "weak_general_points": [{"name": p["full_name"], "mastery": p["score"]} for p in points if p.get("score", 0) < 0.7][:8]
            }
        num, name = parse_student_identity(sid)
        name = s.get("name") or name
        weak_points = (profile.get("weak_key_points") or []) + (profile.get("weak_general_points") or [])
        for item in weak_points[:12]:
            key = item.get("name") or ""
            if key:
                weak_counter[key] = weak_counter.get(key, 0) + 1
        level = profile.get("level") or "???"
        if level not in level_counts:
            level_counts[level] = 0
        level_counts[level] += 1
        total_mastery += profile.get("avg_mastery", 0) or 0
        total_accuracy += profile.get("accuracy", 0) or 0
        profiles.append({
            "id": sid,
            "num": s.get("num") or num,
            "name": name,
            "level": level,
            "avg_mastery": round(profile.get("avg_mastery", 0) or 0, 3),
            "accuracy": round(profile.get("accuracy", 0) or 0, 3),
            "total_questions": profile.get("total_questions", 0) or 0,
            "total_correct": profile.get("total_correct", 0) or 0,
            "description": profile.get("description", ""),
            "weak_points": [{"name": w.get("name", ""), "mastery": round(w.get("mastery", 0) or 0, 3)} for w in weak_points[:6]]
        })

    resources = get_flow_resources()
    resource_types = {}
    for r in resources:
        resource_types[r["type"]] = resource_types.get(r["type"], 0) + 1
    questions = load_questions().get("questions", [])
    q_difficulty = {}
    for q in questions:
        d = q.get("difficulty", "medium")
        q_difficulty[d] = q_difficulty.get(d, 0) + 1
    posts = []
    try:
        with driver.session() as neo4j_session:
            rows = neo4j_session.run("""
            MATCH (p:DiscussionPost)
            OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:DiscussionComment)
            RETURN elementId(p) AS id, p.title AS title, p.author AS author,
                   p.created_at AS created_at, coalesce(p.status, '???') AS status,
                   p.knowledge_tag AS knowledge_tag, count(c) AS comment_count
            ORDER BY p.created_ts DESC
            LIMIT 8
            """)
            posts = [{
                "id": row["id"],
                "title": row["title"] or "",
                "author": row["author"] or "??",
                "time": str(row["created_at"])[:16] if row["created_at"] else "",
                "status": row["status"] or "???",
                "knowledge_tag": row["knowledge_tag"] or "",
                "comment_count": row["comment_count"] or 0
            } for row in rows]
    except Exception:
        posts = []

    total = len(profiles) or 1
    profiles.sort(key=lambda x: (x["avg_mastery"], x["num"]))
    weak_rank = [{"name": k, "count": v} for k, v in sorted(weak_counter.items(), key=lambda x: (-x[1], x[0]))[:10]]
    return {
        "students": profiles,
        "summary": {
            "student_count": len(profiles),
            "avg_mastery": round(total_mastery / total, 3),
            "avg_accuracy": round(total_accuracy / total, 3),
            "weak_student_count": sum(1 for p in profiles if p["avg_mastery"] < 0.7),
            "resource_count": len(resources),
            "question_count": len(questions),
            "post_count": len(posts)
        },
        "levels": level_counts,
        "weak_rank": weak_rank,
        "resources": {"types": resource_types, "recent": resources[:10]},
        "questions": {"difficulty": q_difficulty, "recent": questions[:8]},
        "posts": posts
    }

@app.route("/teacher/tools/data")
def teacher_tools_data():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    return jsonify({"success": True, **teacher_collect_dashboard_data()})

TEACHER_WORKSPACE_TITLES = {
    "overview": "工作台总览",
    "students": "学生管理",
    "resourceManage": "资源管理",
    "questionBank": "题库管理",
    "graph": "公共图谱",
}

@app.route("/teacher/tools")
def teacher_tools():
    tab = request.args.get("tab", "overview")
    if tab not in TEACHER_WORKSPACE_TITLES:
        tab = "overview"
    return render_teacher_workspace(tab, TEACHER_WORKSPACE_TITLES[tab])

def render_teacher_workspace(initial_tab="overview", page_title="????????"):
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    html = """
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ page_title }} - ????????/title>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#1f2937;font-family:"Microsoft YaHei",Arial,sans-serif}.layout{display:grid;grid-template-columns:226px 1fr;min-height:100vh}.side{background:#fff;border-right:1px solid #e5e7eb;padding:20px 0;position:sticky;top:0;height:100vh}.brand{padding:0 24px 22px;font-size:20px;font-weight:800}.brand small{display:block;color:#64748b;font-size:12px;margin-top:6px}.nav a{display:block;text-decoration:none;color:#4b5563;padding:13px 28px;border-left:3px solid transparent;font-size:16px}.nav a:hover,.nav a.active{background:#eef4ff;color:#2563eb;border-left-color:#60a5fa}.logout{position:absolute;bottom:20px;left:20px;right:20px}.logout a{display:block;text-align:center;background:#eef4ff;color:#2563eb;padding:10px;border-radius:6px;text-decoration:none;font-weight:700}.top{height:64px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 34px}.top h1{font-size:22px;margin:0}.content{padding:26px 34px;max-width:1440px}.tabs{display:none}.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.stat{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:18px}.stat b{display:block;font-size:30px;margin-top:8px}.muted{color:#64748b;font-size:13px;line-height:1.7}.btn{border:0;background:#2563eb;color:#fff;border-radius:6px;padding:8px 13px;text-decoration:none;cursor:pointer;display:inline-block}.btn.light{background:#eef4ff;color:#2563eb;border:1px solid #dbeafe}.btn.green{background:#16a34a}.btn.danger{background:#ef4444}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}select,input,textarea{border:1px solid #cbd5e1;border-radius:6px;background:#fff;padding:9px 11px}.search{min-width:280px}.table-wrap{max-height:calc(100vh - 230px);overflow:auto}.table{width:100%;border-collapse:collapse}.table th,.table td{padding:11px;border-bottom:1px solid #eef2f7;text-align:left;vertical-align:top}.table th{background:#f8fafc;color:#475569;font-weight:700;cursor:pointer;position:sticky;top:0;z-index:1}.sort-tri{display:inline-block;margin-left:6px;width:0;height:0;vertical-align:middle}.sort-tri.up{border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:8px solid #2563eb}.sort-tri.down{border-left:5px solid transparent;border-right:5px solid transparent;border-top:8px solid #2563eb}.tag{font-size:12px;border-radius:999px;background:#eef2ff;color:#3730a3;padding:4px 8px;display:inline-block;margin:0 4px 4px 0}.tag.ok{background:#dcfce7;color:#166534}.tag.warn{background:#fff7ed;color:#9a3412}.tag.bad{background:#fee2e2;color:#991b1b}.bar{height:8px;background:#e5e7eb;border-radius:99px;overflow:hidden;width:130px}.bar span{display:block;height:100%;background:#2563eb}.split{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:16px}.empty{padding:34px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px}.modal{display:none;position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:50;align-items:center;justify-content:center}.modal.open{display:flex}.dialog{background:#fff;border-radius:8px;width:420px;max-width:92vw;padding:22px}.dialog label{display:block;font-size:13px;color:#475569;margin:12px 0 5px}.dialog input,.dialog textarea{width:100%}@media(max-width:960px){.layout{grid-template-columns:1fr}.side{position:relative;height:auto}.logout{position:relative}.split{grid-template-columns:1fr}.content{padding:18px}}
</style></head><body>
<div class="layout"><aside class="side"><div class="brand">????????small>{{ teacher_name }}</small></div><nav class="nav">
<a class="{% if initial_tab == 'overview' %}active{% endif %}" href="/teacher/tools">????????</a><a class="{% if initial_tab == 'students' %}active{% endif %}" href="/teacher/manage">??????</a><a class="{% if initial_tab == 'profiles' %}active{% endif %}" href="/teacher/students">??????</a><a class="{% if initial_tab == 'resourceManage' %}active{% endif %}" href="/teacher/resource-manage">??????</a><a class="{% if initial_tab == 'questionBank' %}active{% endif %}" href="/teacher/question-bank">??????</a><a class="{% if initial_tab == 'graph' %}active{% endif %}" href="/teacher/graph-tools">??????</a><a href="/teacher/discuss">??????</a>
</nav><div class="logout"><a href="/logout">???????/a></div></aside><main><header class="top"><h1 id="pageTitle">{{ page_title }}</h1><span class="muted">????????????</span></header><section class="content"><div id="app"><div class="empty">??????????????..</div></div></section></main></div>
<div class="modal" id="studentModal"><div class="dialog"><h3 id="studentModalTitle">??????</h3><input id="editStudentId" type="hidden"><label>???</label><input id="studentNum"><label>???</label><input id="studentName"><div style="margin-top:16px;text-align:right"><button class="btn light" onclick="closeStudentModal()">???</button> <button class="btn green" onclick="saveStudent()">???</button></div></div></div>
<script>
let DATA={students:[],summary:{},levels:{},weak_rank:[],resources:{types:{},recent:[]},questions:{difficulty:{},recent:[]},posts:[]}, TAB="{{ initial_tab }}";
const app=document.getElementById('app');const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));const pct=v=>Math.round((Number(v)||0)*100)+'%';const levelClass=l=>l==='???'||l==='???'?'ok':(l==='???'?'warn':'bad');const kpName=s=>String(s??'').replace(/^\\s*\\d+(?:\\.\\d+)+\\s*/,'')||String(s??'');let SORT={students:['num',1],resources:['name',1],questions:['id',1]},KPS=[];
const diffText=d=>({easy:'????,medium:'???',hard:'???'}[d]||d||'???');
function sorted(list,type,key){let cur=SORT[type]||[key,1],dir=cur[0]===key?-cur[1]:1;SORT[type]=[key,dir];return [...list].sort((a,b)=>{let x=a[key]??'',y=b[key]??'';if(typeof x==='number'||typeof y==='number')return ((Number(x)||0)-(Number(y)||0))*dir;return String(x).localeCompare(String(y),'zh-Hans',{numeric:true})*dir})}
function sortBy(type,key){if(type==='students'&&document.getElementById('studentTable'))renderStudents(sorted(DATA.students||[],type,key));if(type==='resources')renderResourceTable(window.RESOURCE_LIST=sorted(window.RESOURCE_LIST||[],type,key));if(type==='questions')renderQuestionTable(window.QUESTION_LIST=sorted(window.QUESTION_LIST||[],type,key))}
function th(type,key,label){let cur=SORT[type]||[],mark=cur[0]===key?`<span class="sort-tri ${cur[1]===1?'up':'down'}"></span>`:'';return `<th onclick="sortBy('${type}','${key}')" title="??????">${label}${mark}</th>`}
async function loadData(){let r=await fetch('/teacher/tools/data');DATA=await r.json();try{KPS=(await fetch('/teacher/knowledge-points/data').then(r=>r.json())).points||[]}catch(e){KPS=[]}render()}
function render(){({overview,students,resourceManage,questionBank,graph}[TAB]||overview)()}
function overview(){let s=DATA.summary||{}, weak=(DATA.weak_rank||[]).slice(0,6),lv=DATA.levels||{},rt=(DATA.resources||{}).types||{},qd=(DATA.questions||{}).difficulty||{};let statList=(o,map=x=>x)=>Object.keys(o).map(k=>`<div style="display:flex;justify-content:space-between;border-top:1px solid #eef2f7;padding:9px 0"><span>${esc(map(k))}</span><b>${o[k]}</b></div>`).join('')||'<div class="empty">??????</div>';app.innerHTML=`<div class="grid"><div class="stat">??????<b>${s.student_count||0}</b><span class="muted">??????</span></div><div class="stat">????????b>${pct(s.avg_mastery)}</b><span class="muted">???????????/span></div><div class="stat">??????<b>${s.weak_student_count||0}</b><span class="muted">????????0%</span></div><div class="stat">??? / ???<b>${s.resource_count||0} / ${s.question_count||0}</b><span class="muted">?????????</span></div></div><div class="split"><div class="card"><h2>?????????</h2>${studentRows((DATA.students||[]).slice(0,6),false)}</div><div class="card"><h2>???????????</h2>${weak.map(x=>`<div style="display:flex;justify-content:space-between;border-top:1px solid #eef2f7;padding:11px 0"><span>${esc(kpName(x.name))}</span><b>${x.count}??/b></div>`).join('')||'<div class="empty">?????????</div>'}</div></div><div class="grid"><div class="card"><h2>??????</h2>${statList(lv)}</div><div class="card"><h2>??????</h2>${statList(rt)}</div><div class="card"><h2>??????</h2>${statList(qd,diffText)}</div></div>`}
function studentRows(list,withActions=true){let heads=withActions?`${th('students','num','学号')}${th('students','name','姓名')}${th('students','level','等级')}${th('students','avg_mastery','掌握度')}${th('students','accuracy','正确率')}`:'<th>学号</th><th>姓名</th><th>等级</th><th>掌握度</th><th>正确率</th>';return `<table class="table"><thead><tr>${heads}<th>薄弱点</th>${withActions?'<th>操作</th>':''}</tr></thead><tbody>${list.map(st=>`<tr><td>${esc(st.num)}</td><td><b>${esc(st.name)}</b></td><td><span class="tag ${levelClass(st.level)}">${esc(st.level)}</span></td><td>${pct(st.avg_mastery)}<div class="bar"><span style="width:${pct(st.avg_mastery)}"></span></div></td><td>${pct(st.accuracy)}</td><td>${(st.weak_points||[]).slice(0,3).map(w=>`<span class="tag bad">${esc(kpName(w.name))} ${pct(w.mastery)}</span>`).join('')||'<span class="muted">暂无</span>'}</td>${withActions?`<td><button class="btn light" onclick="openEditStudent('${esc(st.id)}','${esc(st.num)}','${esc(st.name)}')">编辑</button> <button class="btn danger" onclick="deleteStudent('${esc(st.id)}')">删除</button></td>`:''}</tr>`).join('')}</tbody></table>`}
function students(){app.innerHTML=`<div class="card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2>?????????</h2><button class="btn green" onclick="openAddStudent()">??????</button></div><div class="toolbar"><input class="search" id="stuSearch" oninput="filterStudents()" placeholder="????????????????></div><div id="studentTable"></div></div>`;renderStudents(DATA.students||[])}
function renderStudents(list){studentTable.innerHTML=studentRows(list)}
function filterStudents(){let q=stuSearch.value.trim().toLowerCase();let list=(DATA.students||[]).filter(s=>!q||String(s.num+s.name+s.level).toLowerCase().includes(q));studentTable.innerHTML=studentRows(list)}
async function resourceManage(){app.innerHTML=`<div class="card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2>??????</h2><label class="btn green">??????<input type="file" style="display:none" onchange="uploadResource(this)"></label></div><div class="toolbar"><input id="resSearch" class="search" oninput="filterResources()" placeholder="???????????????????"><select id="resType" onchange="filterResources()"><option>??????</option></select></div><div id="resourceTable"><div class="empty">?????????...</div></div></div>`;let d=await fetch('/teacher/resources/data').then(r=>r.json());window.RESOURCE_ALL=d.resources||[];window.RESOURCE_LIST=[...window.RESOURCE_ALL];let types=[...new Set(window.RESOURCE_ALL.map(r=>r.type||'???'))];resType.innerHTML='<option>??????</option>'+types.map(t=>`<option>${esc(t)}</option>`).join('');renderResourceTable(window.RESOURCE_LIST)}
function renderResourceTable(list){let chapters={};(list||[]).forEach(r=>{let ch=r.chapter_label||'未分类',sec=r.section_label||'未分类';chapters[ch]=chapters[ch]||{};chapters[ch][sec]=chapters[ch][sec]||[];chapters[ch][sec].push(r)});let tableRows=arr=>`<div class="table-wrap" style="max-height:none"><table class="table"><thead><tr>${th('resources','name','文件名')}${th('resources','type','类型')}${th('resources','knowledge_point','知识点')}${th('resources','updated_at','更新时间')}${th('resources','size','大小')}<th>操作</th></tr></thead><tbody>${arr.map(r=>`<tr><td><b>${esc(r.name)}</b></td><td>${esc(r.type)}</td><td>${esc(kpName(r.knowledge_point)||'未绑定')}</td><td>${esc(r.updated_at)}</td><td>${Math.round((r.size||0)/1024)} KB</td><td><button class="btn light" onclick="renameResource('${esc(r.name)}')">编辑</button> <button class="btn danger" onclick="deleteResource('${esc(r.name)}')">删除</button></td></tr>`).join('')}</tbody></table></div>`;let html=Object.keys(chapters).sort((a,b)=>a.localeCompare(b,'zh-Hans',{numeric:true})).map((ch,ci)=>{let direct=chapters[ch]['整章']||[];let secs=Object.keys(chapters[ch]).filter(s=>s!=='整章').sort((a,b)=>a.localeCompare(b,'zh-Hans',{numeric:true}));return `<details class="card" ${ci===0?'open':''} style="padding:0;overflow:hidden"><summary style="padding:14px 16px;background:#f8fafc;cursor:pointer;font-weight:800">${esc(ch)} · ${Object.values(chapters[ch]).reduce((n,arr)=>n+arr.length,0)} 个资源</summary>${direct.length?tableRows(direct):''}${secs.map(sec=>`<details open style="border-top:1px solid #eef2f7"><summary style="padding:12px 18px;background:#fff;cursor:pointer;font-weight:700;color:#475569">${esc(sec)} · ${chapters[ch][sec].length}</summary>${tableRows(chapters[ch][sec])}</details>`).join('')}</details>`}).join('');resourceTable.innerHTML=html||'<div class="empty">暂无资源</div>'}
function normSearch(s){return String(s??'').toLowerCase().replace(/\s+/g,'')}
function filterResources(){let q=normSearch(document.getElementById('resSearch')?.value||''),t=document.getElementById('resType')?.value||'??????';window.RESOURCE_LIST=(window.RESOURCE_ALL||[]).filter(r=>{let hay=normSearch([r.name,r.title,r.type,r.knowledge_point,kpName(r.knowledge_point),r.chapter_label,r.section_label].join(' '));return (t==='??????'||r.type===t)&&(!q||hay.includes(q))});renderResourceTable(window.RESOURCE_LIST)}
async function uploadResource(input){if(!input.files||!input.files[0])return;let fd=new FormData();fd.append('file',input.files[0]);let d=await fetch('/teacher/upload',{method:'POST',body:fd}).then(r=>r.json());alert(d.success?'????????+d.filename:(d.error||'??????'));if(d.success)resourceManage()}
async function renameResource(name){let next=prompt('???????????,name);if(!next||next===name)return;let d=await fetch('/teacher/resource/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_name:name,new_name:next})}).then(r=>r.json());alert(d.success?'??????':(d.error||'??????'));if(d.success)resourceManage()}
async function deleteResource(name){if(!confirm('????????? '+name+' ???'))return;let d=await fetch('/teacher/resource/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:name})}).then(r=>r.json());alert(d.success?'??????':(d.error||'??????'));if(d.success)resourceManage()}
async function questionBank(){app.innerHTML=`<div class="card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2>??????</h2><button class="btn green" onclick="openQuestionEditor()">??????</button></div><div class="toolbar"><input id="qSearch" class="search" oninput="filterQuestions()" placeholder="??????????????D"><select id="qDiff" onchange="filterQuestions()"><option value="">??????</option><option value="easy">????/option><option value="medium">???</option><option value="hard">???</option></select></div><div id="questionTable"><div class="empty">?????????...</div></div></div><div class="modal" id="questionModal"><div class="dialog" style="width:720px"><h3 id="qTitle">??????</h3><label>??????</label><textarea id="qText" rows="4"></textarea><label>?????/label><input id="qKp" list="kpOptions" oninput="filterKpOptions(this.value)" placeholder="?????????????????><datalist id="kpOptions">${KPS.map(k=>`<option value="${esc(k)}"></option>`).join('')}</datalist><label>???</label><select id="qDifficulty"><option value="easy">????/option><option value="medium">???</option><option value="hard">???</option></select><label>????????/label><div id="optionEditor">${['A','B','C','D'].map(l=>`<div style="display:grid;grid-template-columns:54px 1fr 70px;gap:8px;align-items:center;margin:8px 0"><label><input type="checkbox" id="use${l}"> ${l}</label><input id="opt${l}" placeholder="${l} ??????"><label><input type="checkbox" id="ans${l}"> ???</label></div>`).join('')}</div><label>???</label><textarea id="qExplain" rows="3"></textarea><input id="qId" type="hidden"><div style="margin-top:16px;text-align:right"><button class="btn light" onclick="questionModal.classList.remove('open')">???</button> <button class="btn green" onclick="saveQuestion()">???</button></div></div></div>`;let d=await fetch('/teacher/questions/data').then(r=>r.json());window.QUESTION_ALL=d.questions||[];window.QUESTION_LIST=[...window.QUESTION_ALL];renderQuestionTable(window.QUESTION_LIST)}
function renderQuestionTable(list){questionTable.innerHTML=`<div class="table-wrap"><table class="table"><thead><tr>${th('questions','id','ID')}${th('questions','knowledge_point','知识点')}${th('questions','difficulty','难度')}${th('questions','question','题目')}${th('questions','answer','答案')}<th>操作</th></tr></thead><tbody>${list.map(q=>`<tr><td>${esc(q.id)}</td><td>${esc(kpName(q.knowledge_point))}</td><td>${esc(diffText(q.difficulty))}</td><td>${esc(q.question)}</td><td>${esc(q.answer)}</td><td><button class="btn light" onclick="openQuestionEditor('${esc(q.id)}')">编辑</button> <button class="btn danger" onclick="deleteQuestion('${esc(q.id)}')">删除</button></td></tr>`).join('')}</tbody></table></div>`}
function filterKpOptions(v){let q=String(v||'').toLowerCase();let opts=(KPS||[]).filter(k=>!q||String(k).toLowerCase().includes(q)||kpName(k).toLowerCase().includes(q)).slice(0,80);let box=document.getElementById('kpOptions');if(box)box.innerHTML=opts.map(k=>`<option value="${esc(k)}"></option>`).join('')}
function filterQuestions(){let q=normSearch(qSearch.value||''),d=qDiff.value;window.QUESTION_LIST=(window.QUESTION_ALL||[]).filter(x=>(!d||x.difficulty===d)&&(!q||normSearch([x.id,x.question,x.knowledge_point,kpName(x.knowledge_point),x.answer,diffText(x.difficulty)].join(' ')).includes(q)));renderQuestionTable(window.QUESTION_LIST)}
function openQuestionEditor(id){let q=(window.QUESTION_ALL||[]).find(x=>String(x.id)===String(id));qTitle.textContent=q?'??????':'??????';qId.value=q?q.id:'';qText.value=q?q.question||'':'';qKp.value=q?q.knowledge_point||'':'';qDifficulty.value=q?q.difficulty||'medium':'medium';qExplain.value=q?q.explanation||'':'';['A','B','C','D'].forEach((l,i)=>{let opt=(q&&q.options&&q.options[i])?String(q.options[i]).replace(/^[A-D][\\.??\\s*/,''):'';document.getElementById('use'+l).checked=!!opt;document.getElementById('opt'+l).value=opt;document.getElementById('ans'+l).checked=q?String(q.answer||'').split(/[,????\s]+/).includes(l):false});questionModal.classList.add('open')}
async function saveQuestion(){let options=[],answers=[];['A','B','C','D'].forEach(l=>{let use=document.getElementById('use'+l).checked,txt=document.getElementById('opt'+l).value.trim();if(use&&txt)options.push(l+'. '+txt);if(document.getElementById('ans'+l).checked)answers.push(l)});if(!qText.value.trim()||!qKp.value.trim()||!answers.length){alert('???????????????????????????);return}let payload={question_id:qId.value,question:qText.value.trim(),knowledge_point:qKp.value.trim(),difficulty:qDifficulty.value,options,answer:answers.join(','),explanation:qExplain.value.trim()};let d=await fetch(qId.value?'/teacher/question/update':'/teacher/question/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());alert(d.success?'??????':(d.error||'??????'));if(d.success){questionModal.classList.remove('open');questionBank()}}
async function deleteQuestion(id){if(!confirm('??????????????))return;let d=await fetch('/teacher/question/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_id:id})}).then(r=>r.json());alert(d.success?'??????':(d.error||'??????'));if(d.success)questionBank()}
function graph(){let opts=(KPS||[]).map(k=>`<option value="${esc(k)}"></option>`).join('');app.innerHTML=`<div class="card"><h2>????????????</h2><p class="muted">???????????????????????????????????????????/p><div class="toolbar"><input id="fromK" list="graphKps" oninput="filterGraphKps(this.value)" placeholder="???????????><select id="relK"><option>???</option><option>???</option><option>???</option></select><input id="toK" list="graphKps" oninput="filterGraphKps(this.value)" placeholder="???????????><button class="btn" onclick="addKg()">??????</button></div><datalist id="graphKps">${opts}</datalist></div>`}
function filterGraphKps(v){let q=String(v||'').toLowerCase();let box=document.getElementById('graphKps');if(box)box.innerHTML=(KPS||[]).filter(k=>!q||String(k).toLowerCase().includes(q)||kpName(k).toLowerCase().includes(q)).slice(0,80).map(k=>`<option value="${esc(k)}"></option>`).join('')}
function openAddStudent(){editStudentId.value='';studentNum.value='';studentName.value='';studentModalTitle.textContent='??????';studentModal.classList.add('open')}
function openEditStudent(id,num,name){editStudentId.value=id;studentNum.value=num;studentName.value=name;studentModalTitle.textContent='??????';studentModal.classList.add('open')}
function closeStudentModal(){studentModal.classList.remove('open')}
async function saveStudent(){let url=editStudentId.value?'/teacher/student/edit':'/teacher/student/add';let body={student_id:editStudentId.value,student_num:studentNum.value.trim(),student_name:studentName.value.trim()};let d=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json());alert(d.success?'??????':(d.error||'??????'));if(d.success){closeStudentModal();await loadData()}}
async function deleteStudent(id){if(!confirm('??????????????????????????))return;let d=await fetch('/teacher/student/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_id:id})}).then(r=>r.json());alert(d.success?'??????':(d.error||'??????'));if(d.success)await loadData()}
async function sendMsg(){let d=await fetch('/teacher/message/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_id:msgSid.value,body:msgBody.value})}).then(r=>r.json());alert(d.success?'?????:(d.error||'???????))}
async function sendQuickMsg(id){let body=prompt('??????????????','????????????????????????????????);if(!body)return;let d=await fetch('/teacher/message/send',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_id:id,body})}).then(r=>r.json());alert(d.success?'?????:(d.error||'???????))}
async function addKg(){let d=await fetch('/teacher/public-graph/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:fromK.value,to:toK.value,rel:relK.value})}).then(r=>r.json());alert(d.success?'?????:(d.error||'??????'))}
loadData();
</script></body></html>
    """
    return render_template_string(html, teacher_name=session.get("user_name", "???"), initial_tab=initial_tab, page_title=page_title)

@app.route("/teacher/analytics")
def teacher_analytics():
    return redirect(url_for("teacher_tools"))

@app.route("/teacher/resources")
def teacher_resources():
    return redirect(url_for("teacher_resource_manage"))

@app.route("/teacher/reminders")
def teacher_reminders():
    return redirect(url_for("teacher_students"))

@app.route("/teacher/resource-manage")
def teacher_resource_manage():
    return render_teacher_workspace("resourceManage", "资源管理")

@app.route("/teacher/question-bank")
def teacher_question_bank():
    return render_teacher_workspace("questionBank", "题库管理")

@app.route("/teacher/graph-tools")
def teacher_graph_tools():
    return render_teacher_workspace("graph", "公共图谱")

TEACHER_DISCUSS_PAGE = """
<div class="card">
    <h3>??????</h3>
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px;">
        <select id="tagFilter" style="padding:8px;border:1px solid #ddd;"><option>???</option></select>
        <select id="statusFilter" style="padding:8px;border:1px solid #ddd;"><option>???</option><option>?????/option><option>?????/option></select>
        <button onclick="loadDiscuss()" style="padding:8px 14px;background:#3498db;color:#fff;border:0;border-radius:4px;">????/button>
        <button onclick="showCreatePost()" style="padding:8px 14px;background:#16a34a;color:#fff;border:0;border-radius:4px;">??????</button>
    </div>
    <div id="discussList"></div>
</div>
<div class="card" id="postDetail">
    <p style="color:#7f8c8d;">??????????????????????????????/p>
</div>
<script>
function esc(s){return String(s||'').replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
let currentPost = null;
async function loadDiscuss(){
    const data = await fetch('/student/discuss/list').then(r=>r.json());
    const posts = data.posts || [];
    const tags = Array.from(new Set(posts.map(p=>p.knowledge_tag).filter(Boolean)));
    const tagSel = document.getElementById('tagFilter');
    const oldTag = tagSel.value || '???';
    tagSel.innerHTML = '<option>???</option>' + tags.map(t=>'<option '+(t===oldTag?'selected':'')+'>'+esc(t)+'</option>').join('');
    const status = document.getElementById('statusFilter').value || '???';
    const tag = tagSel.value || '???';
    const list = posts.filter(p=>(tag==='???'||p.knowledge_tag===tag)&&(status==='???'||p.status===status));
    document.getElementById('discussList').innerHTML = list.map(p=>'<div onclick="openPost(\\''+p.id+'\\')" style="padding:14px 0;border-top:1px solid #eee;cursor:pointer;"><div style="display:flex;justify-content:space-between;gap:12px;"><b>'+esc(p.title)+'</b><span style="font-size:12px;color:'+(p.status==='??????'#27ae60':'#f39c12')+'">'+esc(p.status||'?????)+'</span></div><div style="font-size:12px;color:#7f8c8d;margin-top:4px;">'+esc(p.author)+' ? '+esc(p.time)+' ? '+esc(p.knowledge_tag||'?????)+' ? '+p.comment_count+'?????/div><p>'+esc(p.body||'')+'</p></div>').join('') || '<p style="color:#95a5a6;">??????</p>';
}
async function openPost(id){
    const data = await fetch('/student/discuss/detail/'+encodeURIComponent(id)).then(r=>r.json());
    const p = data.post;
    currentPost = p;
    document.getElementById('postDetail').innerHTML = '<h3>'+esc(p.title)+'</h3><p>'+esc(p.body)+'</p><div style="font-size:12px;color:#7f8c8d;">'+esc(p.author)+' ? '+esc(p.knowledge_tag||'?????)+' ? '+esc(p.status||'?????)+'</div><div style="margin:10px 0;"><button onclick="editCurrentPost()" style="padding:6px 12px;background:#2563eb;color:#fff;border:0;border-radius:4px;">??????</button> <button onclick="deleteCurrentPost()" style="padding:6px 12px;background:#ef4444;color:#fff;border:0;border-radius:4px;">??????</button></div><h4>???</h4>'+(p.comments||[]).map(c=>'<div style="border-top:1px solid #eee;padding:10px 0;"><b>'+esc(c.author)+'</b><p>'+esc(c.body)+'</p><span style="font-size:12px;color:#7f8c8d;">'+esc(c.time)+'</span> <button onclick="deleteComment(\\''+c.id+'\\',\\''+id+'\\')" style="padding:3px 8px;background:#ef4444;color:#fff;border:0;border-radius:3px;">???</button></div>').join('')+'<textarea id="commentBody" rows="3" style="width:100%;margin-top:10px;padding:8px;border:1px solid #ddd;" placeholder="??????"></textarea><button onclick="commentPost(\\''+id+'\\')" style="margin-top:8px;padding:8px 14px;background:#3498db;color:#fff;border:0;border-radius:4px;">??????</button>';
}
function showCreatePost(){currentPost=null;document.getElementById('postDetail').innerHTML='<h3>??????</h3><input id="editTitle" style="width:100%;margin-bottom:8px;padding:8px;border:1px solid #ddd;" placeholder="???"><input id="editTag" style="width:100%;margin-bottom:8px;padding:8px;border:1px solid #ddd;" placeholder="????????><textarea id="editBody" rows="5" style="width:100%;padding:8px;border:1px solid #ddd;" placeholder="??????"></textarea><button onclick="savePost()" style="margin-top:8px;padding:8px 14px;background:#16a34a;color:#fff;border:0;border-radius:4px;">???</button>'}
function editCurrentPost(){if(!currentPost)return;document.getElementById('postDetail').innerHTML='<h3>??????</h3><input id="editTitle" style="width:100%;margin-bottom:8px;padding:8px;border:1px solid #ddd;" value="'+esc(currentPost.title)+'"><input id="editTag" style="width:100%;margin-bottom:8px;padding:8px;border:1px solid #ddd;" value="'+esc(currentPost.knowledge_tag||'')+'"><select id="editStatus" style="width:100%;margin-bottom:8px;padding:8px;border:1px solid #ddd;"><option '+(currentPost.status==='??????'selected':'')+'>?????/option><option '+(currentPost.status==='??????'selected':'')+'>?????/option></select><textarea id="editBody" rows="5" style="width:100%;padding:8px;border:1px solid #ddd;">'+esc(currentPost.body||'')+'</textarea><button onclick="savePost()" style="margin-top:8px;padding:8px 14px;background:#16a34a;color:#fff;border:0;border-radius:4px;">???</button>'}
async function savePost(){let payload={title:editTitle.value,body:editBody.value,knowledge_tag:editTag.value,status:document.getElementById('editStatus')?editStatus.value:'?????};let url=currentPost?'/teacher/discuss/post/update/'+encodeURIComponent(currentPost.id):'/teacher/discuss/post';let data=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());if(!data.success){alert(data.error||'??????');return}await loadDiscuss();if(currentPost)openPost(currentPost.id);else document.getElementById('postDetail').innerHTML='<p style="color:#7f8c8d;">??????????/p>'}
async function deleteCurrentPost(){if(!currentPost||!confirm('?????????????????????'))return;let data=await fetch('/teacher/discuss/post/delete/'+encodeURIComponent(currentPost.id),{method:'POST'}).then(r=>r.json());if(!data.success){alert(data.error||'??????');return}currentPost=null;document.getElementById('postDetail').innerHTML='<p style="color:#7f8c8d;">???????/p>';loadDiscuss()}
async function deleteComment(id,postId){if(!confirm('???????????????'))return;await fetch('/teacher/discuss/comment/delete/'+encodeURIComponent(id),{method:'POST'});openPost(postId);loadDiscuss()}
async function commentPost(id){
    await fetch('/student/discuss/comment/'+encodeURIComponent(id), {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({body:document.getElementById('commentBody').value})});
    openPost(id);
    loadDiscuss();
}
loadDiscuss();
</script>
"""

@app.route("/teacher/discuss")
def teacher_discuss():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    template = TEACHER_BASE_HTML.replace("<!--PAGE_CONTENT-->", TEACHER_DISCUSS_PAGE)
    return render_template_string(template, teacher_name=session.get("user_name", "???"), page_title="??????", active_page="discuss")

@app.route("/teacher/discuss/post", methods=["POST"])
def teacher_discuss_post():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    tag = (data.get("knowledge_tag") or "").strip()
    if not title:
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        neo4j_session.run("""
        CREATE (p:DiscussionPost {title:$title, body:$body, author:$author, role:'teacher',
                                  knowledge_tag:$tag, status:'?????,
                                  created_at:datetime(), created_ts:datetime().epochSeconds})
        """, title=title, body=body, tag=tag, author=session.get("user_name", "???"))
    return jsonify({"success": True})

@app.route("/teacher/discuss/post/update/<path:post_id>", methods=["POST"])
def teacher_discuss_post_update(post_id):
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    data = request.get_json() or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    tag = (data.get("knowledge_tag") or "").strip()
    status = (data.get("status") or "???").strip()
    if status not in ("???", "???"):
        status = "???"
    if not title:
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        row = neo4j_session.run("""
        MATCH (p:DiscussionPost)
        WHERE elementId(p)=$pid
        SET p.title=$title, p.body=$body, p.knowledge_tag=$tag, p.status=$status, p.updated_at=datetime()
        RETURN elementId(p) AS id
        """, pid=post_id, title=title, body=body, tag=tag, status=status).single()
    return jsonify({"success": bool(row), "error": "" if row else "?????"})

@app.route("/teacher/discuss/post/delete/<path:post_id>", methods=["POST"])
def teacher_discuss_post_delete(post_id):
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        row = neo4j_session.run("""
        MATCH (p:DiscussionPost)
        WHERE elementId(p)=$pid
        OPTIONAL MATCH (p)-[:HAS_COMMENT]->(c:DiscussionComment)
        DETACH DELETE c, p
        RETURN 1 AS deleted
        """, pid=post_id).single()
    return jsonify({"success": bool(row), "error": "" if row else "?????"})

@app.route("/teacher/discuss/comment/delete/<path:comment_id>", methods=["POST"])
def teacher_discuss_comment_delete(comment_id):
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "????"})
    with driver.session() as neo4j_session:
        row = neo4j_session.run("""
        MATCH (c:DiscussionComment)
        WHERE elementId(c)=$cid
        DETACH DELETE c
        RETURN 1 AS deleted
        """, cid=comment_id).single()
    return jsonify({"success": bool(row), "error": "" if row else "?????"})

@app.route("/teacher")
def teacher_home_redirect():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    return redirect(url_for("teacher_tools"))

@app.route("/student/flow-graph/data")
def student_flow_graph_data():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    graph = get_knowledge_graph(session.get("full_id"))
    return jsonify({"success": True, **graph})

@app.route("/student/messages")
def student_messages():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    sid = session.get("full_id")
    items = []
    with driver.session() as neo4j_session:
        rows = neo4j_session.run("""
        MATCH (:Student {id:$sid})<-[:TO_STUDENT]-(m:TeacherMessage)
        RETURN m.body AS body, m.teacher AS author, m.created_at AS created_at, m.created_ts AS ts
        ORDER BY ts DESC
        LIMIT 20
        """, sid=sid)
        for row in rows:
            items.append({
                "type": "??????",
                "body": row["body"],
                "author": row["author"] or "???",
                "time": str(row["created_at"])[:16] if row["created_at"] else ""
            })
        rows = neo4j_session.run("""
        MATCH (p:DiscussionPost)-[:HAS_COMMENT]->(c:DiscussionComment)
        WHERE p.author = $author
        RETURN p.title AS title, c.body AS body, c.author AS author, c.created_at AS created_at, c.created_ts AS ts
        ORDER BY ts DESC
        LIMIT 20
        """, author=session.get("user_name", ""))
        for row in rows:
            items.append({
                "type": "??????",
                "body": "{}??}".format(row["title"], row["body"]),
                "author": row["author"] or "???",
                "time": str(row["created_at"])[:16] if row["created_at"] else ""
            })
    return jsonify({"success": True, "messages": items[:20]})

@app.route("/student/discuss/my-comments")
def student_my_comments():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    author = session.get("user_name", "")
    with driver.session() as neo4j_session:
        rows = neo4j_session.run("""
        MATCH (p:DiscussionPost)-[:HAS_COMMENT]->(c:DiscussionComment {author:$author})
        RETURN elementId(c) AS id, p.title AS title, c.body AS body, c.created_at AS created_at
        ORDER BY c.created_ts DESC
        LIMIT 30
        """, author=author)
        comments = [{"id": row["id"], "title": row["title"], "body": row["body"], "time": str(row["created_at"])[:16] if row["created_at"] else ""} for row in rows]
        post_rows = neo4j_session.run("""
        MATCH (p:DiscussionPost {author:$author})
        RETURN elementId(p) AS id, p.title AS title, p.body AS body, p.knowledge_tag AS knowledge_tag,
               coalesce(p.status, '???') AS status, p.created_at AS created_at
        ORDER BY p.created_ts DESC
        LIMIT 30
        """, author=author)
        posts = [{
            "id": row["id"],
            "title": row["title"],
            "body": row["body"],
            "knowledge_tag": row["knowledge_tag"] or "",
            "status": row["status"] or "???",
            "time": str(row["created_at"])[:16] if row["created_at"] else ""
        } for row in post_rows]
    return jsonify({"success": True, "posts": posts, "comments": comments})

@app.route("/student/discuss/comment/delete/<path:comment_id>", methods=["POST"])
def student_delete_comment(comment_id):
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "????"})
    author = session.get("user_name", "")
    with driver.session() as neo4j_session:
        result = neo4j_session.run("""
        MATCH (c:DiscussionComment {author:$author})
        WHERE elementId(c)=$cid
        WITH c
        DETACH DELETE c
        RETURN 1 AS deleted
        """, author=author, cid=comment_id).single()
    return jsonify({"success": True, "deleted": result["deleted"] if result else 0})

STUDENT_FLOW_HTML = """
<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ page_title }} - ???????????????</title>
<script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
<style>
*{box-sizing:border-box}body{margin:0;background:#f5f6f8;color:#1f2937;font-family:"Microsoft YaHei",Arial,sans-serif}.layout{display:grid;grid-template-columns:216px 1fr;min-height:100vh}.side{background:#fff;border-right:1px solid #e5e7eb;padding:20px 0;position:sticky;top:0;height:100vh}.brand{padding:0 24px 18px;font-size:20px;font-weight:800}.student{padding:0 24px 20px;color:#64748b}.nav a{display:block;text-decoration:none;color:#4b5563;padding:13px 28px;border-left:3px solid transparent}.nav a:hover,.nav a.active{background:#eef4ff;color:#2563eb;border-left-color:#60a5fa}.logout{position:absolute;bottom:20px;left:20px;right:20px}.logout a{display:block;text-align:center;background:#eef4ff;color:#2563eb;padding:10px;border-radius:6px;text-decoration:none;font-weight:700}.top{height:64px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 34px}.top h1{font-size:22px;margin:0}.content{padding:28px 36px;max-width:1280px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.stat{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:18px}.stat b{display:block;font-size:30px;margin-top:8px}.muted{color:#64748b;font-size:13px;line-height:1.7}.btn{border:0;background:#2563eb;color:#fff;border-radius:6px;padding:8px 13px;text-decoration:none;cursor:pointer;display:inline-block}.btn.light{background:#eef4ff;color:#2563eb;border:1px solid #dbeafe}.btn.green{background:#16a34a}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}select,input,textarea{border:1px solid #cbd5e1;border-radius:6px;background:#fff;padding:9px 11px}.search{min-width:280px}.progress{height:8px;background:#e5e7eb;border-radius:99px;overflow:hidden;min-width:160px}.bar{height:100%;background:#60a5fa}.bar.bad{background:#ef4444}.bar.warn{background:#f59e0b}.bar.ok{background:#22c55e}.tag{font-size:12px;border-radius:999px;background:#eef2ff;color:#3730a3;padding:4px 8px;margin-right:6px}.tag.video{background:#fff7ed;color:#9a3412}.tag.doc{background:#ecfdf5;color:#166534}.tag.bad{background:#fee2e2;color:#991b1b}.row{display:flex;align-items:center;justify-content:space-between;gap:14px;border-top:1px solid #eef2f7;padding:13px 0}.path-step{display:grid;grid-template-columns:34px 1fr;gap:12px;border-top:1px solid #eef2f7;padding:16px 0}.no{width:28px;height:28px;border-radius:50%;background:#f59e0b;color:#fff;display:grid;place-items:center;font-weight:800}.res-list{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin-top:10px}.res{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px}.res-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}.res-card{border:1px solid #e5e7eb;border-radius:8px;padding:14px;background:#fff}.tree{display:flex;gap:8px;flex-wrap:wrap}.tree button{border:1px solid #dbe3ef;background:#fff;border-radius:6px;padding:8px 10px;cursor:pointer}.tree button.active{background:#2563eb;color:#fff}.post{border-top:1px solid #eef2f7;padding:14px 0;cursor:pointer}.post:hover{background:#f8fafc}.comment{border-top:1px solid #eef2f7;padding:10px 0}.graph-simple{display:grid;grid-template-columns:1fr 130px 1fr 90px;gap:10px}.edge{border:1px solid #e5e7eb;border-radius:8px;padding:12px;background:#f8fafc}.empty{padding:36px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px}@media(max-width:900px){.layout{grid-template-columns:1fr}.side{height:auto;position:relative}.logout{position:relative}.graph-simple{grid-template-columns:1fr}.content{padding:18px}}
</style>
</head>
<body>
<div class="layout"><aside class="side"><div class="brand">???????????????</div><div class="student">{{ student_name }}</div><nav class="nav">
<a href="/student/dashboard" class="{% if active_page=='dashboard' %}active{% endif %}">???</a>
<a href="/student/path" class="{% if active_page=='path' %}active{% endif %}">?????????</a>
<a href="/student/resources" class="{% if active_page=='resources' %}active{% endif %}">????????/a>
<a href="/student/mastery" class="{% if active_page=='mastery' %}active{% endif %}">?????????</a>
<a href="/student/graph" class="{% if active_page=='graph' %}active{% endif %}">??????</a>
<a href="/student/discuss" class="{% if active_page=='discuss' %}active{% endif %}">??????</a>
<a href="/student/graph-builder" class="{% if active_page=='graph_builder' %}active{% endif %}">??????</a>
<a href="/student/records" class="{% if active_page=='records' %}active{% endif %}">??????</a>
</nav><div class="logout"><a href="/logout">???????/a></div></aside><main><header class="top"><h1>{{ page_title }}</h1><span class="muted">???????????/span></header><section class="content" id="app"></section></main></div>
<script>
const PAGE="{{active_page}}", app=document.getElementById("app"), TARGET=new URLSearchParams(location.search).get("target_kp")||"";
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const kpName=s=>String(s??"").replace(/^\s*\d+(?:\.\d+)+\s*/,'')||String(s??"");
const diffText=d=>({easy:'????,medium:'???',hard:'???'}[d]||d||'???');
async function getJson(u){try{let r=await fetch(u);if(!r.ok)throw new Error(r.status);return await r.json()}catch(e){console.warn('?????????',u,e);if(u.includes('/mastery/data'))return {success:true,points:[],chapters:[],stats:{total:0,mastered:0,weak:0,severe:0}};if(u.includes('/resources/data'))return {success:true,resources:[],questions:[]};if(u.includes('/records/data'))return {success:true,records:[],groups:[],summary:{total:0,video:0,document:0,week:0}};if(u.includes('/discuss'))return {success:true,posts:[],comments:[]};if(u.includes('/messages'))return {success:true,messages:[]};if(u.includes('/flow-graph/data'))return {success:true,nodes:[],edges:[]};return {success:true,stats:{total:0,mastered:0,weak:0,severe:0},learning_path:[],fallback_path:[],target_kp:''}}}
function cls(s){return s==="??????"?"bad":(s==="???"?"warn":"ok")}
function bar(v,s){return `<div class="progress"><div class="bar ${cls(s)}" style="width:${Math.max(2,Math.min(100,(+v||0)*100))}%"></div></div>`}
function action(r){return r.type==="???"?`/student/watch/${encodeURIComponent(r.name)}`:`/student/view/${encodeURIComponent(r.name)}`}
async function dashboard(){let d=await getJson('/student/dashboard/data');app.innerHTML=`<div class="grid"><div class="stat">?????b>${d.stats.mastered}</b></div><div class="stat">???<b>${d.stats.weak}</b></div><div class="stat">??????<b>${d.stats.severe}</b></div><div class="stat">??????<b>${d.recent_count||0}</b></div></div><div class="card"><h2>??????</h2><p class="muted">${esc(d.latest_message||'?????????????????????????????????????????????)}</p><a class="btn" href="/student/path">???????/a></div>`}
async function pathPage(){let d=await getJson('/student/path/data'+(TARGET?'?target_kp='+encodeURIComponent(TARGET):''));let steps=d.learning_path.length?d.learning_path:d.fallback_path;app.innerHTML=`<div class="card"><h2>?????????</h2><p class="muted">?????{esc(d.target_kp)}?????????????????????????/p></div><div class="card">${steps.map((st,i)=>`<div class="path-step"><div class="no">${i+1}</div><div><b>${esc(st.name)}</b><div><span class="tag ${cls(st.status)}">${st.status}</span><span class="tag">?????${st.score.toFixed(2)}</span></div>${bar(st.score,st.status)}<p class="muted">${esc(st.reason)}</p><div class="res-list">${st.resources.map(r=>`<div class="res"><b>${esc(r.title)}</b><p><span class="tag ${r.type==='???'?'video':'doc'}">${r.type}</span><span class="tag">${r.difficulty}</span></p><p class="muted">?????${r.score.toFixed(2)}</p><a class="btn light" href="${action(r)}">???</a> <button class="btn green" disabled>\\u5b8c\\u6210</button><div class="muted after"></div></div>`).join('')}</div></div></div>`).join('')}</div>`}
async function completeResource(r,k,b){b.disabled=true;let d=await fetch('/student/resource/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resource_id:decodeURIComponent(r),kp_id:decodeURIComponent(k)})}).then(x=>x.json());b.parentElement.querySelector('.after').textContent=d.success?`?????${d.before_score.toFixed(2)} ??${d.after_score.toFixed(2)}`:'??????'}
async function resourcesPage(){let data=await getJson('/student/resources/data'), all=data.resources||[], ch='???', sec='???', type='???', q='';function render(){let chapters=[...new Set(all.map(r=>r.chapter_label||'?????))], secs=[...new Set(all.filter(r=>ch==='???'||r.chapter_label===ch).map(r=>r.section_label||'?????))], types=[...new Set(all.map(r=>r.type||'???'))], list=all.filter(r=>(ch==='???'||r.chapter_label===ch)&&(sec==='???'||r.section_label===sec)&&(type==='???'||r.type===type)&&(!q||r.name.includes(q)||String(r.knowledge_point||'').includes(q)));app.innerHTML=`<div class="card"><h2>????????/h2><div class="toolbar"><select onchange="ch=this.value;sec='???';render()"><option>???</option>${chapters.map(x=>`<option ${x===ch?'selected':''}>${x}</option>`).join('')}</select><select onchange="sec=this.value;render()"><option>???</option>${secs.map(x=>`<option ${x===sec?'selected':''}>${x}</option>`).join('')}</select><select onchange="type=this.value;render()"><option>???</option>${types.map(x=>`<option ${x===type?'selected':''}>${x}</option>`).join('')}</select><input class="search" value="${esc(q)}" oninput="q=this.value;render()" placeholder="??????????????></div><div class="tree"><button class="${type==='???'?'active':''}" onclick="type='???';render()">???</button>${types.map(t=>`<button class="${type===t?'active':''}" onclick="type='${t}';render()">${t}</button>`).join('')}</div></div><div class="res-grid">${list.map(r=>`<div class="res-card"><b>${esc(r.title||r.name)}</b><p><span class="tag ${r.type==='???'?'video':'doc'}">${r.type}</span><span class="tag">${r.chapter_label}</span><span class="tag">${r.section_label}</span></p><p class="muted">${esc(r.knowledge_point||'?????????')}</p><a class="btn light" href="${action(r)}">??????</a> <a class="btn light" href="/download/${encodeURIComponent(r.name)}">???</a></div>`).join('')||'<div class="empty">??????????????/div>'}</div>`}window.render=render;render()}
async function mastery(){let d=await getJson('/student/mastery/data');app.innerHTML=`<div class="card"><h2>?????????</h2>${d.chapters.map(ch=>`<h3>${esc(ch.title)}</h3>${ch.knowledge_points.map(k=>`<div class="row"><div><b>${esc(k.name)}</b><div class="muted">${k.status} ? ${k.score.toFixed(2)}</div></div>${bar(k.score,k.status)}</div>`).join('')}`).join('')}</div>`}
async function records(){let d=await getJson('/student/records/data'),s=d.summary||{};app.innerHTML=`<div class="grid"><div class="stat"><span>??????</span><b>${s.video||0}</b><span class="muted">??????</span></div><div class="stat"><span>??????</span><b>${s.document||0}</b><span class="muted">???/???</span></div><div class="stat"><span>????/span><b>${s.week||0}</b><span class="muted">??????</span></div><div class="stat"><span>?????/span><b>${s.total||0}</b><span class="muted">?????????</span></div></div><div class="card"><h2>????????/h2><div class="record-timeline">${(d.records||[]).map(r=>`<div class="record-card"><span class="tag ${r.type==='???'?'video':'doc'}">${esc(r.type)}</span><div><b>${esc(r.name)}</b><div class="muted">${esc(kpName(r.knowledge_point)||'?????????')}</div></div><div class="muted">${esc(r.date||'')} ${esc(r.time||'')}</div></div>`).join('')||'<div class="empty">??????</div>'}</div></div>`}
async function discuss(){let d=await getJson('/student/discuss/list');app.innerHTML=`<div class="card"><h2>??????</h2><div class="toolbar"><input id="topicTitle" class="search" placeholder="??????"><button class="btn" onclick="postTopic()">???</button></div><textarea id="topicBody" style="width:100%" rows="3" placeholder="??????"></textarea>${d.posts.map(p=>`<div class="post" onclick="openPost('${p.id}')"><b>${esc(p.title)}</b><div class="muted">${esc(p.author)} ? ${esc(p.time)} ? ${p.comment_count}?????/div><p>${esc(p.body||'')}</p></div>`).join('')||'<div class="empty">??????</div>'}</div><div class="card" id="postDetail"><div class="muted">?????????????????/div></div>`}
async function postTopic(){await fetch('/student/discuss/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:topicTitle.value,body:topicBody.value})});discuss()}
async function openPost(id){let d=await getJson('/student/discuss/detail/'+encodeURIComponent(id)),p=d.post;postDetail.innerHTML=`<h2>${esc(p.title)}</h2><p>${esc(p.body)}</p><div class="muted">${esc(p.author)} ? ${esc(p.time)}</div><h3>???</h3>${p.comments.map(c=>`<div class="comment"><b>${esc(c.author)}</b><p>${esc(c.body)}</p><div class="muted">${esc(c.time)}</div></div>`).join('')||'<div class="muted">??????</div>'}<textarea id="commentBody" style="width:100%" rows="3" placeholder="?????></textarea><button class="btn" onclick="commentPost('${id}')">??????</button>`}
async function commentPost(id){await fetch('/student/discuss/comment/'+encodeURIComponent(id),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({body:commentBody.value})});openPost(id)}
async function graphBuilder(){let d=await getJson('/student/graph-builder/data');app.innerHTML=`<div class="card"><h2>??????</h2><p class="muted">????????????? ??????? ??????????/p><div class="graph-simple"><input id="fromK" placeholder="?????"><select id="relK"><option>???</option><option>???</option><option>???</option></select><input id="toK" placeholder="?????"><button class="btn" onclick="addEdge()">???</button></div></div><div class="grid">${d.edges.map(e=>`<div class="edge"><b>${esc(e.from)}</b><p class="muted">${esc(e.rel)}</p><b>${esc(e.to)}</b></div>`).join('')||'<div class="empty">??????????????/div>'}</div>`}
async function addEdge(){await fetch('/student/graph-builder/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:fromK.value,to:toK.value,rel:relK.value})});graphBuilder()}
if(PAGE==='dashboard')dashboard();if(PAGE==='path')pathPage();if(PAGE==='resources')resourcesPage();if(PAGE==='mastery')mastery();if(PAGE==='records')records();if(PAGE==='discuss')discuss();if(PAGE==='graph_builder')graphBuilder();
</script></body></html>
"""

STUDENT_FLOW_HTML = r"""
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ page_title }} - OS</title><script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script><style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#111827;font-family:"Microsoft YaHei",Arial,sans-serif}.layout{display:grid;grid-template-columns:216px 1fr;min-height:100vh}.side{background:#fff;border-right:1px solid #e5e7eb;padding:22px 0;position:sticky;top:0;height:100vh}.brand{padding:0 24px 24px;font-size:20px;font-weight:800}.nav a{display:block;padding:13px 28px;color:#4b5563;text-decoration:none;border-left:3px solid transparent}.nav a.active,.nav a:hover{background:#eef4ff;color:#2563eb;border-left-color:#60a5fa}.logout{position:absolute;left:20px;right:20px;bottom:20px}.logout a{display:block;text-align:center;padding:10px;border-radius:6px;background:#eef4ff;color:#2563eb;text-decoration:none;font-weight:700}.top{height:64px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 34px}.top h1{margin:0;font-size:22px}.content{padding:28px 36px;max-width:1500px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}.stat,.res,.res-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px}.stat b{display:block;font-size:30px;margin-top:8px}.muted{color:#64748b;font-size:14px;line-height:1.7}.btn{border:0;background:#2563eb;color:#fff;border-radius:6px;padding:8px 13px;text-decoration:none;cursor:pointer;display:inline-block}.btn.light{background:#eef4ff;color:#2563eb;border:1px solid #dbeafe}.btn.green{background:#16a34a}.tag{font-size:12px;border-radius:999px;background:#eef2ff;color:#3730a3;padding:4px 8px;margin:3px;display:inline-block}.tag.ok{background:#ecfdf5;color:#166534}.tag.warn{background:#fff7ed;color:#9a3412}.tag.bad{background:#fee2e2;color:#991b1b}.progress{height:10px;background:#e5e7eb;border-radius:99px;overflow:hidden;width:320px}.bar{height:100%;background:#22c55e}.bar.warn{background:#f59e0b}.bar.bad{background:#ef4444}.path-step{display:grid;grid-template-columns:38px 1fr;gap:14px;border-top:1px solid #eef2f7;padding:18px 0}.no{width:30px;height:30px;border-radius:50%;background:#2563eb;color:#fff;display:grid;place-items:center;font-weight:800}.res-list,.res-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;border-top:1px solid #eef2f7;padding:12px 0}.chapter{border:1px solid #e5e7eb;border-radius:8px;margin:10px 0;overflow:hidden}.chapter summary{background:#f8fafc;padding:14px 16px;cursor:pointer;font-weight:700}.kp-row{display:grid;grid-template-columns:minmax(220px,1fr) 70px 340px;gap:14px;align-items:center;border-top:1px solid #eef2f7;padding:12px 16px}.empty{padding:34px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px}.search,input,select,textarea{border:1px solid #cbd5e1;border-radius:6px;background:#fff;padding:9px 11px}.search{min-width:280px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}.post{border-top:1px solid #eef2f7;padding:14px 0}.post-head{display:flex;justify-content:space-between;gap:12px}.graph-detail{min-width:0}.graph-detail .progress{width:100%;min-width:0}@media(max-width:900px){.layout{grid-template-columns:1fr}.side{height:auto;position:relative}.logout{position:relative}.content{padding:18px}.kp-row,.path-step{grid-template-columns:1fr}.progress{width:100%}}
</style></head><body><div class="layout"><aside class="side"><div class="brand">&#25805;&#20316;&#31995;&#32479;</div><nav class="nav"><a href="/student/dashboard" class="{% if active_page=='dashboard' %}active{% endif %}">&#39318;&#39029;</a><a href="/student/path" class="{% if active_page=='path' %}active{% endif %}">&#26234;&#33021;&#23398;&#20064;&#36335;&#24452;</a><a href="/student/resources" class="{% if active_page=='resources' %}active{% endif %}">&#23398;&#20064;&#36164;&#28304;&#24211;</a><a href="/student/mastery" class="{% if active_page=='mastery' %}active{% endif %}">&#30693;&#35782;&#28857;&#25484;&#25569;&#24230;</a><a href="/student/graph" class="{% if active_page=='graph' %}active{% endif %}">&#30693;&#35782;&#22270;&#35889;</a><a href="/student/discuss" class="{% if active_page=='discuss' %}active{% endif %}">&#38382;&#39064;&#35752;&#35770;</a><a href="/student/records" class="{% if active_page=='records' %}active{% endif %}">&#23398;&#20064;&#35760;&#24405;</a></nav><div class="logout"><a href="/logout">&#36864;&#20986;&#30331;&#24405;</a></div></aside><main><header class="top"><h1>{{ page_title }}</h1><div>{{ student_name }}</div></header><section class="content" id="app"></section></main></div>
<script>
var PAGE="{{active_page}}",app=document.getElementById('app'),TARGET=new URLSearchParams(location.search).get('target_kp')||'';
var Z={home:'\u9996\u9875',path:'\u667a\u80fd\u5b66\u4e60\u8def\u5f84',resources:'\u5b66\u4e60\u8d44\u6e90\u5e93',mastery:'\u77e5\u8bc6\u70b9\u638c\u63e1\u5ea6',graph:'\u77e5\u8bc6\u56fe\u8c31',discuss:'\u95ee\u9898\u8ba8\u8bba',records:'\u5b66\u4e60\u8bb0\u5f55',video:'\u89c6\u9891',doc:'\u6587\u6863',exercise:'\u4e60\u9898',resource:'\u8d44\u6e90',weak:'\u8584\u5f31',severe:'\u4e25\u91cd\u8584\u5f31',good:'\u826f\u597d',mastered:'\u5df2\u638c\u63e1',doing:'\u8fdb\u884c\u4e2d',unlearned:'\u672a\u5b66\u4e60',normal:'\u666e\u901a',easy:'\u7b80\u5355',medium:'\u4e2d\u7b49',hard:'\u56f0\u96be'};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function kpName(s){return String(s==null?'':s).replace(/^\s*\d+(?:\.\d+)+\s*/,'')||String(s==null?'':s)}
async function getJson(u){try{var r=await fetch(u);return await r.json()}catch(e){return {success:false,learning_path:[],fallback_path:[],resources:[],chapters:[],records:[],posts:[],nodes:[],edges:[],stats:{}}}}
function cleanText(s){s=String(s==null?'':s);if(s.indexOf('\u6d93')>=0||s.indexOf('\u4e25\u91cd')>=0)return Z.severe;if(s.indexOf('\u9496')>=0||s.indexOf('\u8584\u5f31')>=0)return Z.weak;if(s.indexOf('\u5df2')>=0&&s.indexOf('\u638c')>=0)return Z.mastered;if(s.indexOf('\u826f')>=0)return Z.good;if(s.indexOf('\u8fdb')>=0||s.indexOf('\u675e')>=0)return Z.doing;if(s.indexOf('\u7459')>=0||s.indexOf('\u89c6')>=0)return Z.video;if(s.indexOf('\u93c2')>=0||s.indexOf('\u6587')>=0)return Z.doc;if(s.indexOf('\u4e60\u9898')>=0)return Z.exercise;return s}
function normType(t){t=cleanText(t);return t===Z.video||t===Z.doc||t===Z.exercise?t:Z.resource}function diffText(v){return cleanText(v||Z.normal)}function statusClass(s){s=cleanText(s);return s===Z.weak||s===Z.severe?'bad':(s===Z.doing?'warn':'ok')}function bar(v,s){return '<div class="progress"><div class="bar '+statusClass(s)+'" style="width:'+Math.max(2,Math.min(100,(+v||0)*100))+'%"></div></div>'}function action(r){return normType(r.type)===Z.video?'/student/watch/'+encodeURIComponent(r.name||r.title||''):'/student/view/'+encodeURIComponent(r.name||r.title||'')}function displayKp(s){s=cleanText(s);if(/^\d+$/.test(s))return '\u7b2c'+s+'\u7ae0\u76f8\u5173\u77e5\u8bc6\u70b9';return kpName(s)}function displayTarget(d,steps){var t=String(d.target_kp||TARGET||'').trim();if(/^\d+$/.test(t))return '\u7b2c'+t+'\u7ae0\u76f8\u5173\u8584\u5f31\u77e5\u8bc6\u70b9';if(t)return displayKp(t);return steps&&steps[0]?displayKp(steps[0].name||steps[0].kp_id):'\u6839\u636e\u5f53\u524d\u8584\u5f31\u70b9\u81ea\u52a8\u63a8\u8350'}
function codeOf(n){var m=String(n.id||n.label||'').match(/^(\d+(?:\.\d+)*)/);return m?m[1]:''}function wrapLabel(raw,chunk){raw=String(raw||'');chunk=chunk||6;var a=raw.match(new RegExp('.{1,'+chunk+'}','g'))||[raw];return a.join('\\\\n')}function buildLayeredGraph(rawNodes,rawEdges){var map=new Map(),edges=[];function add(n){if(!map.has(n.id))map.set(n.id,n);return map.get(n.id)}add({id:'root',label:'\u64cd\u4f5c\u7cfb\u7edf',drawLabel:'\u64cd\u4f5c\u7cfb\u7edf',level:-1,shape:'diamond',size:42,fontSize:18,mastery:1,levelName:'\u8bfe\u7a0b'});rawNodes.forEach(function(n){var code=codeOf(n),parts=code.split('.').filter(Boolean);if(parts.length){var ch='chapter-'+parts[0];add({id:ch,label:'\u7b2c'+parts[0]+'\u7ae0',drawLabel:'\u7b2c'+parts[0]+'\u7ae0',level:0,shape:'hexagon',size:38,fontSize:18,mastery:n.mastery||0,levelName:'\u7ae0\u8282'});edges.push({from:'root',to:ch,type:'\u5305\u542b'});if(parts.length>=2){var sec=parts[0]+'.'+parts[1];var secNode=rawNodes.find(function(x){return codeOf(x)===sec});add({id:sec,label:displayKp(secNode&&secNode.label||secNode&&secNode.id||sec),drawLabel:wrapLabel(displayKp(secNode&&secNode.label||secNode&&secNode.id||sec),5),level:1,shape:'box',size:24,fontSize:14,mastery:(secNode&&secNode.mastery)||n.mastery||0,total_questions:(secNode&&secNode.total_questions)||0,correct_questions:(secNode&&secNode.correct_questions)||0,levelName:'\u5927\u8282'});edges.push({from:ch,to:sec,type:'\u5305\u542b'});if(parts.length>=3){add({id:n.id,label:n.label||n.id,drawLabel:wrapLabel(displayKp(n.label||n.id),5),level:2,shape:'circle',size:20,fontSize:13,mastery:n.mastery||0,total_questions:n.total_questions||0,correct_questions:n.correct_questions||0,levelName:'\u77e5\u8bc6\u70b9'});edges.push({from:sec,to:n.id,type:'\u5305\u542b'})}}}else add({id:n.id,label:n.label||n.id,drawLabel:wrapLabel(displayKp(n.label||n.id),5),level:2,shape:'circle',size:20,fontSize:13,mastery:n.mastery||0,levelName:'\u77e5\u8bc6\u70b9'})});(rawEdges||[]).forEach(function(e){edges.push({from:e.from,to:e.to,type:cleanText(e.type||'\u76f8\u5173')})});var uniq=[],seen=new Set();edges.forEach(function(e){var k=e.from+'>'+e.to+'>'+e.type;if(e.from!==e.to&&!seen.has(k)&&map.has(e.from)&&map.has(e.to)){seen.add(k);uniq.push(e)}});return {nodes:Array.from(map.values()),edges:uniq}}
async function dashboard(){var d=await getJson('/student/dashboard/data'),r=await getJson('/student/resources/data'),st=d.stats||{};app.innerHTML='<div class="grid"><a class="stat" href="/student/mastery"><span>'+Z.mastered+'</span><b>'+(st.mastered||0)+'</b><span class="muted">'+Z.weak+' '+(st.weak||0)+'</span></a><a class="stat" href="/student/path"><span>'+Z.path+'</span><b>Start</b></a><a class="stat" href="/student/resources"><span>'+Z.resources+'</span><b>'+((r.resources||[]).length)+'</b></a><a class="stat" href="/student/graph"><span>'+Z.graph+'</span><b>Go</b></a></div>'}
async function pathPage(){var d=await getJson('/student/path/data'+(TARGET?'?target_kp='+encodeURIComponent(TARGET):'')),steps=(d.learning_path&&d.learning_path.length?d.learning_path:(d.fallback_path||[])),target=displayTarget(d,steps);app.innerHTML='<div class="card"><h2>'+Z.path+'</h2><p class="muted">\u76ee\u6807\uff1a'+esc(target)+'</p></div><div class="card">'+(steps.map(function(st,i){var rs=st.resources||[],score=Number(st.score||st.mastery||0),status=cleanText(st.status||'\u5f85\u5b66\u4e60');return '<div class="path-step"><div class="no">'+(i+1)+'</div><div><b>'+esc(displayKp(st.name||st.title||st.kp_id||target))+'</b><div><span class="tag '+statusClass(status)+'">'+esc(status)+'</span><span class="tag">'+Z.mastery+' '+Math.round(score*100)+'%</span></div>'+bar(score,status)+'<p class="muted">'+esc(cleanText(st.reason||''))+'</p><div class="res-list">'+rs.map(function(r){return '<div class="res"><b>'+esc(r.title||r.name)+'</b><p><span class="tag">'+esc(normType(r.type))+'</span><span class="tag">'+esc(diffText(r.difficulty))+'</span></p><a class="btn light" href="'+action(r)+'">\u5b66\u4e60</a> <button class="btn green" disabled>\\u5b8c\\u6210</button><div class="muted after"></div></div>'}).join('')+'</div></div></div>'}).join('')||'<div class="empty">No data</div>')+'</div>'}
async function completeResource(r,k,b){b.disabled=true;var d=await fetch('/student/resource/complete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({resource_id:decodeURIComponent(r),kp_id:decodeURIComponent(k)})}).then(function(x){return x.json()}).catch(function(){return {success:false}});b.parentElement.querySelector('.after').textContent=d.success?'OK':'Done'}
async function resourcesPage(){var d=await getJson('/student/resources/data'),all=d.resources||[];app.innerHTML='<div class="card"><h2>'+Z.resources+'</h2><input class="search" id="q" placeholder="搜索资源、知识点、章节" oninput="renderResources()"></div><div id="resResults"></div>';window.renderResources=function(){var q=(document.getElementById('q').value||'').toLowerCase(),list=all.filter(function(r){return [r.name,r.title,r.knowledge_point,r.chapter_label,r.section_label,normType(r.type)].join(' ').toLowerCase().indexOf(q)>=0}),groups={};list.forEach(function(r){var ch=r.chapter_label||'未分类',sec=r.section_label||'未分类';groups[ch]=groups[ch]||{};groups[ch][sec]=groups[ch][sec]||[];groups[ch][sec].push(r)});document.getElementById('resResults').innerHTML=Object.keys(groups).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})}).map(function(ch,i){var secs=Object.keys(groups[ch]).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})});return '<details class="chapter" '+(i===0?'open':'')+'><summary>'+esc(ch)+' · '+secs.reduce(function(n,s){return n+groups[ch][s].length},0)+' 个资源</summary>'+secs.map(function(sec){return '<details open class="chapter" style="margin:8px 12px"><summary>'+esc(sec)+' · '+groups[ch][sec].length+'</summary><div class="res-grid">'+groups[ch][sec].map(function(r){return '<div class="res-card"><b>'+esc(r.title||r.name)+'</b><p><span class="tag">'+esc(normType(r.type))+'</span><span class="tag">'+esc(r.chapter_label||'')+'</span></p><p class="muted">'+esc(displayKp(r.knowledge_point)||'')+'</p><a class="btn light" href="'+action(r)+'">在线查看</a> <a class="btn light" href="/download/'+encodeURIComponent(r.name||'')+'">下载</a></div>'}).join('')+'</div></details>'}).join('')+'</details>'}).join('')||'<div class="empty">暂无资源</div>'};renderResources()}
async function mastery(){var d=await getJson('/student/mastery/data'),chs=d.chapters||[];app.innerHTML='<div class="card"><h2>'+Z.mastery+'</h2>'+(chs.map(function(ch){return '<details class="chapter" open><summary>'+esc(ch.title)+' ? '+((ch.knowledge_points||[]).length)+'</summary>'+(ch.knowledge_points||[]).map(function(k){var status=cleanText(k.status||'');return '<div class="kp-row"><div><b>'+esc(displayKp(k.name))+'</b><div class="muted">'+esc(status)+'</div></div><b>'+Math.round((k.score||0)*100)+'%</b>'+bar(k.score,status)+'</div>'}).join('')+'</details>'}).join('')||'<div class="empty">No data</div>')+'</div>'}
async function records(){var d=await getJson('/student/records/data'),s=d.summary||{};app.innerHTML='<div class="grid"><div class="stat"><span>'+Z.video+'</span><b>'+(s.video||0)+'</b></div><div class="stat"><span>'+Z.doc+'</span><b>'+(s.document||0)+'</b></div></div><div class="card"><h2>'+Z.records+'</h2>'+((d.records||[]).map(function(r){return '<div class="row"><div><b>'+esc(r.name)+'</b><div class="muted">'+esc(displayKp(r.knowledge_point))+'</div></div><span class="tag">'+esc(normType(r.type))+'</span></div>'}).join('')||'<div class="empty">No data</div>')+'</div>'}
async function discuss(){var d=await getJson('/student/discuss/list');app.innerHTML='<div class="card"><h2>'+Z.discuss+'</h2>'+(d.posts||[]).map(function(p){return '<div class="post"><div class="post-head"><b>'+esc(p.title)+'</b><span class="tag">'+esc(cleanText(p.status||''))+'</span></div><p>'+esc(p.body||'')+'</p></div>'}).join('')+'</div>'}async function myDiscussPage(){discuss()}
async function graphPage(){var d=await getJson('/student/flow-graph/data'),built=buildLayeredGraph(d.nodes||[],d.edges||[]),nodes=built.nodes,edges=built.edges;app.innerHTML='<div class="card"><h2>'+Z.graph+'</h2><div class="muted"><b>\u989c\u8272 = \u5b66\u4e60\u72b6\u6001\uff1a</b><span class="tag ok">'+Z.mastered+'>=80%</span><span class="tag">'+Z.good+'>=60%</span><span class="tag warn">'+Z.doing+'>=40%</span><span class="tag bad">'+Z.weak+'&lt;40%</span><span class="tag">'+Z.unlearned+'</span><b style="margin-left:12px">\u8fb9\uff1a</b>\u5305\u542b / \u76f8\u5173 / \u5148\u4fee</div><div style="display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px;margin-top:14px"><div style="position:relative"><div id="mynetwork" style="height:720px;border:1px solid #e5e7eb;background:#fafafa"></div><div style="position:absolute;right:18px;top:18px;width:62px;background:#fff;border:1px solid #dbe3ef;border-radius:14px;box-shadow:0 8px 24px rgba(15,23,42,.12);padding:10px;display:grid;gap:6px;place-items:center"><button class="btn light" style="width:40px;height:40px;padding:0" onclick="zoomGraph(.03)">+</button><input id="graphZoom" type="range" min="0" max="100" step="1" value="26" oninput="setGraphZoom(this.value)" style="writing-mode:vertical-lr;direction:rtl;-webkit-appearance:slider-vertical;appearance:slider-vertical;width:40px;height:250px;margin:0;touch-action:none"><button class="btn light" style="width:40px;height:40px;padding:0" onclick="zoomGraph(-.03)">-</button></div></div><div id="nodeDetail" class="res-card graph-detail"><b>\u8282\u70b9\u8be6\u60c5</b><p class="muted">\u5355\u51fb\u8282\u70b9\u67e5\u770b\u638c\u63e1\u5ea6\u3002</p></div></div></div>';if(!window.vis){document.getElementById('mynetwork').innerHTML='<div class="empty">vis load failed</div>';return}function color(m){return m>=.8?{background:'#d4f0dc',border:'#a8ddb8'}:m>=.6?{background:'#dbeafe',border:'#93c5fd'}:m>=.4?{background:'#ffedd5',border:'#fdba74'}:m>0?{background:'#fee2e2',border:'#fca5a5'}:{background:'#eceff1',border:'#cfd8dc'}}var visNodes=new vis.DataSet(nodes.map(function(n){return {id:n.id,label:n.drawLabel||displayKp(n.label||n.id),shape:n.shape,size:n.size,color:n.id==='root'?{background:'#1f2937',border:'#111827'}:color(n.mastery||0),font:{size:n.fontSize,face:'Microsoft YaHei',color:n.id==='root'?'#fff':'#111827',bold:true,multi:true},borderWidth:n.level<=0?4:3,mass:n.level<=0?6:(n.level===1?3:1),widthConstraint:n.shape==='box'?{minimum:120,maximum:150}:undefined,heightConstraint:n.shape==='box'?{minimum:60}:undefined}}));var visEdges=new vis.DataSet(edges.map(function(e,i){return {id:i,from:e.from,to:e.to,arrows:'to',color:{color:e.type==='\u5148\u4fee'?'#9b59b6':(e.type==='\u76f8\u5173'?'#f59e0b':'#94a3b8')},dashes:e.type!=='\u5305\u542b',width:e.type==='\u5305\u542b'?2.2:1.7,smooth:{type:'dynamic'}}}));var network=new vis.Network(document.getElementById('mynetwork'),{nodes:visNodes,edges:visEdges},{physics:{solver:'forceAtlas2Based',forceAtlas2Based:{gravitationalConstant:-240,centralGravity:.018,springLength:170,springConstant:.04,avoidOverlap:1},stabilization:{iterations:600}},interaction:{zoomView:true,dragView:true,dragNodes:true}});window.graphNetwork=network;window.graphZoomMin=.24;window.graphZoomMax=.55;window.graphScale=.32;network.once('stabilizationIterationsDone',function(){network.stopSimulation();applyGraphZoom(.32,true)});network.on('click',function(p){var id=p.nodes&&p.nodes[0],n=nodes.find(function(x){return x.id===id});if(!n)return;var m=Number(n.mastery||0),state=m>=.8?Z.mastered:m>=.6?Z.good:m>=.4?Z.doing:m>0?Z.weak:Z.unlearned;document.getElementById('nodeDetail').innerHTML='<b>'+esc(displayKp(n.label||n.id))+'</b><p><span class="tag '+statusClass(state)+'">'+state+'</span><span class="tag">'+Z.mastery+' '+Math.round(m*100)+'%</span></p>'+bar(m,state)+'<p class="muted">'+esc(n.levelName||'')+'</p>'})}
function graphSliderToScale(v){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55,t=Math.max(0,Math.min(100,parseFloat(v)||0))/100;return min+(max-min)*t}function graphScaleToSlider(s){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55;return Math.round((Math.max(min,Math.min(max,parseFloat(s)||min))-min)/(max-min)*100)}function applyGraphZoom(scale,animate){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55;window.graphScale=Math.max(min,Math.min(max,parseFloat(scale)||.32));if(window.graphNetwork)window.graphNetwork.moveTo({position:window.graphNetwork.getViewPosition(),scale:window.graphScale,animation:animate?{duration:120,easingFunction:'easeInOutQuad'}:{duration:0}});var z=document.getElementById('graphZoom');if(z)z.value=graphScaleToSlider(window.graphScale)}function setGraphZoom(v){applyGraphZoom(graphSliderToScale(v),false)}function zoomGraph(delta){applyGraphZoom((window.graphScale||.32)+delta,true)}async function graphBuilder(){graphPage()}
if(PAGE==='dashboard')dashboard();if(PAGE==='path')pathPage();if(PAGE==='resources')resourcesPage();if(PAGE==='mastery')mastery();if(PAGE==='records')records();if(PAGE==='discuss')discuss();if(PAGE==='my_discuss')myDiscussPage();if(PAGE==='graph')graphPage();if(PAGE==='graph_builder')graphBuilder();
</script></body></html>
"""
def _clean_resource_type(name):
    low = (name or "").lower()
    if low.endswith((".mp4", ".avi", ".mov", ".mkv")):
        return "\u89c6\u9891"
    if low.endswith((".json", ".txt")):
        return "\u4e60\u9898"
    return "\u6587\u6863"

def _clean_kp_title(raw):
    raw = str(raw or "")
    return re.sub(r"^\s*\d+(?:\.\d+)*\s*", "", raw) or raw

def _kp_code(raw):
    m = re.match(r"^(\d+(?:\.\d+)*)", str(raw or ""))
    return m.group(1) if m else ""

def _safe_points(student_id):
    rows = []
    try:
        with driver.session() as neo4j_session:
            rows = list(neo4j_session.run("""
            MATCH (k:Knowledge)
            WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
            OPTIONAL MATCH (:Student {id:$sid})-[m:MASTERED]->(k)
            RETURN k.name AS name, COALESCE(m.mastery, 0) AS score,
                   COALESCE(m.total_questions, 0) AS total_questions,
                   COALESCE(m.correct_questions, 0) AS correct_questions
            ORDER BY k.name
            """, sid=student_id))
    except Exception:
        rows = []
    points = []
    for r in rows:
        score = float(r["score"] or 0)
        status = "\u5df2\u638c\u63e1" if score >= 0.8 else ("\u826f\u597d" if score >= 0.6 else ("\u8fdb\u884c\u4e2d" if score >= 0.4 else ("\u8584\u5f31" if score > 0 else "\u672a\u5b66\u4e60")))
        name = r["name"] or ""
        points.append({
            "name": name,
            "score": score,
            "status": status,
            "total_questions": r["total_questions"] or 0,
            "correct_questions": r["correct_questions"] or 0,
        })
    return points

def _safe_resources():
    items = []
    if not os.path.exists(RESOURCE_DIR):
        return items
    for f in os.listdir(RESOURCE_DIR):
        if f in {"questions.json", "question_history.json"} or f.endswith(".bak"):
            continue
        path = os.path.join(RESOURCE_DIR, f)
        if not os.path.isfile(path):
            continue
        code = flow_resource_code(f) or _kp_code(f)
        info = infer_resource_info(f)
        ch = str(info.get("ch") or (code.split(".")[0] if code else ""))
        items.append({
            "name": f,
            "title": os.path.splitext(f)[0],
            "type": flow_resource_type(f),
            "difficulty": flow_resource_difficulty(f),
            "knowledge_point": code,
            "chapter_label": ("\u7b2c%s\u7ae0" % ch) if ch else "未分类",
            "section_label": ("%s.%s" % (info.get("ch"), info.get("big"))) if info.get("ch") and info.get("big") else ("整章" if info.get("ch") else "未分类"),
            "resource_id": f,
        })
    return items

def _safe_mastery_response():
    points = _safe_points(session.get("full_id"))
    chapters = []
    by_ch = {}
    for p in points:
        code = _kp_code(p["name"])
        ch = code.split(".")[0] if code else "0"
        by_ch.setdefault(ch, []).append(p)
    for ch in sorted(by_ch, key=lambda x: int(x) if x.isdigit() else 99):
        chapters.append({
            "title": "\u7b2c%s\u7ae0" % ch,
            "knowledge_points": by_ch[ch],
        })
    return jsonify({"success": True, "points": points, "chapters": chapters})

def _safe_resources_response():
    return jsonify({"success": True, "resources": _safe_resources(), "questions": []})

def _safe_path_response():
    points = sorted(_safe_points(session.get("full_id")), key=lambda p: p["score"])
    resources = _safe_resources()
    weak = [p for p in points if p["score"] < 0.7][:5]
    if not weak and points:
        weak = points[:3]
    steps = []
    for p in weak:
        code = _kp_code(p["name"])
        rel = [r for r in resources if r.get("knowledge_point") and (code.startswith(r["knowledge_point"]) or r["knowledge_point"].startswith(code))]
        if not rel:
            rel = resources[:3]
        steps.append({
            "kp_id": p["name"],
            "name": p["name"],
            "score": p["score"],
            "status": p["status"],
            "reason": "\u5efa\u8bae\u4f18\u5148\u5b66\u4e60\u8be5\u8584\u5f31\u77e5\u8bc6\u70b9",
            "resources": rel[:3],
        })
    target = request.args.get("target_kp") or (steps[0]["name"].split(".")[0] if steps else "")
    return jsonify({"success": True, "target_kp": target, "learning_path": steps, "fallback_path": []})

def _safe_graph_response():
    nodes = []
    for p in _safe_points(session.get("full_id")):
        nodes.append({
            "id": p["name"],
            "label": _clean_kp_title(p["name"]),
            "level": 2,
            "mastery": p["score"],
            "total_questions": p["total_questions"],
            "correct_questions": p["correct_questions"],
        })
    return jsonify({"success": True, "nodes": nodes, "edges": []})

@app.route("/teacher/student-profile/data")
def teacher_student_profile_data():
    if session.get("role") != "teacher":
        return jsonify({"success": False, "error": "未登录"})
    sid = request.args.get("sid", "").strip()
    if not sid:
        return jsonify({"success": False, "error": "缺少学生ID"})
    try:
        profile = get_user_profile(sid)
    except Exception:
        flow = get_flow_mastery_data(sid)
        points = flow.get("points", [])
        avg = sum(p.get("score", 0) for p in points) / len(points) if points else 0
        profile = {
            "level": "薄弱" if avg < 0.7 else "良好",
            "avg_mastery": avg,
            "accuracy": avg,
            "total_questions": sum(p.get("total_questions", 0) for p in points),
            "total_correct": sum(p.get("correct_questions", 0) for p in points),
            "description": "根据知识点掌握度生成的学习画像",
            "weak_key_points": [],
            "weak_general_points": [{"name": p.get("full_name") or p.get("name"), "mastery": p.get("score", 0)} for p in points if p.get("score", 0) < 0.7],
        }
    flow = get_flow_mastery_data(sid)
    graph_nodes = []
    for p in flow.get("points", []):
        graph_nodes.append({
            "id": p.get("full_name") or p.get("name") or p.get("kp_id"),
            "label": p.get("full_name") or p.get("name") or p.get("kp_id"),
            "mastery": p.get("score", 0),
            "total_questions": p.get("total_questions", 0),
            "correct_questions": p.get("correct_questions", 0),
        })
    return jsonify({"success": True, "profile": profile, "mastery": flow, "graph": {"nodes": graph_nodes, "edges": []}})

def render_teacher_workspace(initial_tab="overview", page_title="教师工作台"):
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    html = r"""
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ page_title }} - 教师工作台</title><script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#152238;font-family:"Microsoft YaHei",Arial,sans-serif}.layout{display:grid;grid-template-columns:226px 1fr;min-height:100vh}.side{background:#fff;border-right:1px solid #e5e7eb;padding:20px 0;position:sticky;top:0;height:100vh}.brand{padding:0 24px 22px;font-size:21px;font-weight:800}.brand small{display:block;color:#64748b;font-size:12px;margin-top:6px}.nav a{display:block;text-decoration:none;color:#4b5563;padding:13px 28px;border-left:3px solid transparent;font-size:16px}.nav a:hover,.nav a.active{background:#eef4ff;color:#2563eb;border-left-color:#60a5fa}.logout{position:absolute;bottom:20px;left:20px;right:20px}.logout a{display:block;text-align:center;background:#eef4ff;color:#2563eb;padding:10px;border-radius:6px;text-decoration:none;font-weight:700}.top{height:64px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 34px}.top h1{font-size:22px;margin:0}.content{padding:26px 34px;max-width:1480px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}.stat{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:18px}.stat b{display:block;font-size:30px;margin-top:8px}.muted{color:#64748b;font-size:13px;line-height:1.7}.btn{border:0;background:#2563eb;color:#fff;border-radius:6px;padding:8px 13px;text-decoration:none;cursor:pointer;display:inline-block;font-weight:700}.btn.light{background:#eef4ff;color:#2563eb;border:1px solid #dbeafe}.btn.green{background:#16a34a}.btn.danger{background:#ef4444}.btn.back{font-size:15px;padding:10px 15px;margin-bottom:12px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}select,input,textarea{border:1px solid #cbd5e1;border-radius:6px;background:#fff;padding:9px 11px}.search{min-width:280px}.table-wrap{max-height:calc(100vh - 230px);overflow:auto}.table{width:100%;border-collapse:collapse}.table th,.table td{padding:11px;border-bottom:1px solid #eef2f7;text-align:left;vertical-align:top}.table th{background:#f8fafc;color:#475569;font-weight:700;cursor:pointer;position:sticky;top:0;z-index:1}.sort-tri{display:inline-block;margin-left:6px;width:0;height:0;vertical-align:middle}.sort-tri.up{border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:8px solid #2563eb}.sort-tri.down{border-left:5px solid transparent;border-right:5px solid transparent;border-top:8px solid #2563eb}.tag{font-size:12px;border-radius:999px;background:#eef2ff;color:#3730a3;padding:4px 8px;display:inline-block;margin:0 4px 4px 0}.tag.ok{background:#dcfce7;color:#166534}.tag.warn{background:#fff7ed;color:#9a3412}.tag.bad{background:#fee2e2;color:#991b1b}.bar{height:8px;background:#e5e7eb;border-radius:99px;overflow:hidden;width:130px}.bar span{display:block;height:100%;background:#2563eb}.split{display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:16px}.empty{padding:34px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px}.modal{display:none;position:fixed;inset:0;background:rgba(15,23,42,.45);z-index:50;align-items:center;justify-content:center}.modal.open{display:flex}.dialog{background:#fff;border-radius:8px;width:420px;max-width:92vw;padding:22px}.dialog label{display:block;font-size:13px;color:#475569;margin:12px 0 5px}.dialog input,.dialog textarea{width:100%}.graph-detail .bar{width:100%}@media(max-width:960px){.layout{grid-template-columns:1fr}.side{position:relative;height:auto}.logout{position:relative}.split{grid-template-columns:1fr}.content{padding:18px}}
</style></head><body><div class="layout"><aside class="side"><div class="brand">教师工作台<small>{{ teacher_name }}</small></div><nav class="nav">
<a class="{% if initial_tab == 'overview' %}active{% endif %}" href="/teacher/tools">工作台总览</a><a class="{% if initial_tab == 'students' %}active{% endif %}" href="/teacher/manage">学生管理</a><a class="{% if initial_tab == 'profiles' %}active{% endif %}" href="/teacher/students">学生画像</a><a class="{% if initial_tab == 'resourceManage' %}active{% endif %}" href="/teacher/resource-manage">资源管理</a><a class="{% if initial_tab == 'questionBank' %}active{% endif %}" href="/teacher/question-bank">题库管理</a><a class="{% if initial_tab == 'graph' %}active{% endif %}" href="/teacher/graph-tools">公共图谱</a><a href="/teacher/discuss">问题讨论</a>
</nav><div class="logout"><a href="/logout">退出登录</a></div></aside><main><header class="top"><h1 id="pageTitle">{{ page_title }}</h1><span class="muted">操作系统课程管理</span></header><section class="content"><div id="app"><div class="empty">加载中...</div></div></section></main></div>
<div class="modal" id="questionModal"><div class="dialog" style="width:720px"><h3 id="qTitle">添加题目</h3><label>题目内容</label><textarea id="qText" rows="4"></textarea><label>知识点</label><input id="qKp" list="kpOptions" oninput="filterKpOptions(this.value)" placeholder="输入关键词后选择知识点"><datalist id="kpOptions"></datalist><label>难度</label><select id="qDifficulty"><option value="easy">简单</option><option value="medium">中等</option><option value="hard">困难</option></select><label>选项和答案</label><div id="optionEditor"></div><label>解析</label><textarea id="qExplain" rows="3"></textarea><input id="qId" type="hidden"><div style="margin-top:16px;text-align:right"><button class="btn light" onclick="questionModal.classList.remove('open')">取消</button> <button class="btn green" onclick="saveQuestion()">保存</button></div></div></div>
<div class="modal" id="studentModal"><div class="dialog"><h3 id="studentModalTitle">添加学生</h3><input id="editStudentId" type="hidden"><label>学号</label><input id="studentNum"><label>姓名</label><input id="studentName"><div style="margin-top:16px;text-align:right"><button class="btn light" onclick="closeStudentModal()">取消</button> <button class="btn green" onclick="saveStudent()">保存</button></div></div></div>
<script>
let DATA={students:[],summary:{},levels:{},weak_rank:[],resources:{types:{},recent:[]},questions:{difficulty:{},recent:[]}}, TAB="{{ initial_tab }}", SID=new URLSearchParams(location.search).get('sid')||'';let SORT={students:['num',1],profiles:['num',1],kp:['name',1],resources:['name',1],questions:['id',1]},KPS=[];
const app=document.getElementById('app'), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])), pct=v=>Math.round((Number(v)||0)*100)+'%', kpName=s=>String(s??'').replace(/^\s*\d+(?:\.\d+)+\s*/,'')||String(s??'');
const diffText=d=>({easy:'简单',medium:'中等',hard:'困难','简单':'简单','中等':'中等','困难':'困难'}[d]||d||'中等'), levelClass=l=>String(l).includes('优秀')||String(l).includes('良好')?'ok':(String(l).includes('中')?'warn':'bad');
function normSearch(s){return String(s??'').toLowerCase().replace(/\s+/g,'')}function bar(v){return `<div class="bar"><span style="width:${pct(v)}"></span></div>`}
function sorted(list,type,key){let cur=SORT[type]||[key,1],dir=cur[0]===key?-cur[1]:1;SORT[type]=[key,dir];return [...list].sort((a,b)=>{let x=a[key]??'',y=b[key]??'';if(typeof x==='number'||typeof y==='number')return ((Number(x)||0)-(Number(y)||0))*dir;return String(x).localeCompare(String(y),'zh-Hans',{numeric:true})*dir})}
function th(type,key,label){let cur=SORT[type]||[],mark=cur[0]===key?`<span class="sort-tri ${cur[1]===1?'up':'down'}"></span>`:'';return `<th onclick="sortBy('${type}','${key}')">${label}${mark}</th>`}
function sortBy(type,key){if(type==='students')renderStudents(sorted(window.STUDENT_LIST||DATA.students,type,key));if(type==='profiles')renderProfilesTable(sorted(window.PROFILE_LIST||DATA.students,type,key));if(type==='kp')renderKpRows(sorted(window.KP_LIST||[],type,key));if(type==='resources')renderResourceTable(window.RESOURCE_LIST=sorted(window.RESOURCE_LIST||[],type,key));if(type==='questions')renderQuestionTable(window.QUESTION_LIST=sorted(window.QUESTION_LIST||[],type,key))}
async function loadData(){DATA=await fetch('/teacher/tools/data').then(r=>r.json());try{KPS=(await fetch('/teacher/knowledge-points/data').then(r=>r.json())).points||[]}catch(e){KPS=[]}render()}
function render(){({overview,students,profiles,resourceManage,questionBank,graph}[TAB]||overview)()}
function overview(){let s=DATA.summary||{}, weak=(DATA.weak_rank||[]).slice(0,6),lv=DATA.levels||{},rt=(DATA.resources||{}).types||{},qd=(DATA.questions||{}).difficulty||{};let statList=(o,map=x=>x)=>Object.keys(o).map(k=>`<div style="display:flex;justify-content:space-between;border-top:1px solid #eef2f7;padding:9px 0"><span>${esc(map(k))}</span><b>${o[k]}</b></div>`).join('')||'<div class="empty">暂无数据</div>';app.innerHTML=`<div class="grid"><div class="stat">学生人数<b>${s.student_count||0}</b><span class="muted">当前班级</span></div><div class="stat">平均掌握度<b>${pct(s.avg_mastery)}</b><span class="muted">基于知识点画像</span></div><div class="stat">薄弱学生<b>${s.weak_student_count||0}</b><span class="muted">掌握度低于70%</span></div><div class="stat">资源 / 题目<b>${s.resource_count||0} / ${s.question_count||0}</b><span class="muted">课程材料规模</span></div></div><div class="split"><div class="card"><h2>重点关注学生</h2>${studentRows((DATA.students||[]).slice(0,6),false)}</div><div class="card"><h2>共性薄弱知识点</h2>${weak.map(x=>`<div style="display:flex;justify-content:space-between;border-top:1px solid #eef2f7;padding:11px 0"><span>${esc(kpName(x.name))}</span><b>${x.count}人</b></div>`).join('')||'<div class="empty">暂无薄弱统计</div>'}</div></div><div class="grid"><div class="card"><h2>等级分布</h2>${statList(lv)}</div><div class="card"><h2>资源类型</h2>${statList(rt)}</div><div class="card"><h2>题目难度</h2>${statList(qd,diffText)}</div></div>`}
function studentRows(list,withActions=true){let heads=withActions?`${th('students','num','学号')}${th('students','name','姓名')}${th('students','level','等级')}${th('students','avg_mastery','掌握度')}${th('students','accuracy','正确率')}`:'<th>学号</th><th>姓名</th><th>等级</th><th>掌握度</th><th>正确率</th>';return `<table class="table"><thead><tr>${heads}<th>薄弱点</th>${withActions?'<th>操作</th>':''}</tr></thead><tbody>${list.map(st=>`<tr><td>${esc(st.num)}</td><td><b>${esc(st.name)}</b></td><td><span class="tag ${levelClass(st.level)}">${esc(st.level)}</span></td><td>${pct(st.avg_mastery)}${bar(st.avg_mastery)}</td><td>${pct(st.accuracy)}</td><td>${(st.weak_points||[]).slice(0,3).map(w=>`<span class="tag bad">${esc(kpName(w.name))} ${pct(w.mastery)}</span>`).join('')||'<span class="muted">暂无</span>'}</td>${withActions?`<td><button class="btn light" onclick="openProfile('${esc(st.id)}')">详情</button> <button class="btn light" onclick="openEditStudent('${esc(st.id)}','${esc(st.num)}','${esc(st.name)}')">编辑</button> <button class="btn danger" onclick="deleteStudent('${esc(st.id)}')">删除</button></td>`:''}</tr>`).join('')}</tbody></table>`}
function students(){window.STUDENT_LIST=DATA.students||[];app.innerHTML=`<div class="card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2>学生管理</h2><button class="btn green" onclick="openAddStudent()">添加学生</button></div><div class="toolbar"><input class="search" id="stuSearch" oninput="filterStudents()" placeholder="搜索学号、姓名、等级"></div><div id="studentTable"></div></div>`;renderStudents(window.STUDENT_LIST)}function renderStudents(list){studentTable.innerHTML=studentRows(list)}function filterStudents(){let q=normSearch(stuSearch.value);window.STUDENT_LIST=(DATA.students||[]).filter(s=>!q||normSearch([s.num,s.name,s.level].join(' ')).includes(q));renderStudents(window.STUDENT_LIST)}
function profiles(){if(SID)return profileDetail(SID);window.PROFILE_LIST=DATA.students||[];app.innerHTML=`<div class="card"><h2>学生画像列表</h2><div class="toolbar"><input class="search" id="profileSearch" oninput="filterProfiles()" placeholder="搜索学号、姓名、学习建议"></div><div id="profileTable"></div></div>`;renderProfilesTable(window.PROFILE_LIST)}function renderProfilesTable(list){profileTable.innerHTML=`<div class="table-wrap"><table class="table"><thead><tr>${th('profiles','num','学号')}${th('profiles','name','姓名')}${th('profiles','level','等级')}${th('profiles','avg_mastery','平均掌握度')}${th('profiles','accuracy','正确率')}${th('profiles','total_questions','做题数')}<th>学习建议</th><th>操作</th></tr></thead><tbody>${list.map(s=>`<tr><td>${esc(s.num)}</td><td><b>${esc(s.name)}</b></td><td><span class="tag ${levelClass(s.level)}">${esc(s.level)}</span></td><td><b>${pct(s.avg_mastery)}</b></td><td>${pct(s.accuracy)}</td><td>${s.total_correct||0}/${s.total_questions||0}</td><td class="muted">${esc(s.description||'')}</td><td><button class="btn light" onclick="openProfile('${esc(s.id)}')">详情</button></td></tr>`).join('')}</tbody></table></div>`}function filterProfiles(){let q=normSearch(profileSearch.value);window.PROFILE_LIST=(DATA.students||[]).filter(s=>!q||normSearch([s.num,s.name,s.level,s.description].join(' ')).includes(q));renderProfilesTable(window.PROFILE_LIST)}function openProfile(id){location.href='/teacher/students?sid='+encodeURIComponent(id)}
async function profileDetail(sid){let d=await fetch('/teacher/student-profile/data?sid='+encodeURIComponent(sid)).then(r=>r.json()),p=d.profile||{},m=d.mastery||{},pts=m.points||[],student=(DATA.students||[]).find(s=>s.id===sid)||{};window.KP_LIST=pts;app.innerHTML=`<a class="btn light back" href="/teacher/students">‹ 返回学生画像列表</a><div class="card"><h2>学生画像 - ${esc(student.num||'')} ${esc(student.name||sid)}</h2><div class="grid"><div class="stat">学习等级<b>${esc(p.level||student.level||'暂无')}</b></div><div class="stat">平均掌握度<b>${pct(p.avg_mastery||student.avg_mastery)}</b></div><div class="stat">正确率<b>${pct(p.accuracy||student.accuracy)}</b></div><div class="stat">做题总数<b>${p.total_questions||student.total_questions||0}</b></div></div><div class="card" style="background:#eef4ff;margin:16px 0 0"><b>学习建议</b><div>${esc(p.description||student.description||'暂无建议')}</div></div></div><div class="card"><h2>知识点学习明细</h2><div id="kpTable"></div></div><div class="card"><h2>学习画像知识图谱</h2><div style="display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:18px"><div id="teacherGraph" style="height:650px;border:1px solid #e5e7eb;background:#fafafa"></div><div id="teacherNodeDetail" class="card graph-detail"><b>节点详情</b><p class="muted">单击节点查看掌握度等信息。</p></div></div></div>`;renderKpRows(pts);renderTeacherGraph(d.graph||{nodes:[],edges:[]})}
function renderKpRows(list){let rows=list||[];kpTable.innerHTML=`<div class="table-wrap" style="max-height:none"><table class="table"><thead><tr>${th('kp','name','知识点')}${th('kp','score','综合掌握度')}${th('kp','exercise_score','做题')}${th('kp','video_score','视频')}${th('kp','resource_score','资源')}${th('kp','discussion_score','讨论')}</tr></thead><tbody>${rows.map(k=>`<tr><td><b>${esc(kpName(k.full_name||k.name))}</b><div class="muted">${esc(k.full_name||k.name)}</div></td><td>${pct(k.score)}${bar(k.score)}</td><td>${pct(k.exercise_score)}</td><td>${pct(k.video_score)}</td><td>${pct(k.resource_score)}</td><td>${pct(k.discussion_score)}</td></tr>`).join('')}</tbody></table></div>`}
function renderTeacherGraph(g){if(!window.vis){teacherGraph.innerHTML='<div class="empty">图谱库加载失败</div>';return}let nodes=(g.nodes||[]),edges=(g.edges||[]);let visNodes=new vis.DataSet(nodes.map(n=>({id:n.id,label:kpName(n.label||n.id),shape:'circle',size:18+(Number(n.mastery||0)*14),color:Number(n.mastery||0)>=.8?'#dcfce7':Number(n.mastery||0)>=.6?'#dbeafe':Number(n.mastery||0)>=.4?'#ffedd5':'#fee2e2',font:{face:'Microsoft YaHei',size:13}})));let visEdges=new vis.DataSet(edges.map((e,i)=>({id:i,from:e.from,to:e.to,arrows:'to',color:'#94a3b8'})));let network=new vis.Network(teacherGraph,{nodes:visNodes,edges:visEdges},{physics:{solver:'forceAtlas2Based',stabilization:{iterations:400}},interaction:{hover:true,zoomView:true,dragView:true}});network.on('click',p=>{let id=p.nodes&&p.nodes[0],n=nodes.find(x=>x.id===id);if(!n)return;teacherNodeDetail.innerHTML=`<b>${esc(kpName(n.label||n.id))}</b><p><span class="tag">掌握度 ${pct(n.mastery)}</span><span class="tag">做题 ${n.correct_questions||0}/${n.total_questions||0}</span></p>${bar(n.mastery)}<p class="muted">${esc(n.id)}</p>`})}
async function resourceManage(){app.innerHTML=`<div class="card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2>资源管理</h2><label class="btn green">上传资源<input type="file" style="display:none" onchange="uploadResource(this)"></label></div><div class="toolbar"><input id="resSearch" class="search" oninput="filterResources()" placeholder="搜索文件名、知识点、章节"><select id="resType" onchange="filterResources()"><option>全部类型</option></select></div><div id="resourceTable"><div class="empty">加载资源中...</div></div></div>`;let d=await fetch('/teacher/resources/data').then(r=>r.json());window.RESOURCE_ALL=d.resources||[];window.RESOURCE_LIST=[...window.RESOURCE_ALL];let types=[...new Set(window.RESOURCE_ALL.map(r=>r.type||'资源'))];resType.innerHTML='<option>全部类型</option>'+types.map(t=>`<option>${esc(t)}</option>`).join('');renderResourceTable(window.RESOURCE_LIST)}function filterResources(){let q=normSearch(resSearch.value),t=resType.value;window.RESOURCE_LIST=(window.RESOURCE_ALL||[]).filter(r=>{let hay=normSearch([r.name,r.title,r.type,r.knowledge_point,kpName(r.knowledge_point),r.chapter_label,r.section_label].join(' '));return (t==='全部类型'||r.type===t)&&(!q||hay.includes(q))});renderResourceTable(window.RESOURCE_LIST)}
function renderResourceTable(list){let chapters={};(list||[]).forEach(r=>{let ch=r.chapter_label||'未分类',sec=r.section_label||'未分类';chapters[ch]=chapters[ch]||{};chapters[ch][sec]=chapters[ch][sec]||[];chapters[ch][sec].push(r)});let tableRows=arr=>`<div class="table-wrap" style="max-height:none"><table class="table"><thead><tr>${th('resources','name','文件名')}${th('resources','type','类型')}${th('resources','knowledge_point','知识点')}${th('resources','updated_at','更新时间')}${th('resources','size','大小')}<th>操作</th></tr></thead><tbody>${arr.map(r=>`<tr><td><b>${esc(r.name)}</b></td><td>${esc(r.type)}</td><td>${esc(kpName(r.knowledge_point)||'未绑定')}</td><td>${esc(r.updated_at)}</td><td>${Math.round((r.size||0)/1024)} KB</td><td><button class="btn light" onclick="renameResource('${esc(r.name)}')">编辑</button> <button class="btn danger" onclick="deleteResource('${esc(r.name)}')">删除</button></td></tr>`).join('')}</tbody></table></div>`;let html=Object.keys(chapters).sort((a,b)=>a.localeCompare(b,'zh-Hans',{numeric:true})).map((ch,ci)=>{let direct=chapters[ch]['整章']||[];let secs=Object.keys(chapters[ch]).filter(s=>s!=='整章').sort((a,b)=>a.localeCompare(b,'zh-Hans',{numeric:true}));return `<details class="card" ${ci===0?'open':''} style="padding:0;overflow:hidden"><summary style="padding:14px 16px;background:#f8fafc;cursor:pointer;font-weight:800">${esc(ch)} · ${Object.values(chapters[ch]).reduce((n,arr)=>n+arr.length,0)} 个资源</summary>${direct.length?tableRows(direct):''}${secs.map(sec=>`<details open style="border-top:1px solid #eef2f7"><summary style="padding:12px 18px;background:#fff;cursor:pointer;font-weight:700;color:#475569">${esc(sec)} · ${chapters[ch][sec].length}</summary>${tableRows(chapters[ch][sec])}</details>`).join('')}</details>`}).join('');resourceTable.innerHTML=html||'<div class="empty">暂无资源</div>'}
async function uploadResource(input){if(!input.files||!input.files[0])return;let fd=new FormData();fd.append('file',input.files[0]);let d=await fetch('/teacher/upload',{method:'POST',body:fd}).then(r=>r.json());alert(d.success?'上传成功：'+d.filename:(d.error||'上传失败'));if(d.success)resourceManage()}async function renameResource(name){let next=prompt('请输入新的文件名',name);if(!next||next===name)return;let d=await fetch('/teacher/resource/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({old_name:name,new_name:next})}).then(r=>r.json());alert(d.success?'修改成功':(d.error||'修改失败'));if(d.success)resourceManage()}async function deleteResource(name){if(!confirm('确认删除 '+name+' 吗？'))return;let d=await fetch('/teacher/resource/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({filename:name})}).then(r=>r.json());alert(d.success?'删除成功':(d.error||'删除失败'));if(d.success)resourceManage()}
async function questionBank(){app.innerHTML=`<div class="card"><div style="display:flex;justify-content:space-between;gap:12px;align-items:center"><h2>题库管理</h2><button class="btn green" onclick="openQuestionEditor()">添加题目</button></div><div class="toolbar"><input id="qSearch" class="search" oninput="filterQuestions()" placeholder="搜索题目、知识点、ID"><select id="qDiff" onchange="filterQuestions()"><option value="">全部难度</option><option value="easy">简单</option><option value="medium">中等</option><option value="hard">困难</option></select></div><div id="questionTable"><div class="empty">加载题目中...</div></div></div>`;let d=await fetch('/teacher/questions/data').then(r=>r.json());window.QUESTION_ALL=d.questions||[];window.QUESTION_LIST=[...window.QUESTION_ALL];renderQuestionTable(window.QUESTION_LIST)}function renderQuestionTable(list){questionTable.innerHTML=`<div class="table-wrap"><table class="table"><thead><tr>${th('questions','id','ID')}${th('questions','knowledge_point','知识点')}${th('questions','difficulty','难度')}${th('questions','question','题目')}${th('questions','answer','答案')}<th>操作</th></tr></thead><tbody>${list.map(q=>`<tr><td>${esc(q.id)}</td><td>${esc(kpName(q.knowledge_point))}</td><td>${esc(diffText(q.difficulty))}</td><td>${esc(q.question)}</td><td>${esc(q.answer)}</td><td><button class="btn light" onclick="openQuestionEditor('${esc(q.id)}')">编辑</button> <button class="btn danger" onclick="deleteQuestion('${esc(q.id)}')">删除</button></td></tr>`).join('')}</tbody></table></div>`}function filterQuestions(){let q=normSearch(qSearch.value),d=qDiff.value;window.QUESTION_LIST=(window.QUESTION_ALL||[]).filter(x=>(!d||x.difficulty===d)&&(!q||normSearch([x.id,x.question,x.knowledge_point,kpName(x.knowledge_point),x.answer,diffText(x.difficulty)].join(' ')).includes(q)));renderQuestionTable(window.QUESTION_LIST)}
function filterKpOptions(v){let q=normSearch(v);let box=document.getElementById('kpOptions');box.innerHTML=(KPS||[]).filter(k=>!q||normSearch(k+' '+kpName(k)).includes(q)).slice(0,80).map(k=>`<option value="${esc(k)}"></option>`).join('')}function openQuestionEditor(id){let q=(window.QUESTION_ALL||[]).find(x=>String(x.id)===String(id));qTitle.textContent=q?'编辑题目':'添加题目';qId.value=q?q.id:'';qText.value=q?q.question||'':'';qKp.value=q?q.knowledge_point||'':'';qDifficulty.value=q?q.difficulty||'medium':'medium';qExplain.value=q?q.explanation||'';optionEditor.innerHTML=['A','B','C','D'].map(l=>`<div style="display:grid;grid-template-columns:54px 1fr 70px;gap:8px;align-items:center;margin:8px 0"><label><input type="checkbox" id="use${l}"> ${l}</label><input id="opt${l}" placeholder="${l} 选项内容"><label><input type="checkbox" id="ans${l}"> 答案</label></div>`).join('');['A','B','C','D'].forEach((l,i)=>{let opt=(q&&q.options&&q.options[i])?String(q.options[i]).replace(/^[A-D][\.\、\s]*/,''):'';document.getElementById('use'+l).checked=!!opt;document.getElementById('opt'+l).value=opt;document.getElementById('ans'+l).checked=q?String(q.answer||'').split(/[,，、\s]+/).includes(l):false});filterKpOptions(qKp.value);questionModal.classList.add('open')}async function saveQuestion(){let options=[],answers=[];['A','B','C','D'].forEach(l=>{let use=document.getElementById('use'+l).checked,txt=document.getElementById('opt'+l).value.trim();if(use&&txt)options.push(l+'. '+txt);if(document.getElementById('ans'+l).checked)answers.push(l)});if(!qText.value.trim()||!qKp.value.trim()||!answers.length){alert('请填写题目、知识点并至少选择一个答案');return}let payload={question_id:qId.value,question:qText.value.trim(),knowledge_point:qKp.value.trim(),difficulty:qDifficulty.value,options,answer:answers.join(','),explanation:qExplain.value.trim()};let d=await fetch(qId.value?'/teacher/question/update':'/teacher/question/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)}).then(r=>r.json());alert(d.success?'保存成功':(d.error||'保存失败'));if(d.success){questionModal.classList.remove('open');questionBank()}}async function deleteQuestion(id){if(!confirm('确认删除这道题吗？'))return;let d=await fetch('/teacher/question/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question_id:id})}).then(r=>r.json());alert(d.success?'删除成功':(d.error||'删除失败'));if(d.success)questionBank()}
function graph(){let opts=(KPS||[]).map(k=>`<option value="${esc(k)}"></option>`).join('');app.innerHTML=`<div class="card"><h2>公共知识图谱关系</h2><p class="muted">输入关键词搜索节点名称，纯序号节点已过滤。</p><div class="toolbar"><input id="fromK" list="graphKps" oninput="filterGraphKps(this.value)" placeholder="搜索起点知识点"><select id="relK"><option>相关</option><option>包含</option><option>先修</option></select><input id="toK" list="graphKps" oninput="filterGraphKps(this.value)" placeholder="搜索终点知识点"><button class="btn" onclick="addKg()">添加关系</button></div><datalist id="graphKps">${opts}</datalist></div>`}function filterGraphKps(v){let q=normSearch(v),box=document.getElementById('graphKps');box.innerHTML=(KPS||[]).filter(k=>!q||normSearch(k+' '+kpName(k)).includes(q)).slice(0,80).map(k=>`<option value="${esc(k)}"></option>`).join('')}async function addKg(){let d=await fetch('/teacher/public-graph/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({from:fromK.value,to:toK.value,rel:relK.value})}).then(r=>r.json());alert(d.success?'添加成功':(d.error||'添加失败'))}
function openAddStudent(){editStudentId.value='';studentNum.value='';studentName.value='';studentModalTitle.textContent='添加学生';studentModal.classList.add('open')}
function openEditStudent(id,num,name){editStudentId.value=id;studentNum.value=num;studentName.value=name;studentModalTitle.textContent='编辑学生';studentModal.classList.add('open')}
function closeStudentModal(){studentModal.classList.remove('open')}
async function saveStudent(){let url=editStudentId.value?'/teacher/student/edit':'/teacher/student/add';let body={student_id:editStudentId.value,student_num:studentNum.value.trim(),student_name:studentName.value.trim()};if(!body.student_num||!body.student_name){alert('请填写学号和姓名');return}let d=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json());alert(d.success?'保存成功':(d.error||'保存失败'));if(d.success){closeStudentModal();await loadData()}}
async function deleteStudent(id){if(!confirm('确认删除该学生吗？相关学习记录会一起清理。'))return;let d=await fetch('/teacher/student/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({student_id:id})}).then(r=>r.json());alert(d.success?'删除成功':(d.error||'删除失败'));if(d.success)await loadData()}
loadData();
</script></body></html>
    """
    return render_template_string(html, teacher_name=session.get("user_name", "教师"), initial_tab=initial_tab, page_title=page_title)

def teacher_students_new():
    return render_teacher_workspace("profiles", "学生画像")

def teacher_view_student_new():
    if session.get("role") != "teacher":
        return redirect(url_for("login"))
    sid = request.form.get("student_id") or request.args.get("sid") or ""
    return redirect("/teacher/students?sid={}".format(sid))

app.view_functions["teacher_students"] = teacher_students_new
app.view_functions["teacher_view_student"] = teacher_view_student_new

STUDENT_FLOW_HTML = r"""
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ page_title }} - 操作系统</title><script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#111827;font-family:"Microsoft YaHei",Arial,sans-serif}.layout{display:grid;grid-template-columns:216px 1fr;min-height:100vh}.side{background:#fff;border-right:1px solid #e5e7eb;padding:22px 0;position:sticky;top:0;height:100vh}.brand{padding:0 24px 24px;font-size:20px;font-weight:800}.nav a{display:block;padding:13px 28px;color:#4b5563;text-decoration:none;border-left:3px solid transparent}.nav a.active,.nav a:hover{background:#eef4ff;color:#2563eb;border-left-color:#60a5fa}.logout{position:absolute;left:20px;right:20px;bottom:20px}.logout a{display:block;text-align:center;padding:10px;border-radius:6px;background:#eef4ff;color:#2563eb;text-decoration:none;font-weight:700}.top{height:64px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 34px}.top h1{margin:0;font-size:22px}.content{padding:28px 36px;max-width:1500px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}.stat,.res,.res-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px}.stat b{display:block;font-size:30px;margin-top:8px}.muted{color:#64748b;font-size:14px;line-height:1.7}.btn{border:0;background:#2563eb;color:#fff;border-radius:6px;padding:8px 13px;text-decoration:none;cursor:pointer;display:inline-block}.btn.light{background:#eef4ff;color:#2563eb;border:1px solid #dbeafe}.btn.green{background:#16a34a}.tag{font-size:12px;border-radius:999px;background:#eef2ff;color:#3730a3;padding:4px 8px;margin:3px;display:inline-block}.tag.ok{background:#ecfdf5;color:#166534}.tag.warn{background:#fff7ed;color:#9a3412}.tag.bad{background:#fee2e2;color:#991b1b}.progress{height:10px;background:#e5e7eb;border-radius:99px;overflow:hidden;width:320px}.bar{height:100%;background:#22c55e}.bar.warn{background:#f59e0b}.bar.bad{background:#ef4444}.path-step{display:grid;grid-template-columns:38px 1fr;gap:14px;border-top:1px solid #eef2f7;padding:18px 0}.no{width:30px;height:30px;border-radius:50%;background:#2563eb;color:#fff;display:grid;place-items:center;font-weight:800}.res-list,.res-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;border-top:1px solid #eef2f7;padding:12px 0}.chapter{border:1px solid #e5e7eb;border-radius:8px;margin:10px 0;overflow:hidden}.chapter summary{background:#f8fafc;padding:14px 16px;cursor:pointer;font-weight:700}.section{border-top:1px solid #eef2f7}.section summary{background:#fff;padding:12px 20px;color:#475569}.kp-row{display:grid;grid-template-columns:minmax(220px,1fr) 88px 340px;gap:14px;align-items:center;border-top:1px solid #eef2f7;padding:12px 22px}.empty{padding:34px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px}.search,input,select,textarea{border:1px solid #cbd5e1;border-radius:6px;background:#fff;padding:9px 11px}.search{min-width:280px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}.post{border-top:1px solid #eef2f7;padding:14px 0;cursor:pointer}.post-head{display:flex;justify-content:space-between;gap:12px}.comment{border-top:1px solid #eef2f7;padding:10px 0}.record-timeline{display:grid;gap:10px}.record-card{display:grid;grid-template-columns:80px minmax(0,1fr) 140px;gap:12px;align-items:center;border-top:1px solid #eef2f7;padding:12px 0}.graph-detail{min-width:0}.graph-detail .progress{width:100%;min-width:0}@media(max-width:900px){.layout{grid-template-columns:1fr}.side{height:auto;position:relative}.logout{position:relative}.content{padding:18px}.kp-row,.path-step,.record-card{grid-template-columns:1fr}.progress{width:100%}}
</style></head><body><div class="layout"><aside class="side"><div class="brand">操作系统</div><nav class="nav"><a href="/student/dashboard" class="{% if active_page=='dashboard' %}active{% endif %}">首页</a><a href="/student/path" class="{% if active_page=='path' %}active{% endif %}">智能学习路径</a><a href="/student/resources" class="{% if active_page=='resources' %}active{% endif %}">学习资源库</a><a href="/student/mastery" class="{% if active_page=='mastery' %}active{% endif %}">知识点掌握度</a><a href="/student/graph" class="{% if active_page=='graph' %}active{% endif %}">知识图谱</a><a href="/student/discuss" class="{% if active_page=='discuss' %}active{% endif %}">问题讨论</a><a href="/student/records" class="{% if active_page=='records' %}active{% endif %}">学习记录</a></nav><div class="logout"><a href="/logout">退出登录</a></div></aside><main><header class="top"><h1>{{ page_title }}</h1><div>{{ student_name }}</div></header><section class="content" id="app"></section></main></div>
<script>
var PAGE="{{ active_page }}",app=document.getElementById('app'),TARGET=new URLSearchParams(location.search).get('target_kp')||'';
var Z={path:'智能学习路径',resources:'学习资源库',mastery:'知识点掌握度',graph:'知识图谱',discuss:'问题讨论',records:'学习记录',video:'视频',doc:'文档',exercise:'习题',resource:'资源',weak:'薄弱',severe:'严重薄弱',good:'良好',mastered:'已掌握',doing:'进行中',unlearned:'未学习',normal:'普通',easy:'简单',medium:'中等',hard:'困难'};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function kpName(s){return String(s==null?'':s).replace(/^\s*\d+(?:\.\d+)+\s*/,'')||String(s==null?'':s)}
async function getJson(u){try{var r=await fetch(u);return await r.json()}catch(e){return {success:false,learning_path:[],fallback_path:[],resources:[],chapters:[],records:[],groups:[],posts:[],comments:[],nodes:[],edges:[],stats:{}}}}
function cleanText(s){s=String(s==null?'':s);if(s.indexOf('严重')>=0)return Z.severe;if(s.indexOf('薄弱')>=0)return Z.weak;if(s.indexOf('已')>=0&&s.indexOf('掌')>=0)return Z.mastered;if(s.indexOf('良')>=0)return Z.good;if(s.indexOf('进')>=0)return Z.doing;if(s==='easy')return Z.easy;if(s==='medium')return Z.medium;if(s==='hard')return Z.hard;return s}
function normType(t){t=cleanText(t);return t===Z.video||t===Z.doc||t===Z.exercise?t:(String(t).endsWith('mp4')?Z.video:Z.doc)}function diffText(v){return cleanText(v||Z.normal)}function statusClass(s){s=cleanText(s);return s===Z.weak||s===Z.severe?'bad':(s===Z.doing?'warn':'ok')}function bar(v,s){return '<div class="progress"><div class="bar '+statusClass(s)+'" style="width:'+Math.max(2,Math.min(100,(+v||0)*100))+'%"></div></div>'}function action(r){return normType(r.type)===Z.video?'/student/watch/'+encodeURIComponent(r.name||r.title||''):'/student/view/'+encodeURIComponent(r.name||r.title||'')}
function displayKp(s){s=cleanText(s);if(/^\d+$/.test(s))return '第'+s+'章相关知识点';return kpName(s)}
function codeOf(n){var m=String(n.id||n.label||'').match(/^(\d+(?:\.\d+)*)/);return m?m[1]:''}function wrapLabel(raw,chunk){raw=String(raw||'');chunk=chunk||6;var a=raw.match(new RegExp('.{1,'+chunk+'}','g'))||[raw];return a.join('\\n')}
function buildLayeredGraph(rawNodes,rawEdges){var map=new Map(),edges=[];function add(n){if(!map.has(n.id))map.set(n.id,n);return map.get(n.id)}add({id:'root',label:'操作系统',drawLabel:'操作系统',level:-1,shape:'diamond',size:42,fontSize:18,mastery:1,levelName:'课程'});rawNodes.forEach(function(n){var code=codeOf(n),parts=code.split('.').filter(Boolean);if(parts.length){var ch='chapter-'+parts[0];add({id:ch,label:'第'+parts[0]+'章',drawLabel:'第'+parts[0]+'章',level:0,shape:'hexagon',size:38,fontSize:18,mastery:n.mastery||0,levelName:'章节'});edges.push({from:'root',to:ch,type:'包含'});if(parts.length>=2){var sec=parts[0]+'.'+parts[1];var secNode=rawNodes.find(function(x){return codeOf(x)===sec});add({id:sec,label:displayKp(secNode&&secNode.label||secNode&&secNode.id||sec),drawLabel:wrapLabel(displayKp(secNode&&secNode.label||secNode&&secNode.id||sec),5),level:1,shape:'box',size:24,fontSize:14,mastery:(secNode&&secNode.mastery)||n.mastery||0,total_questions:(secNode&&secNode.total_questions)||0,correct_questions:(secNode&&secNode.correct_questions)||0,levelName:'大节'});edges.push({from:ch,to:sec,type:'包含'});if(parts.length>=3){add({id:n.id,label:n.label||n.id,drawLabel:wrapLabel(displayKp(n.label||n.id),5),level:2,shape:'circle',size:20,fontSize:13,mastery:n.mastery||0,total_questions:n.total_questions||0,correct_questions:n.correct_questions||0,levelName:'知识点'});edges.push({from:sec,to:n.id,type:'包含'})}}}else add({id:n.id,label:n.label||n.id,drawLabel:wrapLabel(displayKp(n.label||n.id),5),level:2,shape:'circle',size:20,fontSize:13,mastery:n.mastery||0,levelName:'知识点'})});(rawEdges||[]).forEach(function(e){edges.push({from:e.from,to:e.to,type:cleanText(e.type||'相关')})});var uniq=[],seen=new Set();edges.forEach(function(e){var k=e.from+'>'+e.to+'>'+e.type;if(e.from!==e.to&&!seen.has(k)&&map.has(e.from)&&map.has(e.to)){seen.add(k);uniq.push(e)}});return {nodes:Array.from(map.values()),edges:uniq}}
async function dashboard(){var d=await getJson('/student/dashboard/data'),r=await getJson('/student/resources/data'),m=await getJson('/student/messages'),st=d.stats||{},msgs=(m.messages||[]).slice(0,3);app.innerHTML='<div class="grid"><a class="stat" href="/student/mastery"><span>已掌握</span><b>'+(st.mastered||0)+'</b><span class="muted">薄弱 '+(st.weak||0)+' / 严重 '+(st.severe||0)+'</span></a><a class="stat" href="/student/path"><span>智能学习路径</span><b>开始</b><span class="muted">根据薄弱点推荐</span></a><a class="stat" href="/student/resources"><span>学习资源库</span><b>'+((r.resources||[]).length)+'</b><span class="muted">视频 / 文档 / 习题</span></a><a class="stat" href="/student/graph"><span>知识图谱</span><b>查看</b><span class="muted">单击节点看掌握度</span></a></div><div class="card"><h2>今日学习建议</h2><p class="muted">'+esc(d.latest_message||'优先完成智能学习路径中排在前面的薄弱知识点，并查看对应资源。')+'</p><a class="btn" href="/student/path">进入学习路径</a></div><div class="card"><h2>最新消息</h2>'+(msgs.map(function(x){return '<div class="row"><div><b>'+esc(x.type||'消息')+'</b><div class="muted">'+esc(x.body||'')+'</div></div><span class="muted">'+esc(x.time||'')+'</span></div>'}).join('')||'<div class="empty">暂无消息</div>')+'</div>'}
async function pathPage(){var d=await getJson('/student/path/data'+(TARGET?'?target_kp='+encodeURIComponent(TARGET):'')),steps=(d.learning_path&&d.learning_path.length?d.learning_path:(d.fallback_path||[]));steps=steps.filter(function(st){return st&&st.name&&!/^(视频|文档|习题|资源)$/.test(String(st.name))});app.innerHTML='<div class="card"><h2>'+Z.path+'</h2><p class="muted">目标：'+esc(displayKp(d.target_kp||TARGET||(steps[0]&&steps[0].name)||''))+'。路径会按薄弱程度、先修关系和资源匹配度排序。</p></div><div class="card">'+(steps.map(function(st,i){var rs=st.resources||[],score=Number(st.score||st.mastery||0),status=cleanText(st.status||'待学习');return '<div class="path-step"><div class="no">'+(i+1)+'</div><div><b>'+esc(displayKp(st.name||st.title||st.kp_id))+'</b><div><span class="tag '+statusClass(status)+'">'+esc(status)+'</span><span class="tag">掌握度 '+Math.round(score*100)+'%</span></div>'+bar(score,status)+'<p class="muted">'+esc(cleanText(st.reason||''))+'</p><div class="res-list">'+rs.map(function(r){return '<div class="res"><b>'+esc(r.title||r.name)+'</b><p><span class="tag">'+esc(normType(r.type))+'</span><span class="tag">'+esc(diffText(r.difficulty))+'</span></p><a class="btn light" href="'+action(r)+'">学习</a> <button class="btn green" disabled>完成</button></div>'}).join('')+'</div></div></div>'}).join('')||'<div class="empty">暂无路径数据</div>')+'</div>'}
async function resourcesPage(){var d=await getJson('/student/resources/data'),all=d.resources||[];app.innerHTML='<div class="card"><h2>'+Z.resources+'</h2><input class="search" id="q" placeholder="搜索资源、知识点、章节" oninput="renderResources()"></div><div id="resResults"></div>';window.renderResources=function(){var q=(document.getElementById('q').value||'').toLowerCase(),list=all.filter(function(r){return [r.name,r.title,r.knowledge_point,r.chapter_label,r.section_label,normType(r.type)].join(' ').toLowerCase().indexOf(q)>=0}),groups={};list.forEach(function(r){var ch=r.chapter_label||'未分类',sec=r.section_label||'未分类';groups[ch]=groups[ch]||{};groups[ch][sec]=groups[ch][sec]||[];groups[ch][sec].push(r)});document.getElementById('resResults').innerHTML=Object.keys(groups).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})}).map(function(ch,i){var secs=Object.keys(groups[ch]).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})});return '<details class="chapter" '+(i===0?'open':'')+'><summary>'+esc(ch)+' · '+secs.reduce(function(n,s){return n+groups[ch][s].length},0)+' 个资源</summary>'+secs.map(function(sec){return '<details open class="section"><summary>'+esc(sec)+' · '+groups[ch][sec].length+'</summary><div class="res-grid" style="padding:12px">'+groups[ch][sec].map(function(r){return '<div class="res-card"><b>'+esc(r.title||r.name)+'</b><p><span class="tag">'+esc(normType(r.type))+'</span><span class="tag">'+esc(diffText(r.difficulty))+'</span></p><p class="muted">'+esc(displayKp(r.knowledge_point)||'')+'</p><a class="btn light" href="'+action(r)+'">在线查看</a> <a class="btn light" href="/download/'+encodeURIComponent(r.name||'')+'">下载</a></div>'}).join('')+'</div></details>'}).join('')+'</details>'}).join('')||'<div class="empty">暂无资源</div>'};renderResources()}
async function mastery(){var d=await getJson('/student/mastery/data'),chs=d.chapters||[];app.innerHTML='<div class="card"><h2>'+Z.mastery+'</h2>'+(chs.map(function(ch){var points=ch.knowledge_points||[],secs={};points.forEach(function(k){var code=String(k.kp_id||k.name||'').match(/^(\d+\.\d+)/);var sec=code?code[1]:'未分节';secs[sec]=secs[sec]||[];secs[sec].push(k)});return '<details class="chapter" open><summary>'+esc(ch.title||('第'+ch.chapter+'章'))+' · '+points.length+' 个知识点</summary>'+Object.keys(secs).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})}).map(function(sec){return '<details class="section" open><summary>'+esc(sec)+' · '+secs[sec].length+'</summary>'+secs[sec].map(function(k){var status=cleanText(k.status||''),score=Number(k.score||0);return '<div class="kp-row"><div><b>'+esc(displayKp(k.full_name||k.name||k.kp_id))+'</b><div class="muted">'+esc(status)+'</div></div><b>'+Math.round(score*100)+'%</b>'+bar(score,status)+'</div>'}).join('')+'</details>'}).join('')+'</details>'}).join('')||'<div class="empty">暂无掌握度数据</div>')+'</div>'}
async function records(){var d=await getJson('/student/records/data'),s=d.summary||{},groups=d.groups||[];app.innerHTML='<div class="grid"><div class="stat"><span>视频学习</span><b>'+(s.video||0)+'</b></div><div class="stat"><span>文档学习</span><b>'+(s.document||0)+'</b></div><div class="stat"><span>本周记录</span><b>'+(s.week||0)+'</b></div><div class="stat"><span>总记录</span><b>'+(s.total||0)+'</b></div></div><div class="card"><h2>'+Z.records+'</h2><div class="record-timeline">'+(groups.map(function(g){return '<details class="chapter" open><summary>'+esc(g.date)+' · '+g.items.length+' 条</summary>'+g.items.map(function(r){return '<div class="record-card"><span class="tag">'+esc(normType(r.type))+'</span><div><b>'+esc(r.name)+'</b><div class="muted">'+esc(displayKp(r.knowledge_point)||'未绑定知识点')+'</div></div><div class="muted">'+esc(r.time||'')+'</div></div>'}).join('')+'</details>'}).join('')||'<div class="empty">暂无学习记录</div>')+'</div></div>'}
async function discuss(){var d=await getJson('/student/discuss/list');app.innerHTML='<div class="card"><h2>'+Z.discuss+'</h2><div class="toolbar"><input id="topicTitle" class="search" placeholder="问题标题"><button class="btn" onclick="postTopic()">发布</button></div><textarea id="topicBody" style="width:100%" rows="3" placeholder="描述你的问题、卡点或学习经验"></textarea></div><div class="card">'+((d.posts||[]).map(function(p){return '<div class="post" onclick="openPost(&quot;'+esc(p.id)+'&quot;)"><div class="post-head"><b>'+esc(p.title)+'</b><span class="tag">'+esc(cleanText(p.status||''))+'</span></div><div class="muted">'+esc(p.author)+' · '+esc(p.time)+' · '+(p.comment_count||0)+' 条回复</div><p>'+esc(p.body||'')+'</p></div>'}).join('')||'<div class="empty">暂无讨论</div>')+'</div><div class="card" id="postDetail"><div class="muted">点击讨论查看详情和回复。</div></div>'}
async function postTopic(){if(!topicTitle.value.trim())return alert('请填写标题');let d=await fetch('/student/discuss/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:topicTitle.value.trim(),body:topicBody.value.trim()})}).then(r=>r.json());alert(d.success?'发布成功':(d.error||'发布失败'));if(d.success)discuss()}
async function openPost(id){let d=await getJson('/student/discuss/detail/'+encodeURIComponent(id)),p=d.post||{};postDetail.innerHTML='<h2>'+esc(p.title)+'</h2><p>'+esc(p.body||'')+'</p><div class="muted">'+esc(p.author||'')+' · '+esc(p.time||'')+'</div><h3>回复</h3>'+((d.comments||[]).map(function(c){return '<div class="comment"><b>'+esc(c.author)+'</b><p>'+esc(c.body)+'</p><div class="muted">'+esc(c.time)+'</div></div>'}).join('')||'<div class="muted">暂无回复</div>')+'<textarea id="commentBody" style="width:100%" rows="3" placeholder="写下回复"></textarea><button class="btn" onclick="commentPost(\\''+id+'\\')">提交回复</button>'}
async function commentPost(id){let body=document.getElementById('commentBody').value.trim();if(!body)return alert('请填写回复');let d=await fetch('/student/discuss/comment/'+encodeURIComponent(id),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({body:body})}).then(r=>r.json());alert(d.success?'回复成功':(d.error||'回复失败'));if(d.success)openPost(id)}
async function graphPage(){var d=await getJson('/student/flow-graph/data'),built=buildLayeredGraph(d.nodes||[],d.edges||[]),nodes=built.nodes,edges=built.edges;app.innerHTML='<div class="card"><h2>'+Z.graph+'</h2><div class="muted"><b>颜色 = 学习状态：</b><span class="tag ok">已掌握>=80%</span><span class="tag">良好>=60%</span><span class="tag warn">进行中>=40%</span><span class="tag bad">薄弱&lt;40%</span><span class="tag">未学习</span><b style="margin-left:12px">边：</b>包含 / 相关 / 先修</div><div style="display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px;margin-top:14px"><div style="position:relative"><div id="mynetwork" style="height:720px;border:1px solid #e5e7eb;background:#fafafa"></div><div style="position:absolute;right:18px;top:18px;width:62px;background:#fff;border:1px solid #dbe3ef;border-radius:14px;box-shadow:0 8px 24px rgba(15,23,42,.12);padding:10px;display:grid;gap:6px;place-items:center"><button class="btn light" style="width:40px;height:40px;padding:0" onclick="zoomGraph(.03)">+</button><input id="graphZoom" type="range" min="0" max="100" step="1" value="26" oninput="setGraphZoom(this.value)" style="writing-mode:vertical-lr;direction:rtl;-webkit-appearance:slider-vertical;appearance:slider-vertical;width:40px;height:250px;margin:0;touch-action:none"><button class="btn light" style="width:40px;height:40px;padding:0" onclick="zoomGraph(-.03)">-</button></div></div><div id="nodeDetail" class="res-card graph-detail"><b>节点详情</b><p class="muted">单击节点查看掌握度。</p></div></div></div>';if(!window.vis){document.getElementById('mynetwork').innerHTML='<div class="empty">vis load failed</div>';return}function color(m){return m>=.8?{background:'#d4f0dc',border:'#a8ddb8'}:m>=.6?{background:'#dbeafe',border:'#93c5fd'}:m>=.4?{background:'#ffedd5',border:'#fdba74'}:m>0?{background:'#fee2e2',border:'#fca5a5'}:{background:'#eceff1',border:'#cfd8dc'}}var visNodes=new vis.DataSet(nodes.map(function(n){return {id:n.id,label:n.drawLabel||displayKp(n.label||n.id),shape:n.shape,size:n.size,color:n.id==='root'?{background:'#1f2937',border:'#111827'}:color(n.mastery||0),font:{size:n.fontSize,face:'Microsoft YaHei',color:n.id==='root'?'#fff':'#111827',bold:true,multi:true},borderWidth:n.level<=0?4:3,mass:n.level<=0?6:(n.level===1?3:1),widthConstraint:n.shape==='box'?{minimum:120,maximum:150}:undefined,heightConstraint:n.shape==='box'?{minimum:60}:undefined}}));var visEdges=new vis.DataSet(edges.map(function(e,i){return {id:i,from:e.from,to:e.to,arrows:'to',color:{color:e.type==='先修'?'#9b59b6':(e.type==='相关'?'#f59e0b':'#94a3b8')},dashes:e.type!=='包含',width:e.type==='包含'?2.2:1.7,smooth:{type:'dynamic'}}}));var network=new vis.Network(document.getElementById('mynetwork'),{nodes:visNodes,edges:visEdges},{physics:{solver:'forceAtlas2Based',forceAtlas2Based:{gravitationalConstant:-240,centralGravity:.018,springLength:170,springConstant:.04,avoidOverlap:1},stabilization:{iterations:600}},interaction:{zoomView:true,dragView:true,dragNodes:true}});window.graphNetwork=network;window.graphZoomMin=.24;window.graphZoomMax=.55;window.graphScale=.32;network.once('stabilizationIterationsDone',function(){network.stopSimulation();applyGraphZoom(.32,true)});network.on('click',function(p){var id=p.nodes&&p.nodes[0],n=nodes.find(function(x){return x.id===id});if(!n)return;var m=Number(n.mastery||0),state=m>=.8?Z.mastered:m>=.6?Z.good:m>=.4?Z.doing:m>0?Z.weak:Z.unlearned;document.getElementById('nodeDetail').innerHTML='<b>'+esc(displayKp(n.label||n.id))+'</b><p><span class="tag '+statusClass(state)+'">'+state+'</span><span class="tag">掌握度 '+Math.round(m*100)+'%</span></p>'+bar(m,state)+'<p class="muted">'+esc(n.levelName||'')+'</p>'})}
function graphSliderToScale(v){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55,t=Math.max(0,Math.min(100,parseFloat(v)||0))/100;return min+(max-min)*t}function graphScaleToSlider(s){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55;return Math.round((Math.max(min,Math.min(max,parseFloat(s)||min))-min)/(max-min)*100)}function applyGraphZoom(scale,animate){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55;window.graphScale=Math.max(min,Math.min(max,parseFloat(scale)||.32));if(window.graphNetwork)window.graphNetwork.moveTo({position:window.graphNetwork.getViewPosition(),scale:window.graphScale,animation:animate?{duration:120,easingFunction:'easeInOutQuad'}:{duration:0}});var z=document.getElementById('graphZoom');if(z)z.value=graphScaleToSlider(window.graphScale)}function setGraphZoom(v){applyGraphZoom(graphSliderToScale(v),false)}function zoomGraph(delta){applyGraphZoom((window.graphScale||.32)+delta,true)}async function graphBuilder(){graphPage()}
if(PAGE==='dashboard')dashboard();if(PAGE==='path')pathPage();if(PAGE==='resources')resourcesPage();if(PAGE==='mastery')mastery();if(PAGE==='records')records();if(PAGE==='discuss')discuss();if(PAGE==='my_discuss')discuss();if(PAGE==='graph')graphPage();if(PAGE==='graph_builder')graphBuilder();
</script></body></html>
"""

def flow_status(score):
    score = float(score or 0)
    if score <= 0:
        return "未学习"
    if score < 0.4:
        return "薄弱"
    if score < 0.7:
        return "进行中"
    if score < 0.85:
        return "良好"
    return "已掌握"

def chapter_title_from_code(chapter):
    return "第{}章".format(chapter) if str(chapter).isdigit() else str(chapter or "未分类")

def natural_sort_key(value):
    parts = re.split(r"(\d+)", str(value or ""))
    return [int(part) if part.isdigit() else part for part in parts]

def build_mastery_chapters(points):
    chapters = {}
    for item in points:
        chapter = str(item.get("chapter") or (flow_kp_code(item.get("kp_id", "")).split(".")[0] if flow_kp_code(item.get("kp_id", "")) else "未分类"))
        chapters.setdefault(chapter, {"chapter": chapter, "title": chapter_title_from_code(chapter), "knowledge_points": []})
        chapters[chapter]["knowledge_points"].append(item)
    for ch in chapters.values():
        ch["knowledge_points"].sort(key=lambda p: natural_sort_key(p.get("kp_id") or p.get("name") or ""))
    return [chapters[k] for k in sorted(chapters.keys(), key=natural_sort_key)]

def fallback_flow_mastery_data():
    catalog = knowledge_point_catalog()
    points = []
    for entry in catalog:
        name = entry.get("name") if isinstance(entry, dict) else str(entry or "")
        code = flow_kp_code(name)
        if not code or code.count(".") < 2 or re.fullmatch(r"\d+(?:\.\d+){0,2}", name.strip()):
            continue
        item = {
            "kp_id": name,
            "name": display_kp_name(name),
            "full_name": name,
            "chapter": code.split(".")[0],
            "score": 0,
            "base_score": 0,
            "mastery_formula": "题目练习、正确率、学习资源和讨论参与综合计算",
            "components": {"exercise": 0, "accuracy": 0, "volume": 0, "video": 0, "resource": 0, "discussion": 0},
            "status": flow_status(0)
        }
        points.append(item)
    if not points:
        for code in ["1.1.1 基本概念", "1.1.2 计算机系统的视图", "2.1.1 进程的概念", "3.4.1 死锁的概念"]:
            item = {
                "kp_id": code, "name": display_kp_name(code), "full_name": code,
                "chapter": flow_kp_code(code).split(".")[0], "score": 0, "base_score": 0,
                "mastery_formula": "题目练习、正确率、学习资源和讨论参与综合计算",
                "components": {"exercise": 0, "accuracy": 0, "volume": 0, "video": 0, "resource": 0, "discussion": 0},
                "status": flow_status(0)
            }
            points.append(item)
    points.sort(key=lambda p: natural_sort_key(p["kp_id"]))
    return {"points": points, "chapters": build_mastery_chapters(points), "stats": {"total": len(points), "mastered": 0, "weak": 0, "severe": len(points)}, "offline": True}

def get_flow_mastery_data(user_id):
    if neo4j_temporarily_offline():
        return fallback_flow_mastery_data()
    try:
        with driver.session() as neo4j_session:
            rows = list(neo4j_session.run("""
            MATCH (k:Knowledge)
            WHERE k.name =~ '^\\d+(\\.\\d+){2}.*'
              AND NOT k.name =~ '^\\d+(\\.\\d+){0,2}\\s*$'
            OPTIONAL MATCH (:Student {id: $sid})-[m:MASTERED]->(k)
            RETURN k.name AS name, COALESCE(m.mastery, 0) AS score,
                   COALESCE(m.total_questions, 0) AS total_questions,
                   COALESCE(m.correct_questions, 0) AS correct_questions
            ORDER BY k.name
            """, sid=user_id))
    except Exception:
        mark_neo4j_offline()
        return fallback_flow_mastery_data()

    activity_scores = {}
    try:
        resources = get_flow_resources(user_id)
        name_to_code = {r["name"]: r["knowledge_point"] for r in resources}
        with driver.session() as neo4j_session:
            act_rows = neo4j_session.run("""
            MATCH (:Student {id:$sid})-[r:VIEWED|WATCHED]->(res)
            RETURN res.name AS name, type(r) AS rel_type,
                   coalesce(r.view_count,0) AS view_count,
                   coalesce(r.download_count,0) AS download_count,
                   coalesce(r.play_count,0) AS play_count
            """, sid=user_id)
            for ar in act_rows:
                code = name_to_code.get(ar["name"] or "")
                if not code:
                    continue
                bucket = activity_scores.setdefault(code, {"video": 0.0, "resource": 0.0, "discussion": 0.0})
                if ar["rel_type"] == "WATCHED":
                    bucket["video"] = max(bucket["video"], min(1.0, (ar["play_count"] or 1) / 3))
                else:
                    bucket["resource"] = max(bucket["resource"], min(1.0, ((ar["view_count"] or 0) + (ar["download_count"] or 0) * 2) / 4))
            solved_rows = neo4j_session.run("""
            MATCH (p:DiscussionPost {author:$author})
            WHERE coalesce(p.status, '') IN ['已解决', '解决', 'solved']
              AND p.knowledge_tag IS NOT NULL AND p.knowledge_tag <> ''
            RETURN p.knowledge_tag AS tag, count(p) AS c
            """, author=session.get("user_name", ""))
            for sr in solved_rows:
                tag = sr["tag"]
                bucket = activity_scores.setdefault(tag, {"video": 0.0, "resource": 0.0, "discussion": 0.0})
                bucket["discussion"] = max(bucket["discussion"], min(1.0, (sr["c"] or 0) / 2))
    except Exception:
        pass

    points = []
    seen = set()
    for row in rows:
        name = str(row["name"] or "").strip()
        code = flow_kp_code(name)
        if not code or code.count(".") < 2 or name in seen:
            continue
        seen.add(name)
        base_score = float(row["score"] or 0)
        total_q = int(row["total_questions"] or 0)
        correct_q = int(row["correct_questions"] or 0)
        if total_q > 0:
            accuracy = correct_q / total_q
            volume_score = min(1.0, total_q / 10)
            exercise_score = 0.6 * accuracy + 0.4 * volume_score
        else:
            accuracy = 0
            volume_score = 0
            exercise_score = base_score
        video_score = resource_score = discussion_score = 0.0
        for b_code, value in activity_scores.items():
            if b_code and (code.startswith(b_code) or b_code.startswith(code)):
                video_score = max(video_score, value.get("video", 0.0))
                resource_score = max(resource_score, value.get("resource", 0.0))
                discussion_score = max(discussion_score, value.get("discussion", 0.0))
        score = min(1.0, 0.70 * exercise_score + 0.12 * video_score + 0.08 * resource_score + 0.10 * discussion_score)
        points.append({
            "kp_id": name,
            "name": display_kp_name(name),
            "full_name": name,
            "chapter": code.split(".")[0],
            "score": round(score, 3),
            "base_score": round(base_score, 3),
            "mastery_formula": "题目练习70% + 视频12% + 资源8% + 讨论10%",
            "components": {"exercise": round(exercise_score, 3), "accuracy": round(accuracy, 3), "volume": round(volume_score, 3), "video": round(video_score, 3), "resource": round(resource_score, 3), "discussion": round(discussion_score, 3)},
            "status": flow_status(score)
        })
    if not points:
        return fallback_flow_mastery_data()
    points.sort(key=lambda p: natural_sort_key(p["kp_id"]))
    stats = {"total": len(points), "mastered": sum(1 for p in points if p["score"] >= 0.85), "weak": sum(1 for p in points if 0.4 <= p["score"] < 0.7), "severe": sum(1 for p in points if p["score"] < 0.4)}
    return {"points": points, "chapters": build_mastery_chapters(points), "stats": stats}

def get_knowledge_graph(student_id):
    data = get_flow_mastery_data(student_id)
    points = data.get("points", [])
    nodes = []
    node_ids = set()
    section_stats = {}
    for p in points:
        code = flow_kp_code(p.get("kp_id", ""))
        if not code:
            continue
        sec_code = ".".join(code.split(".")[:2])
        bucket = section_stats.setdefault(sec_code, {"total": 0, "score_sum": 0.0, "questions": 0, "correct": 0})
        bucket["total"] += 1
        bucket["score_sum"] += float(p.get("score") or 0)
        bucket["questions"] += int((p.get("components") or {}).get("volume", 0) * 10)
        node = {
            "id": p["kp_id"],
            "label": p.get("full_name") or p.get("name") or p["kp_id"],
            "mastery": p.get("score", 0),
            "total_questions": 0,
            "correct_questions": 0
        }
        nodes.append(node)
        node_ids.add(node["id"])
    for sec_code, info in section_stats.items():
        if sec_code in node_ids:
            continue
        nodes.append({
            "id": sec_code,
            "label": sec_code,
            "mastery": round(info["score_sum"] / info["total"], 3) if info["total"] else 0,
            "total_questions": info["questions"],
            "correct_questions": info["correct"]
        })
        node_ids.add(sec_code)
    edges = []
    try:
        if not neo4j_temporarily_offline():
            with driver.session() as neo4j_session:
                rel_rows = neo4j_session.run("""
                MATCH (a:Knowledge)-[r]->(b:Knowledge)
                WHERE (a.name STARTS WITH '1.' OR a.name STARTS WITH '2.' OR a.name STARTS WITH '3.')
                  AND (b.name STARTS WITH '1.' OR b.name STARTS WITH '2.' OR b.name STARTS WITH '3.')
                RETURN a.name AS from_name, b.name AS to_name, type(r) AS rel
                LIMIT 300
                """)
                for row in rel_rows:
                    f = row["from_name"]
                    t = row["to_name"]
                    if f in node_ids and t in node_ids:
                        rel = row["rel"] or "相关"
                        if "PREREQ" in rel.upper():
                            rel = "先修"
                        elif "CONTAIN" in rel.upper() or "HAS" in rel.upper():
                            rel = "包含"
                        else:
                            rel = "相关"
                        edges.append({"from": f, "to": t, "type": rel})
    except Exception:
        pass
    statistics = {n["id"]: {"mastery": n.get("mastery", 0), "total_questions": n.get("total_questions", 0), "correct_questions": n.get("correct_questions", 0)} for n in nodes}
    return {"nodes": nodes, "edges": edges, "statistics": statistics}

def student_records_data_new():
    if session.get("role") != "student":
        return jsonify({"success": False, "error": "未登录"})
    user_id = session.get("full_id")
    records = []
    try:
        if neo4j_temporarily_offline():
            raise RuntimeError("neo4j offline")
        with driver.session() as neo4j_session:
            rows = neo4j_session.run("""
            MATCH (:Student {id: $sid})-[r:VIEWED|WATCHED]->(res)
            RETURN res.name AS name, type(r) AS rel_type,
                   coalesce(r.last_viewed, r.last_downloaded, r.last_watched) AS t
            ORDER BY t DESC
            LIMIT 80
            """, sid=user_id)
            for row in rows:
                name = row["name"] or ""
                records.append({
                    "name": name,
                    "type": "视频" if row["rel_type"] == "WATCHED" or name.endswith(".mp4") else "文档",
                    "knowledge_point": flow_resource_code(name),
                    "time": str(row["t"]) if row["t"] else "",
                    "source": "已学习"
                })
    except Exception:
        records = []
    if not records:
        for idx, resource in enumerate(get_flow_resources(user_id)[:12]):
            records.append({
                "name": resource.get("title") or resource.get("name"),
                "type": resource.get("type") or ("视频" if str(resource.get("name", "")).endswith(".mp4") else "文档"),
                "knowledge_point": resource.get("knowledge_point") or flow_resource_code(resource.get("name", "")),
                "time": "",
                "source": "推荐待学习",
                "_idx": idx
            })
    normalized = []
    for idx, record in enumerate(records):
        display_dt = datetime.now() - timedelta(days=idx // 5, hours=(idx * 3) % 24, minutes=(idx * 7) % 60)
        normalized.append({
            **record,
            "type": "视频" if record.get("type") == "视频" else "文档",
            "time": record.get("time")[:16] if record.get("time") else display_dt.strftime("%H:%M"),
            "date": display_dt.strftime("%Y-%m-%d")
        })
    groups_map = {}
    for record in normalized:
        groups_map.setdefault(record["date"], []).append(record)
    groups = [{"date": key, "items": value} for key, value in sorted(groups_map.items(), reverse=True)]
    summary = {
        "total": len(normalized),
        "video": sum(1 for r in normalized if r["type"] == "视频"),
        "document": sum(1 for r in normalized if r["type"] == "文档"),
        "week": sum(1 for r in normalized if (datetime.now() - datetime.strptime(r["date"], "%Y-%m-%d")).days < 7)
    }
    return jsonify({"success": True, "records": normalized, "groups": groups, "summary": summary})

STUDENT_FLOW_HTML = r"""
<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ page_title }} - 操作系统</title><script src="https://cdn.jsdelivr.net/npm/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>
<style>
*{box-sizing:border-box}body{margin:0;background:#f3f5f8;color:#111827;font-family:"Microsoft YaHei",Arial,sans-serif}.layout{display:grid;grid-template-columns:216px 1fr;min-height:100vh}.side{background:#fff;border-right:1px solid #e5e7eb;padding:22px 0;position:sticky;top:0;height:100vh}.brand{padding:0 24px 24px;font-size:20px;font-weight:800}.nav a{display:block;padding:13px 28px;color:#4b5563;text-decoration:none;border-left:3px solid transparent}.nav a.active,.nav a:hover{background:#eef4ff;color:#2563eb;border-left-color:#60a5fa}.logout{position:absolute;left:20px;right:20px;bottom:20px}.logout a{display:block;text-align:center;padding:10px;border-radius:6px;background:#eef4ff;color:#2563eb;text-decoration:none;font-weight:700}.top{height:64px;background:#fff;border-bottom:1px solid #e5e7eb;display:flex;align-items:center;justify-content:space-between;padding:0 34px}.top h1{margin:0;font-size:22px}.content{padding:28px 36px;max-width:1500px}.card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:16px}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:14px}.stat,.res,.res-card{background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:14px}.stat b{display:block;font-size:30px;margin-top:8px}.muted{color:#64748b;font-size:14px;line-height:1.7}.btn{border:0;background:#2563eb;color:#fff;border-radius:6px;padding:8px 13px;text-decoration:none;cursor:pointer;display:inline-block}.btn.light{background:#eef4ff;color:#2563eb;border:1px solid #dbeafe}.btn.green{background:#16a34a}.tag{font-size:12px;border-radius:999px;background:#eef2ff;color:#3730a3;padding:4px 8px;margin:3px;display:inline-block}.tag.ok{background:#ecfdf5;color:#166534}.tag.warn{background:#fff7ed;color:#9a3412}.tag.bad{background:#fee2e2;color:#991b1b}.progress{height:10px;background:#e5e7eb;border-radius:99px;overflow:hidden;width:320px}.bar{height:100%;background:#22c55e}.bar.warn{background:#f59e0b}.bar.bad{background:#ef4444}.path-step{display:grid;grid-template-columns:38px 1fr;gap:14px;border-top:1px solid #eef2f7;padding:18px 0}.no{width:30px;height:30px;border-radius:50%;background:#2563eb;color:#fff;display:grid;place-items:center;font-weight:800}.res-list,.res-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;border-top:1px solid #eef2f7;padding:12px 0}.chapter{border:1px solid #e5e7eb;border-radius:8px;margin:10px 0;overflow:hidden}.chapter summary{background:#f8fafc;padding:14px 16px;cursor:pointer;font-weight:700}.section{border-top:1px solid #eef2f7}.section summary{background:#fff;padding:12px 20px;color:#475569}.kp-row{display:grid;grid-template-columns:minmax(220px,1fr) 88px 340px;gap:14px;align-items:center;border-top:1px solid #eef2f7;padding:12px 22px}.empty{padding:34px;text-align:center;color:#94a3b8;border:1px dashed #cbd5e1;border-radius:8px}.search,input,select,textarea{border:1px solid #cbd5e1;border-radius:6px;background:#fff;padding:9px 11px}.search{min-width:280px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}.post{border-top:1px solid #eef2f7;padding:14px 0;cursor:pointer}.post-head{display:flex;justify-content:space-between;gap:12px}.comment{border-top:1px solid #eef2f7;padding:10px 0}.record-timeline{display:grid;gap:10px}.record-card{display:grid;grid-template-columns:80px minmax(0,1fr) 140px;gap:12px;align-items:center;border-top:1px solid #eef2f7;padding:12px 0}.graph-detail{min-width:0}.graph-detail .progress{width:100%;min-width:0}@media(max-width:900px){.layout{grid-template-columns:1fr}.side{height:auto;position:relative}.logout{position:relative}.content{padding:18px}.kp-row,.path-step,.record-card{grid-template-columns:1fr}.progress{width:100%}}
</style></head><body><div class="layout"><aside class="side"><div class="brand">操作系统</div><nav class="nav"><a href="/student/dashboard" class="{% if active_page=='dashboard' %}active{% endif %}">首页</a><a href="/student/path" class="{% if active_page=='path' %}active{% endif %}">智能学习路径</a><a href="/student/resources" class="{% if active_page=='resources' %}active{% endif %}">学习资源库</a><a href="/student/mastery" class="{% if active_page=='mastery' %}active{% endif %}">知识点掌握度</a><a href="/student/graph" class="{% if active_page=='graph' %}active{% endif %}">知识图谱</a><a href="/student/discuss" class="{% if active_page=='discuss' %}active{% endif %}">问题讨论</a><a href="/student/records" class="{% if active_page=='records' %}active{% endif %}">学习记录</a></nav><div class="logout"><a href="/logout">退出登录</a></div></aside><main><header class="top"><h1>{{ page_title }}</h1><div>{{ student_name }}</div></header><section class="content" id="app"></section></main></div>
<script>
var PAGE="{{ active_page }}",app=document.getElementById('app'),TARGET=new URLSearchParams(location.search).get('target_kp')||'';
var Z={path:'智能学习路径',resources:'学习资源库',mastery:'知识点掌握度',graph:'知识图谱',discuss:'问题讨论',records:'学习记录',video:'视频',doc:'文档',exercise:'习题',resource:'资源',weak:'薄弱',severe:'薄弱',good:'良好',mastered:'已掌握',doing:'进行中',unlearned:'未学习',normal:'中等',easy:'简单',medium:'中等',hard:'困难'};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function kpName(s){return String(s==null?'':s).replace(/^\s*\d+(?:\.\d+)+\s*/,'')||String(s==null?'':s)}
async function getJson(u){try{var r=await fetch(u);return await r.json()}catch(e){return {success:false,learning_path:[],fallback_path:[],resources:[],chapters:[],records:[],groups:[],posts:[],comments:[],nodes:[],edges:[],stats:{}}}}
function cleanText(s){s=String(s==null?'':s);if(s==='easy')return Z.easy;if(s==='medium')return Z.medium;if(s==='hard')return Z.hard;return s}
function normType(t){t=cleanText(t);return t||Z.doc}function diffText(v){return cleanText(v||Z.normal)}function statusClass(s){s=cleanText(s);return s===Z.weak||s===Z.severe?'bad':(s===Z.doing?'warn':'ok')}function bar(v,s){return '<div class="progress"><div class="bar '+statusClass(s)+'" style="width:'+Math.max(2,Math.min(100,(+v||0)*100))+'%"></div></div>'}function action(r){return normType(r.type)===Z.video?'/student/watch/'+encodeURIComponent(r.name||r.title||''):'/student/view/'+encodeURIComponent(r.name||r.title||'')}function displayKp(s){s=cleanText(s);if(/^\d+$/.test(s))return '第'+s+'章相关知识点';return kpName(s)}
function codeOf(n){var m=String(n.id||n.label||'').match(/^(\d+(?:\.\d+)*)/);return m?m[1]:''}function wrapLabel(raw,chunk){raw=String(raw||'');chunk=chunk||6;var a=raw.match(new RegExp('.{1,'+chunk+'}','g'))||[raw];return a.join('\\n')}
function buildLayeredGraph(rawNodes,rawEdges){var map=new Map(),edges=[];function add(n){if(!map.has(n.id))map.set(n.id,n);return map.get(n.id)}add({id:'root',label:'操作系统',drawLabel:'操作系统',level:-1,shape:'diamond',size:42,fontSize:18,mastery:1,levelName:'课程'});rawNodes.forEach(function(n){var code=codeOf(n),parts=code.split('.').filter(Boolean);if(parts.length){var ch='chapter-'+parts[0];add({id:ch,label:'第'+parts[0]+'章',drawLabel:'第'+parts[0]+'章',level:0,shape:'hexagon',size:38,fontSize:18,mastery:n.mastery||0,levelName:'章节'});edges.push({from:'root',to:ch,type:'包含'});if(parts.length>=2){var sec=parts[0]+'.'+parts[1];var secNode=rawNodes.find(function(x){return codeOf(x)===sec});add({id:sec,label:displayKp(secNode&&secNode.label||secNode&&secNode.id||sec),drawLabel:wrapLabel(displayKp(secNode&&secNode.label||secNode&&secNode.id||sec),5),level:1,shape:'box',size:24,fontSize:14,mastery:(secNode&&secNode.mastery)||n.mastery||0,total_questions:(secNode&&secNode.total_questions)||0,correct_questions:(secNode&&secNode.correct_questions)||0,levelName:'大节'});edges.push({from:ch,to:sec,type:'包含'});if(parts.length>=3){add({id:n.id,label:n.label||n.id,drawLabel:wrapLabel(displayKp(n.label||n.id),5),level:2,shape:'circle',size:20,fontSize:13,mastery:n.mastery||0,total_questions:n.total_questions||0,correct_questions:n.correct_questions||0,levelName:'知识点'});edges.push({from:sec,to:n.id,type:'包含'})}}}else add({id:n.id,label:n.label||n.id,drawLabel:wrapLabel(displayKp(n.label||n.id),5),level:2,shape:'circle',size:20,fontSize:13,mastery:n.mastery||0,levelName:'知识点'})});(rawEdges||[]).forEach(function(e){edges.push({from:e.from,to:e.to,type:cleanText(e.type||'相关')})});var uniq=[],seen=new Set();edges.forEach(function(e){var k=e.from+'>'+e.to+'>'+e.type;if(e.from!==e.to&&!seen.has(k)&&map.has(e.from)&&map.has(e.to)){seen.add(k);uniq.push(e)}});return {nodes:Array.from(map.values()),edges:uniq}}
async function dashboard(){var d=await getJson('/student/dashboard/data'),r=await getJson('/student/resources/data'),m=await getJson('/student/messages'),st=d.stats||{},msgs=(m.messages||[]).slice(0,3);app.innerHTML='<div class="grid"><a class="stat" href="/student/mastery"><span>已掌握</span><b>'+(st.mastered||0)+'</b><span class="muted">薄弱 '+(st.weak||0)+' / 严重 '+(st.severe||0)+'</span></a><a class="stat" href="/student/path"><span>智能学习路径</span><b>开始</b><span class="muted">根据薄弱点推荐</span></a><a class="stat" href="/student/resources"><span>学习资源库</span><b>'+((r.resources||[]).length)+'</b><span class="muted">视频 / 文档 / 习题</span></a><a class="stat" href="/student/graph"><span>知识图谱</span><b>查看</b><span class="muted">单击节点看掌握度</span></a></div><div class="card"><h2>今日学习建议</h2><p class="muted">'+esc(d.latest_message||'优先完成智能学习路径中排在前面的薄弱知识点，并查看对应资源。')+'</p><a class="btn" href="/student/path">进入学习路径</a></div><div class="card"><h2>最新消息</h2>'+(msgs.map(function(x){return '<div class="row"><div><b>'+esc(x.type||'消息')+'</b><div class="muted">'+esc(x.body||'')+'</div></div><span class="muted">'+esc(x.time||'')+'</span></div>'}).join('')||'<div class="empty">暂无消息</div>')+'</div>'}
async function pathPage(){var d=await getJson('/student/path/data'+(TARGET?'?target_kp='+encodeURIComponent(TARGET):'')),steps=(d.learning_path&&d.learning_path.length?d.learning_path:(d.fallback_path||[]));steps=steps.filter(function(st){return st&&st.name&&!/^(视频|文档|习题|资源)$/.test(String(st.name))});app.innerHTML='<div class="card"><h2>'+Z.path+'</h2><p class="muted">目标：'+esc(displayKp(d.target_kp||TARGET||(steps[0]&&steps[0].name)||''))+'。路径会按薄弱程度、先修关系和资源匹配度排序。</p></div><div class="card">'+(steps.map(function(st,i){var rs=st.resources||[],score=Number(st.score||st.mastery||0),status=cleanText(st.status||'待学习');return '<div class="path-step"><div class="no">'+(i+1)+'</div><div><b>'+esc(displayKp(st.name||st.title||st.kp_id))+'</b><div><span class="tag '+statusClass(status)+'">'+esc(status)+'</span><span class="tag">掌握度 '+Math.round(score*100)+'%</span></div>'+bar(score,status)+'<p class="muted">'+esc(cleanText(st.reason||''))+'</p><div class="res-list">'+rs.map(function(r){return '<div class="res"><b>'+esc(r.title||r.name)+'</b><p><span class="tag">'+esc(normType(r.type))+'</span><span class="tag">'+esc(diffText(r.difficulty))+'</span></p><a class="btn light" href="'+action(r)+'">学习</a> <button class="btn green" disabled>完成</button></div>'}).join('')+'</div></div></div>'}).join('')||'<div class="empty">暂无路径数据</div>')+'</div>'}
async function resourcesPage(){var d=await getJson('/student/resources/data'),all=d.resources||[];app.innerHTML='<div class="card"><h2>'+Z.resources+'</h2><input class="search" id="q" placeholder="搜索资源、知识点、章节" oninput="renderResources()"></div><div id="resResults"></div>';window.renderResources=function(){var q=(document.getElementById('q').value||'').toLowerCase(),list=all.filter(function(r){return [r.name,r.title,r.knowledge_point,r.chapter_label,r.section_label,normType(r.type)].join(' ').toLowerCase().indexOf(q)>=0}),groups={};list.forEach(function(r){var ch=r.chapter_label||'未分类',sec=r.section_label||'未分类';groups[ch]=groups[ch]||{};groups[ch][sec]=groups[ch][sec]||[];groups[ch][sec].push(r)});document.getElementById('resResults').innerHTML=Object.keys(groups).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})}).map(function(ch,i){var secs=Object.keys(groups[ch]).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})});return '<details class="chapter" '+(i===0?'open':'')+'><summary>'+esc(ch)+' · '+secs.reduce(function(n,s){return n+groups[ch][s].length},0)+' 个资源</summary>'+secs.map(function(sec){return '<details open class="section"><summary>'+esc(sec)+' · '+groups[ch][sec].length+'</summary><div class="res-grid" style="padding:12px">'+groups[ch][sec].map(function(r){return '<div class="res-card"><b>'+esc(r.title||r.name)+'</b><p><span class="tag">'+esc(normType(r.type))+'</span><span class="tag">'+esc(diffText(r.difficulty))+'</span></p><p class="muted">'+esc(displayKp(r.knowledge_point)||'')+'</p><a class="btn light" href="'+action(r)+'">在线查看</a> <a class="btn light" href="/download/'+encodeURIComponent(r.name||'')+'">下载</a></div>'}).join('')+'</div></details>'}).join('')+'</details>'}).join('')||'<div class="empty">暂无资源</div>'};renderResources()}
async function mastery(){var d=await getJson('/student/mastery/data'),chs=d.chapters||[];app.innerHTML='<div class="card"><h2>'+Z.mastery+'</h2>'+(chs.map(function(ch){var points=ch.knowledge_points||[],secs={};points.forEach(function(k){var code=String(k.kp_id||k.name||'').match(/^(\d+\.\d+)/);var sec=code?code[1]:'未分节';secs[sec]=secs[sec]||[];secs[sec].push(k)});return '<details class="chapter" open><summary>'+esc(ch.title||('第'+ch.chapter+'章'))+' · '+points.length+' 个知识点</summary>'+Object.keys(secs).sort(function(a,b){return a.localeCompare(b,'zh-Hans',{numeric:true})}).map(function(sec){return '<details class="section" open><summary>'+esc(sec)+' · '+secs[sec].length+'</summary>'+secs[sec].map(function(k){var status=cleanText(k.status||''),score=Number(k.score||0);return '<div class="kp-row"><div><b>'+esc(displayKp(k.full_name||k.name||k.kp_id))+'</b><div class="muted">'+esc(status)+'</div></div><b>'+Math.round(score*100)+'%</b>'+bar(score,status)+'</div>'}).join('')+'</details>'}).join('')+'</details>'}).join('')||'<div class="empty">暂无掌握度数据</div>')+'</div>'}
async function records(){var d=await getJson('/student/records/data'),s=d.summary||{},groups=d.groups||[];app.innerHTML='<div class="grid"><div class="stat"><span>视频学习</span><b>'+(s.video||0)+'</b></div><div class="stat"><span>文档学习</span><b>'+(s.document||0)+'</b></div><div class="stat"><span>本周记录</span><b>'+(s.week||0)+'</b></div><div class="stat"><span>总记录</span><b>'+(s.total||0)+'</b></div></div><div class="card"><h2>'+Z.records+'</h2><div class="record-timeline">'+(groups.map(function(g){return '<details class="chapter" open><summary>'+esc(g.date)+' · '+g.items.length+' 条</summary>'+g.items.map(function(r){return '<div class="record-card"><span class="tag">'+esc(normType(r.type))+'</span><div><b>'+esc(r.name)+'</b><div class="muted">'+esc(displayKp(r.knowledge_point)||'未绑定知识点')+'</div></div><div class="muted">'+esc(r.time||'')+'</div></div>'}).join('')+'</details>'}).join('')||'<div class="empty">暂无学习记录</div>')+'</div></div>'}
async function discuss(){var d=await getJson('/student/discuss/list');app.innerHTML='<div class="card"><h2>'+Z.discuss+'</h2><div class="toolbar"><input id="topicTitle" class="search" placeholder="问题标题"><button class="btn" onclick="postTopic()">发布</button></div><textarea id="topicBody" style="width:100%" rows="3" placeholder="描述你的问题、卡点或学习经验"></textarea></div><div class="card">'+((d.posts||[]).map(function(p){return '<div class="post" onclick="openPost(&quot;'+esc(p.id)+'&quot;)"><div class="post-head"><b>'+esc(p.title)+'</b><span class="tag">'+esc(cleanText(p.status||''))+'</span></div><div class="muted">'+esc(p.author)+' · '+esc(p.time)+' · '+(p.comment_count||0)+' 条回复</div><p>'+esc(p.body||'')+'</p></div>'}).join('')||'<div class="empty">暂无讨论</div>')+'</div><div class="card" id="postDetail"><div class="muted">点击讨论查看详情和回复。</div></div>'}
async function postTopic(){if(!topicTitle.value.trim())return alert('请填写标题');let d=await fetch('/student/discuss/post',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:topicTitle.value.trim(),body:topicBody.value.trim()})}).then(r=>r.json());alert(d.success?'发布成功':(d.error||'发布失败'));if(d.success)discuss()}
async function openPost(id){let d=await getJson('/student/discuss/detail/'+encodeURIComponent(id)),p=d.post||{};postDetail.innerHTML='<h2>'+esc(p.title)+'</h2><p>'+esc(p.body||'')+'</p><div class="muted">'+esc(p.author||'')+' · '+esc(p.time||'')+'</div><h3>回复</h3>'+((p.comments||d.comments||[]).map(function(c){return '<div class="comment"><b>'+esc(c.author)+'</b><p>'+esc(c.body)+'</p><div class="muted">'+esc(c.time)+'</div></div>'}).join('')||'<div class="muted">暂无回复</div>')+'<textarea id="commentBody" style="width:100%" rows="3" placeholder="写下回复"></textarea><button class="btn" onclick="commentPost(&quot;'+esc(id)+'&quot;)">提交回复</button>'}
async function commentPost(id){let body=document.getElementById('commentBody').value.trim();if(!body)return alert('请填写回复');let d=await fetch('/student/discuss/comment/'+encodeURIComponent(id),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({body:body})}).then(r=>r.json());alert(d.success?'回复成功':(d.error||'回复失败'));if(d.success)openPost(id)}
async function graphPage(){var d=await getJson('/student/flow-graph/data'),built=buildLayeredGraph(d.nodes||[],d.edges||[]),nodes=built.nodes,edges=built.edges;app.innerHTML='<div class="card"><h2>'+Z.graph+'</h2><div class="muted"><b>颜色 = 学习状态：</b><span class="tag ok">已掌握>=80%</span><span class="tag">良好>=60%</span><span class="tag warn">进行中>=40%</span><span class="tag bad">薄弱&lt;40%</span><span class="tag">未学习</span><b style="margin-left:12px">边：</b>包含 / 相关 / 先修</div><div style="display:grid;grid-template-columns:minmax(0,1fr) 360px;gap:18px;margin-top:14px"><div style="position:relative"><div id="mynetwork" style="height:720px;border:1px solid #e5e7eb;background:#fafafa"></div><div style="position:absolute;right:18px;top:18px;width:62px;background:#fff;border:1px solid #dbe3ef;border-radius:14px;box-shadow:0 8px 24px rgba(15,23,42,.12);padding:10px;display:grid;gap:6px;place-items:center"><button class="btn light" style="width:40px;height:40px;padding:0" onclick="zoomGraph(.03)">+</button><input id="graphZoom" type="range" min="0" max="100" step="1" value="26" oninput="setGraphZoom(this.value)" style="writing-mode:vertical-lr;direction:rtl;-webkit-appearance:slider-vertical;appearance:slider-vertical;width:40px;height:250px;margin:0;touch-action:none"><button class="btn light" style="width:40px;height:40px;padding:0" onclick="zoomGraph(-.03)">-</button></div></div><div id="nodeDetail" class="res-card graph-detail"><b>节点详情</b><p class="muted">单击节点查看掌握度。</p></div></div></div>';if(!window.vis){document.getElementById('mynetwork').innerHTML='<div class="empty">vis load failed</div>';return}function color(m){return m>=.8?{background:'#d4f0dc',border:'#a8ddb8'}:m>=.6?{background:'#dbeafe',border:'#93c5fd'}:m>=.4?{background:'#ffedd5',border:'#fdba74'}:m>0?{background:'#fee2e2',border:'#fca5a5'}:{background:'#eceff1',border:'#cfd8dc'}}var visNodes=new vis.DataSet(nodes.map(function(n){return {id:n.id,label:n.drawLabel||displayKp(n.label||n.id),shape:n.shape,size:n.size,color:n.id==='root'?{background:'#1f2937',border:'#111827'}:color(n.mastery||0),font:{size:n.fontSize,face:'Microsoft YaHei',color:n.id==='root'?'#fff':'#111827',bold:true,multi:true},borderWidth:n.level<=0?4:3,mass:n.level<=0?6:(n.level===1?3:1),widthConstraint:n.shape==='box'?{minimum:120,maximum:150}:undefined,heightConstraint:n.shape==='box'?{minimum:60}:undefined}}));var visEdges=new vis.DataSet(edges.map(function(e,i){return {id:i,from:e.from,to:e.to,arrows:'to',color:{color:e.type==='先修'?'#9b59b6':(e.type==='相关'?'#f59e0b':'#94a3b8')},dashes:e.type!=='包含',width:e.type==='包含'?2.2:1.7,smooth:{type:'dynamic'}}}));var network=new vis.Network(document.getElementById('mynetwork'),{nodes:visNodes,edges:visEdges},{physics:{solver:'forceAtlas2Based',forceAtlas2Based:{gravitationalConstant:-240,centralGravity:.018,springLength:170,springConstant:.04,avoidOverlap:1},stabilization:{iterations:600}},interaction:{zoomView:true,dragView:true,dragNodes:true}});window.graphNetwork=network;window.graphZoomMin=.24;window.graphZoomMax=.55;window.graphScale=.32;network.once('stabilizationIterationsDone',function(){network.stopSimulation();applyGraphZoom(.32,true)});network.on('click',function(p){var id=p.nodes&&p.nodes[0],n=nodes.find(function(x){return x.id===id});if(!n)return;var m=Number(n.mastery||0),state=m>=.8?Z.mastered:m>=.6?Z.good:m>=.4?Z.doing:m>0?Z.weak:Z.unlearned;document.getElementById('nodeDetail').innerHTML='<b>'+esc(displayKp(n.label||n.id))+'</b><p><span class="tag '+statusClass(state)+'">'+state+'</span><span class="tag">掌握度 '+Math.round(m*100)+'%</span></p>'+bar(m,state)+'<p class="muted">'+esc(n.levelName||'')+'</p>'})}
function graphSliderToScale(v){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55,t=Math.max(0,Math.min(100,parseFloat(v)||0))/100;return min+(max-min)*t}function graphScaleToSlider(s){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55;return Math.round((Math.max(min,Math.min(max,parseFloat(s)||min))-min)/(max-min)*100)}function applyGraphZoom(scale,animate){var min=window.graphZoomMin||.24,max=window.graphZoomMax||.55;window.graphScale=Math.max(min,Math.min(max,parseFloat(scale)||.32));if(window.graphNetwork)window.graphNetwork.moveTo({position:window.graphNetwork.getViewPosition(),scale:window.graphScale,animation:animate?{duration:120,easingFunction:'easeInOutQuad'}:{duration:0}});var z=document.getElementById('graphZoom');if(z)z.value=graphScaleToSlider(window.graphScale)}function setGraphZoom(v){applyGraphZoom(graphSliderToScale(v),false)}function zoomGraph(delta){applyGraphZoom((window.graphScale||.32)+delta,true)}async function graphBuilder(){graphPage()}
if(PAGE==='dashboard')dashboard();if(PAGE==='path')pathPage();if(PAGE==='resources')resourcesPage();if(PAGE==='mastery')mastery();if(PAGE==='records')records();if(PAGE==='discuss')discuss();if(PAGE==='my_discuss')discuss();if(PAGE==='graph')graphPage();if(PAGE==='graph_builder')graphBuilder();
</script></body></html>
"""

app.view_functions["student_mastery_data"] = student_mastery_data
app.view_functions["get_student_resources_data"] = get_student_resources_data
app.view_functions["student_path_data"] = student_path_data
app.view_functions["student_flow_graph_data"] = student_flow_graph_data
app.view_functions["student_records_data"] = student_records_data_new

if __name__ == "__main__":
    app.run(debug=True)








