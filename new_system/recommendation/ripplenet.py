import numpy as np
from collections import defaultdict
from data_processing.neo4j_manager import Neo4jManager


class RippleNetRecommender:
    """
    RippleNet: Propagating User Preferences on the Knowledge Graph
    在知识图谱上进行用户偏好的多跳传播
    
    核心思想：
    1. 从用户交互过的知识点出发，在知识图谱上进行多跳传播
    2. 每一跳（hop）根据关系类型进行加权传播
    3. 最终得到用户对各个知识点的偏好分数
    """

    def __init__(self, n_hops=2, decay_factor=0.5):
        self.neo4j = Neo4jManager()
        self.n_hops = n_hops
        self.decay_factor = decay_factor
        
        self.relation_weights = {
            "先修": 0.8,
            "相关": 0.6,
            "包含": 0.4
        }

    def get_user_interacted_kps(self, student_id, threshold=0.6):
        """
        获取用户已经交互过且掌握度较高的知识点作为种子节点
        """
        query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE r.mastery >= $threshold
        RETURN k.name AS name, r.mastery AS mastery
        """
        result = self.neo4j.run_query(query, {"sid": student_id, "threshold": threshold})
        
        interacted = {}
        for r in result:
            interacted[r["name"]] = r["mastery"]
        return interacted

    def build_kg_graph(self):
        """
        构建知识图谱的邻接表
        """
        query = """
        MATCH (a)-[r]->(b)
        WHERE type(r) IN ['先修', '相关', '包含']
        RETURN a.name AS from_node, type(r) AS rel_type, b.name AS to_node
        """
        result = self.neo4j.run_query(query)
        
        adj_list = defaultdict(list)
        for r in result:
            weight = self.relation_weights.get(r["rel_type"], 0.5)
            adj_list[r["from_node"]].append({
                "to": r["to_node"],
                "rel": r["rel_type"],
                "weight": weight
            })
        
        return adj_list

    def ripple_propagation(self, student_id):
        """
        RippleNet传播算法
        
        对于每个hop h:
        preference_h = (preference_{h-1} * W_h) / |N|
        
        其中W_h是第h跳的关系权重矩阵，N是邻居节点数
        """
        interacted_kps = self.get_user_interacted_kps(student_id)
        if not interacted_kps:
            return {}
        
        adj_list = self.build_kg_graph()
        
        preferences = defaultdict(float)
        
        for seed_kp, seed_mastery in interacted_kps.items():
            preferences[seed_kp] = max(preferences[seed_kp], seed_mastery)
        
        current_nodes = set(interacted_kps.keys())
        
        for hop in range(1, self.n_hops + 1):
            decay = self.decay_factor ** hop
            next_nodes = set()
            
            for node in current_nodes:
                if node in adj_list:
                    for neighbor in adj_list[node]:
                        neighbor_node = neighbor["to"]
                        rel_weight = neighbor["weight"]
                        
                        new_score = preferences[node] * rel_weight * decay
                        
                        if new_score > preferences[neighbor_node]:
                            preferences[neighbor_node] = new_score
                        
                        next_nodes.add(neighbor_node)
            
            current_nodes = next_nodes
            if not current_nodes:
                break
        
        return dict(preferences)

    def recommend(self, student_id, top_k=10):
        """
        基于RippleNet生成推荐
        
        返回用户对各个知识点的偏好分数，
        优先推荐用户尚未掌握但偏好分数高的知识点
        """
        preferences = self.ripple_propagation(student_id)
        
        query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        RETURN k.name AS name, r.mastery AS mastery
        """
        result = self.neo4j.run_query(query, {"sid": student_id})
        
        user_mastery = {}
        for r in result:
            user_mastery[r["name"]] = r["mastery"]
        
        recommendations = []
        for kp_name, pref_score in preferences.items():
            mastery = user_mastery.get(kp_name, 0.0)
            
            if mastery < 0.7:
                recommend_score = pref_score * (1.0 - mastery)
                recommendations.append({
                    "name": kp_name,
                    "mastery": mastery,
                    "preference_score": round(pref_score, 4),
                    "score": round(recommend_score, 4),
                    "source": "ripplenet"
                })
        
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:top_k]

    def close(self):
        self.neo4j.close()


if __name__ == "__main__":
    rn = RippleNetRecommender(n_hops=2, decay_factor=0.5)
    recs = rn.recommend("3220602001刘大", top_k=5)
    for r in recs:
        print(f"{r['name']} | 掌握度: {r['mastery']:.4f} | "
              f"偏好分: {r['preference_score']:.4f} | 推荐分: {r['score']:.4f}")
    rn.close()
