"""数据模型 —— 对话、简历、岗位."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """单条对话消息."""

    role: str  # "user" | "assistant"
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResumeVersion:
    """简历版本记录."""

    id: Optional[int] = None
    filename: str = ""
    filepath: str = ""
    format: str = ""  # pdf / docx / md
    summary: str = ""  # 简历摘要（Agent 生成）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class JobApplication:
    """求职记录."""

    id: Optional[int] = None
    company: str = ""
    position: str = ""
    jd_source: str = ""  # URL 或文件路径
    status: str = "wishlist"  # wishlist / applied / interview / offer / rejected
    applied_date: Optional[str] = None
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
