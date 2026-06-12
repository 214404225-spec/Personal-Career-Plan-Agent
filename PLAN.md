# Personal Career Plan Agent —— 框架搭建计划

> **创建时间**：2026-06-05
> **状态**：设计完成，待实施

## Context

用户需要一个**个人使用的职业规划 Agent**，覆盖简历管理、实习申请、秋招准备等全流程。计划调用 Qwen3.7-plus（阿里云百炼）作为 Orchestrator Agent。核心需求：

1. 能读取多种文件格式（PDF、MD、PNG、JPG 等）
2. 高度个人可定制
3. 更多功能按需扩展

参考了企业级 Agent 框架调研文档（AgentScope / DeepAgents / pi-mono / Coze / Dify），但面向个人使用场景重新选型。

**选型结论**：采用**方案 B —— LangChain + DeepAgents 启发式架构**。不引入重量级企业框架，用 LangChain 做 LLM 调用和工具编排底层，借鉴 DeepAgents 的四大核心机制（任务规划 / 文件系统工具 / 子 Agent 委托 / 记忆系统），上层自建 FastAPI Web 界面。

## 整体架构（四层）

```
┌─────────────────────────────────────────────────────────────┐
│                      Web UI Layer (FastAPI)                  │
│  • 聊天界面  • SSE 流式输出  • 简历管理面板  • 求职看板      │
├──────────────────────────────────────────────────────────────┤
│                   Agent Orchestration Layer                  │
│  • Orchestrator Agent (Qwen 3.7-plus)                       │
│    → 意图理解 + 任务拆解 (write_todos) + 子Agent调度 (task) │
│  • 3个子Agent: Resume / Job Match / Interview Prep          │
│    各自独立上下文窗口 + 受限工具集                          │
├──────────────────────────────────────────────────────────────┤
│                       Tool & Memory Layer                    │
│  • 文件解析: PyMuPDF(PDF) / python-docx(DOCX) / Pillow+Qwen VL(图片) │
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
- **子 Agent 隔离**：每个子 Agent 独立上下文窗口，只看到 Orchestrator 给的 task description + 自己系统提示词 + 工具结果
- **Local First**：所有数据本地存储，仅 Qwen API 调用依赖云服务

## Agent 编排层

### Orchestrator Agent（主控）

| 职责 | 工具 | 说明 |
|------|------|------|
| 理解意图 | 内置推理 | 判断用户想做什么：改简历？找岗位？准备面试？组合？ |
| 拆解任务 | `write_todos` | 复杂任务拆成步骤清单，写入 TODO.md 防止跑偏 |
| 调度子Agent | `task(subagent, description)` | 委派子任务，等结果后整合输出 |

Orchestrator 不亲自做具体工作，只规划和整合。

### 三个子 Agent

| 子 Agent | 工具 | 输入 | 输出 |
|----------|------|------|------|
| Resume Agent | read_resume, read_jd, write_file, list_files | 用户原始简历 + 目标 JD | 优化版简历(MD) + 修改说明 |
| Job Match Agent | read_resume, read_jd, web_search(可选) | 简历 + 目标岗位 | 匹配度评分 + 技能差距 + 提升建议 |
| Interview Prep Agent | read_resume, read_jd, write_file | 简历 + JD + 岗位类型 | 预测问题清单 + 回答要点 + 模拟脚本 |

## 工具层

| 工具 | 支持格式 | 底层库 | 权限 |
|------|----------|--------|------|
| `read_resume` | PDF, DOCX, MD, TXT | PyMuPDF, python-docx | Resume/Job Match/Interview |
| `read_image` | PNG, JPG, WEBP | Pillow + Qwen VL | 全部 |
| `read_jd` | URL, PDF, 纯文本 | httpx, BeautifulSoup, PyMuPDF | Resume/Job Match/Interview |
| `read_notes` | MD, TXT | 原生 | 全部 |
| `list_files` | — | 原生 | 全部 |
| `write_file` | MD | 原生 | Resume/Interview |
| `web_search` | — | 可选 | Job Match |

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
│   ├── agent/                     # Agent 编排层
│   │   ├── orchestrator.py        # 主 Orchestrator
│   │   ├── sub_agents/            # 三个子 Agent
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
├── .env.example
└── README.md
```

## 实施步骤

### Phase 1：项目骨架 + 配置
- 创建 Python 项目结构，`requirements.txt`
- `config.py`：读取 .env（百炼 API Key、endpoint、模型名、本地路径）
- `main.py`：FastAPI 最小可运行入口

### Phase 2：工具层
- `file_reader.py`：PDF (PyMuPDF)、DOCX (python-docx)、MD/TXT
- `image_reader.py`：Pillow 基础信息 + Qwen VL 文字提取
- `jd_reader.py`：httpx 抓取 URL + BeautifulSoup 正文提取
- `file_writer.py`：Markdown 写入

### Phase 3：Agent 层
- Qwen 接入（langchain-openai ChatOpenAI → 百炼 endpoint）
- Orchestrator Agent（系统提示词 + write_todos + task 调度）
- 三个子 Agent（各自系统提示词 + 受限工具集）

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
4. 发送"帮我针对某岗位优化简历"→ 确认 Orchestrator 拆解任务 → 子 Agent 产出优化版简历文件
5. 检查 `workspace/MEMORY.md` 和 SQLite 中记忆是否正确更新
