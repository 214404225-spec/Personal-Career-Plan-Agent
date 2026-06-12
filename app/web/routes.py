"""Web 路由 —— / (聊天页)、POST /chat (SSE流式)、POST /upload (文件上传)."""

import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.agent.agent import get_agent
from app.web.sse import sse_stream
from app.memory.memory_consolidator import update_from_message, consolidate_memory_md

router = APIRouter()

# Jinja2 模板路径
_templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


# ---------------------------------------------------------------------------
# 页面路由
# ---------------------------------------------------------------------------

@router.get("/", response_class=HTMLResponse)
async def chat_page(request: Request):
    """主聊天页面."""
    return templates.TemplateResponse(request, "chat.html")


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """设置页面."""
    from app.memory.profile import get_all_profiles
    profiles = get_all_profiles()
    return templates.TemplateResponse(
        request,
        "settings.html",
        context={"profiles": profiles, "model": settings.MODEL_NAME},
    )


# ---------------------------------------------------------------------------
# API 路由
# ---------------------------------------------------------------------------

@router.post("/chat")
async def chat(request: Request):
    """SSE 流式对话接口.

    前端通过 EventSource POST + 读取 response body（或 fetch + ReadableStream）.
    """
    data = await request.json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return JSONResponse({"error": "消息不能为空"}, status_code=400)

    agent = get_agent()

    # 后台更新记忆
    try:
        update_from_message(user_message)
    except Exception:
        pass

    stream = agent.chat_stream(user_message)
    return await sse_stream(stream)


@router.post("/upload")
async def upload_file(file: UploadFile = File(...), file_type: str = Form("resume")):
    """文件上传接口.

    Args:
        file: 上传的文件
        file_type: resume / jd / notes — 决定存放子目录
    """
    # 安全检查：扩展名白名单
    allowed_ext = {".pdf", ".docx", ".doc", ".md", ".txt", ".markdown", ".png", ".jpg", ".jpeg", ".webp"}
    ext = Path(file.filename or "").suffix.lower()
    if ext not in allowed_ext:
        return JSONResponse({"error": f"不支持的文件格式: {ext}"}, status_code=400)

    # 目标目录
    subdir = {"resume": "resumes", "jd": "jds", "notes": "notes"}.get(file_type, "resumes")
    dest_dir = settings.DATA_DIR / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)

    # 生成唯一文件名避免覆盖
    safe_name = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    dest_path = dest_dir / safe_name

    try:
        with open(dest_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"error": f"保存失败: {e}"}, status_code=500)

    return JSONResponse({
        "filename": file.filename,
        "saved_as": safe_name,
        "path": str(dest_path.relative_to(settings.PROJECT_ROOT)),
        "type": file_type,
        "size": dest_path.stat().st_size,
    })


@router.post("/api/profile")
async def save_profile(request: Request):
    """保存用户画像."""
    from app.memory.profile import set_profile, get_all_profiles

    data = await request.json()
    for key, value in data.items():
        if value:
            set_profile(key, str(value))

    consolidate_memory_md()
    return JSONResponse({"status": "ok", "profiles": get_all_profiles()})


@router.post("/api/applications")
async def add_application(request: Request):
    """添加求职记录."""
    from app.memory.job_timeline import add_application, get_applications

    data = await request.json()
    app_id = add_application(
        company=data.get("company", ""),
        position=data.get("position", ""),
        jd_source=data.get("jd_source", ""),
        status=data.get("status", "wishlist"),
        notes=data.get("notes", ""),
    )
    consolidate_memory_md()
    return JSONResponse({"status": "ok", "id": app_id})


@router.get("/api/applications")
async def list_applications(status: str | None = None):
    """获取求职记录列表."""
    from app.memory.job_timeline import get_applications
    apps = get_applications(status)
    return JSONResponse({"applications": apps})


@router.get("/api/files")
async def list_files(directory: str = "resumes"):
    """列出用户文件."""
    from app.tools.file_reader import list_files as lf
    subdir = {"resumes": "resumes", "jds": "jds", "notes": "notes", "outputs": "outputs"}.get(directory, "resumes")
    target = settings.DATA_DIR / subdir
    files = lf(str(target)) if target.exists() else []
    return JSONResponse({"directory": directory, "files": files})
