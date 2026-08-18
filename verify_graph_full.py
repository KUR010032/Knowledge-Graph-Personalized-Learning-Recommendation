import sys
sys.path.insert(0, 'app')
from app import get_knowledge_graph, build_knowledge_catalog_names

# Test catalog names
names = build_knowledge_catalog_names()
print('=== CATALOG NAMES COUNT ===')
print('Total names:', len(names))
print('1.1:', names.get('1.1', 'MISSING'))
print('1.6:', names.get('1.6', 'MISSING'))
print()

# Test graph data
graph = get_knowledge_graph('S001')
nodes = graph.get('nodes', [])
edges = graph.get('edges', [])

shapes = {}
for n in nodes:
    s = n.get('shape', 'circle')
    shapes[s] = shapes.get(s, 0) + 1

levels = {}
for n in nodes:
    l = n.get('level', -99)
    levels[l] = levels.get(l, 0) + 1

etypes = {}
for e in edges:
    t = e.get('type', '?')
    etypes[t] = etypes.get(t, 0) + 1

print('=== NODE COUNTS ===')
print('Total nodes:', len(nodes))
print('Total edges:', len(edges))
print('Shapes:', shapes)
print('Levels:', levels)
print('Edge types:', etypes)

print()
print('=== 10 SAMPLE NODES ===')
for n in nodes[:10]:
    print('  id=%s, label=%s, shape=%s, level=%s, mastery=%s, levelName=%s' % (
        n.get('id',''), n.get('label','')[:50], n.get('shape',''),
        n.get('level','?'), n.get('mastery',0), n.get('levelName','?')
    ))

print()
print('=== SPECIFIC NODES (1.1*, 1.6) ===')
for n in nodes:
    lid = str(n.get('id', ''))
    if lid.startswith('1.1') or lid == '1.6':
        print('  id=%s, label=%s, shape=%s' % (n.get('id',''), n.get('label',''), n.get('shape','')))

contain_edges = [e for e in edges if e.get('type') == '包含']
prereq_edges = [e for e in edges if e.get('type') == '先修']
related_edges = [e for e in edges if e.get('type') == '相关']

print()
print('Containment edges:', len(contain_edges))
print('Prerequisite edges:', len(prereq_edges))
print('Related edges:', len(related_edges))

chapters = [n for n in nodes if n.get('shape') == 'hexagon' or n.get('level') == 0]
sections = [n for n in nodes if n.get('shape') == 'square' or n.get('level') == 1]
leaves = [n for n in nodes if n.get('shape') == 'circle' and n.get('level', -1) >= 2]
diamonds = [n for n in nodes if n.get('shape') == 'diamond']

print()
print('Chapter (hexagon) nodes:', len(chapters))
print('Section (square) nodes:', len(sections))
print('Subsection (circle) nodes:', len(leaves))
print('Root (diamond) nodes:', len(diamonds))

# Check 1.1 and 1.6 full names
for n in nodes:
    lid = str(n.get('id', ''))
    if lid == '1.1':
        print('\n1.1 full label:', n.get('label',''))
    if lid == '1.6':
        print('1.6 full label:', n.get('label',''))

# Clean sort for natural ordering
import re
def nat_key(s):
    parts = re.split(r'(\d+)', str(s))
    return [int(p) if p.isdigit() else p for p in parts]

print('\n=== ALL NODES (sorted) ===')
for n in sorted(nodes, key=lambda x: nat_key(x.get('id',''))):
    print('  %-8s %-45s %-10s lvl=%-2s m=%-4s' % (
        n.get('id',''), n.get('label','')[:45], n.get('shape',''),
        n.get('level','?'), n.get('mastery',0)
    ))

print()
print('=== CONTAINMENT EDGES (sorted) ===')
for e in sorted(contain_edges, key=lambda x: nat_key(x.get('to',''))):
    print('  %s -> %s' % (e.get('from','?'), e.get('to','?')))