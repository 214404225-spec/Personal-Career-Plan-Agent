"""FastAPI 入口."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.config import settings
from app.web.routes import router as web_router

app = FastAPI(
    title="Personal Career Plan Agent",
    description="个人职业规划助手 —— 简历管理、岗位匹配、面试准备",
    version="0.1.0",
)

# 确保目录结构
settings.ensure_dirs()

# 静态文件
static_dir = Path(__file__).parent / "web" / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Web 路由（页面 + API）
app.include_router(web_router)


@app.get("/api/health")
async def health_check():
    """健康检查接口."""
    return {
        "status": "ok",
        "model": settings.MODEL_NAME,
        "version": "0.1.0",
    }
