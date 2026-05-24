import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_processing.knowledge_graph_builder import KnowledgeGraphBuilder
from data_processing.student_data_loader import StudentDataLoader
from recommendation.hybrid_recommender import HybridRecommender
from data_processing.neo4j_manager import Neo4jManager

def test_knowledge_graph():
    print("=== Testing Knowledge Graph Builder ===")
    with open("data/studentdata/catalog.txt", "r", encoding="utf-8") as f:
        catalog = f.read()
    
    builder = KnowledgeGraphBuilder()
    builder.build_graph(catalog)
    builder.close()
    print("Knowledge graph built successfully!\n")

def test_student_data():
    print("=== Testing Student Data Loader ===")
    loader = StudentDataLoader()
    
    csv_path = "data/studentdata/3220602001刘大.csv"
    if os.path.exists(csv_path):
        loader.load_student_from_csv(csv_path, "3220602001刘大")
        print(f"Loaded data for 3220602001刘大\n")
    else:
        print(f"CSV file not found: {csv_path}\n")
    
    loader.close()

def test_recommendations():
    print("=== Testing Recommendation System ===")
    recommender = HybridRecommender()
    
    try:
        recs = recommender.recommend("3220602001刘大", top_k=5)
        print(f"Got {len(recs)} recommendations:")
        for r in recs:
            print(f"  {r['name']} | 总分: {r['total_score']:.3f} | 掌握度: {r['mastery']:.2f}")
    except Exception as e:
        print(f"Error: {e}")
    
    recommender.close()

def test_queries():
    print("\n=== Testing Neo4j Queries ===")
    neo4j = Neo4jManager()
    
    # Test chapter count
    result = neo4j.run_query("MATCH (c:Chapter) RETURN count(c) AS cnt")
    print(f"Chapters: {result[0]['cnt']}")
    
    # Test knowledge count
    result = neo4j.run_query("MATCH (k:Knowledge) RETURN count(k) AS cnt")
    print(f"Knowledge points: {result[0]['cnt']}")
    
    # Test student count
    result = neo4j.run_query("MATCH (s:Student) RETURN count(s) AS cnt")
    print(f"Students: {result[0]['cnt']}")
    
    # Test subsection count
    result = neo4j.run_query("""
        MATCH (c:Chapter)-[:包含]->(s:Knowledge)-[:包含]->(ss:Knowledge)
        WHERE c.name STARTS WITH '第1章'
        RETURN count(ss) AS cnt
    """)
    print(f"Subsections in Chapter 1: {result[0]['cnt']}")
    
    neo4j.close()

if __name__ == "__main__":
    test_knowledge_graph()
    test_student_data()
    test_queries()
    test_recommendations()
