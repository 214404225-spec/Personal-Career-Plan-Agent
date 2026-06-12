"""文件读取工具 —— 支持 PDF、DOCX、MD、TXT 格式."""

from pathlib import Path
from typing import Optional


def read_pdf(file_path: str) -> str:
    """使用 PyMuPDF 读取 PDF 文本."""
    import fitz  # PyMuPDF

    doc = fitz.open(file_path)
    texts = []
    for page in doc:
        texts.append(page.get_text())
    doc.close()
    return "\n\n".join(texts)


def read_docx(file_path: str) -> str:
    """使用 python-docx 读取 Word 文档."""
    from docx import Document

    doc = Document(file_path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def read_markdown(file_path: str) -> str:
    """读取 Markdown / 纯文本文件."""
    return Path(file_path).read_text(encoding="utf-8")


def read_resume(file_path: str) -> dict:
    """读取简历文件，自动识别格式.

    Returns:
        {"filename": str, "format": str, "content": str, "error": Optional[str]}
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "filename": path.name,
            "format": "",
            "content": "",
            "error": f"文件不存在: {file_path}",
        }

    ext = path.suffix.lower()
    content = ""
    error = None

    try:
        if ext == ".pdf":
            content = read_pdf(file_path)
            fmt = "pdf"
        elif ext in (".docx", ".doc"):
            content = read_docx(file_path)
            fmt = "docx"
        elif ext in (".md", ".txt", ".markdown"):
            content = read_markdown(file_path)
            fmt = "markdown"
        else:
            error = f"不支持的简历格式: {ext}"
            fmt = ext
    except Exception as e:
        error = f"读取失败: {e}"
        fmt = ext

    return {
        "filename": path.name,
        "format": fmt,
        "content": content.strip(),
        "error": error,
    }


def read_notes(file_path: str) -> dict:
    """读取笔记文件 (MD/TXT)."""
    path = Path(file_path)
    if not path.exists():
        return {"filename": path.name, "content": "", "error": f"文件不存在: {file_path}"}

    try:
        content = read_markdown(file_path)
        return {"filename": path.name, "content": content.strip(), "error": None}
    except Exception as e:
        return {"filename": path.name, "content": "", "error": f"读取失败: {e}"}


def list_files(directory: str, pattern: str = "*") -> list[str]:
    """列出目录下的文件."""
    p = Path(directory)
    if not p.exists():
        return []
    return sorted(
        [str(f.relative_to(p)) for f in p.rglob(pattern) if f.is_file()]
    )
