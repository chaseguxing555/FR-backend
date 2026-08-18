"""
@file database.py
@description SQLAlchemy 引擎、会话与声明基类（FastAPI）
@module app.database
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.0.0
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """
    ORM 声明基类
    """


# SQLite 需关闭同线程检查；PostgreSQL 不受影响
_connect_args = {}
# 判断是否 SQLite
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    get_db - FastAPI 依赖：请求级数据库会话

    @yields {Session} SQLAlchemy Session
    """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
