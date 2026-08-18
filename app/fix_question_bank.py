# -*- coding: utf-8 -*-
import json
import os
import random
import time
from collections import defaultdict

os.chdir(os.path.dirname(os.path.abspath(__file__)))

STUDENT_TYPES = {
    '3220602001': 'excellent',  # 刘大
    '3220602004': 'medium',     # 李四
    '3220602006': 'weak',       # 赵六
    '3220602002': 'excellent',  # 陈二
    '3220602003': 'excellent',  # 张三
    '3220602005': 'medium',     # 王五
    '3220602007': 'medium',     # 周七
    '3220602008': 'medium',     # 吴八
    '3220602009': 'medium',     # 郑九
    '3220602010': 'medium',     # 冯十
    '3220602011': 'weak',       # 陈琳
    '3220602012': 'weak',       # 黄明
    '3220602013': 'medium',     # 林芳
    '3220602014': 'medium',     # 何强
    '3220602015': 'medium',     # 罗伟
    '3220602016': 'weak',       # 梁静
    '3220602017': 'weak',       # 宋涛
    '3220602018': 'medium',     # 唐洁
    '3220602019': 'medium',     # 韩冰
    '3220602020': 'weak',       # 曹洋
    '3220602021': 'medium',     # 许晴
    '3220602022': 'medium',     # 邓超
    '3220602023': 'medium',     # 彭飞
    '3220602024': 'medium',     # 蒋丽
    '3220602025': 'weak',       # 沈杰
    '3220602026': 'weak',       # 姚远
    '3220602027': 'medium',     # 姜悦
    '3220602028': 'medium',     # 范明
    '3220602029': 'medium',     # 方芳
    '3220602030': 'weak',       # 石磊
}

with open('resources/students_meta.json', 'r', encoding='utf-8') as f:
    META = json.load(f)

STUDENT_NAME_MAP = {}
for sid, info in META.items():
    STUDENT_NAME_MAP[sid] = info['name']

# ============================================================
# PART 1: NEW QUESTIONS
# ============================================================

NEW_QUESTIONS = [
    # ---- 1.2 操作系统的形成和发展 (easy=+2, hard=+2) ----
    {
        "id": "q1_2_11",
        "knowledge_point": "1.2 操作系统的形成和发展",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "第一台电子计算机ENIAC诞生于（）年。",
        "options": ["A. 1945", "B. 1946", "C. 1947", "D. 1948"],
        "answer": "B",
        "explanation": "ENIAC（电子数字积分计算机）于1946年在美国宾夕法尼亚大学诞生，是公认的第一台通用电子计算机。",
        "title": "第一台电子计算机ENIAC诞生于（）年。",
        "question_text": "第一台电子计算机ENIAC诞生于（）年。",
        "analysis": "ENIAC（电子数字积分计算机）于1946年在美国宾夕法尼亚大学诞生，是公认的第一台通用电子计算机。",
        "knowledge_id": "1.2",
        "knowledge_name": "1.2 操作系统的形成和发展",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_2_12",
        "knowledge_point": "1.2 操作系统的形成和发展",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "操作系统发展的最初阶段是（）。",
        "options": [
            "A. 批处理操作系统",
            "B. 分时操作系统",
            "C. 手工操作阶段",
            "D. 实时操作系统"
        ],
        "answer": "C",
        "explanation": "操作系统的发展经历了手工操作阶段、批处理阶段、多道程序设计和分时系统等阶段。最初是手工操作，用户直接使用计算机硬件。",
        "title": "操作系统发展的最初阶段是（）。",
        "question_text": "操作系统发展的最初阶段是（）。",
        "analysis": "操作系统的发展经历了手工操作阶段、批处理阶段、多道程序设计和分时系统等阶段。最初是手工操作，用户直接使用计算机硬件。",
        "knowledge_id": "1.2",
        "knowledge_name": "1.2 操作系统的形成和发展",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_2_13",
        "knowledge_point": "1.2 操作系统的形成和发展",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "推动操作系统从单道批处理向多道批处理发展的关键技术是（）。",
        "options": [
            "A. 中断技术",
            "B. 通道技术和中断技术",
            "C. 高速缓存技术",
            "D. 虚拟存储技术"
        ],
        "answer": "B",
        "explanation": "通道技术使CPU与I/O设备可以并行工作，中断技术使CPU可以在I/O完成时及时响应，两者结合实现了多道程序的并发执行。",
        "title": "推动操作系统从单道批处理向多道批处理发展的关键技术是（）。",
        "question_text": "推动操作系统从单道批处理向多道批处理发展的关键技术是（）。",
        "analysis": "通道技术使CPU与I/O设备可以并行工作，中断技术使CPU可以在I/O完成时及时响应，两者结合实现了多道程序的并发执行。",
        "knowledge_id": "1.2",
        "knowledge_name": "1.2 操作系统的形成和发展",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_2_14",
        "knowledge_point": "1.2 操作系统的形成和发展",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "以下关于操作系统发展历程的描述，正确的是（）。",
        "options": [
            "A. 先出现分时系统，后出现批处理系统",
            "B. 微机操作系统是操作系统发展的起点",
            "C. 手工操作阶段之后进入了单道批处理阶段",
            "D. 网络操作系统早于批处理系统出现"
        ],
        "answer": "C",
        "explanation": "操作系统发展顺序为：手工操作阶段→单道批处理系统→多道批处理系统→分时系统→实时系统→微机操作系统→网络操作系统等。",
        "title": "以下关于操作系统发展历程的描述，正确的是（）。",
        "question_text": "以下关于操作系统发展历程的描述，正确的是（）。",
        "analysis": "操作系统发展顺序为：手工操作阶段→单道批处理系统→多道批处理系统→分时系统→实时系统→微机操作系统→网络操作系统等。",
        "knowledge_id": "1.2",
        "knowledge_name": "1.2 操作系统的形成和发展",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },

    # ---- 1.3 操作系统的分类 (easy=+2, hard=+2) ----
    {
        "id": "q1_3_11",
        "knowledge_point": "1.3 操作系统的分类",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "允许多个用户通过终端同时使用一台计算机的操作系统是（）。",
        "options": [
            "A. 批处理操作系统",
            "B. 分时操作系统",
            "C. 实时操作系统",
            "D. 个人计算机操作系统"
        ],
        "answer": "B",
        "explanation": "分时操作系统允许多个用户通过各自的终端同时使用一台主机，操作系统以时间片轮转方式为每个用户服务。",
        "title": "允许多个用户通过终端同时使用一台计算机的操作系统是（）。",
        "question_text": "允许多个用户通过终端同时使用一台计算机的操作系统是（）。",
        "analysis": "分时操作系统允许多个用户通过各自的终端同时使用一台主机，操作系统以时间片轮转方式为每个用户服务。",
        "knowledge_id": "1.3",
        "knowledge_name": "1.3 操作系统的分类",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_3_12",
        "knowledge_point": "1.3 操作系统的分类",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "以下哪种操作系统主要用于工业控制和武器系统等对响应时间要求极高的领域（）。",
        "options": [
            "A. 网络操作系统",
            "B. 分布式操作系统",
            "C. 实时操作系统",
            "D. 嵌入式操作系统"
        ],
        "answer": "C",
        "explanation": "实时操作系统能够在规定时间内对外部事件做出响应，常用于工业控制、导弹发射、医疗设备等对实时性要求高的场景。",
        "title": "以下哪种操作系统主要用于工业控制和武器系统等对响应时间要求极高的领域（）。",
        "question_text": "以下哪种操作系统主要用于工业控制和武器系统等对响应时间要求极高的领域（）。",
        "analysis": "实时操作系统能够在规定时间内对外部事件做出响应，常用于工业控制、导弹发射、医疗设备等对实时性要求高的场景。",
        "knowledge_id": "1.3",
        "knowledge_name": "1.3 操作系统的分类",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_3_13",
        "knowledge_point": "1.3 操作系统的分类",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "以下关于网络操作系统和分布式操作系统的区别，描述正确的是（）。",
        "options": [
            "A. 网络操作系统中，用户可以知道资源在哪个节点上",
            "B. 分布式操作系统仅支持局域网环境",
            "C. 网络操作系统中的多台计算机对用户是透明的",
            "D. 分布式操作系统不需要网络连接"
        ],
        "answer": "A",
        "explanation": "在网络操作系统中，用户必须知道资源所在的位置（节点）；而分布式操作系统中，多台计算机对用户是透明的，系统自动调度资源。",
        "title": "以下关于网络操作系统和分布式操作系统的区别，描述正确的是（）。",
        "question_text": "以下关于网络操作系统和分布式操作系统的区别，描述正确的是（）。",
        "analysis": "在网络操作系统中，用户必须知道资源所在的位置（节点）；而分布式操作系统中，多台计算机对用户是透明的，系统自动调度资源。",
        "knowledge_id": "1.3",
        "knowledge_name": "1.3 操作系统的分类",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_3_14",
        "knowledge_point": "1.3 操作系统的分类",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "硬实时系统与软实时系统的主要区别在于（）。",
        "options": [
            "A. 使用的内存大小不同",
            "B. 是否必须在严格规定的时间内完成任务",
            "C. 是否需要CPU支持多核",
            "D. 是否支持多用户"
        ],
        "answer": "B",
        "explanation": "硬实时系统要求任务必须在截止时间前完成，否则系统会失效（如导弹控制系统）；软实时系统允许偶尔超时，仍可接受（如视频播放）。",
        "title": "硬实时系统与软实时系统的主要区别在于（）。",
        "question_text": "硬实时系统与软实时系统的主要区别在于（）。",
        "analysis": "硬实时系统要求任务必须在截止时间前完成，否则系统会失效（如导弹控制系统）；软实时系统允许偶尔超时，仍可接受（如视频播放）。",
        "knowledge_id": "1.3",
        "knowledge_name": "1.3 操作系统的分类",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },

    # ---- 1.4 操作系统的运行环境 (easy=+3, medium=+3, hard=+2) ----
    {
        "id": "q1_4_4",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "CPU的工作状态中，操作系统内核运行在（）。",
        "options": [
            "A. 目态（用户态）",
            "B. 管态（核心态）",
            "C. 任何一种状态都可以",
            "D. 取决于CPU型号"
        ],
        "answer": "B",
        "explanation": "操作系统内核运行在管态（核心态/内核态），可以执行特权指令；用户程序运行在目态（用户态），不能执行特权指令。",
        "title": "CPU的工作状态中，操作系统内核运行在（）。",
        "question_text": "CPU的工作状态中，操作系统内核运行在（）。",
        "analysis": "操作系统内核运行在管态（核心态/内核态），可以执行特权指令；用户程序运行在目态（用户态），不能执行特权指令。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_4_5",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "系统调用是由操作系统提供给用户的（）。",
        "options": [
            "A. 应用程序",
            "B. 编程接口",
            "C. 硬件设备",
            "D. 编译器"
        ],
        "answer": "B",
        "explanation": "系统调用是操作系统提供给用户程序的一组编程接口，用户程序通过系统调用请求操作系统的服务。",
        "title": "系统调用是由操作系统提供给用户的（）。",
        "question_text": "系统调用是由操作系统提供给用户的（）。",
        "analysis": "系统调用是操作系统提供给用户程序的一组编程接口，用户程序通过系统调用请求操作系统的服务。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_4_6",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "中断和异常的区别在于（）。",
        "options": [
            "A. 中断来自外部事件，异常来自处理器内部",
            "B. 中断来自处理器内部，异常来自外部事件",
            "C. 两者没有区别",
            "D. 中断只能由软件产生"
        ],
        "answer": "A",
        "explanation": "中断是由外部硬件设备产生的异步事件（如I/O完成），异常是由处理器内部执行指令时产生的同步事件（如除零错误）。",
        "title": "中断和异常的区别在于（）。",
        "question_text": "中断和异常的区别在于（）。",
        "analysis": "中断是由外部硬件设备产生的异步事件（如I/O完成），异常是由处理器内部执行指令时产生的同步事件（如除零错误）。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_4_7",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "medium",
        "type": "single_choice",
        "question": "特权指令只能在（）状态下执行。",
        "options": [
            "A. 用户态",
            "B. 核心态",
            "C. 用户态和核心态均可",
            "D. 中断服务程序执行的任意状态"
        ],
        "answer": "B",
        "explanation": "特权指令（如I/O指令、设置时钟等）只能在核心态下执行，以防止用户程序破坏系统。用户态程序需要使用系统调用来请求这些服务。",
        "title": "特权指令只能在（）状态下执行。",
        "question_text": "特权指令只能在（）状态下执行。",
        "analysis": "特权指令（如I/O指令、设置时钟等）只能在核心态下执行，以防止用户程序破坏系统。用户态程序需要使用系统调用来请求这些服务。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_4_8",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "medium",
        "type": "single_choice",
        "question": "系统从用户态转换到核心态的途径不包括（）。",
        "options": [
            "A. 系统调用",
            "B. 中断",
            "C. 用户程序直接跳转",
            "D. 异常"
        ],
        "answer": "C",
        "explanation": "用户态到核心态的转换只能通过系统调用、中断或异常这三种途径，用户程序不能直接跳转到核心态。",
        "title": "系统从用户态转换到核心态的途径不包括（）。",
        "question_text": "系统从用户态转换到核心态的途径不包括（）。",
        "analysis": "用户态到核心态的转换只能通过系统调用、中断或异常这三种途径，用户程序不能直接跳转到核心态。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_4_9",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "medium",
        "type": "single_choice",
        "question": "中断处理过程的第一步是（）。",
        "options": [
            "A. 执行中断服务程序",
            "B. 恢复被中断程序的上下文",
            "C. 保存被中断程序的上下文",
            "D. 发出中断响应信号"
        ],
        "answer": "C",
        "explanation": "中断处理过程为：保存被中断程序的上下文（即保护现场），然后执行中断服务程序，最后恢复现场并返回被中断的程序。",
        "title": "中断处理过程的第一步是（）。",
        "question_text": "中断处理过程的第一步是（）。",
        "analysis": "中断处理过程为：保存被中断程序的上下文（即保护现场），然后执行中断服务程序，最后恢复现场并返回被中断的程序。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_4_10",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "在系统调用过程中，参数传递的常用方法不包括（）。",
        "options": [
            "A. 通过寄存器传递参数",
            "B. 在内存的指定区域存放参数",
            "C. 通过栈传递参数",
            "D. 通过硬盘交换区传递参数"
        ],
        "answer": "D",
        "explanation": "系统调用参数传递的常用方法有：(1)通过通用寄存器传递；(2)将参数存放在内存指定区域（如表、块），其地址通过寄存器传递；(3)通过栈传递参数。不存在通过硬盘交换区传递参数的方式。",
        "title": "在系统调用过程中，参数传递的常用方法不包括（）。",
        "question_text": "在系统调用过程中，参数传递的常用方法不包括（）。",
        "analysis": "系统调用参数传递的常用方法有：(1)通过通用寄存器传递；(2)将参数存放在内存指定区域（如表、块），其地址通过寄存器传递；(3)通过栈传递参数。不存在通过硬盘交换区传递参数的方式。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_4_11",
        "knowledge_point": "1.4 操作系统的运行环境",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "以下关于系统调用的叙述中，错误的是（）。",
        "options": [
            "A. 系统调用会引发CPU状态从用户态切换到核心态",
            "B. 系统调用的处理过程类似于一次中断处理",
            "C. 系统调用是操作系统提供给用户程序的唯一接口",
            "D. 每个系统调用都有一个唯一的编号"
        ],
        "answer": "C",
        "explanation": "系统调用是编程接口，但操作系统还提供命令接口（如Shell命令行）和图形用户接口（GUI）等其他接口供用户使用。",
        "title": "以下关于系统调用的叙述中，错误的是（）。",
        "question_text": "以下关于系统调用的叙述中，错误的是（）。",
        "analysis": "系统调用是编程接口，但操作系统还提供命令接口（如Shell命令行）和图形用户接口（GUI）等其他接口供用户使用。",
        "knowledge_id": "1.4",
        "knowledge_name": "1.4 操作系统的运行环境",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },

    # ---- 1.5 操作系统的结构 (easy=+3, medium=+3, hard=+2) ----
    {
        "id": "q1_5_4",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "将操作系统划分为若干层次，每层只能调用相邻下层功能的体系结构是（）。",
        "options": [
            "A. 整体式结构",
            "B. 层次式结构",
            "C. 微内核结构",
            "D. 客户/服务器结构"
        ],
        "answer": "B",
        "explanation": "层次式结构将操作系统划分为多个层次，每层只能调用其下层提供的功能，上层通过下层接口获得服务。",
        "title": "将操作系统划分为若干层次，每层只能调用相邻下层功能的体系结构是（）。",
        "question_text": "将操作系统划分为若干层次，每层只能调用相邻下层功能的体系结构是（）。",
        "analysis": "层次式结构将操作系统划分为多个层次，每层只能调用其下层提供的功能，上层通过下层接口获得服务。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_5_5",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "微内核结构的核心思想是（）。",
        "options": [
            "A. 将所有操作系统功能放在内核中",
            "B. 将尽可能多的功能移到内核外，内核只提供最基本功能",
            "C. 使用单层结构设计操作系统",
            "D. 将内核分为多个层次"
        ],
        "answer": "B",
        "explanation": "微内核结构将操作系统中最基本的功能（如进程通信、内存管理基础）保留在内核中，其他服务（如文件系统、网络协议）以用户进程方式运行在用户态。",
        "title": "微内核结构的核心思想是（）。",
        "question_text": "微内核结构的核心思想是（）。",
        "analysis": "微内核结构将操作系统中最基本的功能（如进程通信、内存管理基础）保留在内核中，其他服务（如文件系统、网络协议）以用户进程方式运行在用户态。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_5_6",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "easy",
        "type": "single_choice",
        "question": "最早的UNIX操作系统采用的是（）结构。",
        "options": [
            "A. 整体式（模块化）结构",
            "B. 微内核结构",
            "C. 虚拟机结构",
            "D. 客户/服务器结构"
        ],
        "answer": "A",
        "explanation": "早期的UNIX系统采用整体式（模块化）结构，所有内核功能在一个大内核中实现，各模块之间可以直接相互调用。",
        "title": "最早的UNIX操作系统采用的是（）结构。",
        "question_text": "最早的UNIX操作系统采用的是（）结构。",
        "analysis": "早期的UNIX系统采用整体式（模块化）结构，所有内核功能在一个大内核中实现，各模块之间可以直接相互调用。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_5_7",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "medium",
        "type": "single_choice",
        "question": "整体式结构的优点是（）。",
        "options": [
            "A. 系统可靠性高",
            "B. 模块隔离性好",
            "C. 代码执行效率高",
            "D. 易于维护和移植"
        ],
        "answer": "C",
        "explanation": "整体式结构中各模块可直接相互调用，减少了通信开销，代码执行效率高；但其缺点是结构混乱、难以维护和移植。",
        "title": "整体式结构的优点是（）。",
        "question_text": "整体式结构的优点是（）。",
        "analysis": "整体式结构中各模块可直接相互调用，减少了通信开销，代码执行效率高；但其缺点是结构混乱、难以维护和移植。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_5_8",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "medium",
        "type": "single_choice",
        "question": "以下关于微内核结构的描述，错误的是（）。",
        "options": [
            "A. 内核精简，只提供最基本的服务",
            "B. 其他操作系统服务以用户进程形式运行",
            "C. 微内核的代码量比单内核大",
            "D. 进程间通信是微内核提供的基本服务之一"
        ],
        "answer": "C",
        "explanation": "微内核结构的内核代码量远小于整体式（单内核）结构，因为微内核只保留了最基本的服务，所以代码更精简。",
        "title": "以下关于微内核结构的描述，错误的是（）。",
        "question_text": "以下关于微内核结构的描述，错误的是（）。",
        "analysis": "微内核结构的内核代码量远小于整体式（单内核）结构，因为微内核只保留了最基本的服务，所以代码更精简。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_5_9",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "medium",
        "type": "single_choice",
        "question": "虚拟机结构的核心思想是（）。",
        "options": [
            "A. 使用一个操作系统虚拟出多个硬件平台",
            "B. 将多个物理机合并为一台",
            "C. 将操作系统分为多个微内核",
            "D. 取消内核，所有功能在用户态实现"
        ],
        "answer": "A",
        "explanation": "虚拟机结构通过虚拟机监控层（VMM/Hypervisor）将一台物理计算机虚拟化为多台逻辑计算机，每台可以运行独立的操作系统。",
        "title": "虚拟机结构的核心思想是（）。",
        "question_text": "虚拟机结构的核心思想是（）。",
        "analysis": "虚拟机结构通过虚拟机监控层（VMM/Hypervisor）将一台物理计算机虚拟化为多台逻辑计算机，每台可以运行独立的操作系统。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_5_10",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "微内核结构的主要设计缺陷是（）。",
        "options": [
            "A. 内核代码太大",
            "B. 进程通信开销导致性能下降",
            "C. 安全性较差",
            "D. 无法支持分布式系统"
        ],
        "answer": "B",
        "explanation": "微内核结构中，大部分操作系统服务运行在用户态，各服务之间以及服务与内核之间需要通过进程间通信（IPC）进行交互，频繁的IPC会造成性能开销，这是微内核的主要缺陷。",
        "title": "微内核结构的主要设计缺陷是（）。",
        "question_text": "微内核结构的主要设计缺陷是（）。",
        "analysis": "微内核结构中，大部分操作系统服务运行在用户态，各服务之间以及服务与内核之间需要通过进程间通信（IPC）进行交互，频繁的IPC会造成性能开销，这是微内核的主要缺陷。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
    {
        "id": "q1_5_11",
        "knowledge_point": "1.5 操作系统的结构",
        "difficulty": "hard",
        "type": "single_choice",
        "question": "客户/服务器结构（C/S结构）的优点是（）。",
        "options": [
            "A. 避免了进程间通信",
            "B. 便于实现分布式处理",
            "C. 操作系统代码集中在单一内核中",
            "D. 不需要网络支持"
        ],
        "answer": "B",
        "explanation": "客户/服务器结构将操作系统功能划分为服务器进程和客户进程，两者通过消息传递进行通信，这种模式天然适合分布式环境。",
        "title": "客户/服务器结构（C/S结构）的优点是（）。",
        "question_text": "客户/服务器结构（C/S结构）的优点是（）。",
        "analysis": "客户/服务器结构将操作系统功能划分为服务器进程和客户进程，两者通过消息传递进行通信，这种模式天然适合分布式环境。",
        "knowledge_id": "1.5",
        "knowledge_name": "1.5 操作系统的结构",
        "chapter_id": "1",
        "chapter_name": "第1章",
        "status": "enabled",
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    },
]

print("=" * 60)
print("PART 1: New Questions Count")
print("=" * 60)
for q in NEW_QUESTIONS:
    print("  %s: %s [%s]" % (q['id'], q['knowledge_id'], q['difficulty']))
print("  Total new questions: %d" % len(NEW_QUESTIONS))

# ============================================================
# Write questions.json
# ============================================================
print()
print("=" * 60)
print("Writing questions.json...")
print("=" * 60)

with open('resources/questions.json', 'r', encoding='utf-8') as f:
    qdata = json.load(f)

existing_ids = {q['id'] for q in qdata['questions']}
print("  Existing question count: %d" % len(qdata['questions']))
print("  Existing IDs: %d unique" % len(existing_ids))

new_count = 0
for q in NEW_QUESTIONS:
    if q['id'] not in existing_ids:
        qdata['questions'].append(q)
        new_count += 1
    else:
        print("  SKIP duplicate: %s" % q['id'])

with open('resources/questions.json', 'w', encoding='utf-8') as f:
    json.dump(qdata, f, ensure_ascii=False, indent=2)

print("  Added %d new questions" % new_count)
print("  Total questions after: %d" % len(qdata['questions']))

# ============================================================
# PART 2: Generate Question History
# ============================================================
print()
print("=" * 60)
print("PART 2: Generating Question History for 1.2-1.5")
print("=" * 60)

with open('resources/question_history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)

TARGET_KPS = ['1.2', '1.3', '1.4', '1.5']

target_question_ids = []
for q in qdata['questions']:
    kid = q.get('knowledge_id', '')
    if kid in TARGET_KPS:
        target_question_ids.append(q['id'])

existing_qids_for_history = set()
for sid, records in history.items():
    for qid in records:
        if qid in target_question_ids:
            existing_qids_for_history.add((sid, qid))

print("  Target question IDs: %d" % len(target_question_ids))
print("  Existing history entries: %d" % len(existing_qids_for_history))

def generate_answer_timestamps(correct_count, wrong_count, seed_offset=0):
    """Generate realistic timestamped answers"""
    random.seed(int(time.time() * 1000) % 10000 + seed_offset)
    answers = []
    total = correct_count + wrong_count
    base_date = "2025-09-01"
    month = 9
    day = 1 + seed_offset % 10
    hour = 8 + seed_offset % 12

    for i in range(total):
        is_correct = i < correct_count
        ts = "2025-%02d-%02dT%02d:%02d:00" % (month, day, hour, random.randint(0, 59))
        option_idx = 0 if is_correct else random.randint(1, 3)
        answers.append({
            "answer": chr(ord('A') + option_idx),
            "correct": is_correct,
            "timestamp": ts
        })
        day += 1
        if day > 28:
            day = 1
            month += 1
        hour += 1
    return answers, ts

def calc_consecutive_correct(answers):
    consecutive = 0
    for a in reversed(answers):
        if a['correct']:
            consecutive += 1
        else:
            break
    return consecutive

# Generate records for each student
for sid, stype in STUDENT_TYPES.items():
    name = STUDENT_NAME_MAP.get(sid, '')
    history_key = sid + name

    if history_key not in history:
        history[history_key] = {}

    for q in qdata['questions']:
        kid = q.get('knowledge_id', '')
        if kid not in TARGET_KPS:
            continue
        qid = q['id']
        diff = q.get('difficulty', 'medium')

        # Skip if already has history
        if qid in history[history_key]:
            continue

        seed = hash(sid + qid) % 10000

        if stype == 'excellent':
            if diff == 'easy':
                correct = random.Random(seed + 1).randint(3, 5)
                wrong = random.Random(seed + 2).randint(0, 1)
            elif diff == 'medium':
                correct = random.Random(seed + 1).randint(2, 4)
                wrong = random.Random(seed + 2).randint(1, 2)
            else:
                correct = random.Random(seed + 1).randint(1, 3)
                wrong = random.Random(seed + 2).randint(1, 2)
        elif stype == 'medium':
            if diff == 'easy':
                correct = random.Random(seed + 1).randint(2, 4)
                wrong = random.Random(seed + 2).randint(1, 2)
            elif diff == 'medium':
                correct = random.Random(seed + 1).randint(1, 3)
                wrong = random.Random(seed + 2).randint(1, 3)
            else:
                correct = random.Random(seed + 1).randint(0, 2)
                wrong = random.Random(seed + 2).randint(1, 3)
        else:
            if diff == 'easy':
                correct = random.Random(seed + 1).randint(0, 3)
                wrong = random.Random(seed + 2).randint(0, 4)
                # At least attempt some
                if correct + wrong == 0:
                    correct = 0
                    wrong = random.Random(seed + 3).randint(1, 2)
            elif diff == 'medium':
                correct = random.Random(seed + 1).randint(0, 2)
                wrong = random.Random(seed + 2).randint(0, 3)
                if correct + wrong == 0:
                    wrong = 1
            else:
                correct = random.Random(seed + 1).randint(0, 1)
                wrong = random.Random(seed + 2).randint(0, 2)
                if random.Random(seed + 3).random() < 0.4:
                    correct = 0
                    wrong = 0

        # For 赵六 (weak), generate fewer records (only easy ones, fewer attempts)
        if sid == '3220602006':
            if diff == 'hard':
                correct = 0
                wrong = 0
            elif diff == 'medium':
                if random.Random(seed + 3).random() < 0.6:
                    correct = 0
                    wrong = 0

        if correct == 0 and wrong == 0:
            continue

        answers, last_ts = generate_answer_timestamps(correct, wrong, seed)
        consecutive = calc_consecutive_correct(answers)

        history[history_key][qid] = {
            "correct_count": correct,
            "wrong_count": wrong,
            "last_answer": last_ts,
            "consecutive_correct": consecutive,
            "answers": answers
        }

with open('resources/question_history.json', 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# Count generated records
for sid, stype in [('3220602001', 'excellent'), ('3220602004', 'medium'), ('3220602006', 'weak')]:
    name = STUDENT_NAME_MAP.get(sid, '')
    hk = sid + name
    sh = history.get(hk, {})
    kp_counts = defaultdict(int)
    for qid, qi in sh.items():
        for q in qdata['questions']:
            if q['id'] == qid:
                kid = q.get('knowledge_id', '')
                if kid in TARGET_KPS:
                    kp_counts[kid] += 1
    print("  %s(%s) records: 1.2=%d, 1.3=%d, 1.4=%d, 1.5=%d" % (
        name, sid, kp_counts['1.2'], kp_counts['1.3'], kp_counts['1.4'], kp_counts['1.5']))

# ============================================================
# PART 3: Recalculate Mastery
# ============================================================
print()
print("=" * 60)
print("PART 3: Recalculating students_mastery.json")
print("=" * 60)

with open('resources/students_mastery.json', 'r', encoding='utf-8') as f:
    mastery = json.load(f)

with open('resources/learning_records.json', 'r', encoding='utf-8') as f:
    learning = json.load(f)

def calc_question_performance(sid, kid):
    name = STUDENT_NAME_MAP.get(sid, '')
    hk = sid + name
    sh = history.get(hk, {})
    total_correct = 0
    total_wrong = 0
    for qid, qi in sh.items():
        for q in qdata['questions']:
            if q['id'] == qid and q.get('knowledge_id', '') == kid:
                total_correct += qi.get('correct_count', 0)
                total_wrong += qi.get('wrong_count', 0)
    total = total_correct + total_wrong
    if total == 0:
        return 0.0
    return total_correct / total

def calc_resource_performance(sid, kid):
    name = STUDENT_NAME_MAP.get(sid, '')
    full_sid = sid + name
    completed = 0
    total = 0
    for rec in learning:
        if rec.get('student_id') == full_sid and rec.get('knowledge_id') == kid:
            total += 1
            if rec.get('action_type') == 'complete':
                completed += 1
    if total == 0:
        return 0.0
    return completed / total

KP_NAMES = {
    '1.2': '1.2 操作系统的形成和发展',
    '1.3': '1.3 操作系统的分类',
    '1.4': '1.4 操作系统的运行环境',
    '1.5': '1.5 操作系统的结构',
}

for sid in STUDENT_TYPES:
    sm = mastery.get(sid, {})
    for kid, kp_name in KP_NAMES.items():
        qp = calc_question_performance(sid, kid)
        rp = calc_resource_performance(sid, kid)
        new_m = 0.7 * qp + 0.3 * rp
        old_m = sm.get(kp_name, 0)
        sm[kp_name] = round(new_m, 4)
    mastery[sid] = sm

with open('resources/students_mastery.json', 'w', encoding='utf-8') as f:
    json.dump(mastery, f, ensure_ascii=False, indent=2)

print()
print("MASTERY RESULTS (1.2-1.5):")
print("-" * 60)
for sid in ['3220602001', '3220602004', '3220602006']:
    sm = mastery.get(sid, {})
    name = STUDENT_NAME_MAP.get(sid, '')
    print("  %s (%s):" % (name, sid))
    for kid, kp_name in KP_NAMES.items():
        m = sm.get(kp_name, 0)
        print("    %s (%s): %.4f (%.1f%%)" % (kid, kp_name, m, m * 100))

# ============================================================
# Verification
# ============================================================
print()
print("=" * 60)
print("VERIFICATION")
print("=" * 60)

# Count after
kps_after = defaultdict(lambda: {'count': 0, 'easy': 0, 'medium': 0, 'hard': 0})
for q in qdata['questions']:
    kid = q.get('knowledge_id', '')
    kps_after[kid]['count'] += 1
    diff = q.get('difficulty', '')
    if diff in ('easy', 'medium', 'hard'):
        kps_after[kid][diff] += 1

for kp in TARGET_KPS:
    info = kps_after[kp]
    print("  %s: total=%d, easy=%d, medium=%d, hard=%d" % (
        kp, info['count'], info['easy'], info['medium'], info['hard']))

print()
print("  DONE: All 1.2-1.5 questions added, history generated, mastery recalculated.")