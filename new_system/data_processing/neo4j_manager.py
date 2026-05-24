from neo4j import GraphDatabase
from config import Config

class Neo4jManager:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
    
    def close(self):
        self.driver.close()
    
    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return list(result)
    
    def execute_write(self, query, parameters=None):
        with self.driver.session() as session:
            session.execute_write(lambda tx: tx.run(query, parameters or {}))
    
    def clear_database(self):
        self.execute_write("MATCH (n) DETACH DELETE n")
    
    def create_indexes(self):
        indexes = [
            "CREATE INDEX knowledge_name IF NOT EXISTS FOR (n:Knowledge) ON (n.name)",
            "CREATE INDEX chapter_name IF NOT EXISTS FOR (n:Chapter) ON (n.name)",
            "CREATE INDEX student_id IF NOT EXISTS FOR (n:Student) ON (n.id)",
            "CREATE INDEX resource_name IF NOT EXISTS FOR (n:Resource) ON (n.name)"
        ]
        for idx in indexes:
            try:
                self.execute_write(idx)
            except Exception as e:
                print(f"Index creation warning: {e}")
