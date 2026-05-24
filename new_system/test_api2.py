import urllib.request
import json

url = 'http://127.0.0.1:5000/api/knowledge-graph/2021001'
resp = urllib.request.urlopen(url)
data = json.loads(resp.read().decode('utf-8'))

print(f"Total nodes: {len(data['nodes'])}")
print(f"Total edges: {len(data['edges'])}")

print("\n=== Chapter nodes ===")
for n in data['nodes']:
    if n['level'] == 0:
        print(f"  {n['label']}")

print("\n=== Section nodes ===")
for n in data['nodes']:
    if n['level'] == 1:
        print(f"  {n['label']}")

print("\n=== Subsection nodes (first 10) ===")
count = 0
for n in data['nodes']:
    if n['level'] == 2:
        print(f"  {n['label']}")
        count += 1
        if count >= 10:
            break

print(f"\nTotal subsections: {sum(1 for n in data['nodes'] if n['level'] == 2)}")

print("\n=== Edges from Chapter 3 ===")
for e in data['edges']:
    if '第3章' in e['from'] or '第3章' in e['to']:
        print(f"  {e['from']} --[{e['type']}]--> {e['to']}")

print("\n=== Edges from 3.x sections ===")
for e in data['edges']:
    if e['from'].startswith('3.') or e['to'].startswith('3.'):
        print(f"  {e['from']} --[{e['type']}]--> {e['to']}")
