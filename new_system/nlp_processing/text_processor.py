import re
import jieba
import jieba.analyse
from collections import Counter
import numpy as np

class TextProcessor:
    def __init__(self):
        self.stopwords = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'])
    
    def extract_keywords(self, text, top_k=10):
        keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=True)
        return keywords
    
    def tokenize(self, text):
        words = jieba.lcut(text)
        return [w for w in words if w not in self.stopwords and len(w) > 1]
    
    def calculate_similarity(self, text1, text2):
        words1 = set(self.tokenize(text1))
        words2 = set(self.tokenize(text2))
        
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return 0.0
        return len(intersection) / len(union)
    
    def extract_entities(self, text):
        pattern = r'(\d+\.\d+(?:\.\d+)?)\s+(.+)'
        match = re.match(pattern, text)
        if match:
            return {
                'code': match.group(1),
                'name': match.group(2)
            }
        return None

class Word2VecProcessor:
    def __init__(self):
        self.embeddings = {}
        self.knowledge_embeddings = {}
    
    def build_knowledge_embeddings(self, knowledge_points):
        for kp in knowledge_points:
            words = jieba.lcut(kp)
            # Simple average embedding (placeholder for real word2vec)
            vec = np.random.randn(100)
            self.knowledge_embeddings[kp] = vec / np.linalg.norm(vec)
    
    def calculate_semantic_similarity(self, kp1, kp2):
        if kp1 not in self.knowledge_embeddings or kp2 not in self.knowledge_embeddings:
            return 0.0
        
        v1 = self.knowledge_embeddings[kp1]
        v2 = self.knowledge_embeddings[kp2]
        
        return float(np.dot(v1, v2))

if __name__ == "__main__":
    processor = TextProcessor()
    text = "操作系统是管理计算机硬件与软件资源的系统软件"
    print(processor.extract_keywords(text))
    print(processor.tokenize(text))
