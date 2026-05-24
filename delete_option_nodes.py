from neo4j import GraphDatabase

neo4j_uri = "bolt://localhost:7687"
driver = GraphDatabase.driver(neo4j_uri, auth=("neo4j", "12345678"))

with driver.session() as session:
    # 先删除所有与Option节点相关的关系
    session.run("MATCH (:Option)-[r]-() DELETE r")
    # 删除所有Option节点
    result = session.run("MATCH (o:Option) DELETE o RETURN count(o) as deleted")
    record = result.single()
    print(f"Deleted {record['deleted']} Option nodes")

driver.close()
