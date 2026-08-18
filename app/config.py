"""
@file config.py
@description 应用配置：开发环境使用 SQLite，可通过 DATABASE_URL 切换 PostgreSQL
@module app.config
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.1.0
"""

import os
from datetime import timedelta

from dotenv import load_dotenv


# 项目根目录（backend/）
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 加载 backend/.env
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Settings:
    """
    Settings - 运行时配置

    @description 统一读取环境变量，供 FastAPI 与数据库使用
    """

    SECRET_KEY = os.getenv("SECRET_KEY", "fishing-ranking-dev-secret-key-32b!")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fishing-ranking-jwt-secret-key-32b!")
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'fishing_ranking.db')}",
    )

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    # 图片上限 10MB
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}
    # 视频上限 50MB，支持常见手机格式
    MAX_VIDEO_CONTENT_LENGTH = 50 * 1024 * 1024
    ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov"}
    MAX_UPLOAD_COUNT = 3

    # APP_ENV：development / production
    ENV = os.getenv("APP_ENV", "development")
    DEBUG = ENV != "production"


settings = Settings()
