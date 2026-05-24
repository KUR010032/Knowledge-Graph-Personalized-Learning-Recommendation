import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ContentBasedRecommender:
    def __init__(self):
        self.tfidf = TfidfVectorizer(max_features=100)
        self.item_vectors = None
        self.item_ids = []
    
    def fit(self, item_descriptions):
        """
        item_descriptions: dict {item_id: description_text}
        """
        self.item_ids = list(item_descriptions.keys())
        texts = [item_descriptions[iid] for iid in self.item_ids]
        self.item_vectors = self.tfidf.fit_transform(texts)
    
    def get_similar_items(self, item_id, top_k=5):
        if item_id not in self.item_ids:
            return []
        
        item_idx = self.item_ids.index(item_id)
        item_vector = self.item_vectors[item_idx]
        
        similarities = cosine_similarity(item_vector, self.item_vectors).flatten()
        similar_indices = np.argsort(similarities)[::-1][1:top_k+1]
        
        return [(self.item_ids[i], similarities[i]) for i in similar_indices]
    
    def recommend_for_user(self, user_history, top_k=10):
        """
        user_history: dict {item_id: rating}
        """
        if not user_history:
            return []
        
        # Create user profile from liked items
        user_vector = np.zeros(self.item_vectors.shape[1])
        total_weight = 0
        
        for item_id, rating in user_history.items():
            if item_id in self.item_ids:
                idx = self.item_ids.index(item_id)
                user_vector += rating * self.item_vectors[idx].toarray().flatten()
                total_weight += rating
        
        if total_weight > 0:
            user_vector /= total_weight
        
        # Find similar items
        similarities = cosine_similarity(user_vector.reshape(1, -1), self.item_vectors).flatten()
        
        recommendations = []
        for i, sim in enumerate(similarities):
            item_id = self.item_ids[i]
            if item_id not in user_history or user_history[item_id] < 0.6:
                recommendations.append((item_id, sim))
        
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:top_k]

class TopicModelRecommender:
    def __init__(self, n_topics=5):
        self.n_topics = n_topics
        self.topic_distributions = {}
    
    def fit(self, item_texts):
        """
        Simple topic modeling using keyword clustering
        """
        # Placeholder for LDA implementation
        pass
    
    def get_item_topics(self, item_id):
        return self.topic_distributions.get(item_id, [])

if __name__ == "__main__":
    cbr = ContentBasedRecommender()
    descriptions = {
        "1.1": "操作系统基本概念 计算机系统",
        "1.2": "操作系统发展历史 演变",
        "2.1": "进程概念 并发执行"
    }
    cbr.fit(descriptions)
    print(cbr.get_similar_items("1.1"))
