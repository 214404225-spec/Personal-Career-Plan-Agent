# Personal Career Plan Agent —— 框架搭建计划

> **创建时间**：2026-06-05
> **状态**：设计完成，待实施

## Context

用户需要一个**个人使用的职业规划 Agent**，覆盖简历管理、实习申请、秋招准备等全流程。计划调用 Qwen3.7-plus（阿里云百炼）作为核心 Agent。核心需求：

1. 能读取多种文件格式（PDF、MD、PNG、JPG 等）
2. 高度个人可定制
3. 更多功能按需扩展

参考了企业级 Agent 框架调研文档（AgentScope / DeepAgents / pi-mono / Coze / Dify），但面向个人使用场景重新选型。

**选型结论**：采用**方案 B —— LangChain + DeepAgents 启发式架构**。不引入重量级企业框架，用 LangChain 做 LLM 调用和工具编排底层，借鉴 DeepAgents 的核心机制（任务规划 / 文件系统工具 / 记忆系统），上层自建 FastAPI Web 界面。

## 整体架构（四层）

```
┌─────────────────────────────────────────────────────────────┐
│                      Web UI Layer (FastAPI)                  │
│  • 聊天界面  • SSE 流式输出  • 简历管理面板  • 求职看板      │
├──────────────────────────────────────────────────────────────┤
│                      Agent Layer (Qwen 3.7-plus)              │
│  • 单 Agent，拥有全部工具，对话式交互                          │
│  • 意图理解 → 工具调用 → 记忆读写，无需子 Agent 委派           │
├──────────────────────────────────────────────────────────────┤
│                       Tool & Memory Layer                    │
│  • 文件解析: PyMuPDF(PDF) / python-docx(DOCX) / MinerU(图片) │
│  • JD抓取: httpx + BeautifulSoup                            │
│  • 双层记忆: 短期(对话窗口) + 长期(SQLite + MEMORY.md)       │
├──────────────────────────────────────────────────────────────┤
│                      Data & Storage Layer                    │
│  • 本地文件系统 (简历/JD/笔记/输出)   • SQLite (结构化数据)  │
└──────────────────────────────────────────────────────────────┘
```

**FastAPI 的角色**：HTTP API 服务（/chat SSE流式、/upload）、静态页面托管、WebSocket/SSE 实时推送。是浏览器和本地 Agent 之间的桥梁。

## 关键设计决策

- **Qwen 接入**：阿里云百炼提供 OpenAI 兼容接口，直接用 `langchain-openai` 的 `ChatOpenAI` 指向百炼 endpoint
- **上下文连续性**：单 Agent 全程持有完整对话历史 + 用户画像，无需跨 Agent 传递上下文片段
- **Local First**：所有数据本地存储，仅 Qwen API 调用依赖云服务

## Agent 层

单 Agent 架构——Qwen 3.7-plus 同时承担意图理解和工具执行，无需委派子 Agent。

### 工作模式

| 阶段 | 说明 |
|------|------|
| 理解意图 | Agent 判断用户当前需求：改简历？找岗位？准备面试？组合？ |
| 调用工具 | 根据需要调用 read_resume / read_jd / read_image / write_file 等 |
| 整合输出 | 工具结果直接在对话中整合呈现，无需跨 Agent 传递 |

### 典型对话流程

```
用户: "帮我看看简历有什么问题"
  → Agent 调用 read_resume → 分析 → 流式输出建议

用户: "针对这个 JD 优化一下"
  → Agent 调用 read_jd → 对比简历 → write_file 输出优化版

用户: "这个岗位面试会问什么"
  → Agent 调用 read_jd + read_resume → 生成预测问题 + 回答要点
```

所有功能复用同一套工具和同一份上下文，不需要 Orchestrator 拆解委派再整合。

## 工具层

| 工具 | 支持格式 | 底层库 |
|------|----------|--------|
| `read_resume` | PDF, DOCX, MD, TXT | PyMuPDF, python-docx |
| `read_image` | PNG, JPG, WEBP | MinerU |
| `read_jd` | URL, PDF, 纯文本 | httpx, BeautifulSoup, PyMuPDF |
| `read_notes` | MD, TXT | 原生 |
| `list_files` | — | 原生 |
| `write_file` | MD | 原生 |
| `web_search` | — | 可选 |

## 记忆系统

- **短期**：LangChain ConversationBufferWindow（默认保留最近 20 轮）
- **长期（SQLite + MEMORY.md）**：
  - 用户画像（教育背景、技能栈、目标行业）
  - 简历版本索引
  - 求职时间线（投递记录、面试、offer）
  - 偏好设置（目标城市、薪资、公司偏好）
- **注入方式**：每轮对话动态拼入系统提示词前段

## Web UI

- **技术**：FastAPI + Jinja2 + HTMX + SSE
- **布局**：左侧主聊天区（SSE 流式 Markdown）+ 右侧面板（快捷操作 + 文件列表）
- **页面**：主聊天页、设置页（用户画像 + API Key + 偏好）
- **快捷操作**：优化简历、匹配岗位、模拟面试、求职看板

## 项目目录结构

```
Personal-Career-Plan-Agent/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 入口
│   ├── config.py                  # 配置管理
│   ├── web/                       # Web UI 层
│   │   ├── routes.py              # /chat, /upload, /
│   │   ├── sse.py                 # SSE 流式响应
│   │   ├── templates/             # Jinja2 模板
│   │   └── static/                # 静态资源
│   ├── agent/                     # Agent 层
│   │   ├── agent.py               # 单 Agent（Qwen 接入 + 工具绑定）
│   │   └── prompts/               # 系统提示词模板(.md)
│   ├── tools/                     # 工具层
│   │   ├── file_reader.py         # PDF/DOCX/MD 读取
│   │   ├── image_reader.py        # 图片读取
│   │   ├── jd_reader.py           # JD 解析
│   │   └── file_writer.py         # 文件写入
│   ├── memory/                    # 记忆系统
│   │   ├── store.py               # SQLite 操作
│   │   ├── profile.py             # 用户画像
│   │   ├── job_timeline.py        # 求职时间线
│   │   └── memory_consolidator.py # 长期记忆合并
│   └── models/                    # 数据模型
│       ├── conversation.py
│       ├── resume.py
│       └── job.py
├── data/                          # 用户数据 (gitignore)
│   ├── resumes/  jds/  notes/  outputs/
├── workspace/                     # Agent 运行时工作区
│   ├── MEMORY.md  TODO.md
├── tests/
│   ├── test_tools.py  test_agent.py  test_memory.py
├── requirements.txt
├── .env
└── README.md
```

## 实施步骤

### Phase 1：项目骨架 + 配置
- 创建 Python 项目结构，`requirements.txt`
- `config.py`：读取 .env（百炼 API Key、endpoint、模型名、本地路径）
- `main.py`：FastAPI 最小可运行入口

### Phase 2：工具层
- `file_reader.py`：PDF (PyMuPDF)、DOCX (python-docx)、MD/TXT
- `image_reader.py`：MinerU（结构化 Markdown 提取，含 OCR）
- `jd_reader.py`：httpx 抓取 URL + BeautifulSoup 正文提取
- `file_writer.py`：Markdown 写入

### Phase 3：Agent 层
- Qwen 接入（langchain-openai ChatOpenAI → 百炼 endpoint）
- `agent.py`：单 Agent，绑定全部工具 + 系统提示词
- Agent 直接对话式响应，无需子 Agent 委派

### Phase 4：记忆系统
- SQLite 建表 + store.py 基础 CRUD
- `profile.py` 用户画像管理
- `memory_consolidator.py`：从对话中提取事实更新画像

### Phase 5：Web UI
- routes.py：`/` 主页面、`POST /chat` SSE流式、`POST /upload`
- Jinja2 模板：base.html、chat.html、settings.html
- SSE 流式输出实现

### Phase 6：集成测试 + 文档
- 各层单元测试
- README 使用说明

## 验证方式

1. 启动 FastAPI 服务，浏览器打开主页
2. 上传一份 PDF 简历，确认文本正确提取
3. 发送"帮我看看这份简历有什么可以优化的"→ 确认 Qwen 流式回复正常
4. 发送"帮我针对某岗位优化简历"→ 确认 Agent 调用工具 → 产出优化版简历文件
5. 检查 `workspace/MEMORY.md` 和 SQLite 中记忆是否正确更新
