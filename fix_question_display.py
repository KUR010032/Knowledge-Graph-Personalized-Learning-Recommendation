from neo4j import GraphDatabase

neo4j_uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "12345678"))

with driver.session() as session:
    # Update Question nodes to use id as display name
    result = session.run("""
        MATCH (q:Question)
        SET q.name = q.id
        RETURN count(q) as updated
    """)
    record = result.single()
    print(f"Updated {record['updated']} Question nodes to use id as name")

driver.close()
