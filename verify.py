import urllib.request, json, http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login
data = urllib.parse.urlencode({'role':'student','user_id':'3220602001','password':'123456'}).encode()
opener.open('http://localhost:5001/login', data)

# ===== DASHBOARD PAGE =====
r = opener.open('http://localhost:5001/student/dashboard')
html = r.read().decode()

print("=" * 60)
print("HOMEPAGE VERIFICATION")
print("=" * 60)

checks = {
    'has_学习资源推荐_entry': '学习资源推荐' in html,
    'has_查看推荐_button': '查看推荐' in html,
    'has_开始学习_button': '开始学习' in html,
    'has_查看图谱_button': '查看图谱' in html,
    'has_今日学习概览': '今日学习概览' in html,
    'has_学习画像': '学习画像' in html,
    'has_知识点掌握度': '知识点掌握度' in html,
    'has_学习资源推荐_link': '/student/recommend' in html,
    'has_学习资源库_link': '/student/resources' in html,
    'has_知识图谱_link': '/student/graph' in html,
    'has_最近学习记录': '最近学习记录' in html,
    'has_今日推荐摘要': '今日推荐摘要' in html,
    'has_薄弱知识点_Top3': '薄弱知识点 Top3' in html,
    'has_最近学习摘要': '最近学习摘要' in html,
    'has_学习建议': '学习建议' in html,
    'has_综合掌握度': '综合掌握度' in html,
    'has_今日学习': '今日学习' in html,
    'has_做题总数': '做题总数' in html,
    'has_错题待练': '错题待练' in html,
}

for k, v in checks.items():
    status = 'OK' if v else 'MISSING!'
    print('  %s: %s' % (k, status))

# Check NO "智能学习路径" in sidebar/button context (should be "学习资源推荐")
if '智能学习路径' in html:
    # Count occurrences to see if only in old templates
    count = html.count('智能学习路径')
    print('  WARNING: "智能学习路径" found %d times in page' % count)
else:
    print('  OK: No "智能学习路径" found in page')

# Check dashboard stats rendering
print()
print("DASHBOARD STATS (from API):")
r = opener.open('http://localhost:5001/student/dashboard/data')
d = json.loads(r.read().decode())
s = d['stats']
total = s['mastered']+s['good']+s['weak']+s['unlearned']
print('  mastered=%s good=%s weak=%s unlearned=%s total=%s' % (s['mastered'], s['good'], s['weak'], s['unlearned'], s['total']))
print('  Sum check: %s+%s+%s+%s = %s (expected %s)' % (s['mastered'], s['good'], s['weak'], s['unlearned'], total, s['total']))
print('  avg_mastery: %s (%s%%)' % (d['profile'].get('avg_mastery'), round(d['profile'].get('avg_mastery',0)*100)))
print('  Is mastery NOT 0%%? %s' % (d['profile'].get('avg_mastery',0) > 0))

# ===== WRONG PAGE =====
r = opener.open('http://localhost:5001/student/wrong-questions')
html2 = r.read().decode()

print()
print("=" * 60)
print("WRONG PAGE VERIFICATION")
print("=" * 60)

wrong_checks = {
    'has_错题总数': '错题总数' in html2,
    'has_已掌握_stat': '已掌握</span>' in html2,
    'has_多次错误_stat': '多次错误' in html2,
    'has_错误1次_filter': '错误1次' in html2,
    'has_错误2次及以上_filter': '错误2次及以上' in html2,
    'has_做对1次_filter': '做对1次' in html2,
    'NO_未做对_filter': '未做对</option>' not in html2,
    'NO_未做对_label': html2.count('未做对') <= 0,
    'NO_连续对2次': '连续对2次' not in html2,
    'NO_连续做对2次': '连续做对2次' not in html2,
}

for k, v in wrong_checks.items():
    status = 'OK' if v else 'MISSING!'
    print('  %s: %s' % (k, status))

# Check wrong filter option values
import re
filter_opts = re.findall(r'<option value="([^"]+)">([^<]+)</option>', html2)
print()
print('  Filter options in HTML:')
for val, label in filter_opts:
    print('    value=%s -> %s' % (val, label))

# Check wrong page stats
print()
print('  Wrong page API data:')
r = opener.open('http://localhost:5001/student/wrong-questions/data')
d = json.loads(r.read().decode())
qs = d.get('questions', [])
active = [q for q in qs if (q.get('consecutive_correct', 0) or 0) < 2]
mastered = [q for q in qs if (q.get('consecutive_correct', 0) or 0) >= 2]
multi = [q for q in active if (q.get('wrong_count', 0) or 0) >= 2]
print('  Total: %d, Active: %d, Mastered: %d, MultiWrong: %d' % (len(qs), len(active), len(mastered), len(multi)))

print()
print("=" * 60)
print("ALL CHECKS COMPLETE")
print("=" * 60)