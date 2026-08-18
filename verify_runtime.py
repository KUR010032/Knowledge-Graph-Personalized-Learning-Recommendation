# encoding: utf-8
import urllib.request, json, http.cookiejar, re

SERVER = 'http://localhost:5000'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

print("=== LOGIN ===")
data = urllib.parse.urlencode({'role':'student','user_id':'3220602001','password':'123456'}).encode()
r = opener.open(SERVER + '/login', data)
print("Login status:", r.status)

r = opener.open(SERVER + '/student/dashboard')
html = r.read().decode()
print("\n=== DASHBOARD PAGE ===")
checks = [
    ('综合掌握度', '首页综合掌握度'),
    ('今日学习概览', '今日学习概览'),
    ('学习画像', '学习画像'),
    ('最近学习记录', '最近学习记录'),
    ('今日推荐摘要', '今日推荐摘要'),
    ('薄弱知识点', '薄弱知识点(含Top3)'),
    ('学习资源推荐', '学习资源推荐入口(含查看推荐)'),
    ('查看推荐', '按钮\"查看推荐\"'),
    ('开始学习', '按钮\"开始学习\"'),
    ('错题待练', '错题待练统计'),
    ('查看图谱', '按钮\"查看图谱\"'),
]
all_pass = True
for kw, desc in checks:
    ok = kw in html
    flag = 'PASS' if ok else 'FAIL'
    if not ok: all_pass = False
    print(f"  [{flag}] {desc}: {'YES' if ok else 'NO'}")

old_check = '智能学习路径'
cnt = html.count(old_check)
print(f"\n  '智能学习路径' 出现次数: {cnt} {'PASS' if cnt == 0 else 'FAIL (应为0)'}")
if cnt > 0: all_pass = False

# Check dashboard function
dash_count = html.count('async function dashboard()')
print(f"  dashboard() 函数数量: {dash_count}")

# API data test
print("\n=== DASHBOARD API ===")
r2 = opener.open(SERVER + '/student/dashboard/data')
d2 = json.loads(r2.read().decode())
st = d2.get('stats', {})
total = (st.get('mastered',0) + st.get('good',0) + st.get('weak',0) + st.get('unlearned',0))
p = d2.get('profile', {})
avg = p.get('avg_mastery', 0)
print(f"  已掌握: {st.get('mastered', 0)}")
print(f"  良好: {st.get('good', 0)}")
print(f"  需巩固: {st.get('weak', 0)}")
print(f"  未学习: {st.get('unlearned', 0)}")
print(f"  总和: {total} (应=37)")
print(f"  整体掌握度: {avg:.1f}% {'PASS' if avg > 0 else 'FAIL (不应为0)'}")
if avg == 0: all_pass = False
print(f"  推荐资源数: {len(d2.get('recommendations', []))}")
print(f"  薄弱知识点: {len(d2.get('weak_points', []))}")
print(f"  最近学习组: {len(d2.get('recent_groups', []))}")

print("\n=== WRONG QUESTIONS PAGE ===")
r3 = opener.open(SERVER + '/student/wrong-questions')
html3 = r3.read().decode()

for kw, desc in [
    ('错误1次', '筛选项/标签\"错误1次\"'),
    ('错误2次及以上', '筛选项\"错误2次及以上\"'),
    ('做对1次', '筛选项/标签\"做对1次\"'),
    ('错题总数', '顶部统计\"错题总数\"'),
    ('已掌握', '顶部统计\"已掌握\"'),
    ('多次错误', '顶部统计\"多次错误\"'),
    ('已移出', '说明\"已移出\"'),
    ('连续做对2次', '说明\"连续做对2次\"'),
]:
    ok = kw in html3
    flag = 'PASS' if ok else 'FAIL'
    if not ok: all_pass = False
    print(f"  [{flag}] {desc}: {'YES' if ok else 'NO'}")

for kw in ['未做对', '连续对2次', '连续做对2']:
    ok = kw not in html3
    flag = 'PASS' if ok else 'FAIL'
    if not ok: all_pass = False
    print(f"  [{flag}] 不应出现\"{kw}\": {'OK(未出现)' if ok else 'FAIL(仍然存在!)'}")

# Check filters
filters = re.findall(r'<option value="([^"]+)"[^>]*>([^<]+)</option>', html3)
print(f"\n  筛选项: {[(v,l) for v,l in filters]}")

print(f"\n{'='*40}")
print(f"总结果: {'ALL PASS' if all_pass else 'SOME FAILURES'}")