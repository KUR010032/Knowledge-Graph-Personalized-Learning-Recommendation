from neo4j import GraphDatabase
import json

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "12345678"),
    connection_timeout=5
)

print("=== Neo4j Diagnostic ===")

with driver.session() as s:
    print("\n1. Relation Types:")
    try:
        r = s.run("CALL db.relationshipTypes()")
        for row in r:
            print("  ", row[0])
    except Exception as e:
        print("  Error:", e)

    print("\n2. Relation Type Counts:")
    try:
        r = s.run("MATCH ()-[r]->() RETURN type(r) AS relation, count(r) AS count ORDER BY count DESC")
        for row in r:
            print("  ", row["relation"], ":", row["count"])
    except Exception as e:
        print("  Error:", e)

    print("\n3. Node Label Counts:")
    try:
        r = s.run("MATCH (n) RETURN labels(n) AS labels, count(n) AS count")
        for row in r:
            print("  ", row["labels"], ":", row["count"])
    except Exception as e:
        print("  Error:", e)

    print("\n4. Containment Relations (first 20):")
    try:
        r = s.run("""
        MATCH (a)-[r]->(b)
        WHERE type(r) IN ['包含','CONTAINS','HAS_KNOWLEDGE','BELONGS_TO']
        RETURN labels(a) AS a_labels, a.name AS a_name,
               labels(b) AS b_labels, b.name AS b_name,
               type(r) AS rel_type
        LIMIT 20
        """)
        count = 0
        for row in r:
            count += 1
            print("  [{count}] ({a_labels}) {a_name} --[{rel}]--> ({b_labels}) {b_name}".format(
                count=count,
                a_labels=row["a_labels"],
                a_name=row["a_name"],
                rel=row["rel_type"],
                b_labels=row["b_labels"],
                b_name=row["b_name"]
            ))
        print("  Total shown:", count)
    except Exception as e:
        print("  Error:", e)

    print("\n5. Knowledge nodes (first 10):")
    try:
        r = s.run("MATCH (k:Knowledge) RETURN k.name AS name LIMIT 10")
        for row in r:
            print("  ", row["name"])
    except Exception as e:
        print("  Error:", e)

    print("\n6. Chapter nodes:")
    try:
        r = s.run("MATCH (c:Chapter) RETURN c.name AS name")
        for row in r:
            print("  ", row["name"])
    except Exception as e:
        print("  Error:", e)

    print("\n7. Total containment relation count:")
    try:
        r = s.run("""
        MATCH ()-[r]->()
        WHERE type(r) IN ['包含','CONTAINS','HAS_KNOWLEDGE','BELONGS_TO']
        RETURN count(r) AS cnt
        """)
        for row in r:
            print("  Count:", row["cnt"])
    except Exception as e:
        print("  Error:", e)

    print("\n8. Total Knowledge nodes:")
    try:
        r = s.run("MATCH (k:Knowledge) RETURN count(k) AS cnt")
        for row in r:
            print("  Count:", row["cnt"])
    except Exception as e:
        print("  Error:", e)

print("\n=== Done ===")
driver.close()