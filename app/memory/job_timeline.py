"""求职时间线 —— 投递记录跟踪."""

from typing import Optional
from datetime import datetime

from app.memory.store import get_db, insert, update, query_all, query_one


STATUS_LABELS = {
    "wishlist": "想投",
    "applied": "已投递",
    "interview": "面试中",
    "offer": "已 Offer",
    "rejected": "已拒",
    "accepted": "已接受",
}


def add_application(
    company: str,
    position: str,
    jd_source: str = "",
    status: str = "wishlist",
    notes: str = "",
) -> int:
    """添加一条求职记录."""
    return insert("job_applications", {
        "company": company,
        "position": position,
        "jd_source": jd_source,
        "status": status,
        "notes": notes,
    })


def update_status(app_id: int, status: str, notes: str = "") -> None:
    """更新求职状态."""
    data = {"status": status}
    if notes:
        data["notes"] = notes
    if status == "applied":
        data["applied_date"] = datetime.now().strftime("%Y-%m-%d")
    update("job_applications", app_id, data)


def get_applications(status: str | None = None) -> list[dict]:
    """获取求职记录列表，可按状态筛选."""
    if status:
        return query_all("job_applications", "status = ? ORDER BY updated_at DESC", (status,))
    return query_all("job_applications", "1=1 ORDER BY updated_at DESC")


def get_application(app_id: int) -> Optional[dict]:
    """获取单条求职记录."""
    return query_one("job_applications", "id = ?", (app_id,))


def delete_application(app_id: int) -> None:
    """删除求职记录."""
    from app.memory.store import delete
    delete("job_applications", app_id)


def get_timeline_summary() -> str:
    """生成求职时间线摘要（注入系统提示词用）."""
    apps = get_applications()
    if not apps:
        return ""

    # 按状态分组统计
    counts = {}
    for app in apps:
        s = app["status"]
        counts[s] = counts.get(s, 0) + 1

    summary_parts = [f"共 {len(apps)} 条求职记录"]
    for status_code, label in STATUS_LABELS.items():
        if counts.get(status_code):
            summary_parts.append(f"- {label}: {counts[status_code]}")

    # 最近 5 条
    recent = apps[:5]
    if recent:
        summary_parts.append("\n最近记录:")
        for r in recent:
            summary_parts.append(
                f"- [{STATUS_LABELS.get(r['status'], r['status'])}] "
                f"{r['company']} — {r['position']}"
            )

    return "\n".join(summary_parts)
