# -*- coding: utf-8 -*-
import json

with open('resources/students_mastery.json', 'r', encoding='utf-8') as f:
    m = json.load(f)

with open('resources/questions.json', 'r', encoding='utf-8') as f:
    qdata = json.load(f)

kps = ['1.2 操作系统的形成和发展', '1.3 操作系统的分类', '1.4 操作系统的运行环境', '1.5 操作系统的结构']
sids = ['3220602001', '3220602004', '3220602006']

print('=== students_mastery.json Verification ===')
for sid in sids:
    sm = m.get(sid, {})
    print('  %s:' % sid)
    for k in kps:
        v = sm.get(k, 0)
        print('    %s: %.4f (%.1f%%)' % (k, v, v * 100))
    print()

print('=== All-zero check (1.2-1.5) ===')
zero_found = False
for sid in m:
    sm = m[sid]
    for k in kps:
        if k in sm and sm[k] == 0:
            print('  %s: %s = 0' % (sid, k))
            zero_found = True

if not zero_found:
    print('  No zero mastery for 1.2-1.5 across all students!')

print()
print('=== Question Count by KP ===')
kps_by_id = {'1.2': {'easy': 0, 'medium': 0, 'hard': 0, 'total': 0},
             '1.3': {'easy': 0, 'medium': 0, 'hard': 0, 'total': 0},
             '1.4': {'easy': 0, 'medium': 0, 'hard': 0, 'total': 0},
             '1.5': {'easy': 0, 'medium': 0, 'hard': 0, 'total': 0}}
for q in qdata.get('questions', []):
    kid = q.get('knowledge_id', '')
    if kid in kps_by_id:
        kps_by_id[kid]['total'] += 1
        diff = q.get('difficulty', '')
        if diff in ('easy', 'medium', 'hard'):
            kps_by_id[kid][diff] += 1

for kid, info in kps_by_id.items():
    print('  %s: total=%d, easy=%d, medium=%d, hard=%d' % (
        kid, info['total'], info['easy'], info['medium'], info['hard']))

SAMPLE_IDS = ['q1_2_11', 'q1_2_13', 'q1_3_11', 'q1_3_13', 'q1_4_4', 'q1_4_9', 'q1_5_4', 'q1_5_10']

print()
print('=== New Question Sample (8 questions) ===')
for q in qdata.get('questions', []):
    if q['id'] in SAMPLE_IDS:
        print('  %s [%s/%s]: %s' % (q['id'], q['knowledge_id'], q['difficulty'], q['question'][:60]))
        print('    answer=%s, options=%s' % (q.get('answer'), [o[:30] for o in q.get('options', [])]))
        print()