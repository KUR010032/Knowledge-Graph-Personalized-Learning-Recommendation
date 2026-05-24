import sys
import json
sys.path.insert(0, 'c:\\Users\\zzlyx\\Desktop\\lunwen\\app')
from app import app

with app.test_client() as client:
    with app.test_request_context('/student/graph'):
        with app.app_context():
            from flask import session, request
            
            # 正确设置session
            with client.session_transaction() as sess:
                sess['role'] = 'student'
                sess['full_id'] = '2021001'
                sess['user_name'] = '测试学生'
            
            response = client.get('/student/graph', follow_redirects=False)
            html = response.data.decode('utf-8')
            
            print(f"Response status: {response.status_code}")
            print(f"Response location header: {response.headers.get('Location', 'N/A')}")
            print(f"HTML length: {len(html)} characters")
            
            if response.status_code == 302:
                print("\n[REDIRECT] Being redirected to login page!")
                print("This means session is not properly set or user is not logged in")
                
                # 尝试跟随重定向
                response2 = client.get('/student/graph', follow_redirects=True)
                html2 = response2.data.decode('utf-8')
                if "login" in html2.lower() or "登录" in html2:
                    print("[CONFIRMED] Redirected to login page")
            else:
                # 检查是否包含"未找到学习数据"
                if "未找到学习数据" in html:
                    print("\n[ERROR] Found '未找到学习数据' - graph_data is None or empty!")
                    print("This means get_knowledge_graph() returned empty nodes")
                    
                    # 直接调用函数检查
                    from app import get_knowledge_graph
                    result = get_knowledge_graph('2021001')
                    print(f"\nDirect function call result:")
                    print(f"  Nodes: {len(result.get('nodes', []))}")
                    print(f"  Edges: {len(result.get('edges', []))}")
                else:
                    print("\n[OK] Graph data exists in template")
                
                # 检查是否包含JavaScript代码
                if "var graphData =" in html:
                    print("[OK] JavaScript variable 'graphData' found in HTML")
                    
                    # 提取graphData的值
                    start_idx = html.find("var graphData =") + len("var graphData =")
                    end_idx = html.find(";", start_idx)
                    json_str = html[start_idx:end_idx].strip()
                    
                    try:
                        data = json.loads(json_str)
                        print(f"\nGraph data parsed successfully:")
                        print(f"  - Nodes: {len(data.get('nodes', []))}")
                        print(f"  - Edges: {len(data.get('edges', []))}")
                        
                        # 保存完整HTML用于调试
                        with open('debug_graph.html', 'w', encoding='utf-8') as f:
                            f.write(html)
                        print(f"\n[DEBUG] Full HTML saved to debug_graph.html")
                        print(f"[SUCCESS] Data is correctly passed to frontend!")
                    except Exception as e:
                        print(f"\n[ERROR] Failed to parse JSON: {e}")
                        print(f"JSON string preview: {json_str[:200]}...")
                else:
                    print("\n[ERROR] JavaScript variable 'graphData' NOT found!")
                    print("Template rendering issue - graph_data not passed to JS")
