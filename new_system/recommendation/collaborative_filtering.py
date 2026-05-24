import numpy as np
from data_processing.neo4j_manager import Neo4jManager
from recommendation.mastery_based import MasteryCalculator


class CollaborativeFiltering:
    """
    4.3 基于协同过滤的推荐算法
    4.3.1 用户相似度计算（余弦相似度）：
        sim(u,v) = (sum_i r_u,i * r_v,i) / (sqrt(sum_i r_u,i^2) * sqrt(sum_i r_v,i^2))
    4.3.2 推荐评分计算：
        Score(u,i) = sum_{v in N(u)} sim(u,v) * r_v,i
    """

    def __init__(self, alpha=0.7, beta=0.3):
        self.neo4j = Neo4jManager()
        self.calculator = MasteryCalculator(alpha=alpha, beta=beta)
        self.user_ids = []
        self.item_ids = []
        self.user_item_matrix = None
        self.user_similarity = None

    def build_user_item_matrix(self):
        query = """
        MATCH (s:Student)-[r:MASTERED]->(k:Knowledge)
        WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
        RETURN s.id AS student_id, k.name AS kp, r.correct_questions AS correct,
               r.total_questions AS total
        """
        result = self.neo4j.run_query(query)

        student_data = {}
        for r in result:
            sid = r["student_id"]
            kp = r["kp"]
            total = r["total"] or 0
            correct = r["correct"] or 0
            accuracy = correct / total if total > 0 else 0.0

            n_max = self._get_n_max()
            mastery = self.calculator.compute_mastery(accuracy, total, n_max)

            if sid not in student_data:
                student_data[sid] = {}
            student_data[sid][kp] = mastery

        self.user_ids = list(student_data.keys())
        all_items = set()
        for data in student_data.values():
            all_items.update(data.keys())
        self.item_ids = sorted(list(all_items))

        matrix = np.zeros((len(self.user_ids), len(self.item_ids)))
        for i, uid in enumerate(self.user_ids):
            for j, iid in enumerate(self.item_ids):
                matrix[i, j] = student_data[uid].get(iid, 0.0)

        self.user_item_matrix = matrix
        self.user_similarity = self._compute_cosine_similarity(matrix)

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

    def _compute_cosine_similarity(self, matrix):
        """
        sim(u,v) = (sum_i r_u,i * r_v,i) / (sqrt(sum_i r_u,i^2) * sqrt(sum_i r_v,i^2))
        """
        n_users = matrix.shape[0]
        sim_matrix = np.zeros((n_users, n_users))

        for u in range(n_users):
            norm_u = np.sqrt(np.sum(matrix[u] ** 2))
            if norm_u == 0:
                continue
            for v in range(u, n_users):
                norm_v = np.sqrt(np.sum(matrix[v] ** 2))
                if norm_v == 0:
                    continue
                dot_product = np.dot(matrix[u], matrix[v])
                sim = dot_product / (norm_u * norm_v)
                sim_matrix[u, v] = sim
                sim_matrix[v, u] = sim

        return sim_matrix

    def get_similar_users(self, user_id, top_k=5):
        if user_id not in self.user_ids:
            return []

        user_idx = self.user_ids.index(user_id)
        similarities = self.user_similarity[user_idx]

        similar_indices = np.argsort(similarities)[::-1][1:top_k + 1]
        return [(self.user_ids[i], similarities[i]) for i in similar_indices
                if similarities[i] > 0]

    def recommend(self, student_id, top_k=10):
        """
        Score(u,i) = sum_{v in N(u)} sim(u,v) * r_v,i
        """
        self.build_user_item_matrix()

        if student_id not in self.user_ids:
            return []

        user_idx = self.user_ids.index(student_id)
        similar_users = self.get_similar_users(student_id, top_k=5)

        if not similar_users:
            return []

        scores = np.zeros(len(self.item_ids))
        total_similarity = 0.0

        for sim_user_id, similarity in similar_users:
            sim_user_idx = self.user_ids.index(sim_user_id)
            scores += similarity * self.user_item_matrix[sim_user_idx]
            total_similarity += similarity

        if total_similarity > 0:
            scores /= total_similarity

        user_scores = self.user_item_matrix[user_idx]
        recommendations = []

        for i, score in enumerate(scores):
            if user_scores[i] < 0.6:
                recommendations.append({
                    "name": self.item_ids[i],
                    "mastery": round(user_scores[i], 4),
                    "predicted_mastery": round(score, 4),
                    "score": round(score, 4),
                    "source": "collaborative"
                })

        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:top_k]

    def close(self):
        self.calculator.close()
        self.neo4j.close()


if __name__ == "__main__":
    cf = CollaborativeFiltering(alpha=0.7, beta=0.3)
    recs = cf.recommend("3220602001刘大", top_k=5)
    for r in recs:
        print(f"{r['name']} | 掌握度: {r['mastery']:.4f} | "
              f"预测掌握度: {r['predicted_mastery']:.4f} | 推荐分: {r['score']:.4f}")
    cf.close()
