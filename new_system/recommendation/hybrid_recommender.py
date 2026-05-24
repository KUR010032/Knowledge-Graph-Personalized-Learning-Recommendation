import numpy as np
import os
import sys
import re
from data_processing.neo4j_manager import Neo4jManager
from recommendation.mastery_based import MasteryBasedRecommender, MasteryCalculator
from recommendation.knowledge_graph_recommender import KnowledgeGraphRecommender
from recommendation.collaborative_filtering import CollaborativeFiltering
from recommendation.ripplenet import RippleNetRecommender
from recommendation.multi_behavior import MultiBehaviorModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config


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


class HybridRecommender:
    """
    4.4 多策略融合推荐模型（改进版）
    4.4.1 融合策略：
        FinalScore = lambda1 * M + lambda2 * G + lambda3 * C + lambda4 * R + lambda5 * B
        lambda1 + lambda2 + lambda3 + lambda4 + lambda5 = 1

    M: 基于掌握度推荐结果 (4.1)
    G: 基于知识图谱推荐结果 (4.2)
    C: 基于协同过滤推荐结果 (4.3)
    R: 基于RippleNet偏好传播推荐结果 (4.4)
    B: 基于多行为建模推荐结果 (4.5)
    """

    def __init__(self, alpha=0.7, beta=0.3,
                 lambda1=0.25, lambda2=0.2, lambda3=0.2, lambda4=0.2, lambda5=0.15):
        self.alpha = alpha
        self.beta = beta
        self.lambda1 = lambda1
        self.lambda2 = lambda2
        self.lambda3 = lambda3
        self.lambda4 = lambda4
        self.lambda5 = lambda5

        self.neo4j = Neo4jManager()
        self.mastery_rec = MasteryBasedRecommender(alpha=alpha, beta=beta)
        self.kg_rec = KnowledgeGraphRecommender(alpha=alpha, beta=beta)
        self.cf_rec = CollaborativeFiltering(alpha=alpha, beta=beta)
        self.ripplenet_rec = RippleNetRecommender(n_hops=2, decay_factor=0.5)
        self.multi_behavior = MultiBehaviorModel(alpha=alpha, beta=beta)
        self.calculator = MasteryCalculator(alpha=alpha, beta=beta)

    def recommend(self, student_id, top_k=10):
        """
        4.4.2 算法流程：
        1. 计算学习者知识点掌握度
        2. 基于掌握度生成初始推荐列表
        3. 在知识图谱中扩展关联知识点
        4. 计算用户相似度并进行协同过滤推荐
        5. RippleNet偏好传播推荐
        6. 多行为建模推荐
        7. 融合所有结果生成最终推荐列表（直接推荐资源/题目）
        """
        kp_recommendations = {}

        # Step 1-2: Mastery-based recommendations (M)
        m_recs = self.mastery_rec.recommend(student_id, top_k * 2)
        for rec in m_recs:
            kp = rec["name"]
            kp_recommendations[kp] = {
                "name": kp,
                "mastery": rec["mastery"],
                "accuracy": rec.get("accuracy", 0),
                "n_done": rec.get("n_done", 0),
                "M_score": rec["score"],
                "G_score": 0.0,
                "C_score": 0.0,
                "R_score": 0.0,
                "B_score": 0.0,
                "total_score": self.lambda1 * rec["score"],
                "prerequisites": [],
                "related": [],
                "sources": ["mastery"]
            }

        # Step 3: Knowledge graph recommendations (G)
        g_recs = self.kg_rec.recommend(student_id, top_k * 2)
        for rec in g_recs:
            kp = rec["name"]
            if kp in kp_recommendations:
                kp_recommendations[kp]["G_score"] = rec["score"]
                kp_recommendations[kp]["total_score"] += self.lambda2 * rec["score"]
                kp_recommendations[kp]["prerequisites"] = rec.get("prerequisites", [])
                kp_recommendations[kp]["related"] = rec.get("related", [])
                kp_recommendations[kp]["sources"].append("knowledge_graph")
            else:
                kp_recommendations[kp] = {
                    "name": kp,
                    "mastery": rec["mastery"],
                    "accuracy": rec.get("accuracy", 0),
                    "n_done": rec.get("n_done", 0),
                    "M_score": 0.0,
                    "G_score": rec["score"],
                    "C_score": 0.0,
                    "R_score": 0.0,
                    "B_score": 0.0,
                    "total_score": self.lambda2 * rec["score"],
                    "prerequisites": rec.get("prerequisites", []),
                    "related": rec.get("related", []),
                    "sources": ["knowledge_graph"]
                }

        # Step 4: Collaborative filtering recommendations (C)
        c_recs = self.cf_rec.recommend(student_id, top_k * 2)
        for rec in c_recs:
            kp = rec["name"]
            if kp in kp_recommendations:
                kp_recommendations[kp]["C_score"] = rec["score"]
                kp_recommendations[kp]["total_score"] += self.lambda3 * rec["score"]
                kp_recommendations[kp]["sources"].append("collaborative")
            else:
                kp_recommendations[kp] = {
                    "name": kp,
                    "mastery": rec["mastery"],
                    "accuracy": 0,
                    "n_done": 0,
                    "M_score": 0.0,
                    "G_score": 0.0,
                    "C_score": rec["score"],
                    "R_score": 0.0,
                    "B_score": 0.0,
                    "total_score": self.lambda3 * rec["score"],
                    "prerequisites": [],
                    "related": [],
                    "sources": ["collaborative"]
                }

        # Step 5: RippleNet recommendations (R)
        r_recs = self.ripplenet_rec.recommend(student_id, top_k * 2)
        for rec in r_recs:
            kp = rec["name"]
            if kp in kp_recommendations:
                kp_recommendations[kp]["R_score"] = rec["score"]
                kp_recommendations[kp]["total_score"] += self.lambda4 * rec["score"]
                kp_recommendations[kp]["sources"].append("ripplenet")
            else:
                kp_recommendations[kp] = {
                    "name": kp,
                    "mastery": rec["mastery"],
                    "accuracy": 0,
                    "n_done": 0,
                    "M_score": 0.0,
                    "G_score": 0.0,
                    "C_score": 0.0,
                    "R_score": rec["score"],
                    "B_score": 0.0,
                    "total_score": self.lambda4 * rec["score"],
                    "prerequisites": [],
                    "related": [],
                    "sources": ["ripplenet"]
                }

        # Step 6: Multi-behavior recommendations (B)
        behavior_scores = self.multi_behavior.compute_multi_behavior_score(student_id)
        mastery_map = self.calculator.get_student_mastery(student_id)
        
        for kp, b_scores in behavior_scores.items():
            if kp in mastery_map:
                mastery = mastery_map[kp]["mastery"]
                recommend_score = b_scores["total_score"] * (1.0 - mastery)
                
                if kp in kp_recommendations:
                    kp_recommendations[kp]["B_score"] = recommend_score
                    kp_recommendations[kp]["total_score"] += self.lambda5 * recommend_score
                    kp_recommendations[kp]["sources"].append("multi_behavior")
                else:
                    kp_recommendations[kp] = {
                        "name": kp,
                        "mastery": mastery,
                        "accuracy": mastery_map[kp]["accuracy"],
                        "n_done": mastery_map[kp]["n_done"],
                        "M_score": 0.0,
                        "G_score": 0.0,
                        "C_score": 0.0,
                        "R_score": 0.0,
                        "B_score": recommend_score,
                        "total_score": self.lambda5 * recommend_score,
                        "prerequisites": [],
                        "related": [],
                        "sources": ["multi_behavior"]
                    }

        # Step 7: Sort by total score
        sorted_kps = sorted(kp_recommendations.values(),
                           key=lambda x: x["total_score"], reverse=True)

        # Step 8: 转换为资源/题目推荐（不再直接推荐知识点）
        # 限制最终推荐数量为top_k个（7-8个）
        final_recommendations = []
        max_items = top_k
        
        for kp_rec in sorted_kps:
            if len(final_recommendations) >= max_items:
                break
                
            kp_name = kp_rec["name"]
            
            labels = self._get_knowledge_labels(kp_name)
            resources = self._get_resources_for_kp(kp_name)
            questions = self._get_questions_for_kp(kp_name)
            
            for res in resources:
                if len(final_recommendations) >= max_items:
                    break
                final_recommendations.append({
                    "type": "resource",
                    "resource_type": res["type"],
                    "name": res["name"],
                    "url": res["url"],
                    "knowledge_point": kp_name,
                    "knowledge_labels": labels,
                    "recommend_score": kp_rec["total_score"],
                    "mastery": kp_rec["mastery"],
                    "sources": kp_rec["sources"],
                    "scores": {
                        "M": kp_rec["M_score"],
                        "G": kp_rec["G_score"],
                        "C": kp_rec["C_score"],
                        "R": kp_rec["R_score"],
                        "B": kp_rec["B_score"]
                    }
                })
            
            for q in questions:
                if len(final_recommendations) >= max_items:
                    break
                final_recommendations.append({
                    "type": "question",
                    "name": q["content"][:50] + "..." if len(q["content"]) > 50 else q["content"],
                    "question_id": q["id"],
                    "full_question": q,
                    "knowledge_point": kp_name,
                    "knowledge_labels": labels,
                    "recommend_score": kp_rec["total_score"],
                    "mastery": kp_rec["mastery"],
                    "sources": kp_rec["sources"],
                    "scores": {
                        "M": kp_rec["M_score"],
                        "G": kp_rec["G_score"],
                        "C": kp_rec["C_score"],
                        "R": kp_rec["R_score"],
                        "B": kp_rec["B_score"]
                    }
                })
        
        return final_recommendations[:max_items]

    def _get_knowledge_labels(self, kp_name):
        query = """
        MATCH (k:Knowledge {name: $name})
        RETURN k.difficulty AS difficulty, k.importance AS importance
        """
        result = self.neo4j.run_query(query, {"name": kp_name})
        if result and result[0]:
            return {
                "difficulty": result[0].get("difficulty", "medium"),
                "importance": result[0].get("importance", "normal")
            }
        return {"difficulty": "medium", "importance": "normal"}

    def _get_resources_for_kp(self, kp_name):
        resources = []
        
        ch_match = re.match(r'(\d+)\.', kp_name)
        if ch_match:
            ch_num = int(ch_match.group(1))
            ch_key = f"第{ch_num}章"
            if ch_key in RESOURCE_MAP:
                for f in RESOURCE_MAP[ch_key]:
                    ext = os.path.splitext(f)[1].lower()
                    rtype = "video" if ext == ".mp4" else "ppt" if ext == ".pptx" else "doc" if ext in [".docx", ".doc"] else "other"
                    resources.append({"name": f, "type": rtype, "url": f"/api/download/{f}"})
        
        if kp_name in VIDEO_MAP:
            for f in VIDEO_MAP[kp_name]:
                resources.append({"name": f, "type": "video", "url": f"/api/download/{f}"})
        
        resource_dir = Config.RESOURCE_DIR
        if os.path.exists(resource_dir):
            kp_prefix = kp_name.split(' ')[0] if ' ' in kp_name else kp_name
            for f in os.listdir(resource_dir):
                if f.startswith(kp_prefix) and f != "questions.json":
                    ext = os.path.splitext(f)[1].lower()
                    rtype = "video" if ext == ".mp4" else "ppt" if ext == ".pptx" else "doc" if ext in [".docx", ".doc"] else "other"
                    if not any(r["name"] == f for r in resources):
                        resources.append({"name": f, "type": rtype, "url": f"/api/download/{f}"})
        
        return resources

    def _get_questions_for_kp(self, kp_name):
        query = """
        MATCH (q:Question)-[:属于]->(k:Knowledge {name: $name})
        RETURN q.id AS id, q.content AS content, q.options AS options,
               q.answer AS answer, q.difficulty AS difficulty,
               q.importance AS importance
        LIMIT 5
        """
        result = self.neo4j.run_query(query, {"name": kp_name})
        questions = []
        for r in result:
            q = {
                "id": r["id"],
                "content": r["content"],
                "options": r["options"],
                "answer": r["answer"],
                "difficulty": r.get("difficulty", "medium"),
                "importance": r.get("importance", "normal")
            }
            questions.append(q)
        return questions

    def close(self):
        self.mastery_rec.close()
        self.kg_rec.close()
        self.cf_rec.close()
        self.ripplenet_rec.close()
        self.multi_behavior.close()
        self.calculator.close()
        self.neo4j.close()


if __name__ == "__main__":
    hr = HybridRecommender(alpha=0.7, beta=0.3,
                           lambda1=0.25, lambda2=0.2, lambda3=0.2, lambda4=0.2, lambda5=0.15)
    recs = hr.recommend("3220602001刘大", top_k=5)
    print(f"共推荐 {len(recs)} 个资源/题目:")
    for r in recs:
        if r["type"] == "resource":
            print(f"[资源] {r['name']} | 知识点: {r['knowledge_point']} | 推荐分: {r['recommend_score']:.4f}")
        else:
            print(f"[题目] {r['name']} | 知识点: {r['knowledge_point']} | 推荐分: {r['recommend_score']:.4f}")
    hr.close()
