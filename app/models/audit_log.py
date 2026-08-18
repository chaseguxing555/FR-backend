"""
@file audit_log.py
@description 审核日志表模型（audit_logs）
@module app.models.audit_log
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    """
    审核日志模型
    """

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    catch_id = Column(Integer, ForeignKey("catches.id"), nullable=False, index=True)
    admin_id = Column(Integer, ForeignKey("admins.id"), nullable=False, index=True)
    action = Column(Integer, nullable=False)
    reason = Column(String(200), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    catch = relationship("Catch", back_populates="audit_logs")
    admin = relationship("Admin", back_populates="audit_logs")

    def to_dict(self):
        """
        to_dict - 将审核日志转为字典

        @returns {dict} 审核日志字典
        """
        return {
            "id": self.id,
            "catch_id": self.catch_id,
            "admin_id": self.admin_id,
            "action": self.action,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<AuditLog id={self.id} catch_id={self.catch_id} action={self.action}>"
