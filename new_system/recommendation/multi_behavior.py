import numpy as np
from collections import defaultdict
from data_processing.neo4j_manager import Neo4jManager


class MultiBehaviorModel:
    """
    多行为建模：考虑用户的多种学习行为
    - 做题行为：答题正确率、做题次数
    - 视频观看：观看时长、完成度
    - 资源浏览：PPT/文档访问次数
    
    不同行为反映不同的兴趣强度：
    做题 > 视频观看 > 资源浏览
    """

    def __init__(self, alpha=0.7, beta=0.3):
        self.neo4j = Neo4jManager()
        self.alpha = alpha
        self.beta = beta
        
        self.behavior_weights = {
            "practice": 0.5,
            "video": 0.3,
            "resource": 0.2
        }

    def get_practice_behavior(self, student_id):
        """
        获取用户的做题行为数据
        """
        query = """
        MATCH (s:Student {id: $sid})-[r:MASTERED]->(k:Knowledge)
        WHERE r.total_questions > 0
        RETURN k.name AS kp, r.correct_questions AS correct,
               r.total_questions AS total, r.mastery AS mastery
        """
        result = self.neo4j.run_query(query, {"sid": student_id})
        
        behaviors = {}
        for r in result:
            behaviors[r["kp"]] = {
                "correct": r["correct"] or 0,
                "total": r["total"] or 0,
                "accuracy": (r["correct"] or 0) / (r["total"] or 1),
                "mastery": r["mastery"] or 0
            }
        return behaviors

    def get_video_behavior(self, student_id):
        """
        获取用户的视频观看行为
        模拟数据：根据知识点匹配视频资源
        """
        query = """
        MATCH (k:Knowledge)
        WHERE k.name =~ '\\d+\\.\\d+\\.\\d+.*'
        RETURN k.name AS kp
        """
        result = self.neo4j.run_query(query)
        
        behaviors = {}
        for r in result:
            kp = r["kp"]
            ch_num = int(kp.split('.')[0])
            section_num = int(kp.split('.')[1])
            
            seed = hash(student_id + kp) % 100
            
            if seed < 60:
                watch_rate = 0.7 + (seed % 30) / 100
            elif seed < 80:
                watch_rate = 0.4 + (seed % 20) / 100
            else:
                watch_rate = (seed % 40) / 100
            
            behaviors[kp] = {
                "watch_rate": round(watch_rate, 4),
                "completed": watch_rate > 0.8
            }
        
        return behaviors

    def get_resource_behavior(self, student_id):
        """
        获取用户的资源浏览行为
        模拟数据：根据知识点匹配PPT/文档资源
        """
        query = """
        MATCH (c:Chapter)
        RETURN c.name AS chapter
        """
        result = self.neo4j.run_query(query)
        
        behaviors = {}
        for r in result:
            chapter = r["chapter"]
            ch_num = int(chapter.replace('第', '').replace('章', ''))
            
            seed = hash(student_id + chapter) % 100
            
            if seed < 50:
                view_count = 3 + (seed % 5)
            elif seed < 80:
                view_count = 1 + (seed % 3)
            else:
                view_count = 0
            
            behaviors[chapter] = {
                "view_count": view_count,
                "downloaded": view_count > 2
            }
        
        return behaviors

    def compute_multi_behavior_score(self, student_id):
        """
        综合多种行为计算用户对知识点的兴趣分数
        
        Score(kp) = w1 * Practice(kp) + w2 * Video(kp) + w3 * Resource(kp)
        """
        practice = self.get_practice_behavior(student_id)
        video = self.get_video_behavior(student_id)
        resource = self.get_resource_behavior(student_id)
        
        all_kps = set()
        all_kps.update(practice.keys())
        all_kps.update(video.keys())
        
        for kp in resource.keys():
            all_kps.add(kp)
        
        scores = {}
        for kp in all_kps:
            practice_score = 0
            video_score = 0
            resource_score = 0
            
            if kp in practice:
                p = practice[kp]
                practice_score = p["mastery"] * 0.6 + p["accuracy"] * 0.4
            
            if kp in video:
                video_score = video[kp]["watch_rate"]
            
            ch_match = kp.split('.')[0] + '.' if '.' in kp else kp
            for ch, res in resource.items():
                if ch_match.startswith(ch[:2]):
                    resource_score = min(res["view_count"] / 5.0, 1.0)
                    break
            
            total_score = (self.behavior_weights["practice"] * practice_score +
                          self.behavior_weights["video"] * video_score +
                          self.behavior_weights["resource"] * resource_score)
            
            scores[kp] = {
                "practice_score": round(practice_score, 4),
                "video_score": round(video_score, 4),
                "resource_score": round(resource_score, 4),
                "total_score": round(total_score, 4)
            }
        
        return scores

    def get_behavior_features(self, student_id, kp_name):
        """
        获取特定知识点的多行为特征
        """
        practice = self.get_practice_behavior(student_id)
        video = self.get_video_behavior(student_id)
        resource = self.get_resource_behavior(student_id)
        
        features = {
            "practice": None,
            "video": None,
            "resource": None
        }
        
        if kp_name in practice:
            features["practice"] = practice[kp_name]
        
        if kp_name in video:
            features["video"] = video[kp_name]
        
        ch_num = kp_name.split('.')[0] if '.' in kp_name else None
        if ch_num:
            chapter_key = f"第{ch_num}章"
            if chapter_key in resource:
                features["resource"] = resource[chapter_key]
        
        return features

    def close(self):
        self.neo4j.close()


if __name__ == "__main__":
    mbm = MultiBehaviorModel(alpha=0.7, beta=0.3)
    scores = mbm.compute_multi_behavior_score("3220602001刘大")
    
    print("多行为评分结果（前10个知识点）:")
    sorted_scores = sorted(scores.items(), key=lambda x: x[1]["total_score"], reverse=True)
    for kp, s in sorted_scores[:10]:
        print(f"{kp} | 总分: {s['total_score']:.4f} | "
              f"做题: {s['practice_score']:.4f} | "
              f"视频: {s['video_score']:.4f} | "
              f"资源: {s['resource_score']:.4f}")
    
    mbm.close()
