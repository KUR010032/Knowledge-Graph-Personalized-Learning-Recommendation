# -*- coding: utf-8 -*-
import json
import time
from app import kgcf_recommend_data

students = ['3220602001刘大', '3220602004李四', '3220602006赵六']

for sid in students:
    t0 = time.time()
    r = kgcf_recommend_data(sid, max_targets=6)
    cost = (time.time() - t0) * 1000
    print(f'=== {sid} ===')
    print(f'Cost: {cost:.0f}ms')
    print(f'Type: {r["student"]["type"]}, Recommend: {r["recommend_type"]}, Avg: {r["avg_mastery"]:.4f}')
    print(f'Targets count: {len(r["targets"])}')
    for t in r['targets']:
        print(f'  {t["code"]} {t["name"]}: M={t["mastery"]:.4f}, status={t["status"]}, reason={t.get("reason","")}')
        print(f'    resources={len(t.get("resources",[]))}, questions={len(t.get("questions",[]))}')
        for res in t.get('resources', []):
            print(f'      -> {res.get("title","")} [{res.get("type","")}] ({res.get("relation","")})')
        for q in t.get('questions', []):
            print(f'      Q: {q.get("title","")} [{q.get("difficulty","")}] ({q.get("reason","")})')
    print()