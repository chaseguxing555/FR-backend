"""
@file __init__.py
@description FastAPI 应用工厂（含奖励结算定时任务）
@module app
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-14
@version 3.1.0
"""

import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, settings
from app.utils.logging_setup import setup_file_logging
from app.utils.response import AppError
from app.utils.schema import ensure_schema


# 进程启动时间
APP_STARTED_AT = datetime.utcnow()


@asynccontextmanager
async def app_lifespan(application: FastAPI):
    """
    app_lifespan - 应用生命周期：启动/停止奖励结算定时任务
    """
    from app.scheduler import start_scheduler, stop_scheduler

    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


def create_app() -> FastAPI:
    """
    create_app - 创建 FastAPI 应用

    @returns {FastAPI} 应用实例
    """
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)

    app_logger = setup_file_logging()

    application = FastAPI(
        title="野钓记录榜 API",
        version="3.1.0",
        docs_url="/api/docs",
        redoc_url="/redoc",
        lifespan=app_lifespan,
    )
    application.state.started_at = APP_STARTED_AT
    application.state.logger = app_logger

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(AppError)
    async def app_error_handler(_request: Request, exc: AppError):
        """
        app_error_handler - 业务错误统一响应
        """
        return JSONResponse(
            status_code=exc.http_status,
            content={"code": exc.code, "message": exc.message, "data": None},
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_request: Request, exc: RequestValidationError):
        """
        validation_error_handler - Pydantic 校验错误转统一响应
        """
        error_message = "请求参数不正确"
        error_list = exc.errors()
        # 判断是否有校验错误
        if error_list:
            first_error = error_list[0]
            raw_message = first_error.get("msg") or error_message
            # Pydantic v2 自定义 ValueError 前缀为 Value error, 
            if isinstance(raw_message, str) and raw_message.startswith("Value error, "):
                error_message = raw_message[len("Value error, ") :]
            else:
                error_message = str(raw_message)
        return JSONResponse(
            status_code=400,
            content={"code": 1, "message": error_message, "data": None},
        )

    # 建表 / 补列 / seed
    ensure_schema()

    # 注册路由
    from app.api.admin import router as admin_router
    from app.api.auth import router as auth_router
    from app.api.catches import router as catches_router
    from app.api.home import router as home_router
    from app.api.meta import router as meta_router
    from app.api.notifications import router as notifications_router
    from app.api.rankings import router as rankings_router
    from app.api.rewards import router as rewards_router
    from app.api.upload import router as upload_router
    from app.api.users import router as users_router

    application.include_router(auth_router)
    application.include_router(upload_router)
    application.include_router(catches_router)
    application.include_router(rankings_router)
    application.include_router(home_router)
    application.include_router(users_router)
    application.include_router(admin_router)
    application.include_router(meta_router)
    application.include_router(notifications_router)
    application.include_router(rewards_router)

    from app.api.hall import router as hall_router
    from app.api.titles import router as titles_router

    application.include_router(hall_router)
    application.include_router(titles_router)

    @application.get("/")
    def index():
        """
        index - 根路径说明
        """
        return {
            "code": 0,
            "message": "野钓记录榜后端服务运行中（FastAPI）",
            "data": {
                "frontend": "http://127.0.0.1:5173",
                "admin": "http://127.0.0.1:5174",
                "docs": "http://127.0.0.1:5000/docs",
                "health": "http://127.0.0.1:5000/api/health",
            },
        }

    @application.get("/api/health")
    def health_check():
        """
        health_check - 健康检查
        """
        return {"code": 0, "message": "ok", "data": {"status": "running"}}

    # 上传静态目录
    application.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOAD_FOLDER),
        name="uploads",
    )

    return application


# uvicorn 入口：app.main:app 或 app:app
app = create_app()
