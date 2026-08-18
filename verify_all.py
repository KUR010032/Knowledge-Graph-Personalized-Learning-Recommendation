import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'app')
import app
app._MASTERY_TREE_CACHE = {}
app._KGCF_RECOMMEND_CACHE = {}

from app import kgcf_recommend_data, normalize_student_id

students = {
    "3220602001": "刘大",
    "3220602004": "李四",
    "3220602006": "赵六",
}

for sid_str, name in students.items():
    t0 = time.time()
    data = kgcf_recommend_data(sid_str, max_targets=6)
    elapsed = (time.time() - t0) * 1000
    
    stype = data.get("student", {}).get("type", "?")
    reco = data.get("recommend_type", "?")
    avg = data.get("avg_mastery", 0)
    
    print("=" * 70)
    print("%s (%s) | type=%s | rec=%s | avg=%.3f | time=%.0fms" % (name, sid_str, stype, reco, avg, elapsed))
    
    targets = data.get("targets", [])
    for t in targets:
        code = t.get("code", "")
        m = t.get("mastery", 0)
        status = t.get("status", "")
        n_res = len(t.get("resources", []))
        n_q = len(t.get("questions", []))
        res_kps = set(r.get("knowledge_id", "") for r in t.get("resources", []))
        res_labels = set(r.get("relation_label", "") for r in t.get("resources", []))
        q_kps = set(q.get("knowledge_id", "") for q in t.get("questions", []))
        print("  %-8s m=%.3f %-6s | %dR %dQ | resKPs=%s | labels=%s | qKPs=%s" % (
            code, m, status, n_res, n_q, sorted(res_kps), sorted(res_labels), sorted(q_kps)))
    
    all_res_kps = set()
    all_q_kps = set()
    for t in targets:
        for r in t.get("resources", []):
            all_res_kps.add(r.get("knowledge_id", ""))
        for q in t.get("questions", []):
            all_q_kps.add(q.get("knowledge_id", ""))
    
    has_313 = any("3.1.3" in kp for kp in all_res_kps)
    all_have_res = all(len(t.get("resources", [])) > 0 for t in targets)
    all_have_q = all(len(t.get("questions", [])) > 0 for t in targets)
    
    print("  3.1.3 in resources: %s | All have R: %s | All have Q: %s" % (has_313, all_have_res, all_have_q))

print("\nDone!")