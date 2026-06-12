"""JD（职位描述）解析工具 —— 支持 URL 抓取和 PDF/纯文本解析."""

import re
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from app.tools.file_reader import read_pdf, read_markdown


def fetch_url(url: str, timeout: int = 15) -> str:
    """抓取网页 HTML 内容."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }
    response = httpx.get(url, headers=headers, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    return response.text


def extract_text_from_html(html: str) -> str:
    """从 HTML 中提取正文文本."""
    soup = BeautifulSoup(html, "lxml" if _has_lxml() else "html.parser")

    # 移除 script / style / nav / footer
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # 压缩多余空行
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _has_lxml() -> bool:
    try:
        import lxml  # noqa: F401
        return True
    except ImportError:
        return False


def read_jd(source: str) -> dict:
    """读取 JD，自动识别来源类型.

    Args:
        source: URL（https://...）、PDF 路径、或纯文本/MD 路径

    Returns:
        {"source": str, "type": str, "content": str, "error": Optional[str]}
    """
    # URL
    if source.startswith(("http://", "https://")):
        try:
            html = fetch_url(source)
            text = extract_text_from_html(html)
            return {"source": source, "type": "url", "content": text, "error": None}
        except Exception as e:
            return {"source": source, "type": "url", "content": "", "error": f"抓取失败: {e}"}

    # 本地文件
    path = Path(source)
    if not path.exists():
        return {"source": source, "type": "unknown", "content": "", "error": f"文件不存在: {source}"}

    ext = path.suffix.lower()
    try:
        if ext == ".pdf":
            content = read_pdf(source)
            return {"source": source, "type": "pdf", "content": content, "error": None}
        elif ext in (".md", ".txt", ".markdown"):
            content = read_markdown(source)
            return {"source": source, "type": "text", "content": content, "error": None}
        else:
            # 尝试当纯文本读取
            content = read_markdown(source)
            return {"source": source, "type": "text", "content": content, "error": None}
    except Exception as e:
        return {"source": source, "type": ext, "content": "", "error": f"读取失败: {e}"}
