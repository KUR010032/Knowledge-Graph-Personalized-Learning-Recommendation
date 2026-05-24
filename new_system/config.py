import os

class Config:
    SECRET_KEY = 'knowledge_graph_learning_system_2024'
    NEO4J_URI = 'bolt://localhost:7687'
    NEO4J_USER = 'neo4j'
    NEO4J_PASSWORD = '12345678'
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = os.path.join(os.path.dirname(BASE_DIR), 'app', 'resources')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    
    STUDENT_DATA_DIR = os.path.join(DATA_DIR, 'studentdata')
    CATALOG_FILE = os.path.join(STUDENT_DATA_DIR, 'catalog.txt')
    
    TEACHERS = {
        "1000002401": {"password": "admin1", "name": "教师"}
    }
    
    STUDENTS = {
        "3220602001": {"password": "123456", "name": "刘大", "full_id": "3220602001刘大"},
        "3220602002": {"password": "123456", "name": "陈二", "full_id": "3220602002陈二"},
        "3220602003": {"password": "123456", "name": "张三", "full_id": "3220602003张三"},
        "3220602004": {"password": "123456", "name": "李四", "full_id": "3220602004李四"},
        "3220602005": {"password": "123456", "name": "王五", "full_id": "3220602005王五"}
    }
