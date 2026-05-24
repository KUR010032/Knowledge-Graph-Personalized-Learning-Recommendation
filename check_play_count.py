from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', '12345678'))

with driver.session() as session:
    print('=== 李四的视频播放记录 ===')
    result = session.run("""
    MATCH (s:Student {id: '3220602004李四'})-[r:WATCHED]->(v:Video)
    RETURN v.name AS 视频名称, r.play_count AS 播放次数, r.watch_duration AS 观看时长, r.completion_rate AS 完成率
    ORDER BY r.play_count DESC
    """)
    
    records = list(result)
    if records:
        for rec in records:
            print(f"  {rec['视频名称']}: 播放{rec['播放次数']}次, 时长{rec['观看时长']}秒, 完成率{rec['完成率']*100:.1f}%")
    else:
        print('  暂无视频播放记录')
    
    print('\n=== 李四的资源查看记录 ===')
    result2 = session.run("""
    MATCH (s:Student {id: '3220602004李四'})-[r:VIEWED]->(res:Resource)
    RETURN res.name AS 资源名称, r.view_count AS 查看次数, r.download_count AS 下载次数, r.downloaded AS 是否下载
    ORDER BY r.view_count DESC
    """)
    
    records2 = list(result2)
    if records2:
        for rec in records2:
            print(f"  {rec['资源名称']}: 查看{rec['查看次数']}次, 下载{rec['下载次数']}次, 已下载={rec['是否下载']}")
    else:
        print('  暂无资源查看记录')

driver.close()
