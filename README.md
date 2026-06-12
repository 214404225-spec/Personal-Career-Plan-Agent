# Personal Career Plan Agent

个人职业规划助手 —— 基于 Qwen 3.7-plus，覆盖简历管理、岗位匹配、面试准备全流程。

## 架构

```
Web UI (FastAPI + Jinja2 + SSE)
    ↓
Agent Layer (单 Agent, Qwen 3.7-plus + 全部工具)
    ↓
Tool & Memory Layer (文件解析 / JD抓取 / SQLite + MEMORY.md)
    ↓
Data & Storage (本地文件系统 + SQLite)
```

## 快速开始

### 1. 安装依赖

```bash
cd D:\Files\Cityudg\Job\Personal-Career-Plan-Agent #此处为绝对，请自行修改为实际路径
pip install -r requirements.txt
```

### 2. 配置 API Key

在 `.env` 中填入 API Key 即可


### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 打开浏览器

访问 http://localhost:8000

## 功能

| 功能 | 说明 |
|------|------|
| 📝 简历优化 | 上传简历，AI 分析亮点和不足，给出优化建议 |
| 🔍 岗位匹配 | 读 JD（URL 或文件），对比简历给出匹配度 |
| 🎤 面试准备 | 根据岗位生成预测问题和回答要点 |
| 📊 求职看板 | 跟踪投递、面试、offer 进度 |
| 🧠 长期记忆 | 自动记录用户画像和求职时间线 |

## 项目结构

```
app/
├── main.py          # FastAPI 入口
├── config.py        # 配置管理
├── web/             # Web UI（routes, SSE, templates, static）
├── agent/           # Agent 层（单 Agent + 系统提示词）
├── tools/           # 工具层（文件读取、JD解析、图片解析）
├── memory/          # 记忆系统（SQLite + MEMORY.md）
└── models/          # 数据模型

data/                # 用户数据（resumes/ jds/ notes/ outputs/）
workspace/           # Agent 运行时（MEMORY.md, TODO.md）
tests/               # 测试
```

## 运行测试

```bash
pytest tests/ -v
```

## 技术栈

- **LLM**: Qwen 3.7-plus (阿里云百炼)
- **框架**: FastAPI + LangChain
- **文件解析**: PyMuPDF (PDF), python-docx (DOCX), MinerU (图片)
- **记忆**: SQLite + MEMORY.md
- **前端**: Jinja2 + HTMX + SSE 流式
