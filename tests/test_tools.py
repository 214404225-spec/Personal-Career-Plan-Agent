"""工具层单元测试."""

import pytest
from pathlib import Path
from app.tools.file_reader import read_resume, read_notes, list_files
from app.tools.jd_reader import extract_text_from_html
from app.tools.file_writer import write_file, append_file


class TestFileReader:
    """文件读取测试."""

    def test_read_resume_file_not_found(self):
        result = read_resume("/nonexistent/file.pdf")
        assert result["error"] is not None
        assert "不存在" in result["error"]

    def test_read_resume_markdown(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("# Hello\nWorld", encoding="utf-8")
        result = read_resume(str(p))
        assert result["error"] is None
        assert result["format"] == "markdown"
        assert "Hello" in result["content"]

    def test_read_notes(self, tmp_path):
        p = tmp_path / "notes.md"
        p.write_text("Meeting notes", encoding="utf-8")
        result = read_notes(str(p))
        assert result["error"] is None
        assert "Meeting notes" in result["content"]

    def test_list_files(self, tmp_path):
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        files = list_files(str(tmp_path))
        assert len(files) == 2


class TestJDReader:
    """JD 解析测试."""

    def test_extract_text_from_html(self):
        html = """
        <html><head><script>alert(1)</script></head>
        <body><h1>Software Engineer</h1><p>We are hiring!</p></body>
        </html>
        """
        text = extract_text_from_html(html)
        assert "Software Engineer" in text
        assert "We are hiring" in text
        assert "alert" not in text


class TestFileWriter:
    """文件写入测试."""

    def test_write_file(self, tmp_path):
        result = write_file("Hello, world!", "test.md", str(tmp_path))
        assert result["written"] is True
        assert Path(result["filepath"]).exists()
        assert Path(result["filepath"]).read_text() == "Hello, world!"

    def test_write_file_no_overwrite(self, tmp_path):
        p = tmp_path / "test.md"
        p.write_text("original")
        result = write_file("new content", "test.md", str(tmp_path), overwrite=False)
        assert result["written"] is True
        assert result["filename"] != "test.md"  # 应带时间戳
        assert p.read_text() == "original"  # 原文件未覆盖

    def test_append_file(self, tmp_path):
        p = tmp_path / "log.md"
        p.write_text("line1")
        result = append_file("line2", str(p))
        assert result["appended"] is True
        assert "line2" in p.read_text()
