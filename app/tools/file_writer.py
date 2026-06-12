"""文件写入工具 —— Markdown 文件输出."""

from pathlib import Path
from datetime import datetime


def write_file(
    content: str,
    filename: str,
    directory: str | None = None,
    overwrite: bool = False,
) -> dict:
    """写入 Markdown 文件.

    Args:
        content: 文件内容
        filename: 文件名（不含路径）
        directory: 目标目录，默认为 data/outputs/
        overwrite: 是否覆盖已有文件（默认在文件名后加时间戳）

    Returns:
        {"filepath": str, "filename": str, "written": bool, "error": str|None}
    """
    if directory is None:
        from app.config import settings
        directory = str(settings.DATA_DIR / "outputs")

    out_dir = Path(directory)
    out_dir.mkdir(parents=True, exist_ok=True)

    target = out_dir / filename

    if target.exists() and not overwrite:
        # 添加时间戳避免覆盖
        stem = target.stem
        suffix = target.suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = out_dir / f"{stem}_{timestamp}{suffix}"

    try:
        target.write_text(content, encoding="utf-8")
        return {
            "filepath": str(target),
            "filename": target.name,
            "written": True,
            "error": None,
        }
    except Exception as e:
        return {
            "filepath": str(target),
            "filename": target.name,
            "written": False,
            "error": f"写入失败: {e}",
        }


def append_file(content: str, filepath: str) -> dict:
    """追加内容到已有文件末尾.

    Returns:
        {"filepath": str, "appended": bool, "error": str|None}
    """
    path = Path(filepath)
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n\n" + content)
        return {"filepath": str(path), "appended": True, "error": None}
    except Exception as e:
        return {"filepath": str(path), "appended": False, "error": f"追加失败: {e}"}
