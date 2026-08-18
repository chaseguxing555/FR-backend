"""
@file notification.py
@description 站内消息表模型（notifications）
@module app.models.notification
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.constants import (
    AUDIT_ACTION_APPROVE,
    NOTIFICATION_TYPE_AUDIT_PASS,
    NOTIFICATION_TYPE_AUDIT_REJECT,
)
from app.database import Base


class Notification(Base):
    """
    站内消息模型
    """

    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String(32), nullable=False, index=True)
    title = Column(String(80), nullable=False)
    content = Column(String(500), nullable=False)
    catch_id = Column(Integer, ForeignKey("catches.id"), nullable=True, index=True)
    is_read = Column(Integer, nullable=False, default=0, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

    def to_dict(self):
        """
        to_dict - 将消息转为字典

        @returns {dict} 消息信息
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type,
            "title": self.title,
            "content": self.content,
            "catch_id": self.catch_id,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Notification id={self.id} type={self.type} user_id={self.user_id}>"


def build_audit_notification(user_id, catch, action, reason=None):
    """
    build_audit_notification - 根据审核结果构造站内消息（未 commit）

    @param {int} user_id - 用户 ID
    @param {Catch} catch - 鱼获记录
    @param {int} action - 审核动作
    @param {str} [reason=None] - 拒绝原因

    @returns {Notification} 消息实例
    """
    species_text = catch.fish_species
    weight_text = f"{float(catch.weight)}kg"
    # 判断是否通过
    if action == AUDIT_ACTION_APPROVE:
        return Notification(
            user_id=user_id,
            type=NOTIFICATION_TYPE_AUDIT_PASS,
            title="鱼获审核通过",
            content=f"你的「{species_text} · {weight_text}」已通过审核，已出现在排行榜。",
            catch_id=catch.id,
            is_read=0,
        )

    reason_text = reason or "未填写原因"
    return Notification(
        user_id=user_id,
        type=NOTIFICATION_TYPE_AUDIT_REJECT,
        title="鱼获未通过审核",
        content=f"你的「{species_text} · {weight_text}」未通过。原因：{reason_text}。可修改后重新上传。",
        catch_id=catch.id,
        is_read=0,
    )
