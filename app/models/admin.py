"""
@file admin.py
@description 管理员表模型（admins）
@module app.models.admin
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Admin(Base):
    """
    管理员模型
    """

    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(30), unique=True, nullable=False, index=True)
    password = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    audit_logs = relationship("AuditLog", back_populates="admin", lazy="dynamic")

    def to_dict(self):
        """
        to_dict - 将管理员对象转为字典

        @returns {dict} 管理员信息字典
        """
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Admin id={self.id} username={self.username}>"
