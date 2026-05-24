import numpy as np
from data_processing.neo4j_manager import Neo4jManager
from recommendation.mastery_based import MasteryCalculator


class KnowledgeGraphRecommender:
    """
    4.2 基于知识图谱关联的推荐算法
    4.2.1 关联传播机制：前置知识、同层相关、上下游结构
    4.2.2 关联推荐公式：
        Score_i = sum_{j in Adj(i)} w_ij * (1 - Mastery_j)
    """

    def __init__(self, alpha=0.7, beta=0.3):
        self.neo4j = Neo4jManager()
        self.calculator = MasteryCalculator(alpha=alpha, beta=beta)

        self.relation_weights = {
            "先修": 0.8,
            "相关": 0.5,
            "包含": 0.3
        }

    def get_adjacent_nodes(self, knowledge_point):
        adjacent = {}

        prereq_query = """
        MATCH (k:Knowledge {name: $kp})-[r:先修]-(adj:Knowledge)
        RETURN adj.name AS name, type(r) AS rel_type
        """
        result = self.neo4j.run_query(prereq_query, {"kp": knowledge_point})
        for r in result:
            name = r["name"]
            rel = r["rel_type"]
            w = self.relation_weights.get("先修", 0.8)
            if name not in adjacent or adjacent[name] < w:
                adjacent[name] = w

        related_query = """
        MATCH (k:Knowledge {name: $kp})-[r:相关]-(adj:Knowledge)
        RETURN adj.name AS name
        """
        result = self.neo4j.run_query(related_query, {"kp": knowledge_point})
        for r in result:
            name = r["name"]
            w = self.relation_weights.get("相关", 0.5)
            if name not in adjacent or adjacent[name] < w:
                adjacent[name] = w

        parent_query = """
        MATCH (parent:Knowledge)-[:包含]->(k:Knowledge {name: $kp})
        RETURN parent.name AS name
        """
        result = self.neo4j.run_query(parent_query, {"kp": knowledge_point})
        for r in result:
            name = r["name"]
            w = self.relation_weights.get("包含", 0.3)
            if name not in adjacent or adjacent[name] < w:
                adjacent[name] = w

        child_query = """
        MATCH (k:Knowledge {name: $kp})-[:包含]->(child:Knowledge)
        RETURN child.name AS name
        """
        result = self.neo4j.run_query(child_query, {"kp": knowledge_point})
        for r in result:
            name = r["name"]
            w = self.relation_weights.get("包含", 0.3)
            if name not in adjacent or adjacent[name] < w:
                adjacent[name] = w

        return adjacent

    def compute_association_score(self, student_id, knowledge_point):
        """
        Score_i = sum_{j in Adj(i)} w_ij * (1 - Mastery_j)
        """
        adjacent = self.get_adjacent_nodes(knowledge_point)
        if not adjacent:
            return 0.0

        mastery_map = self.calculator.get_student_mastery(student_id)

        total_score = 0.0
        total_weight = 0.0

        for adj_name, weight in adjacent.items():
            if adj_name in mastery_map:
                adj_mastery = mastery_map[adj_name]["mastery"]
                score_contribution = weight * (1.0 - adj_mastery)
                total_score += score_contribution
                total_weight += weight

        if total_weight > 0:
            return total_score / total_weight
        return 0.0

    def recommend(self, student_id, top_k=10):
        mastery_map = self.calculator.get_student_mastery(student_id)

        recommendations = {}
        for kp_name, info in mastery_map.items():
            base_score = 1.0 - info["mastery"]
            assoc_score = self.compute_association_score(student_id, kp_name)

            combined_score = 0.6 * base_score + 0.4 * assoc_score

            adjacent = self.get_adjacent_nodes(kp_name)
            prereqs = [n for n, w in adjacent.items() if w >= 0.8]
            related = [n for n, w in adjacent.items() if 0.4 <= w < 0.8]

            recommendations[kp_name] = {
                "name": kp_name,
                "mastery": info["mastery"],
                "accuracy": info["accuracy"],
                "n_done": info["n_done"],
                "base_score": round(base_score, 4),
                "assoc_score": round(assoc_score, 4),
                "score": round(combined_score, 4),
                "source": "knowledge_graph",
                "prerequisites": prereqs[:3],
                "related": related[:3]
            }

        sorted_recs = sorted(recommendations.values(), key=lambda x: x["score"], reverse=True)
        return sorted_recs[:top_k]

    def close(self):
        self.calculator.close()
        self.neo4j.close()


if __name__ == "__main__":
    kgr = KnowledgeGraphRecommender(alpha=0.7, beta=0.3)
    recs = kgr.recommend("3220602001刘大", top_k=5)
    for r in recs:
        print(f"{r['name']} | 掌握度: {r['mastery']:.4f} | "
              f"基础分: {r['base_score']:.4f} | 关联分: {r['assoc_score']:.4f} | "
              f"总分: {r['score']:.4f}")
    kgr.close()
