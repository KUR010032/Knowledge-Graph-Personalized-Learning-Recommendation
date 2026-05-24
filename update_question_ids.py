import json
from neo4j import GraphDatabase

# Load real questions
with open('app/resources/questions.json', 'r', encoding='utf-8') as f:
    qdata = json.load(f)

all_questions = qdata['questions']
print(f"Loaded {len(all_questions)} questions from questions.json")

neo4j_uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "12345678"))

with driver.session() as session:
    # Delete all existing Question nodes and their relationships
    session.run("MATCH (q:Question)-[r]-() DELETE r")
    result = session.run("MATCH (q:Question) DELETE q RETURN count(q) as deleted")
    record = result.single()
    print(f"Deleted {record['deleted']} old Question nodes")
    
    # Add real questions with proper IDs
    added = 0
    for q in all_questions:
        session.run("""
            MERGE (q:Question {id: $qid})
            SET q.content = $content, q.options = $options,
                q.answer = $answer, q.difficulty = $difficulty,
                q.knowledge_point = $kp
            WITH q
            MATCH (k:Knowledge {name: $kp})
            MERGE (q)-[:属于]->(k)
        """, {
            "qid": q['id'],
            "content": q['question'],
            "options": q.get('options', []),
            "answer": q.get('answer', ''),
            "difficulty": q.get('difficulty', 'medium'),
            "kp": q['knowledge_point']
        })
        added += 1
    
    print(f"Added {added} real Question nodes with proper IDs")

driver.close()
