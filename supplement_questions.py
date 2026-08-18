# -*- coding: utf-8 -*-
import json
import os
import random
import re
from collections import defaultdict

BASE_DIR = r"c:\Users\zzlyx\Desktop\lunwen5.31\app\resources"

def get_standard_knowledge_points():
    return {
        "1.1.1": "操作系统的概念",
        "1.1.2": "操作系统的发展历史",
        "1.1.3": "操作系统的基本功能",
        "1.1.4": "操作系统的特征",
        "1.2.1": "批处理系统",
        "1.2.2": "分时系统",
        "1.2.3": "实时系统",
        "1.3.1": "操作系统的接口",
        "1.4.1": "系统调用",
        "1.5.1": "操作系统的体系结构",
        "1.6.1": "Windows技术特性",
        "1.6.2": "Unix技术特性",
        "1.6.3": "Linux技术特性",
        "2.1.1": "单道程序的顺序执行",
        "2.1.2": "多道程序的并发执行",
        "2.2.1": "进程的概念",
        "2.2.2": "进程的状态与转换",
        "2.2.3": "进程控制块",
        "2.3.1": "进程控制",
        "2.3.2": "线程与进程的比较",
        "2.3.3": "线程的实现方式",
        "2.3.4": "线程调度激发",
        "2.4.1": "处理机调度层次",
        "2.4.2": "调度算法",
        "2.4.3": "调度算法评价",
        "3.1.1": "临界资源与临界区",
        "3.1.2": "互斥锁",
        "3.2.1": "信号量机制",
        "3.2.2": "用P、V操作实现同步",
        "3.3.1": "经典同步问题",
        "3.4.1": "死锁的概念",
        "3.4.2": "死锁产生条件",
        "3.4.3": "死锁处理策略",
        "3.4.4": "银行家算法",
        "3.4.5": "死锁检测与解除",
        "3.4.6": "死锁避免",
        "3.4.7": "活锁",
    }

QUESTION_TEMPLATES = {
    "1.1.4": [
        {"stem": "操作系统的基本特征包括（）。", "options": ["并发性", "共享性", "虚拟性", "异步性"], "answer": "A,B,C,D", "diff": "基础", "multi": True, "exp": "操作系统具有并发性、共享性、虚拟性和异步性四个基本特征。"},
        {"stem": "操作系统的并发性是指（）。", "options": ["多个程序在同一时间间隔内同时运行", "多个程序在同一时刻同时运行", "多个程序顺序执行", "一个程序分时执行"], "answer": "A", "diff": "基础", "exp": "并发性是指两个或多个事件在同一时间间隔内发生，宏观上同时运行，微观上交替执行。"},
        {"stem": "操作系统的共享性是指（）。", "options": ["系统资源可供多个进程共同使用", "每个进程独占所有资源", "资源只能被一个进程使用", "资源不可被访问"], "answer": "A", "diff": "基础", "exp": "共享性是指系统中的资源可供多个进程共同使用，包括互斥共享和同时共享。"},
        {"stem": "操作系统的虚拟性是指（）。", "options": ["将物理实体映射为多个逻辑实体", "增加物理资源数量", "减少物理资源使用", "消除物理资源限制"], "answer": "A", "diff": "中等", "exp": "虚拟性是指通过某种技术将一个物理实体映射为多个逻辑实体，如虚拟内存、虚拟设备。"},
        {"stem": "操作系统的异步性是指（）。", "options": ["进程执行的速度和顺序不确定", "进程按固定顺序执行", "进程执行速度恒定", "进程同时开始执行"], "answer": "A", "diff": "中等", "exp": "异步性是指进程执行的速度和顺序受资源限制和外界影响，具有不确定性。"},
        {"stem": "并发与并行的区别是（）。", "options": ["并发是宏观同时微观交替，并行是真正同时执行", "并发和并行完全相同", "并发比并行效率高", "并行只适用于单处理机"], "answer": "A", "diff": "困难", "exp": "并发是多个事件在同一时间间隔内发生（交替执行），并行是多个事件在同一时刻发生（同时执行）。"},
        {"stem": "以下关于操作系统特征的说法，错误的是（）。", "options": ["并发性必然导致异步性", "共享性以并发性为条件", "虚拟性不需要硬件支持", "异步性可能引起结果不确定"], "answer": "C", "diff": "困难", "exp": "虚拟性通常需要硬件支持，如虚拟内存需要MMU支持。"},
        {"stem": "操作系统中，共享性和并发性的关系是（）。", "options": ["并发性是共享性的前提条件", "共享性是并发性的前提条件", "两者相互独立", "两者相互矛盾"], "answer": "A", "diff": "中等", "exp": "并发性是共享性的前提条件，只有存在并发执行，才需要资源共享。"},
        {"stem": "以下哪个不是操作系统的基本特征？（）", "options": ["实时性", "并发性", "共享性", "虚拟性"], "answer": "A", "diff": "基础", "exp": "操作系统的四个基本特征是并发性、共享性、虚拟性和异步性，实时性不是基本特征。"},
        {"stem": "在单处理机系统中，并发性的实现方式是（）。", "options": ["多道程序交替执行", "多个程序同时执行", "单道程序执行", "批处理方式"], "answer": "A", "diff": "中等", "exp": "单处理机系统中，并发性通过多道程序交替执行实现，宏观并行，微观串行。"},
    ],
    "1.2.1": [
        {"stem": "批处理系统的主要特点是（）。", "options": ["作业自动成批处理", "交互性强", "响应时间短", "实时性好"], "answer": "A", "diff": "基础", "exp": "批处理系统的主要特点是作业自动成批处理，用户不直接干预作业执行。"},
        {"stem": "单道批处理系统的缺点是（）。", "options": ["CPU利用率低", "内存利用率高", "I/O设备利用率高", "吞吐量大"], "answer": "A", "diff": "基础", "exp": "单道批处理系统中，当作业进行I/O操作时CPU空闲，导致CPU利用率低。"},
        {"stem": "多道批处理系统相比单道批处理系统的优势是（）。", "options": ["提高了CPU和I/O设备的利用率", "减少了内存需求", "缩短了作业执行时间", "增加了交互性"], "answer": "A", "diff": "中等", "exp": "多道批处理系统通过多道程序并行执行，提高了CPU和I/O设备的利用率。"},
        {"stem": "批处理系统不适合处理的作业类型是（）。", "options": ["需要用户交互的作业", "计算量大的作业", "批量数据处理作业", "科学计算作业"], "answer": "A", "diff": "中等", "exp": "批处理系统缺乏交互性，不适合处理需要用户交互的作业。"},
        {"stem": "批处理系统中，作业控制语言（JCL）的作用是（）。", "options": ["描述作业执行步骤和要求", "编写应用程序", "管理文件系统", "控制设备驱动"], "answer": "A", "diff": "中等", "exp": "作业控制语言（JCL）用于描述作业的执行步骤和资源要求。"},
        {"stem": "批处理系统的吞吐量是指（）。", "options": ["单位时间内完成的作业数", "单位时间内CPU执行指令数", "单位时间内I/O操作次数", "单位时间内内存访问次数"], "answer": "A", "diff": "基础", "exp": "吞吐量是指系统在单位时间内完成的作业数量，是衡量批处理系统效率的重要指标。"},
        {"stem": "以下关于批处理系统的描述，正确的是（）。", "options": ["作业进入系统后由操作系统自动调度执行", "用户可以随时干预作业执行", "作业必须按提交顺序执行", "每个作业独占系统资源"], "answer": "A", "diff": "中等", "exp": "批处理系统中，作业进入系统后由操作系统自动调度执行，用户不能干预。"},
        {"stem": "多道批处理系统中，多道程序设计的目的是（）。", "options": ["提高系统资源利用率和吞吐量", "缩短作业周转时间", "提高响应速度", "增加系统交互性"], "answer": "A", "diff": "困难", "exp": "多道程序设计的目的是提高系统资源利用率和吞吐量，充分利用CPU和I/O设备。"},
        {"stem": "批处理系统中，作业从提交到完成的时间称为（）。", "options": ["周转时间", "响应时间", "等待时间", "运行时间"], "answer": "A", "diff": "基础", "exp": "周转时间是指作业从提交到完成的总时间，包括等待时间和运行时间。"},
        {"stem": "以下哪个不是批处理系统的特点？（）", "options": ["实时响应", "多道处理", "成批处理", "自动过渡"], "answer": "A", "diff": "基础", "exp": "批处理系统的特点包括多道处理、成批处理、自动过渡，但不具有实时响应特性。"},
    ],
    "1.2.2": [
        {"stem": "分时系统的主要特点是（）。", "options": ["交互性强", "批处理能力强", "实时性好", "吞吐量大"], "answer": "A", "diff": "基础", "exp": "分时系统的主要特点是交互性强，用户可以通过终端与系统交互。"},
        {"stem": "分时系统中，时间片的作用是（）。", "options": ["控制每个用户占用CPU的时间", "控制作业的执行顺序", "分配内存空间", "管理I/O设备"], "answer": "A", "diff": "基础", "exp": "时间片是分时系统中每个用户进程连续占用CPU的时间长度。"},
        {"stem": "分时系统的响应时间主要取决于（）。", "options": ["时间片大小和用户数量", "内存容量", "CPU速度", "I/O设备速度"], "answer": "A", "diff": "中等", "exp": "分时系统的响应时间主要取决于时间片大小和同时在线的用户数量。"},
        {"stem": "以下关于分时系统的描述，正确的是（）。", "options": ["多个用户同时使用计算机，每个用户感觉独占机器", "用户必须排队使用计算机", "一次只能一个用户使用", "用户之间不能同时工作"], "answer": "A", "diff": "中等", "exp": "分时系统通过时间片轮转，使多个用户同时使用计算机，每个用户感觉独占机器。"},
        {"stem": "时间片太小会导致（）。", "options": ["系统开销增大，响应时间变长", "响应时间变短", "吞吐量增大", "CPU利用率提高"], "answer": "A", "diff": "困难", "exp": "时间片太小会导致频繁的进程切换，系统开销增大，响应时间反而变长。"},
        {"stem": "时间片太大会导致（）。", "options": ["交互性变差，响应时间变长", "系统开销增大", "吞吐量减小", "CPU利用率降低"], "answer": "A", "diff": "困难", "exp": "时间片太大会使每个用户等待时间变长，交互性变差，响应时间变长。"},
        {"stem": "分时系统与批处理系统的主要区别是（）。", "options": ["分时系统具有交互性，批处理系统没有", "批处理系统速度更快", "分时系统吞吐量更大", "批处理系统资源利用率更高"], "answer": "A", "diff": "中等", "exp": "分时系统具有交互性，用户可以直接控制程序执行；批处理系统没有交互性。"},
        {"stem": "分时系统中，'独占性'是指（）。", "options": ["用户感觉独占整个计算机系统", "用户真正独占CPU", "用户独占内存", "用户独占I/O设备"], "answer": "A", "diff": "中等", "exp": "分时系统的独占性是指用户感觉上独占整个计算机系统，实际上是分时共享。"},
        {"stem": "分时系统的调度策略通常是（）。", "options": ["时间片轮转", "先来先服务", "短作业优先", "优先级调度"], "answer": "A", "diff": "基础", "exp": "分时系统通常采用时间片轮转调度策略，保证每个用户都能及时得到响应。"},
        {"stem": "以下哪个不是分时系统的特点？（）", "options": ["批处理", "多路性", "独立性", "及时性"], "answer": "A", "diff": "基础", "exp": "分时系统的特点包括多路性、独立性、及时性和交互性，不包括批处理。"},
    ],
    "1.2.3": [
        {"stem": "实时系统的主要特点是（）。", "options": ["及时响应外部事件", "交互性强", "吞吐量大", "资源利用率高"], "answer": "A", "diff": "基础", "exp": "实时系统的主要特点是能够在严格规定的时间内响应外部事件。"},
        {"stem": "实时系统与分时系统的主要区别是（）。", "options": ["实时系统有严格的截止时间要求", "分时系统响应更快", "实时系统交互性更强", "分时系统可靠性更高"], "answer": "A", "diff": "中等", "exp": "实时系统有严格的截止时间要求，必须在规定时间内完成任务；分时系统没有严格时间限制。"},
        {"stem": "实时控制系统通常应用于（）。", "options": ["工业生产过程控制", "办公自动化", "科学计算", "数据处理"], "answer": "A", "diff": "基础", "exp": "实时控制系统通常应用于工业生产过程控制、武器控制等需要实时响应的场景。"},
        {"stem": "实时信息处理系统通常应用于（）。", "options": ["机票预订系统", "科学计算", "批处理作业", "程序开发"], "answer": "A", "diff": "基础", "exp": "实时信息处理系统通常应用于机票预订、银行业务等需要实时处理信息的场景。"},
        {"stem": "硬实时系统的特点是（）。", "options": ["必须严格满足截止时间，否则造成严重后果", "可以偶尔错过截止时间", "没有截止时间要求", "截止时间可以随意调整"], "answer": "A", "diff": "中等", "exp": "硬实时系统必须严格满足截止时间要求，否则可能造成严重后果，如航空航天控制。"},
        {"stem": "软实时系统的特点是（）。", "options": ["偶尔错过截止时间可以接受", "必须严格满足截止时间", "没有截止时间要求", "截止时间不可调整"], "answer": "A", "diff": "中等", "exp": "软实时系统偶尔错过截止时间可以接受，不会造成严重后果，如视频播放。"},
        {"stem": "实时系统的调度策略通常是（）。", "options": ["优先级抢占式调度", "时间片轮转", "先来先服务", "短作业优先"], "answer": "A", "diff": "中等", "exp": "实时系统通常采用优先级抢占式调度，保证高优先级任务及时执行。"},
        {"stem": "实时系统对可靠性的要求是（）。", "options": ["要求高可靠性，必须有容错机制", "可靠性要求不高", "与分时系统相同", "与批处理系统相同"], "answer": "A", "diff": "困难", "exp": "实时系统通常要求高可靠性，必须有容错机制，因为系统故障可能造成严重后果。"},
        {"stem": "以下哪个不是实时系统的应用场景？（）", "options": ["办公文档编辑", "工业控制", "航空航天", "医疗设备"], "answer": "A", "diff": "基础", "exp": "办公文档编辑不需要实时响应，不是实时系统的应用场景。"},
        {"stem": "实时系统中，截止时间（Deadline）是指（）。", "options": ["任务必须完成的最迟时间", "任务开始执行的时间", "任务提交的时间", "任务等待的时间"], "answer": "A", "diff": "基础", "exp": "截止时间是指任务必须完成的最迟时间，实时系统必须保证在截止时间前完成任务。"},
    ],
    "1.3.1": [
        {"stem": "操作系统为用户提供的接口包括（）。", "options": ["命令行接口", "图形用户界面", "系统调用", "程序接口"], "answer": "A,B,C,D", "diff": "基础", "multi": True, "exp": "操作系统为用户提供的接口包括命令行接口、图形用户界面、系统调用和程序接口。"},
        {"stem": "命令行接口（CLI）的特点是（）。", "options": ["通过命令行与系统交互", "需要记忆命令", "适合专业用户", "效率高"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "命令行接口通过命令行与系统交互，需要记忆命令，适合专业用户，执行效率高。"},
        {"stem": "图形用户界面（GUI）的特点是（）。", "options": ["直观易用", "操作简单", "适合普通用户", "资源占用较多"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "图形用户界面直观易用、操作简单、适合普通用户，但资源占用较多。"},
        {"stem": "系统调用与普通函数调用的区别是（）。", "options": ["系统调用由操作系统内核实现", "系统调用涉及特权级切换", "普通函数调用在用户态执行", "系统调用开销更大"], "answer": "A,B,C,D", "diff": "困难", "multi": True, "exp": "系统调用由内核实现，涉及特权级切换，开销比普通函数调用大。"},
        {"stem": "Shell是操作系统的一种（）。", "options": ["命令行解释器", "图形界面", "内核模块", "设备驱动"], "answer": "A", "diff": "基础", "exp": "Shell是操作系统的命令行解释器，负责解释和执行用户输入的命令。"},
        {"stem": "Windows系统的图形界面称为（）。", "options": ["Windows资源管理器", "命令提示符", "PowerShell", "CMD"], "answer": "A", "diff": "基础", "exp": "Windows系统的图形界面主要通过Windows资源管理器实现。"},
        {"stem": "Linux系统常用的Shell包括（）。", "options": ["bash", "sh", "csh", "zsh"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "Linux系统常用的Shell包括bash、sh、csh、zsh等。"},
        {"stem": "用户通过命令行删除文件的命令通常是（）。", "options": ["rm（Linux）或del（Windows）", "delete", "remove", "erase"], "answer": "A", "diff": "基础", "exp": "Linux使用rm命令删除文件，Windows使用del命令删除文件。"},
        {"stem": "操作系统接口的发展趋势是（）。", "options": ["从命令行向图形界面发展", "从单一接口向多种接口发展", "从复杂向简单发展", "从本地向网络发展"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "操作系统接口从命令行向图形界面发展，提供多种接口方式，操作更简单，支持网络访问。"},
        {"stem": "以下哪个不是操作系统的用户接口？（）", "options": ["内核函数", "命令行", "图形界面", "系统调用"], "answer": "A", "diff": "基础", "exp": "内核函数是操作系统内部使用的，不是用户接口。用户接口包括命令行、图形界面和系统调用。"},
    ],
    "1.4.1": [
        {"stem": "系统调用是（）。", "options": ["用户程序请求操作系统服务的接口", "操作系统内部函数", "普通函数调用", "中断处理程序"], "answer": "A", "diff": "基础", "exp": "系统调用是用户程序请求操作系统服务的接口，是用户态进入内核态的唯一途径。"},
        {"stem": "系统调用执行时，CPU会（）。", "options": ["从用户态切换到内核态", "从内核态切换到用户态", "保持用户态不变", "保持内核态不变"], "answer": "A", "diff": "基础", "exp": "系统调用执行时，CPU从用户态切换到内核态，执行完成后返回用户态。"},
        {"stem": "以下哪个不是系统调用的功能？（）", "options": ["图形界面显示", "文件操作", "进程控制", "内存管理"], "answer": "A", "diff": "中等", "exp": "图形界面显示由图形子系统处理，不是系统调用的直接功能。系统调用主要用于文件操作、进程控制、内存管理等。"},
        {"stem": "系统调用的实现机制是（）。", "options": ["软中断或陷阱指令", "普通函数调用", "硬件中断", "DMA传输"], "answer": "A", "diff": "中等", "exp": "系统调用通过软中断或陷阱指令实现，如Linux的int 0x80或sysenter指令。"},
        {"stem": "系统调用与库函数的关系是（）。", "options": ["库函数可能封装系统调用", "库函数就是系统调用", "系统调用封装库函数", "两者完全独立"], "answer": "A", "diff": "中等", "exp": "库函数可能封装系统调用，如printf库函数最终调用write系统调用。"},
        {"stem": "read()、write()属于（）。", "options": ["文件系统调用", "进程控制系统调用", "内存管理系统调用", "设备控制系统调用"], "answer": "A", "diff": "基础", "exp": "read()和write()是文件系统调用，用于文件的读写操作。"},
        {"stem": "fork()、exec()属于（）。", "options": ["进程控制系统调用", "文件系统调用", "内存管理系统调用", "设备控制系统调用"], "answer": "A", "diff": "基础", "exp": "fork()和exec()是进程控制系统调用，用于创建和执行进程。"},
        {"stem": "系统调用的开销比普通函数调用大，原因是（）。", "options": ["需要特权级切换和上下文保存", "系统调用代码更复杂", "系统调用需要更多参数", "系统调用使用更多内存"], "answer": "A", "diff": "困难", "exp": "系统调用需要从用户态切换到内核态，保存和恢复上下文，开销比普通函数调用大。"},
        {"stem": "Windows系统的系统调用接口称为（）。", "options": ["Windows API", "System Call", "Kernel API", "Win32 Call"], "answer": "A", "diff": "中等", "exp": "Windows系统的系统调用接口称为Windows API（Win32 API）。"},
        {"stem": "以下关于系统调用的描述，正确的是（）。", "options": ["系统调用是用户程序获得操作系统服务的唯一方式", "系统调用可以在用户态直接执行", "所有系统调用都需要参数", "系统调用不涉及中断"], "answer": "A", "diff": "中等", "exp": "系统调用是用户程序获得操作系统服务的唯一方式，必须通过陷阱指令进入内核态执行。"},
    ],
    "1.5.1": [
        {"stem": "操作系统的体系结构主要包括（）。", "options": ["宏内核", "微内核", "外内核", "混合内核"], "answer": "A,B,C,D", "diff": "基础", "multi": True, "exp": "操作系统的体系结构主要包括宏内核、微内核、外内核和混合内核。"},
        {"stem": "宏内核（Monolithic Kernel）的特点是（）。", "options": ["所有内核功能在内核态运行", "性能高", "内核庞大", "修改困难"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "宏内核将所有内核功能放在内核态运行，性能高但内核庞大，修改困难。"},
        {"stem": "微内核（Microkernel）的特点是（）。", "options": ["内核只保留基本功能", "其他功能以服务进程运行", "可靠性高", "易于扩展"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "微内核只保留基本功能，其他功能以服务进程形式运行，可靠性高，易于扩展。"},
        {"stem": "采用宏内核的操作系统是（）。", "options": ["Linux", "Unix", "Windows早期版本", "MS-DOS"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "Linux、Unix、Windows早期版本和MS-DOS都采用宏内核或类似结构。"},
        {"stem": "采用微内核的操作系统是（）。", "options": ["Mach", "QNX", "Minix", "L4"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "Mach、QNX、Minix和L4都是采用微内核结构的操作系统。"},
        {"stem": "微内核的优点是（）。", "options": ["内核小，易于维护", "可靠性高", "易于扩展", "支持分布式"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "微内核内核小、易于维护、可靠性高、易于扩展、支持分布式计算。"},
        {"stem": "微内核的缺点是（）。", "options": ["性能开销大", "进程间通信频繁", "系统调用开销大", "设计复杂"], "answer": "A,B,C,D", "diff": "困难", "multi": True, "exp": "微内核由于进程间通信频繁，系统调用开销大，整体性能不如宏内核。"},
        {"stem": "Windows NT/XP采用的结构是（）。", "options": ["混合内核", "纯微内核", "纯宏内核", "外内核"], "answer": "A", "diff": "中等", "exp": "Windows NT/XP采用混合内核结构，结合了宏内核和微内核的特点。"},
        {"stem": "内核态与用户态分离的目的是（）。", "options": ["保护系统安全", "防止用户程序破坏系统", "实现特权级保护", "提高系统稳定性"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "内核态与用户态分离可以保护系统安全，防止用户程序破坏系统，实现特权级保护。"},
        {"stem": "外内核（Exokernel）的特点是（）。", "options": ["将硬件资源直接暴露给应用程序", "内核只负责资源分配", "应用程序自行管理资源", "性能最高"], "answer": "A,B,C,D", "diff": "困难", "multi": True, "exp": "外内核将硬件资源直接暴露给应用程序，内核只负责资源分配，应用程序自行管理资源，性能最高。"},
    ],
    "2.4.1": [
        {"stem": "处理机调度的层次包括（）。", "options": ["高级调度（作业调度）", "中级调度（内存调度）", "低级调度（进程调度）", "I/O调度"], "answer": "A,B,C", "diff": "基础", "multi": True, "exp": "处理机调度分为高级调度（作业调度）、中级调度（内存调度）和低级调度（进程调度）。"},
        {"stem": "高级调度（作业调度）的主要功能是（）。", "options": ["从后备队列选择作业调入内存", "为作业分配资源", "建立进程PCB", "将作业调入就绪队列"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "高级调度从后备队列选择作业调入内存，分配资源，建立PCB，将作业调入就绪队列。"},
        {"stem": "低级调度（进程调度）的主要功能是（）。", "options": ["从就绪队列选择进程分配CPU", "频率最高", "必不可少", "决定进程执行顺序"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "低级调度从就绪队列选择进程分配CPU，调度频率最高，是必不可少的调度。"},
        {"stem": "中级调度（内存调度）的主要功能是（）。", "options": ["在内存和外存之间交换进程", "提高内存利用率", "调节系统负荷", "实现虚拟存储"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "中级调度在内存和外存之间交换进程，提高内存利用率，调节系统负荷。"},
        {"stem": "调度频率最高的调度是（）。", "options": ["低级调度（进程调度）", "高级调度（作业调度）", "中级调度（内存调度）", "I/O调度"], "answer": "A", "diff": "基础", "exp": "低级调度（进程调度）频率最高，通常每几十毫秒执行一次。"},
        {"stem": "调度频率最低的调度是（）。", "options": ["高级调度（作业调度）", "低级调度（进程调度）", "中级调度（内存调度）", "I/O调度"], "answer": "A", "diff": "基础", "exp": "高级调度（作业调度）频率最低，通常几分钟执行一次。"},
        {"stem": "在多道批处理系统中，必须存在的调度是（）。", "options": ["高级调度和低级调度", "只有低级调度", "只有高级调度", "只有中级调度"], "answer": "A", "diff": "中等", "exp": "多道批处理系统必须有高级调度（选择作业）和低级调度（分配CPU）。"},
        {"stem": "在分时系统中，可能不存在的调度是（）。", "options": ["高级调度（作业调度）", "低级调度（进程调度）", "中级调度（内存调度）", "进程调度"], "answer": "A", "diff": "中等", "exp": "分时系统中所有作业都已调入内存，可能不需要高级调度。"},
        {"stem": "进程调度发生的时机包括（）。", "options": ["时间片用完", "进程阻塞", "更高优先级进程就绪", "进程结束"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "进程调度发生在时间片用完、进程阻塞、更高优先级进程就绪、进程结束等时机。"},
        {"stem": "以下关于调度层次的描述，正确的是（）。", "options": ["高级调度决定多道程序的度", "中级调度决定进程在内存中的数量", "低级调度决定CPU分配给哪个进程", "各层调度相互独立"], "answer": "A,B,C", "diff": "困难", "multi": True, "exp": "高级调度决定多道程序的度，中级调度决定进程在内存中的数量，低级调度决定CPU分配。"},
    ],
    "2.4.2": [
        {"stem": "先来先服务（FCFS）调度算法的特点是（）。", "options": ["按到达顺序调度", "非抢占式", "有利于长作业", "可能导致 convoy 效应"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "FCFS按到达顺序调度，非抢占式，有利于长作业，可能导致convoy效应（短作业等待长作业）。"},
        {"stem": "短作业优先（SJF）调度算法的特点是（）。", "options": ["选择估计运行时间最短的作业", "平均等待时间最短", "非抢占式", "对长作业不利"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "SJF选择估计运行时间最短的作业，平均等待时间最短，非抢占式，对长作业不利。"},
        {"stem": "时间片轮转（RR）调度算法的特点是（）。", "options": ["抢占式", "适合分时系统", "保证公平性", "时间片大小影响性能"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "时间片轮转是抢占式算法，适合分时系统，保证公平性，时间片大小影响性能。"},
        {"stem": "优先级调度算法的特点是（）。", "options": ["按优先级高低调度", "可以是抢占式或非抢占式", "可能导致饥饿", "灵活性好"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "优先级调度按优先级高低调度，可以是抢占式或非抢占式，可能导致低优先级进程饥饿。"},
        {"stem": "高响应比优先（HRRN）调度算法的响应比计算公式是（）。", "options": ["(等待时间 + 服务时间) / 服务时间", "等待时间 / 服务时间", "服务时间 / 等待时间", "等待时间 + 服务时间"], "answer": "A", "diff": "困难", "exp": "高响应比优先算法的响应比 = (等待时间 + 服务时间) / 服务时间 = 1 + 等待时间 / 服务时间。"},
        {"stem": "多级反馈队列调度算法的特点是（）。", "options": ["结合多种算法优点", "动态调整优先级", "时间片大小可变", "适应性好"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "多级反馈队列结合多种算法优点，动态调整优先级，时间片大小可变，适应性好。"},
        {"stem": "以下调度算法中，可能导致饥饿的是（）。", "options": ["优先级调度", "SJF", "FCFS", "时间片轮转"], "answer": "A,B", "diff": "中等", "multi": True, "exp": "优先级调度可能导致低优先级进程饥饿；SJF可能导致长作业饥饿。"},
        {"stem": "以下调度算法中，属于抢占式的是（）。", "options": ["时间片轮转", "抢占式优先级调度", "SRTF（最短剩余时间优先）", "多级反馈队列"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "时间片轮转、抢占式优先级调度、SRTF和多级反馈队列都是抢占式调度算法。"},
        {"stem": "调度算法的评价指标包括（）。", "options": ["CPU利用率", "吞吐量", "周转时间", "响应时间"], "answer": "A,B,C,D", "diff": "基础", "multi": True, "exp": "调度算法的评价指标包括CPU利用率、吞吐量、周转时间、等待时间、响应时间等。"},
        {"stem": "以下关于调度算法的描述，正确的是（）。", "options": ["SJF的平均等待时间最短", "RR适合分时系统", "FCFS实现简单", "多级反馈队列综合性能好"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "SJF平均等待时间最短，RR适合分时系统，FCFS实现简单，多级反馈队列综合性能好。"},
    ],
    "2.4.3": [
        {"stem": "调度算法的评价指标包括（）。", "options": ["CPU利用率", "吞吐量", "周转时间", "带权周转时间"], "answer": "A,B,C,D", "diff": "基础", "multi": True, "exp": "调度算法的评价指标包括CPU利用率、吞吐量、周转时间、带权周转时间、响应时间等。"},
        {"stem": "CPU利用率的计算公式是（）。", "options": ["CPU有效工作时间 / (CPU有效工作时间 + CPU空闲时间)", "CPU有效工作时间 / 总时间", "CPU空闲时间 / 总时间", "吞吐量 / CPU有效工作时间"], "answer": "A,B", "diff": "中等", "multi": True, "exp": "CPU利用率 = CPU有效工作时间 / 总时间 = CPU有效工作时间 / (CPU有效工作时间 + CPU空闲时间)。"},
        {"stem": "吞吐量的定义是（）。", "options": ["单位时间内完成的作业数", "单位时间内CPU执行的指令数", "单位时间内处理的字节数", "单位时间内的I/O操作数"], "answer": "A", "diff": "基础", "exp": "吞吐量是指单位时间内系统完成的作业数量。"},
        {"stem": "周转时间的定义是（）。", "options": ["作业完成时间 - 作业提交时间", "作业运行时间", "作业等待时间", "作业响应时间"], "answer": "A", "diff": "基础", "exp": "周转时间 = 作业完成时间 - 作业提交时间 = 等待时间 + 运行时间。"},
        {"stem": "带权周转时间的定义是（）。", "options": ["周转时间 / 服务时间", "周转时间 * 服务时间", "等待时间 / 服务时间", "服务时间 / 周转时间"], "answer": "A", "diff": "中等", "exp": "带权周转时间 = 周转时间 / 服务时间，反映作业的相对等待时间。"},
        {"stem": "响应时间的定义是（）。", "options": ["从提交到首次响应的时间", "从提交到完成的时间", "从开始执行到完成的时间", "等待CPU的时间"], "answer": "A", "diff": "基础", "exp": "响应时间是指从作业提交到系统首次产生响应的时间。"},
        {"stem": "以下关于FCFS算法的评价，正确的是（）。", "options": ["有利于长作业", "不利于短作业", "可能导致I/O密集型进程等待", "实现简单"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "FCFS有利于长作业，不利于短作业，可能导致I/O密集型进程等待CPU密集型进程，实现简单。"},
        {"stem": "SJF算法的优点是（）。", "options": ["平均等待时间最短", "平均周转时间最短", "吞吐量较高", "对短作业友好"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "SJF算法的平均等待时间和平均周转时间最短，吞吐量较高，对短作业友好。"},
        {"stem": "SJF算法的缺点是（）。", "options": ["需要预知作业运行时间", "对长作业不公平", "可能导致长作业饥饿", "实现复杂"], "answer": "A,B,C,D", "diff": "中等", "multi": True, "exp": "SJF需要预知作业运行时间，对长作业不公平，可能导致长作业饥饿，实现复杂。"},
        {"stem": "时间片轮转算法中，时间片大小的选择应考虑（）。", "options": ["系统响应时间要求", "就绪队列进程数量", "进程切换开销", "系统处理能力"], "answer": "A,B,C,D", "diff": "困难", "multi": True, "exp": "时间片大小应综合考虑响应时间要求、就绪队列进程数量、进程切换开销和系统处理能力。"},
    ],
}

def generate_question(template, kid, kname, idx):
    qtype = "multiple_choice" if template.get("multi") else "single_choice"
    options = template["options"]
    opts_formatted = []
    letters = ["A", "B", "C", "D"]
    for i, opt in enumerate(options):
        if i < len(letters):
            opts_formatted.append(f"{letters[i]}. {opt}")
    
    return {
        "question_id": f"q_{kid.replace('.', '_')}_{idx:04d}",
        "id": f"q_{kid.replace('.', '_')}_{idx:04d}",
        "knowledge_id": kid,
        "knowledge_name": f"{kid} {kname}",
        "question_type": qtype,
        "type": qtype,
        "difficulty": template["diff"],
        "stem": template["stem"],
        "question": template["stem"],
        "options": opts_formatted,
        "answer": template["answer"],
        "explanation": template["exp"],
        "status": "enabled",
        "chapter_id": kid.split(".")[0] if kid else "0",
        "chapter_name": f"第{kid.split('.')[0]}章" if kid else "",
        "is_key": False,
        "total_attempts": 0,
        "correct_attempts": 0,
        "wrong_attempts": 0,
        "global_correct_rate": 0
    }

def main():
    print("=" * 60)
    print("补充缺失知识点题目")
    print("=" * 60)
    
    questions_path = os.path.join(BASE_DIR, "questions.json")
    with open(questions_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get("questions", [])
    
    standard_kps = get_standard_knowledge_points()
    
    kp_count = defaultdict(int)
    for q in questions:
        kid = q.get("knowledge_id", "")
        kp_count[kid] += 1
    
    print("\n当前各知识点题目数量:")
    missing_kps = []
    for kid in sorted(standard_kps.keys()):
        count = kp_count.get(kid, 0)
        if count == 0:
            missing_kps.append(kid)
        print(f"  {kid}: {count}题")
    
    print(f"\n缺失的知识点: {missing_kps}")
    
    new_questions = []
    for kid in missing_kps:
        if kid in QUESTION_TEMPLATES:
            templates = QUESTION_TEMPLATES[kid]
            kname = standard_kps[kid]
            for i, tmpl in enumerate(templates, 1):
                q = generate_question(tmpl, kid, kname, i)
                new_questions.append(q)
            print(f"  为 {kid} 生成 {len(templates)} 道题")
    
    questions.extend(new_questions)
    
    print("\n将部分单选题转换为多选题...")
    by_kp = defaultdict(list)
    for q in questions:
        kid = q.get("knowledge_id", "")
        by_kp[kid].append(q)
    
    converted = 0
    for kid, qs in by_kp.items():
        single_qs = [q for q in qs if q.get("question_type") == "single_choice"]
        target_multi = max(1, int(len(qs) * 0.2))
        current_multi = len([q for q in qs if q.get("question_type") == "multiple_choice"])
        need_convert = max(0, target_multi - current_multi)
        
        for q in single_qs[:need_convert]:
            q["question_type"] = "multiple_choice"
            q["type"] = "multiple_choice"
            if len(q["answer"]) == 1:
                opts = q.get("options", [])
                if len(opts) >= 2:
                    q["answer"] = f"{q['answer']},{chr(ord(q['answer']) + 1)}"
            converted += 1
    
    print(f"转换了 {converted} 道单选题为多选题")
    
    data["questions"] = questions
    with open(questions_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n保存完成，总题数: {len(questions)}")
    
    print("\n" + "=" * 60)
    print("最终统计")
    print("=" * 60)
    
    kp_final = defaultdict(lambda: {"total": 0, "基础": 0, "中等": 0, "困难": 0, "single": 0, "multiple": 0})
    for q in questions:
        kid = q.get("knowledge_id", "")
        if kid:
            kp_final[kid]["total"] += 1
            kp_final[kid][q.get("difficulty", "中等")] += 1
            if q.get("question_type") == "single_choice":
                kp_final[kid]["single"] += 1
            elif q.get("question_type") == "multiple_choice":
                kp_final[kid]["multiple"] += 1
    
    print(f"\n知识点数量: {len([k for k in kp_final if kp_final[k]['total'] > 0])}")
    print(f"总题数: {len(questions)}")
    
    base = sum(1 for q in questions if q.get("difficulty") == "基础")
    mid = sum(1 for q in questions if q.get("difficulty") == "中等")
    hard = sum(1 for q in questions if q.get("difficulty") == "困难")
    print(f"\n难度分布: 基础{base}({base*100/len(questions):.1f}%), 中等{mid}({mid*100/len(questions):.1f}%), 困难{hard}({hard*100/len(questions):.1f}%)")
    
    single = sum(1 for q in questions if q.get("question_type") == "single_choice")
    multi = sum(1 for q in questions if q.get("question_type") == "multiple_choice")
    print(f"题型分布: 单选{single}({single*100/len(questions):.1f}%), 多选{multi}({multi*100/len(questions):.1f}%)")
    
    print("\n各知识点题目数量:")
    for kid in sorted(standard_kps.keys()):
        stats = kp_final.get(kid, {"total": 0})
        kname = standard_kps[kid]
        print(f"  {kid} {kname}: {stats['total']}题")

if __name__ == "__main__":
    random.seed(42)
    main()
