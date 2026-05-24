from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', '12345678'))

with driver.session() as session:
    print('=== 李四查看的资源（正确属性名）===')
    result = session.run("""
    MATCH (s:Student {id: '3220602004李四'})-[r:VIEWED]->(res:Resource)
    RETURN res.name, r.view_count, r.downloaded, r.view_time
    ORDER BY r.view_count DESC
    LIMIT 10
    """)
    
    for r in result:
        print(f"  {r['res.name']}: 查看{r['r.view_count']}次, 下载={r['r.downloaded']}")
    
    print('\n=== 李四观看的视频（正确属性名）===')
    result2 = session.run("""
    MATCH (s:Student {id: '3220602004李四'})-[r:WATCHED]->(v:Video)
    RETURN v.name, r.watch_duration, r.completion_rate, r.watch_time
    ORDER BY r.completion_rate DESC
    LIMIT 10
    """)
    
    for r in result2:
        print(f"  {r['v.name']}: 观看{r['r.watch_duration']}秒, 完成率{r['r.completion_rate']*100:.1f}%")

driver.close()
