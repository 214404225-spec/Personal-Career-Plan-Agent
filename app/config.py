"""配置管理 —— 读取 .env 和提供全局设置."""

import os
from pathlib import Path
from dotenv import load_dotenv

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 加载 .env
load_dotenv(PROJECT_ROOT / ".env")


class Settings:
    """全局配置单例."""

    # 项目根目录
    PROJECT_ROOT: Path = PROJECT_ROOT

    # 阿里云百炼
    DASHSCOPE_API_KEY: str = os.getenv("API_KEY", "")
    DASHSCOPE_BASE_URL: str = os.getenv(
        "BASE_URL",
        "https://token-plan.cn-beijing.maas.aliyuncs.com/compatible-mode/v1",
    )
    MODEL_NAME: str = os.getenv("MODEL_NAME", "qwen3.7-plus")

    # 目录
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
    WORKSPACE_DIR: Path = Path(
        os.getenv("WORKSPACE_DIR", str(PROJECT_ROOT / "workspace"))
    )

    # 记忆
    MEMORY_FILE: Path = WORKSPACE_DIR / "MEMORY.md"
    TODO_FILE: Path = WORKSPACE_DIR / "TODO.md"
    DB_PATH: Path = DATA_DIR / "career_agent.db"

    # 对话
    MAX_CONVERSATION_TURNS: int = 20

    @classmethod
    def ensure_dirs(cls) -> None:
        """确保所有必要目录存在."""
        for d in [
            cls.DATA_DIR,
            cls.DATA_DIR / "resumes",
            cls.DATA_DIR / "jds",
            cls.DATA_DIR / "notes",
            cls.DATA_DIR / "outputs",
            cls.WORKSPACE_DIR,
        ]:
            d.mkdir(parents=True, exist_ok=True)

        # 确保 MEMORY.md 和 TODO.md 存在
        cls.MEMORY_FILE.touch(exist_ok=True)
        cls.TODO_FILE.touch(exist_ok=True)


settings = Settings()
