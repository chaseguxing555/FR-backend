"""
@file catch.py
@description 鱼获记录表模型（catches）
@module app.models.catch
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

import json
from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from app.constants import AUDIT_ACTION_REJECT, CATCH_STATUS_PENDING, CATCH_STATUS_REJECTED
from app.database import Base


class Catch(Base):
    """
    鱼获记录模型

    @description 对应 PRD 5.2 鱼获记录表
    """

    __tablename__ = "catches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    fish_species = Column(String(20), nullable=False)
    # 钓法：手竿 / 路亚 / 水底，与鱼种组合形成分榜
    fishing_method = Column(String(20), nullable=False, default="手竿", index=True)
    weight = Column(Numeric(6, 2), nullable=False)
    province = Column(String(20), nullable=False, index=True)
    city = Column(String(20), nullable=False, index=True)
    location_detail = Column(String(100), nullable=True)
    # 饵料：用户填写，详情可见
    bait = Column(String(50), nullable=True)
    caught_at = Column(Date, nullable=False)
    image_urls = Column(Text, nullable=False)
    # 可选视频证明（单条）
    video_url = Column(String(255), nullable=True)
    description = Column(String(200), nullable=True)
    status = Column(Integer, nullable=False, default=CATCH_STATUS_PENDING, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship("User", back_populates="catches")
    audit_logs = relationship("AuditLog", back_populates="catch", lazy="dynamic")

    def get_image_url_list(self):
        """
        get_image_url_list - 解析照片 URL 列表

        @returns {list} 照片 URL 列表
        """
        # 空值时返回空列表
        if not self.image_urls:
            return []
        return json.loads(self.image_urls)

    def set_image_url_list(self, url_list):
        """
        set_image_url_list - 写入照片 URL 列表

        @param {list} url_list - 照片 URL 列表
        """
        self.image_urls = json.dumps(url_list, ensure_ascii=False)

    def to_dict(self, include_user=True):
        """
        to_dict - 将鱼获记录转为字典

        @param {bool} [include_user=True] - 是否包含上传人昵称

        @returns {dict} 鱼获记录字典
        """
        image_list = self.get_image_url_list()
        image_thumbnail = image_list[0] if image_list else None

        result = {
            "id": self.id,
            "user_id": self.user_id,
            "fish_species": self.fish_species,
            "fishing_method": self.fishing_method,
            "weight": float(self.weight) if self.weight is not None else None,
            "province": self.province,
            "city": self.city,
            "location_detail": self.location_detail,
            "bait": self.bait,
            "caught_at": self.caught_at.isoformat() if self.caught_at else None,
            "image_urls": image_list,
            "image_thumbnail": image_thumbnail,
            "video_url": self.video_url,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

        # 判断是否需要附带上传人昵称
        if include_user and self.user is not None:
            result["user_nickname"] = self.user.nickname

        # 未通过时附带最近一次拒绝原因
        if self.status == CATCH_STATUS_REJECTED:
            reject_logs = self.audit_logs.filter_by(action=AUDIT_ACTION_REJECT).all()
            # 判断是否有拒绝日志
            if reject_logs:
                latest_reject = max(
                    reject_logs,
                    key=lambda item: item.created_at or datetime.min,
                )
                result["reject_reason"] = latest_reject.reason

        return result

    def __repr__(self):
        return f"<Catch id={self.id} species={self.fish_species} weight={self.weight}>"
