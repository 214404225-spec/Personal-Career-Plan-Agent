"""单 Agent —— Qwen 接入 + 工具绑定.

使用 LangChain 的 ChatOpenAI 指向阿里云百炼 endpoint（OpenAI 兼容），
绑定全部工具，对话式交互。
"""

from typing import AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool

from app.config import settings


# ---------------------------------------------------------------------------
# 工具定义（LangChain @tool 包装）
# ---------------------------------------------------------------------------

@tool
def tool_read_resume(file_path: str) -> dict:
    """读取简历文件，支持 PDF / DOCX / MD / TXT 格式.

    Args:
        file_path: 简历文件的路径
    """
    from app.tools.file_reader import read_resume
    return read_resume(file_path)


@tool
def tool_read_image(file_path: str) -> dict:
    """读取图片文件（PNG/JPG/WEBP），使用 MinerU 提取文字和结构化内容.

    Args:
        file_path: 图片文件路径
    """
    from app.tools.image_reader import read_image
    return read_image(file_path)


@tool
def tool_read_jd(source: str) -> dict:
    """读取职位描述（JD），支持 URL、PDF、纯文本.

    Args:
        source: JD 的 URL 或本地文件路径
    """
    from app.tools.jd_reader import read_jd
    return read_jd(source)


@tool
def tool_read_notes(file_path: str) -> dict:
    """读取笔记文件（MD / TXT）.

    Args:
        file_path: 笔记文件路径
    """
    from app.tools.file_reader import read_notes
    return read_notes(file_path)


@tool
def tool_list_files(directory: str) -> list[str]:
    """列出指定目录下的所有文件.

    Args:
        directory: 目录路径
    """
    from app.tools.file_reader import list_files
    return list_files(directory)


@tool
def tool_write_file(content: str, filename: str) -> dict:
    """将内容写入 Markdown 文件，保存到 data/outputs/.

    Args:
        content: 要写入的内容（Markdown 格式）
        filename: 文件名（如 optimized_resume.md）
    """
    from app.tools.file_writer import write_file
    return write_file(content, filename)


ALL_TOOLS = [
    tool_read_resume,
    tool_read_image,
    tool_read_jd,
    tool_read_notes,
    tool_list_files,
    tool_write_file,
]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class CareerAgent:
    """个人职业规划 Agent —— 单 Agent 架构."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or settings.MODEL_NAME
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            temperature=0.7,
        )
        self.llm_with_tools = self.llm.bind_tools(ALL_TOOLS)
        self._system_prompt = self._load_system_prompt()

    def _load_system_prompt(self) -> str:
        """加载系统提示词，注入用户记忆."""
        prompt_file = settings.PROJECT_ROOT / "app" / "agent" / "prompts" / "system_prompt.md"
        base = prompt_file.read_text(encoding="utf-8") if prompt_file.exists() else ""

        # 注入长期记忆
        memory_context = self._build_memory_context()
        if memory_context:
            base += f"\n\n## 用户长期记忆\n\n{memory_context}"

        return base

    def _build_memory_context(self) -> str:
        """从 MEMORY.md 和 SQLite 构建记忆上下文字符串."""
        parts = []

        # 读取 MEMORY.md
        if settings.MEMORY_FILE.exists():
            mem = settings.MEMORY_FILE.read_text(encoding="utf-8").strip()
            if mem:
                parts.append(mem)

        # 读取用户画像
        try:
            from app.memory.profile import get_profile_summary
            profile = get_profile_summary()
            if profile:
                parts.append(f"### 用户画像\n{profile}")
        except Exception:
            pass

        # 读取求职时间线
        try:
            from app.memory.job_timeline import get_timeline_summary
            timeline = get_timeline_summary()
            if timeline:
                parts.append(f"### 求职进度\n{timeline}")
        except Exception:
            pass

        return "\n\n".join(parts)

    async def chat_stream(self, user_message: str) -> AsyncIterator[str]:
        """流式对话，SSE 推送 token."""
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=user_message),
        ]

        async for chunk in self.llm_with_tools.astream(messages):
            # chunk 可能是 AIMessageChunk 或 ToolCallChunk
            content = getattr(chunk, "content", None)
            if content:
                yield content

    def chat_sync(self, user_message: str) -> str:
        """同步对话，返回完整回复."""
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content=self._system_prompt),
            HumanMessage(content=user_message),
        ]

        response = self.llm_with_tools.invoke(messages)
        return response.content

    def reload_memory(self) -> None:
        """重新加载记忆（在记忆更新后调用）."""
        self._system_prompt = self._load_system_prompt()


# 全局单例
_agent: CareerAgent | None = None


def get_agent() -> CareerAgent:
    """获取 Agent 全局单例."""
    global _agent
    if _agent is None:
        _agent = CareerAgent()
    return _agent
