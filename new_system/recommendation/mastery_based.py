import numpy as np
from data_processing.neo4j_manager import Neo4jManager


class MasteryCalculator:
    """
    4.1.1 掌握度计算模型
    Mastery_i = alpha * Accuracy_i + beta * (N_i / N_max)
    alpha + beta = 1
    """

    def __init__(self, alpha=0.7, beta=0.3):
        self.alpha = alpha
        self.beta = beta
        self.neo4j = Neo4jManager()

    def compute_mastery(self, accuracy, n_done, n_max):
        if n_max == 0:
            return 0.0
        return self.alpha * accuracy + self.beta * (n_done / n_max)

    def get_student_mastery(self, student_id):
        query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
        RETURN k.name AS name, r.correct_questions AS correct,
               r.total_questions AS total, r.mastery AS old_mastery
        """
        result = self.neo4j.run_query(query, {"sid": student_id})

        mastery_map = {}
        for r in result:
            name = r["name"]
            total = r["total"] or 0
            correct = r["correct"] or 0
            accuracy = correct / total if total > 0 else 0.0

            n_max = self._get_n_max()
            new_mastery = self.compute_mastery(accuracy, total, n_max)

            mastery_map[name] = {
                "name": name,
                "accuracy": round(accuracy, 4),
                "n_done": total,
                "n_max": n_max,
                "mastery": round(new_mastery, 4),
                "correct": correct,
                "total": total
            }

        return mastery_map

    def _get_n_max(self):
        query = """
        MATCH (s:Student)-[r:MASTERED]->(k:Knowledge)
        WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
        RETURN max(r.total_questions) AS n_max
        """
        result = self.neo4j.run_query(query)
        if result and result[0]["n_max"]:
            return result[0]["n_max"]
        return 30

    def update_mastery_in_db(self, student_id, knowledge_point):
        query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge {name: $kp})
        RETURN r.correct_questions AS correct, r.total_questions AS total
        """
        result = self.neo4j.run_query(query, {"sid": student_id, "kp": knowledge_point})
        if not result:
            return None

        r = result[0]
        total = r["total"] or 0
        correct = r["correct"] or 0
        accuracy = correct / total if total > 0 else 0.0
        n_max = self._get_n_max()
        new_mastery = self.compute_mastery(accuracy, total, n_max)

        self.neo4j.execute_write("""
            MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge {name: $kp})
            SET r.mastery = $m
        """, {"sid": student_id, "kp": knowledge_point, "m": new_mastery})

        return new_mastery

    def close(self):
        self.neo4j.close()


class MasteryBasedRecommender:
    """
    4.1.2 基于掌握度的推荐策略
    Recommend_i = 1 - Mastery_i
    优先推荐掌握度较低的知识点
    """

    def __init__(self, alpha=0.7, beta=0.3):
        self.calculator = MasteryCalculator(alpha=alpha, beta=beta)

    def recommend(self, student_id, top_k=10):
        mastery_map = self.calculator.get_student_mastery(student_id)

        recommendations = []
        for name, info in mastery_map.items():
            recommend_score = 1.0 - info["mastery"]
            recommendations.append({
                "name": name,
                "mastery": info["mastery"],
                "accuracy": info["accuracy"],
                "n_done": info["n_done"],
                "score": round(recommend_score, 4),
                "source": "mastery"
            })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:top_k]

    def close(self):
        self.calculator.close()


if __name__ == "__main__":
    mbr = MasteryBasedRecommender(alpha=0.7, beta=0.3)
    recs = mbr.recommend("3220602001刘大", top_k=5)
    for r in recs:
        print(f"{r['name']} | 掌握度: {r['mastery']:.4f} | 推荐分: {r['score']:.4f}")
    mbr.close()
