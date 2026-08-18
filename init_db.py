"""
@file init_db.py
@description 初始化数据库：创建全部表，并写入默认管理员账号
@module init_db
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from app.database import SessionLocal
from app.models import Admin
from app.utils.schema import ensure_schema
from app.utils.security import hash_password


# 默认管理员账号（仅开发环境使用）
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"


def init_database():
    """
    init_database - 初始化数据库表结构与默认管理员
    """
    ensure_schema()
    print(
        "数据库表就绪：users / catches / admins / audit_logs / notifications / system_settings / reward_awards"
    )

    database = SessionLocal()
    try:
        existing_admin = (
            database.query(Admin).filter_by(username=DEFAULT_ADMIN_USERNAME).first()
        )
        # 判断默认管理员是否已存在
        if existing_admin is None:
            admin = Admin(
                username=DEFAULT_ADMIN_USERNAME,
                password=hash_password(DEFAULT_ADMIN_PASSWORD),
            )
            database.add(admin)
            database.commit()
            print(
                f"已创建默认管理员：用户名={DEFAULT_ADMIN_USERNAME}，密码={DEFAULT_ADMIN_PASSWORD}"
            )
        else:
            print(f"默认管理员已存在：用户名={DEFAULT_ADMIN_USERNAME}")
        print("数据库初始化完成。")
    finally:
        database.close()


if __name__ == "__main__":
    init_database()
