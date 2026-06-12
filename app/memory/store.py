"""SQLite 数据库操作 —— 建表与基础 CRUD."""

import sqlite3
from pathlib import Path
from typing import Optional

from app.config import settings


def get_db(db_path: str | None = None) -> sqlite3.Connection:
    """获取数据库连接，自动建表."""
    path = db_path or str(settings.DB_PATH)
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """确保必要表存在."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS resume_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            format TEXT,
            summary TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            jd_source TEXT,
            status TEXT DEFAULT 'wishlist',
            applied_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            updated_at TEXT DEFAULT (datetime('now', 'localtime'))
        );

        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now', 'localtime'))
        );
    """)
    conn.commit()


# ---------------------------------------------------------------------------
# 通用 CRUD
# ---------------------------------------------------------------------------

def insert(table: str, data: dict) -> int:
    """插入一行，返回 id."""
    columns = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    db = get_db()
    cur = db.execute(
        f"INSERT INTO {table} ({columns}) VALUES ({placeholders})",
        list(data.values()),
    )
    db.commit()
    db.close()
    return cur.lastrowid


def update(table: str, row_id: int, data: dict) -> None:
    """按 id 更新一行."""
    sets = ", ".join(f"{k} = ?" for k in data)
    db = get_db()
    db.execute(
        f"UPDATE {table} SET {sets}, updated_at = datetime('now', 'localtime') WHERE id = ?",
        list(data.values()) + [row_id],
    )
    db.commit()
    db.close()


def delete(table: str, row_id: int) -> None:
    """按 id 删除一行."""
    db = get_db()
    db.execute(f"DELETE FROM {table} WHERE id = ?", (row_id,))
    db.commit()
    db.close()


def query_all(table: str, where: str = "", params: tuple = ()) -> list[dict]:
    """查询所有匹配行."""
    db = get_db()
    sql = f"SELECT * FROM {table}"
    if where:
        sql += f" WHERE {where}"
    rows = db.execute(sql, params).fetchall()
    db.close()
    return [dict(r) for r in rows]


def query_one(table: str, where: str = "", params: tuple = ()) -> Optional[dict]:
    """查询单行."""
    rows = query_all(table, where, params)
    return rows[0] if rows else None
