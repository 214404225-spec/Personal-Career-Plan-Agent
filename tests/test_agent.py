"""Agent 层测试（不需要真实 API Key 的结构测试）."""

import pytest
from app.config import settings


class TestAgentConfig:
    """Agent 配置测试."""

    def test_settings_defaults(self):
        assert settings.MODEL_NAME is not None
        assert settings.DASHSCOPE_BASE_URL is not None

    def test_memory_paths(self):
        assert settings.MEMORY_FILE is not None
        assert settings.DB_PATH is not None
        assert settings.DATA_DIR is not None

    def test_system_prompt_exists(self):
        prompt_file = (
            settings.PROJECT_ROOT
            / "app"
            / "agent"
            / "prompts"
            / "system_prompt.md"
        )
        assert prompt_file.exists(), f"系统提示词不存在: {prompt_file}"
        content = prompt_file.read_text(encoding="utf-8")
        assert len(content) > 100, "系统提示词内容过短"


class TestToolBinding:
    """工具绑定测试."""

    def test_tools_importable(self):
        from app.agent.agent import ALL_TOOLS
        assert len(ALL_TOOLS) == 6

    def test_tool_names(self):
        from app.agent.agent import ALL_TOOLS
        names = [t.name for t in ALL_TOOLS]
        expected = [
            "tool_read_resume",
            "tool_read_image",
            "tool_read_jd",
            "tool_read_notes",
            "tool_list_files",
            "tool_write_file",
        ]
        assert names == expected
