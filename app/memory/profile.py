"""用户画像管理 —— 持久化用户教育背景、技能栈、目标等."""

from typing import Optional
from app.memory.store import get_db, insert, update, query_all


# 预定义 key 列表
PROFILE_KEYS = {
    "name": "姓名",
    "education": "教育背景",
    "school": "学校",
    "major": "专业",
    "graduation_year": "毕业年份",
    "skills": "技能栈（逗号分隔）",
    "target_industry": "目标行业",
    "target_city": "目标城市",
    "salary_expectation": "期望薪资",
    "company_preference": "公司偏好",
    "self_summary": "自我描述",
}


def set_profile(key: str, value: str, category: str = "general") -> None:
    """设置或更新用户画像字段."""
    db = get_db()
    existing = db.execute(
        "SELECT id FROM user_profile WHERE key = ?", (key,)
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE user_profile SET value = ?, category = ?, updated_at = datetime('now', 'localtime') WHERE key = ?",
            (value, category, key),
        )
    else:
        db.execute(
            "INSERT INTO user_profile (key, value, category) VALUES (?, ?, ?)",
            (key, value, category),
        )
    db.commit()
    db.close()


def get_profile(key: str) -> Optional[str]:
    """获取单个画像字段."""
    from app.memory.store import query_one
    row = query_one("user_profile", "key = ?", (key,))
    return row["value"] if row else None


def get_all_profiles() -> dict[str, str]:
    """获取全部画像字段."""
    rows = query_all("user_profile")
    return {r["key"]: r["value"] for r in rows}


def get_profile_summary() -> str:
    """生成用户画像摘要（注入系统提示词用）."""
    all_profiles = get_all_profiles()
    if not all_profiles:
        return ""

    lines = []
    for key, label in PROFILE_KEYS.items():
        if key in all_profiles:
            lines.append(f"- **{label}**: {all_profiles[key]}")

    # 自定义 key
    for key, value in all_profiles.items():
        if key not in PROFILE_KEYS:
            lines.append(f"- **{key}**: {value}")

    return "\n".join(lines) if lines else ""


def delete_profile(key: str) -> None:
    """删除一个画像字段."""
    from app.memory.store import delete
    db = get_db()
    db.execute("DELETE FROM user_profile WHERE key = ?", (key,))
    db.commit()
    db.close()
