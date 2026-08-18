import urllib.request, http.cookiejar, urllib.parse, json

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.open('http://127.0.0.1:5000/login', urllib.parse.urlencode({
    'role': 'student', 'user_id': '3220602001', 'password': '123456'
}).encode())

r = opener.open('http://127.0.0.1:5000/student/flow-graph/data')
d = json.loads(r.read())
nodes = d['nodes']
edges = d['edges']

print("=" * 60)
print("1. 节点类型统计")
print("=" * 60)
shapes = {}
for n in nodes:
    s = n.get('shape', 'circle')
    shapes[s] = shapes.get(s, 0) + 1
for s, c in sorted(shapes.items()):
    print(f"  {s}: {c}")
print(f"  Total: {len(nodes)}")

print()
print("=" * 60)
print("2. 关系类型统计")
print("=" * 60)
etypes = {}
for e in edges:
    t = e.get('type', '?')
    etypes[t] = etypes.get(t, 0) + 1
for t, c in sorted(etypes.items()):
    print(f"  {t}: {c}")

print()
print("=" * 60)
print("3. 包含关系数量")
print("=" * 60)
contains = [e for e in edges if e.get('type') == '包含']
print(f"  Total: {len(contains)}")

print()
print("=" * 60)
print("4. 图谱接口 nodes 数量: {0}".format(len(nodes)))
print("5. 图谱接口 links 数量: {0}".format(len(edges)))

print()
print("=" * 60)
print("6. 任意5条包含关系示例")
print("=" * 60)
node_map = {n['id']: n.get('label', n['id'])[:30] for n in nodes}
for i, e in enumerate(contains[:5]):
    fn = node_map.get(e['from'], e['from'])
    tn = node_map.get(e['to'], e['to'])
    print(f"  {i+1}. {e['from']}({fn}) --包含--> {e['to']}({tn})")

print()
print("=" * 60)
print("7. 任意5个节点颜色状态示例")
print("=" * 60)
shown = 0
for n in nodes:
    if shown >= 5:
        break
    if n.get('shape') in ('square', 'circle'):
        m = n.get('mastery', 0)
        s = '已掌握' if m >= 0.8 else ('良好' if m >= 0.6 else ('需巩固' if m > 0 else '未学习'))
        print(f"  {n['id']} {n.get('label','')[:30]} shape={n['shape']} mastery={round(m,2):.2f} -> {s}")
        shown += 1

print()
print("=" * 60)
print("8. 方形节点和圆形节点连接证明")
print("=" * 60)
sq_ids = {n['id'] for n in nodes if n.get('shape') == 'square'}
sq_to_circle = [e for e in contains if e['from'] in sq_ids]
print(f"  方形节点到圆形节点的包含关系: {len(sq_to_circle)} 条")
for e in sq_to_circle[:5]:
    print(f"  {e['from']} -> {e['to']}")

print()
print("=" * 60)
print("9. 颜色与掌握度阈值对应")
print("=" * 60)
for n in nodes:
    if n['id'] == '1.1.1':
        m = n.get('mastery', 0)
        s = '已掌握' if m >= 0.8 else ('良好' if m >= 0.6 else ('需巩固' if m > 0 else '未学习'))
        print(f"  1.1.1 mastery={round(m,2):.2f} status={s}")