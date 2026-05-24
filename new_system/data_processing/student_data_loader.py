import csv
import random
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_processing.neo4j_manager import Neo4jManager

class StudentDataLoader:
    def __init__(self):
        self.neo4j = Neo4jManager()
    
    def load_student_from_csv(self, csv_path, student_id):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                kp_name = row["知识点"].strip()
                mastery = float(row["掌握度"])
                total = int(row["总题数"])
                correct = int(row["正确数"])
                
                self.neo4j.execute_write("""
                    MERGE (s:Student {id: $sid})
                    MERGE (k:Knowledge {name: $kp})
                    MERGE (s)-[r:MASTERED]->(k)
                    SET r.mastery = $mastery,
                        r.total_questions = $total,
                        r.correct_questions = $correct
                """, {
                    "sid": student_id,
                    "kp": kp_name,
                    "mastery": mastery,
                    "total": total,
                    "correct": correct
                })
    
    def generate_synthetic_data(self, student_id, knowledge_points):
        for kp in knowledge_points:
            mastery = round(random.uniform(0.1, 0.95), 4)
            total = random.randint(5, 20)
            correct = int(total * mastery)
            
            self.neo4j.execute_write("""
                MERGE (s:Student {id: $sid})
                MERGE (k:Knowledge {name: $kp})
                MERGE (s)-[r:MASTERED]->(k)
                SET r.mastery = $mastery,
                    r.total_questions = $total,
                    r.correct_questions = $correct
            """, {
                "sid": student_id,
                "kp": kp,
                "mastery": mastery,
                "total": total,
                "correct": correct
            })
    
    def close(self):
        self.neo4j.close()

if __name__ == "__main__":
    loader = StudentDataLoader()
    # Load real student data
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "studentdata", "3220602001刘大.csv")
    loader.load_student_from_csv(csv_path, "3220602001刘大")
    loader.close()
