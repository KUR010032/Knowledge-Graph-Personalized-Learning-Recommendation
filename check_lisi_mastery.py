from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', '12345678'))

with driver.session() as session:
    print('=== 李四掌握度最低的知识点 ===')
    result = session.run("""
    MATCH (s:Student {id: '3220602004李四'})-[r:MASTERED]->(k:Knowledge)
    WHERE k.name STARTS WITH '1.' OR k.name STARTS WITH '2.' OR k.name STARTS WITH '3.'
    RETURN k.name AS name, r.mastery AS mastery
    ORDER BY r.mastery ASC
    LIMIT 10
    """)
    
    for r in result:
        print(f"  {r['name']}: {r['mastery']*100:.1f}%")
    
    print('\n=== 检查特定知识点是否存在 ===')
    kps_to_check = ['多核环境下的进程同步', '两阶段加锁', '打瞌睡的理发师问题']
    for kp in kps_to_check:
        result2 = session.run("""
        MATCH (k:Knowledge {name: $kp})
        RETURN k.name AS name
        """, kp=kp)
        records = list(result2)
        if records:
            print(f"  {kp}: 存在")
        else:
            print(f"  {kp}: 不存在")

driver.close()
