# 基于知识图谱的个性化学习推荐系统

## 技术路线

### 1. 数据处理与知识图谱构建
- **Python** 进行数据收集和处理
- **Neo4j** 图数据库进行知识图谱的构建和存储
- 支持从目录结构自动构建章节-大节-小节三层知识图谱

### 2. 自然语言处理 (NLP)
- **jieba** 中文分词和关键词提取
- **spaCy** 文本处理（可扩展）
- **Word2Vec** 词嵌入技术增强语义理解

### 3. 个性化推荐算法
- **协同过滤**：基于用户的协同过滤算法
- **内容推荐**：TF-IDF文本相似度计算
- **知识图谱推荐**：基于先修关系、相关关系的图推荐
- **混合推荐模型**：综合多种推荐策略

### 4. 系统开发
- **Flask** 后端服务
- **Vue.js** 前端界面
- **RESTful API** 前后端数据交互
- **vis-network** 知识图谱可视化

## 项目结构

```
new_system/
├── backend/
│   └── app.py              # Flask后端API
├── data_processing/
│   ├── neo4j_manager.py    # Neo4j数据库管理
│   ├── knowledge_graph_builder.py  # 知识图谱构建
│   └── student_data_loader.py      # 学生数据加载
├── nlp_processing/
│   └── text_processor.py   # NLP文本处理
├── recommendation/
│   ├── collaborative_filtering.py  # 协同过滤
│   ├── content_based.py            # 内容推荐
│   ├── knowledge_graph_recommender.py  # 知识图谱推荐
│   └── hybrid_recommender.py       # 混合推荐
├── frontend/
│   ├── index.html          # 前端页面
│   ├── styles.css          # 样式文件
│   └── app.js              # Vue.js应用
├── config.py               # 配置文件
├── requirements.txt        # Python依赖
└── run.py                  # 启动脚本
```

## 安装与运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置Neo4j
确保Neo4j数据库运行在 `bolt://localhost:7687`，默认用户名密码为 `neo4j/12345678`。

### 3. 初始化数据库
```bash
python run.py setup
```

### 4. 启动服务
```bash
python run.py
```

### 5. 访问系统
打开浏览器访问 `http://127.0.0.1:5000`

## API接口

- `POST /api/login` - 用户登录
- `GET /api/knowledge-graph/<student_id>` - 获取知识图谱
- `GET /api/recommendations/<student_id>` - 获取个性化推荐
- `GET /api/resources` - 获取学习资源列表
- `GET /api/progress/<student_id>` - 获取学习进度
- `POST /api/submit` - 提交答题结果

## 功能特性

1. **知识图谱可视化**：三层结构（章-大节-小节），支持掌握度颜色显示
2. **个性化推荐**：基于薄弱知识点、先修关系、相关知识的混合推荐
3. **学习资源管理**：支持资源下载和分类
4. **学习进度跟踪**：实时显示各知识点掌握度
5. **交互式学习**：支持在线答题和掌握度更新
