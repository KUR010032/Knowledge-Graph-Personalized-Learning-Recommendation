from data_processing.neo4j_manager import Neo4jManager

neo4j = Neo4jManager()

print("=== Chapter 3 containment ===")
result = neo4j.run_query("""
    MATCH (c:Chapter {name: '第3章 互斥与同步'})-[:包含]->(s:Knowledge)
    RETURN s.name AS name
""")
print(f"Found {len(result)} direct children")
for r in result:
    print(f"  {r['name']}")

print("\n=== All nodes with their labels ===")
result2 = neo4j.run_query("""
    MATCH (n)
    WHERE n.name CONTAINS '3'
    RETURN labels(n) AS labels, n.name AS name
""")
for r in result2:
    print(f"  {r['labels']}: {r['name']}")

print("\n=== Orphan nodes (no incoming 包含 edges) ===")
result3 = neo4j.run_query("""
    MATCH (n:Knowledge)
    WHERE NOT (n)-[:包含]->() AND NOT ()-[:包含]->(n)
    AND NOT (n:Chapter)
    RETURN n.name AS name
""")
print(f"Found {len(result3)} orphan knowledge nodes")
for r in result3:
    print(f"  {r['name']}")

neo4j.close()
