"""长期记忆合并器 —— 从对话中提取事实，更新 MEMORY.md 和 SQLite."""

from datetime import datetime
from app.config import settings
from app.memory.profile import set_profile, get_all_profiles
from app.memory.job_timeline import get_timeline_summary


def consolidate_memory_md() -> None:
    """将 SQLite 中的结构化记忆同步到 MEMORY.md（Markdown 格式，可手动编辑）.

    MEMORY.md 采用 Claude Code 兼容格式，每行一条记忆文件指针。
    """
    profiles = get_all_profiles()
    timeline = get_timeline_summary()

    lines = [
        "# Personal Career Agent — 长期记忆",
        f"\n> 最后合并时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "\n## 用户画像\n",
    ]

    if profiles:
        for key, value in profiles.items():
            lines.append(f"- **{key}**: {value}")
    else:
        lines.append("（尚无用户画像信息）")

    lines.append("\n## 求职时间线\n")
    if timeline:
        lines.append(timeline)
    else:
        lines.append("（尚无求职记录）")

    settings.MEMORY_FILE.write_text("\n".join(lines), encoding="utf-8")


def extract_facts_from_message(message: str) -> list[tuple[str, str]]:
    """从单条用户消息中提取事实（简单的关键词匹配，后续可升级为 LLM 提取）.

    Returns:
        [(key, value), ...] 可写入 user_profile 的事实列表
    """
    facts = []

    # 简单的关键词 → key 映射
    patterns = [
        ("目标城市", ["目标城市", "想去", "城市是", "在.*工作"]),
        ("skills", ["技能", "掌握", "熟练", "精通", "会"]),
        ("target_industry", ["行业", "目标行业", "想做"]),
        ("education", ["学历", "本科", "硕士", "博士", "研究生"]),
        ("school", ["学校", "毕业于", "大学", "学院"]),
        ("salary_expectation", ["薪资", "工资", "月薪", "年薪"]),
    ]

    # 简单的模式匹配（TODO: 后续升级为 LLM 实体提取）
    for key, keywords in patterns:
        for kw in keywords:
            if kw in message:
                # 提取冒号后或逗号分隔的值（简化版）
                facts.append((key, message))
                break

    return facts


def update_from_message(message: str) -> list[str]:
    """从用户消息中更新记忆.

    Returns:
        更新日志列表
    """
    log = []
    facts = extract_facts_from_message(message)

    for key, value in facts:
        set_profile(key, value)
        log.append(f"updated {key}")

    # 同步 MEMORY.md
    if log:
        consolidate_memory_md()

    return log
