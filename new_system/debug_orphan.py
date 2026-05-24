from data_processing.neo4j_manager import Neo4jManager

neo4j = Neo4jManager()

print("=== All Knowledge nodes without incoming 包含 edges ===")
result = neo4j.run_query("""
    MATCH (n:Knowledge)
    WHERE NOT ()-[:包含]->(n)
    RETURN n.name AS name
""")
print(f"Found {len(result)} nodes")
for r in result:
    print(f"  {r['name']}")

print("\n=== All Knowledge nodes without outgoing 包含 edges ===")
result2 = neo4j.run_query("""
    MATCH (n:Knowledge)
    WHERE NOT (n)-[:包含]->()
    RETURN n.name AS name
""")
print(f"Found {len(result2)} nodes")
for r in result2:
    print(f"  {r['name']}")

print("\n=== Check 3.x nodes specifically ===")
result3 = neo4j.run_query("""
    MATCH (n:Knowledge)
    WHERE n.name STARTS WITH '3.'
    OPTIONAL MATCH (n)-[:包含]->(child)
    OPTIONAL MATCH (parent)-[:包含]->(n)
    RETURN n.name AS name, collect(child.name) AS children, collect(parent.name) AS parents
""")
for r in result3:
    print(f"  {r['name']}")
    print(f"    children: {r['children']}")
    print(f"    parents: {r['parents']}")

neo4j.close()
