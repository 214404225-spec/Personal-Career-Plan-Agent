"""图片读取工具 —— 使用 MinerU 进行结构化 Markdown 提取（含 OCR）.

MinerU 通过命令行调用，输出结构化 Markdown。
参见: https://github.com/opendatalab/MinerU
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional


def read_image_mineru(file_path: str) -> dict:
    """使用 MinerU 解析图片，提取文字和结构化内容.

    Args:
        file_path: 图片路径（支持 PNG, JPG, WEBP 等常见格式）

    Returns:
        {"filename": str, "content": str, "error": Optional[str]}
    """
    path = Path(file_path)
    if not path.exists():
        return {"filename": path.name, "content": "", "error": f"文件不存在: {file_path}"}

    # 检查 MinerU 是否可用
    try:
        result = subprocess.run(
            ["mineru", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            return {
                "filename": path.name,
                "content": "",
                "error": "MinerU 未正确安装，请运行: pip install mineru",
            }
    except FileNotFoundError:
        return {
            "filename": path.name,
            "content": "",
            "error": "MinerU 未安装，请运行: pip install mineru",
        }
    except Exception as e:
        return {
            "filename": path.name,
            "content": "",
            "error": f"MinerU 检查失败: {e}",
        }

    # 使用临时目录存放 MinerU 输出
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                [
                    "mineru",
                    "-p", str(path),
                    "-o", tmpdir,
                ],
                capture_output=True,
                text=True,
                timeout=120,
                check=True,
            )

            # MinerU 输出目录下找 .md 文件
            output_dir = Path(tmpdir)
            md_files = list(output_dir.rglob("*.md"))
            if md_files:
                content = md_files[0].read_text(encoding="utf-8")
                return {"filename": path.name, "content": content.strip(), "error": None}
            else:
                return {
                    "filename": path.name,
                    "content": "",
                    "error": "MinerU 未产生输出文件",
                }

        except subprocess.TimeoutExpired:
            return {
                "filename": path.name,
                "content": "",
                "error": "MinerU 解析超时（120s）",
            }
        except subprocess.CalledProcessError as e:
            return {
                "filename": path.name,
                "content": "",
                "error": f"MinerU 解析失败: {e.stderr}",
            }
        except Exception as e:
            return {"filename": path.name, "content": "", "error": f"解析异常: {e}"}


def read_image(file_path: str) -> dict:
    """读取图片的便捷入口，自动路由到 MinerU.

    也接受非图片文件（PDF 等），MinerU 均支持。
    """
    return read_image_mineru(file_path)
