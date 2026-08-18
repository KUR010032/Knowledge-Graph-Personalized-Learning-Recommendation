import urllib.request
import urllib.parse
import json
import http.cookiejar
import time

BASE_URL = "http://127.0.0.1:5000"

def time_request(name, url, session, method="GET", data=None):
    t0 = time.time()
    try:
        if method == "GET":
            r = session.open(url)
        else:
            encoded = urllib.parse.urlencode(data).encode() if data else None
            r = session.open(urllib.request.Request(url, data=encoded))
        cost = (time.time() - t0) * 1000
        status = r.status
        body_len = len(r.read())
        flag = "SLOW!" if cost > 2000 else ("WARN" if cost > 1000 else "OK")
        print("  [{}] {:>6.0f}ms  HTTP {}  {} bytes  | {}".format(flag, cost, status, body_len, name))
        return cost, status
    except Exception as e:
        cost = (time.time() - t0) * 1000
        print("  [FAIL] {:>6.0f}ms  {}  | {}".format(cost, str(e)[:60], name))
        return cost, 0

def main():
    cj = http.cookiejar.CookieJar()
    session = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    print("=" * 80)
    print("Performance Test Report")
    print("=" * 80)

    # 1. Login
    print("\n--- LOGIN ---")
    time_request("Login", BASE_URL + "/login", session, "POST",
                 {"user_id": "3220602004", "password": "123456", "role": "student"})

    # 2. Dashboard
    print("\n--- 1. STUDENT DASHBOARD ---")
    time_request("Page: dashboard", BASE_URL + "/student/dashboard", session)
    time_request("API: /student/dashboard/data", BASE_URL + "/student/dashboard/data", session)

    # 3. Recommend
    print("\n--- 2. RECOMMEND ---")
    time_request("Page: recommend", BASE_URL + "/student/recommend", session)
    time_request("API: /student/recommend/data", BASE_URL + "/student/recommend/data", session)

    # 4. Resources
    print("\n--- 3. RESOURCES ---")
    time_request("Page: resources", BASE_URL + "/student/resources", session)
    time_request("API: /student/resources/data", BASE_URL + "/student/resources/data", session)

    # 5. Mastery
    print("\n--- 4. MASTERY ---")
    time_request("Page: mastery", BASE_URL + "/student/mastery", session)
    time_request("API: /student/mastery/data", BASE_URL + "/student/mastery/data", session)

    # 6. Graph
    print("\n--- 5. GRAPH ---")
    time_request("Page: graph", BASE_URL + "/student/graph", session)
    time_request("API: /student/graph-builder/data", BASE_URL + "/student/graph-builder/data", session)

    # 7. Discuss
    print("\n--- 6. DISCUSS ---")
    time_request("Page: discuss", BASE_URL + "/student/discuss", session)
    time_request("API: /student/discuss/list", BASE_URL + "/student/discuss/list", session)

    # 8. Wrong questions
    print("\n--- 7. WRONG QUESTIONS ---")
    time_request("Page: wrong-questions", BASE_URL + "/student/wrong-questions", session)
    time_request("API: /student/wrong-questions/data", BASE_URL + "/student/wrong-questions/data", session)

    # 9. Records
    print("\n--- 8. RECORDS ---")
    time_request("Page: records", BASE_URL + "/student/records", session)
    time_request("API: /student/records/data", BASE_URL + "/student/records/data", session)

    print("\n" + "=" * 80)
    print("Test complete - check server console for [PERF] logs")
    print("=" * 80)

if __name__ == "__main__":
    main()