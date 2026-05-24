const { createApp } = Vue;

const API_BASE = window.location.origin + '/api';

function createWaterLevelSVG(label, mastery, level) {
    const size = level === 0 ? 120 : level === 1 ? 90 : 70;
    const r = size / 2 - 4;
    const cx = size / 2;
    const cy = size / 2;
    const uid = 'w' + Math.random().toString(36).substr(2, 8);

    let fillColor = '#bdc3c7';
    let waterY = cy + r;

    if (mastery != null && mastery !== undefined) {
        if (mastery <= 0.333) fillColor = '#e74c3c';
        else if (mastery <= 0.667) fillColor = '#f39c12';
        else fillColor = '#27ae60';
        waterY = cy + r - mastery * 2 * r;
    }

    const fontSize = level === 0 ? 12 : level === 1 ? 10 : 9;
    const lineHeight = fontSize + 3;

    let lines = [];
    
    if (level === 0) {
        const chMatch = label.match(/(第\d+章)\s*(.+)/);
        if (chMatch) {
            lines.push(chMatch[1]);
            const rest = chMatch[2];
            if (rest.length > 8) {
                const mid = Math.ceil(rest.length / 2);
                lines.push(rest.substring(0, mid));
                lines.push(rest.substring(mid));
            } else {
                lines.push(rest);
            }
        } else if (label.length > 10) {
            const mid = Math.ceil(label.length / 2);
            lines.push(label.substring(0, mid));
            lines.push(label.substring(mid));
        } else {
            lines.push(label);
        }
    } else if (level === 1) {
        if (label.length > 12) {
            const dotIdx = label.indexOf(' ');
            if (dotIdx > 0) {
                lines.push(label.substring(0, dotIdx));
                const rest = label.substring(dotIdx + 1);
                if (rest.length > 10) {
                    const mid = Math.ceil(rest.length / 2);
                    lines.push(rest.substring(0, mid));
                    lines.push(rest.substring(mid));
                } else {
                    lines.push(rest);
                }
            } else {
                const mid = Math.ceil(label.length / 2);
                lines.push(label.substring(0, mid));
                lines.push(label.substring(mid));
            }
        } else {
            lines.push(label);
        }
    } else {
        if (label.length > 14) {
            const dotIdx = label.indexOf(' ');
            if (dotIdx > 0) {
                lines.push(label.substring(0, dotIdx));
                const rest = label.substring(dotIdx + 1);
                if (rest.length > 12) {
                    const mid = Math.ceil(rest.length / 2);
                    lines.push(rest.substring(0, mid));
                    lines.push(rest.substring(mid));
                } else {
                    lines.push(rest);
                }
            } else {
                const mid = Math.ceil(label.length / 2);
                lines.push(label.substring(0, mid));
                lines.push(label.substring(mid));
            }
        } else {
            lines.push(label);
        }
    }

    const maxLines = 3;
    if (lines.length > maxLines) {
        lines = lines.slice(0, maxLines);
    }

    const totalTextHeight = lines.length * lineHeight;
    const startY = cy - totalTextHeight / 2 + fontSize * 0.8;

    let textElements = '';
    lines.forEach((line, i) => {
        const maxChars = level === 0 ? 10 : level === 1 ? 9 : 8;
        const displayLine = line.length > maxChars ? line.substring(0, maxChars - 2) + '..' : line;
        textElements += '<text x="' + cx + '" y="' + (startY + i * lineHeight) + '" text-anchor="middle" font-size="' + fontSize + '" fill="#2c3e50" font-family="Microsoft YaHei, sans-serif" font-weight="' + (level === 0 ? 'bold' : 'normal') + '">' + displayLine + '</text>';
    });

    const svg = '<svg xmlns="http://www.w3.org/2000/svg" width="' + size + '" height="' + size + '" viewBox="0 0 ' + size + ' ' + size + '">'
        + '<defs><clipPath id="' + uid + '"><circle cx="' + cx + '" cy="' + cy + '" r="' + r + '"/></clipPath></defs>'
        + '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="#ecf0f1" stroke="#bdc3c7" stroke-width="2"/>'
        + '<rect x="0" y="' + waterY + '" width="' + size + '" height="' + size + '" fill="' + fillColor + '" clip-path="url(#' + uid + ')"/>'
        + '<circle cx="' + cx + '" cy="' + cy + '" r="' + r + '" fill="none" stroke="' + (level === 0 ? '#2c3e50' : '#7f8c8d') + '" stroke-width="' + (level === 0 ? 3 : 2) + '"/>'
        + textElements
        + '</svg>';

    return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

createApp({
    data() {
        return {
            isLoggedIn: false,
            userRole: '',
            userName: '',
            userId: '',
            currentPage: 'graph',
            loginRole: 'student',
            loginForm: { user_id: '', password: '' },
            loginError: '',
            recommendations: [],
            resources: [],
            resourceChapters: [],
            progress: [],
            expandedChapters: {},
            expandedResourceChapters: {},
            graphNetwork: null,

            showPractice: false,
            practiceKp: '',
            practiceQuestions: [],
            currentQuestionIndex: 0,
            selectedAnswer: '',
            showResult: false,
            isCorrect: false,

            // Teacher features
            selectedStudentId: '',
            studentList: [],
            chapterOptions: [
                { value: '1', label: '第1章 操作系统概述' },
                { value: '2', label: '第2章 进程与线程' },
                { value: '3', label: '第3章 同步与互斥' },
                { value: '4', label: '第4章 处理机调度' },
                { value: '5', label: '第5章 内存管理' },
                { value: '6', label: '第6章 文件管理' },
                { value: '7', label: '第7章 设备管理' },
                { value: '8', label: '第8章 操作系统安全' },
                { value: '9', label: '第9章 新型操作系统简介' },
                { value: '10', label: '第10章 操作系统设计问题' }
            ],
            uploadForm: {
                type: 'video',
                chapter: '',
                knowledgePoint: '',
                file: null,
                fileName: ''
            },
            uploadMessage: '',
            uploadMessageType: ''
        }
    },

    computed: {
        currentQuestion() {
            if (this.practiceQuestions.length === 0) return {};
            return this.practiceQuestions[this.currentQuestionIndex] || {};
        }
    },

    mounted() {
        const token = localStorage.getItem('token');
        if (token) {
            this.isLoggedIn = true;
            this.userRole = localStorage.getItem('role');
            this.userName = localStorage.getItem('name');
            this.userId = localStorage.getItem('userId');
            this.loadPageData();
        }
    },

    watch: {
        currentPage(newPage) {
            if (newPage === 'graph') {
                this.$nextTick(() => this.loadKnowledgeGraph());
            } else if (newPage === 'recommend') {
                this.recommendations = [];
                this.loadRecommendations();
            } else if (newPage === 'resources') {
                this.loadResources();
            } else if (newPage === 'progress') {
                this.loadProgress();
            } else if (newPage === 'upload' && this.userRole === 'teacher') {
                // Upload page
            }
        }
    },

    methods: {
        async login() {
            try {
                const response = await fetch(`${API_BASE}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: this.loginForm.user_id,
                        password: this.loginForm.password,
                        role: this.loginRole
                    })
                });
                const data = await response.json();
                if (data.success) {
                    this.isLoggedIn = true;
                    this.userRole = data.role;
                    this.userName = data.name;
                    this.userId = data.full_id || data.name;
                    localStorage.setItem('token', 'logged_in');
                    localStorage.setItem('role', data.role);
                    localStorage.setItem('name', data.name);
                    localStorage.setItem('userId', this.userId);
                    this.loadPageData();
                } else {
                    this.loginError = data.error || '登录失败';
                }
            } catch (error) {
                this.loginError = '网络错误: ' + error.message;
            }
        },

        logout() {
            this.isLoggedIn = false;
            this.userRole = '';
            this.userName = '';
            this.userId = '';
            localStorage.clear();
        },

        loadPageData() {
            if (this.currentPage === 'graph') {
                this.$nextTick(() => this.loadKnowledgeGraph());
            }
        },

        async loadKnowledgeGraph() {
            try {
                const response = await fetch(`${API_BASE}/knowledge-graph/${this.userId}`);
                const data = await response.json();
                if (data.nodes && data.edges) {
                    console.log('Graph data:', data.nodes.length, 'nodes,', data.edges.length, 'edges');
                    const ch3Nodes = data.nodes.filter(n => n.label && n.label.includes('3'));
                    console.log('Chapter 3 related nodes:', ch3Nodes.map(n => n.label));
                    const ch3Edges = data.edges.filter(e => (e.from && e.from.includes('3')) || (e.to && e.to.includes('3')));
                    console.log('Chapter 3 related edges:', ch3Edges.length);
                    this.renderGraph(data.nodes, data.edges);
                }
            } catch (error) {
                console.error('Failed to load knowledge graph:', error);
            }
        },

        renderGraph(nodes, edges) {
            const container = document.getElementById('knowledgeGraph');
            if (!container) return;

            const visNodes = new vis.DataSet(
                nodes.map(n => ({
                    id: n.id,
                    shape: 'image',
                    image: createWaterLevelSVG(n.label, n.mastery, n.level),
                    size: n.level === 0 ? 60 : n.level === 1 ? 45 : 35,
                    label: '',
                    title: n.label + (n.mastery != null ? ' | 掌握度: ' + (n.mastery * 100).toFixed(0) + '%' : '')
                }))
            );

            const visEdges = new vis.DataSet(
                edges.map(e => {
                    let color, dashes, width, arrows;
                    if (e.type === '包含') {
                        color = { color: '#3498db', opacity: 0.3 };
                        dashes = false;
                        width = 1;
                        arrows = 'to';
                    } else if (e.type === '先修') {
                        color = { color: '#e74c3c', opacity: 0.5 };
                        dashes = false;
                        width = 1.5;
                        arrows = 'to';
                    } else {
                        color = { color: '#f39c12', opacity: 0.4 };
                        dashes = true;
                        width = 1;
                        arrows = '';
                    }
                    return {
                        from: e.from,
                        to: e.to,
                        arrows: arrows,
                        color: color,
                        dashes: dashes,
                        width: width,
                        smooth: { type: 'curvedCW', roundness: 0.2 },
                        title: e.type
                    };
                })
            );

            const options = {
                layout: {
                    improvedLayout: true,
                    randomSeed: 42
                },
                physics: {
                    enabled: true,
                    solver: 'forceAtlas2Based',
                    forceAtlas2Based: {
                        gravitationalConstant: -80,
                        centralGravity: 0.005,
                        springLength: 120,
                        springConstant: 0.08,
                        damping: 0.4,
                        avoidOverlap: 0.8
                    },
                    stabilization: {
                        enabled: true,
                        iterations: 300,
                        fit: true
                    }
                },
                interaction: {
                    dragNodes: true,
                    zoomView: true,
                    dragView: true,
                    hover: true
                }
            };

            if (this.graphNetwork) {
                this.graphNetwork.destroy();
            }

            this.graphNetwork = new vis.Network(container, { nodes: visNodes, edges: visEdges }, options);
        },

        async loadRecommendations() {
            try {
                const response = await fetch(`${API_BASE}/recommendations/${this.userId}`);
                const data = await response.json();
                if (data.success) {
                    this.recommendations = data.recommendations;
                }
            } catch (error) {
                console.error('Failed to load recommendations:', error);
            }
        },

        async startPracticeWithQuestion(rec) {
            if (!rec.full_question) {
                alert('题目信息不完整');
                return;
            }
            
            this.practiceKp = rec.knowledge_point;
            this.showPractice = true;
            this.currentQuestionIndex = 0;
            this.selectedAnswer = '';
            this.showResult = false;
            this.isCorrect = false;
            this.practiceQuestions = [rec.full_question];
        },

        async loadResources() {
            try {
                const response = await fetch(`${API_BASE}/resources`);
                const data = await response.json();
                if (data.success) {
                    this.resources = data.resources;
                    this.groupResourcesByChapter(data.resources);
                }
            } catch (error) {
                console.error('Failed to load resources:', error);
            }
        },

        groupResourcesByChapter(resources) {
            const chapters = {};
            const CHAPTER_NAMES = {
                1: '第1章 操作系统概述',
                2: '第2章 进程与线程',
                3: '第3章 同步与互斥',
                4: '第4章 处理机调度',
                5: '第5章 内存管理',
                6: '第6章 文件管理',
                7: '第7章 设备管理',
                8: '第8章 操作系统安全',
                9: '第9章 新型操作系统简介',
                10: '第10章 操作系统设计问题'
            };

            const VIDEO_CHAPTER_MAP = {
                '2.2.1 进程的概念.mp4': 2,
                '2.2.3 进程状态和转换.mp4': 2,
                '3.1.4 信号量和PV操作.mp4': 3,
                '3.4.2 死锁的必要条件.mp4': 3,
                '3.5.2 哲学家进餐问题.mp4': 3
            };

            resources.forEach(res => {
                let chNum = null;
                const chMatch = res.name.match(/第(\d+)章/);
                if (chMatch) {
                    chNum = parseInt(chMatch[1]);
                } else if (VIDEO_CHAPTER_MAP[res.name]) {
                    chNum = VIDEO_CHAPTER_MAP[res.name];
                } else {
                    const numMatch = res.name.match(/^(\d+)\./);
                    if (numMatch) chNum = parseInt(numMatch[1]);
                }

                if (!chNum || !CHAPTER_NAMES[chNum]) return;

                const chKey = CHAPTER_NAMES[chNum];
                if (!chapters[chKey]) {
                    chapters[chKey] = { name: chKey, sections: {}, chapterResources: [] };
                }

                // Check if this is a chapter-level resource (PPT for the whole chapter)
                const isChapterResource = res.name.match(/^第\d+章.*\.pptx$/) || res.name.match(/^第\d+章.*\.pdf$/);
                
                if (isChapterResource) {
                    chapters[chKey].chapterResources.push(res);
                    return;
                }

                let sectionKey = '其他';
                const sectionMatch = res.name.match(/^(\d+\.\d+)\s/);
                if (sectionMatch) {
                    sectionKey = sectionMatch[1];
                } else if (VIDEO_CHAPTER_MAP[res.name]) {
                    const kpMatch = res.name.match(/^(\d+\.\d+\.\d+)\s/);
                    if (kpMatch) {
                        sectionKey = kpMatch[1].replace(/\.\d+$/, '');
                    }
                }

                if (!chapters[chKey].sections[sectionKey]) {
                    chapters[chKey].sections[sectionKey] = { name: sectionKey, items: [] };
                }
                chapters[chKey].sections[sectionKey].items.push(res);
            });

            this.resourceChapters = Object.values(chapters).map(ch => {
                const sections = Object.values(ch.sections).sort((a, b) => {
                    if (a.name === '其他') return 1;
                    if (b.name === '其他') return -1;
                    return a.name.localeCompare(b.name, 'zh-CN', { numeric: true });
                });
                let totalItems = ch.chapterResources.length;
                sections.forEach(s => totalItems += s.items.length);
                return { name: ch.name, sections, totalItems, chapterResources: ch.chapterResources };
            }).sort((a, b) => {
                const na = parseInt(a.name.match(/第(\d+)章/)[1]);
                const nb = parseInt(b.name.match(/第(\d+)章/)[1]);
                return na - nb;
            });

            this.resourceChapters.forEach(ch => {
                if (!(ch.name in this.expandedResourceChapters)) {
                    this.expandedResourceChapters[ch.name] = false;
                }
                ch.sections.forEach(s => {
                    if (!(ch.name + '_' + s.name in this.expandedResourceChapters)) {
                        this.expandedResourceChapters[ch.name + '_' + s.name] = false;
                    }
                });
            });
        },

        toggleResourceChapter(chapterName) {
            this.expandedResourceChapters[chapterName] = !this.expandedResourceChapters[chapterName];
        },

        toggleResourceSection(chapterName, sectionName) {
            const key = chapterName + '_' + sectionName;
            this.expandedResourceChapters[key] = !this.expandedResourceChapters[key];
        },

        async loadProgress() {
            if (this.userRole === 'teacher') {
                await this.loadStudentList();
                if (this.selectedStudentId) {
                    await this.loadProgressForStudent();
                } else {
                    this.progress = [];
                }
            } else {
                await this.loadProgressForStudent(this.userId);
            }
        },

        async loadStudentList() {
            try {
                const response = await fetch(`${API_BASE}/students`);
                const data = await response.json();
                if (data.success) {
                    this.studentList = data.students;
                }
            } catch (error) {
                console.error('Failed to load student list:', error);
            }
        },

        async loadProgressForStudent(studentId) {
            const sid = studentId || this.selectedStudentId;
            if (!sid) return;
            
            try {
                const response = await fetch(`${API_BASE}/progress/${sid}`);
                const data = await response.json();
                if (data.success) {
                    this.progress = data.progress;
                    this.progress.forEach(ch => {
                        if (!(ch.chapter in this.expandedChapters)) {
                            this.expandedChapters[ch.chapter] = true;
                        }
                    });
                }
            } catch (error) {
                console.error('Failed to load progress:', error);
            }
        },

        async loadProgressForManualStudent() {
            if (!this.selectedStudentId.trim()) return;
            
            try {
                const response = await fetch(`${API_BASE}/progress/${this.selectedStudentId.trim()}`);
                const data = await response.json();
                if (data.success) {
                    this.progress = data.progress;
                    this.progress.forEach(ch => {
                        if (!(ch.chapter in this.expandedChapters)) {
                            this.expandedChapters[ch.chapter] = true;
                        }
                    });
                } else {
                    alert('未找到该学生的进度信息');
                }
            } catch (error) {
                console.error('Failed to load progress:', error);
                alert('查询失败，请检查学号是否正确');
            }
        },

        toggleChapter(chapter) {
            this.expandedChapters[chapter] = !this.expandedChapters[chapter];
        },

        getMasteryClass(mastery) {
            if (mastery <= 0.333) return 'low';
            if (mastery <= 0.667) return 'medium';
            return 'high';
        },

        getProgressColor(mastery) {
            if (mastery <= 0.333) return '#e74c3c';
            if (mastery <= 0.667) return '#f39c12';
            return '#27ae60';
        },

        difficultyLabel(d) {
            const map = { easy: '简单', medium: '中等', hard: '困难' };
            return map[d] || d || '中等';
        },

        importanceLabel(i) {
            const map = { important: '重点', normal: '普通' };
            return map[i] || i || '普通';
        },

        getResourceIcon(type) {
            if (type === 'video') return '🎬';
            if (type === 'ppt') return '📊';
            return '📄';
        },

        async startPractice(rec) {
            this.practiceKp = rec.name;
            this.showPractice = true;
            this.currentQuestionIndex = 0;
            this.selectedAnswer = '';
            this.showResult = false;
            this.isCorrect = false;

            if (rec.questions && rec.questions.length > 0) {
                this.practiceQuestions = rec.questions;
            } else {
                try {
                    const response = await fetch(`${API_BASE}/questions/${encodeURIComponent(rec.name)}`);
                    const data = await response.json();
                    if (data.success) {
                        this.practiceQuestions = data.questions;
                    } else {
                        this.practiceQuestions = [];
                    }
                } catch (error) {
                    console.error('Failed to load questions:', error);
                    this.practiceQuestions = [];
                }
            }
        },

        closePractice() {
            this.showPractice = false;
            this.practiceQuestions = [];
            this.currentQuestionIndex = 0;
            this.selectedAnswer = '';
            this.showResult = false;
            this.isCorrect = false;
        },

        selectAnswer(option) {
            if (this.showResult) return;
            this.selectedAnswer = option;
        },

        handleFileSelect(event) {
            const file = event.target.files[0];
            if (file) {
                this.uploadForm.file = file;
                this.uploadForm.fileName = file.name;
            }
        },

        async uploadResource() {
            if (!this.uploadForm.file || !this.uploadForm.chapter) {
                this.uploadMessage = '请选择文件和章节';
                this.uploadMessageType = 'error';
                return;
            }

            const formData = new FormData();
            formData.append('file', this.uploadForm.file);
            formData.append('type', this.uploadForm.type);
            formData.append('chapter', this.uploadForm.chapter);
            formData.append('knowledge_point', this.uploadForm.knowledgePoint);

            try {
                this.uploadMessage = '正在上传...';
                this.uploadMessageType = 'info';
                
                const response = await fetch(`${API_BASE}/upload`, {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.success) {
                    this.uploadMessage = '上传成功！';
                    this.uploadMessageType = 'success';
                    this.uploadForm.file = null;
                    this.uploadForm.fileName = '';
                    this.uploadForm.knowledgePoint = '';
                    this.$refs.fileInput.value = '';
                } else {
                    this.uploadMessage = data.error || '上传失败';
                    this.uploadMessageType = 'error';
                }
            } catch (error) {
                this.uploadMessage = '网络错误: ' + error.message;
                this.uploadMessageType = 'error';
            }
        },

        async submitAnswer() {
            if (!this.selectedAnswer) return;
            const question = this.currentQuestion;
            this.isCorrect = this.selectedAnswer === question.answer;
            this.showResult = true;
            try {
                await fetch(`${API_BASE}/submit`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        student_id: this.userId,
                        knowledge: this.practiceKp,
                        is_correct: this.isCorrect
                    })
                });
            } catch (error) {
                console.error('Failed to submit answer:', error);
            }
        },

        nextQuestion() {
            this.currentQuestionIndex++;
            this.selectedAnswer = '';
            this.showResult = false;
            this.isCorrect = false;
        },

        finishPractice() {
            this.closePractice();
            this.loadRecommendations();
            this.loadProgress();
        }
    }
}).mount('#app');
