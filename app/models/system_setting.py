"""
@file system_setting.py
@description 系统配置表模型（system_settings）
@module app.models.system_setting
@author fishing-ranking
@created 2026-08-13
@updated 2026-09-11
@version 1.2.0
"""

import json
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.orm import Session

from app.database import Base


# 默认配置（seed 用）
DEFAULT_SETTINGS = {
    "site_name": "野钓记录榜审核后台",
    "audit_tip": (
        "审核标准：鱼体完整可见；有鱼尺或参照物；能看出户外水域背景；"
        "图片清晰；重量与照片体型大致匹配。"
    ),
    "reject_reason_presets": [
        "照片不清晰",
        "缺少参照物",
        "看不出户外水域背景",
        "重量与照片体型不符",
        "信息填写不完整",
    ],
    "list_per_page": 20,
    # 上线日：开榜元老判定用（YYYY-MM-DD）
    "launch_date": "2026-08-01",
    # ICP 备案号：用户站页脚展示
    "icp_number": "",
}


class SystemSetting(Base):
    """
    系统配置模型
    """

    __tablename__ = "system_settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def get_parsed_value(self):
        """
        get_parsed_value - 解析 JSON 值

        @returns {*} 解析后的 Python 对象
        """
        return json.loads(self.value)

    def set_parsed_value(self, raw_value):
        """
        set_parsed_value - 写入 JSON 值

        @param {*} raw_value - 任意可序列化值
        """
        self.value = json.dumps(raw_value, ensure_ascii=False)

    def to_dict(self):
        """
        to_dict - 转为字典

        @returns {dict} 配置项
        """
        return {
            "key": self.key,
            "value": self.get_parsed_value(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<SystemSetting key={self.key}>"


def get_all_settings_map(db: Session):
    """
    get_all_settings_map - 读取全部配置为字典（缺省用默认值）

    @param {Session} db - 数据库会话

    @returns {dict} 配置 map
    """
    result = dict(DEFAULT_SETTINGS)
    rows = db.query(SystemSetting).all()
    for row in rows:
        result[row.key] = row.get_parsed_value()
    return result


def seed_default_settings(db: Session):
    """
    seed_default_settings - 写入缺失的默认配置

    @param {Session} db - 数据库会话
    """
    for key_name, default_value in DEFAULT_SETTINGS.items():
        existing = db.get(SystemSetting, key_name)
        # 判断是否已存在
        if existing is not None:
            continue
        setting = SystemSetting(key=key_name)
        setting.set_parsed_value(default_value)
        db.add(setting)
    db.commit()
