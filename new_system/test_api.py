import requests
import json

resp = requests.get('http://127.0.0.1:5000/api/knowledge-graph/2021001')
data = resp.json()

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

print("\n=== Subsection nodes ===")
for n in data['nodes']:
    if n['level'] == 2:
        print(f"  {n['label']}")

print("\n=== Edges containing Chapter 3 ===")
for e in data['edges']:
    if '3' in e['from'] or '3' in e['to']:
        print(f"  {e['from']} --[{e['type']}]--> {e['to']}")
