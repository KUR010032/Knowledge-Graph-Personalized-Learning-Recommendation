import sys
sys.path.insert(0, 'app')
from app import get_knowledge_graph

graph = get_knowledge_graph('S001')
nodes = graph.get('nodes', [])
edges = graph.get('edges', [])

print('=== SUMMARY STATS ===')
print('Total nodes:', len(nodes))
print('Total edges:', len(edges))

diamonds = [n for n in nodes if n.get('shape') == 'diamond']
hexagons = [n for n in nodes if n.get('shape') == 'hexagon']
squares = [n for n in nodes if n.get('shape') == 'square']
circles = [n for n in nodes if n.get('shape') == 'circle']

print('Diamond (course root):', len(diamonds))
print('Hexagon (chapters):', len(hexagons))
print('Square (sections):', len(squares))
print('Circle (subsections):', len(circles))

contain = [e for e in edges if e.get('type') == '包含']
prereq = [e for e in edges if e.get('type') == '先修']
related = [e for e in edges if e.get('type') == '相关']
print('Containment edges:', len(contain))
print('Prerequisite edges:', len(prereq))
print('Related edges:', len(related))

# Check 1.1 and 1.6
for n in nodes:
    if n.get('id') == '1.1':
        print('\n1.1 label:', n.get('label'))
    if n.get('id') == '1.6':
        print('1.6 label:', n.get('label'))

# 10 random sample
print('\n=== 10 SAMPLE NODES ===')
for n in nodes[5:15]:
    print('  %-10s | %-40s | %-10s | mastery=%.0f%% | level=%s' % (
        n.get('id',''), n.get('label','')[:40], n.get('shape',''),
        (n.get('mastery',0) or 0)*100, n.get('level','?')
    ))

# Node sizes check
print('\n=== SIZE CHECK ===')
for n in nodes:
    print('  %-10s shape=%-10s size=%s font=%s' % (
        n.get('id',''), n.get('shape',''), n.get('size','?'), n.get('fontSize','?')
    ))