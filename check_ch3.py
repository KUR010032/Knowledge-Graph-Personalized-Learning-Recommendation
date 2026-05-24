import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'new_system'))

from data_processing.neo4j_manager import Neo4jManager

neo4j = Neo4jManager()

print("=" * 60)
print("检查第三章相关节点")
print("=" * 60)

# Check all Chapter 3 related nodes
result = neo4j.run_query('MATCH (n) WHERE n.name =~ "3\\\\..*" RETURN n.name AS name ORDER BY n.name')
print('\n所有以3.开头的节点:')
for r in result:
    print(f"  - {r['name']}")

# Check Chapter 3 sections
result2 = neo4j.run_query('MATCH (c:Chapter)-[:包含]->(s:Knowledge) WHERE c.name CONTAINS "第3章" RETURN s.name AS name ORDER BY s.name')
print('\n第3章直接包含的节:')
for r in result2:
    print(f"  - {r['name']}")

# Check subsections under Chapter 3 sections
result3 = neo4j.run_query('''
MATCH (c:Chapter)-[:包含]->(s:Knowledge)-[:包含]->(k:Knowledge)
WHERE c.name CONTAINS "第3章"
RETURN s.name AS section, k.name AS subsection
ORDER BY s.name, k.name
''')
print('\n第3章的小节关系:')
for r in result3:
    print(f"  {r['section']} -> {r['subsection']}")

# Check for orphaned nodes (no incoming 包含 edges)
result4 = neo4j.run_query('''
MATCH (n:Knowledge)
WHERE NOT (n:Chapter)
AND NOT ()-[:包含]->(n)
RETURN n.name AS name
''')
print('\n游离节点 (没有 incoming 包含 关系):')
for r in result4:
    print(f"  - {r['name']}")

# Check all chapters and their section counts
result5 = neo4j.run_query('''
MATCH (c:Chapter)-[:包含]->(s:Knowledge)
WHERE s.name =~ "\\d+\\.\\d+ .*" AND NOT s.name =~ "\\d+\\.\\d+\\.\\d+.*"
RETURN c.name AS chapter, count(s) AS section_count
ORDER BY c.name
''')
print('\n各章节的节数量:')
for r in result5:
    print(f"  {r['chapter']}: {r['section_count']} 个节")

# Check all chapters
result6 = neo4j.run_query('MATCH (c:Chapter) RETURN c.name AS name ORDER BY c.name')
print('\n所有章节:')
for r in result6:
    print(f"  - {r['name']}")

neo4j.close()
