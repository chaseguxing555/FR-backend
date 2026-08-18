"""
@file schema.py
@description 轻量 schema 补齐：建表 / 补列 / seed 配置
@module app.utils.schema
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from sqlalchemy import inspect, text

from app.database import Base, SessionLocal, engine


def ensure_schema():
    """
    ensure_schema - 确保新增表与列存在

    @description create_all 创建缺失表；对已有 users 表补 avatar 列；seed 系统配置
    """
    # 注册全部模型 metadata
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    # 判断 users 表是否存在
    if "users" in table_names:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        # 判断是否已有 avatar 列
        if "avatar" not in user_columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR(255)"))

    # 判断 catches 表是否已有 fishing_method 列
    if "catches" in table_names:
        catch_columns = {column["name"] for column in inspector.get_columns("catches")}
        # 判断补钓法列（旧数据默认手竿）
        if "fishing_method" not in catch_columns:
            with engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE catches ADD COLUMN fishing_method "
                        "VARCHAR(20) NOT NULL DEFAULT '手竿'"
                    )
                )
        # 判断补视频列
        if "video_url" not in catch_columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE catches ADD COLUMN video_url VARCHAR(255)")
                )
        # 判断补饵料列
        if "bait" not in catch_columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE catches ADD COLUMN bait VARCHAR(50)")
                )

    database = SessionLocal()
    try:
        from app.models.system_setting import seed_default_settings

        seed_default_settings(database)
    finally:
        database.close()

    # 荣誉数据轻量回填：首个纪录 + 称号
    _backfill_honor_data()


def _backfill_honor_data():
    """
    _backfill_honor_data - 为已有通过记录补首个纪录与称号
    """
    from app.constants import CATCH_STATUS_APPROVED
    from app.models.catch import Catch
    from app.models.user import User
    from app.models.user_title import FirstSpeciesRecord
    from app.services.title_service import (
        ensure_first_species_record,
        evaluate_user_titles,
        sync_all_record_titles,
    )

    database = SessionLocal()
    try:
        first_count = database.query(FirstSpeciesRecord).count()
        # 判断尚未有首个纪录则回填
        if first_count == 0:
            approved_list = (
                database.query(Catch)
                .filter_by(status=CATCH_STATUS_APPROVED)
                .order_by(Catch.created_at.asc())
                .all()
            )
            for catch in approved_list:
                ensure_first_species_record(database, catch)

        user_ids = [row[0] for row in database.query(User.id).all()]
        for user_id in user_ids:
            evaluate_user_titles(database, user_id)
        sync_all_record_titles(database)
        database.commit()
    except Exception:
        database.rollback()
    finally:
        database.close()