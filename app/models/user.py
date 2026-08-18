"""
@file user.py
@description 用户表模型（users）
@module app.models.user
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.constants import USER_STATUS_NORMAL
from app.database import Base


class User(Base):
    """
    用户模型

    @description 对应 PRD 5.1 用户表，存储注册用户信息
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(11), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    nickname = Column(String(20), nullable=False)
    avatar = Column(String(255), nullable=True)
    province = Column(String(20), nullable=True)
    city = Column(String(20), nullable=True)
    total_catches = Column(Integer, nullable=False, default=0)
    status = Column(Integer, nullable=False, default=USER_STATUS_NORMAL)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    catches = relationship("Catch", back_populates="user", lazy="dynamic")
    notifications = relationship("Notification", back_populates="user", lazy="dynamic")

    def to_dict(self, mask_phone=True):
        """
        to_dict - 将用户对象转为字典

        @param {bool} [mask_phone=True] - 是否对手机号脱敏

        @returns {dict} 用户信息字典
        """
        # 脱敏规则：保留前3位与后4位
        if mask_phone and self.phone and len(self.phone) == 11:
            display_phone = f"{self.phone[:3]}****{self.phone[-4:]}"
        else:
            display_phone = self.phone

        return {
            "id": self.id,
            "phone": display_phone,
            "nickname": self.nickname,
            "avatar": self.avatar,
            "province": self.province,
            "city": self.city,
            "total_catches": self.total_catches,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User id={self.id} phone={self.phone}>"
