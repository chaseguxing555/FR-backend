"""
@file hall_member.py
@description 名人堂成员表（永久入堂记录）
@module app.models.hall_member
@author fishing-ranking
@created 2026-08-14
@version 1.0.0
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.constants import HALL_TIER_META
from app.database import Base


class HallMember(Base):
    """
    名人堂成员

    @description 满足任一条入堂路径后永久写入；同人同年同路径同角色不重复
    """

    __tablename__ = "hall_members"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "inducted_year",
            "path_code",
            "role_key",
            name="uq_hall_member_slot",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # 入堂年份（展示用）
    inducted_year = Column(Integer, nullable=False, index=True)
    # annual_champion / record_keeper / legend_angler / dominate_master
    path_code = Column(String(32), nullable=False, index=True)
    # legend / record / master
    tier_code = Column(String(20), nullable=False, index=True)
    # 去重键：overall / method:手竿 / species:鲤鱼 / dominate:手竿 / legend:翘嘴
    role_key = Column(String(60), nullable=False, default="")
    # 展示角色：全榜冠军 / 手竿冠军 / 鲤鱼纪录 / 传奇·翘嘴 等
    role_label = Column(String(80), nullable=False)
    fishing_method = Column(String(20), nullable=True)
    fish_species = Column(String(20), nullable=True)
    catch_id = Column(Integer, ForeignKey("catches.id"), nullable=True)
    weight = Column(Numeric(6, 2), nullable=True)
    reason = Column(String(200), nullable=False, default="")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")
    catch = relationship("Catch")

    def to_dict(self, include_user=True):
        """
        to_dict - 名人堂成员字典
        """
        tier_meta = HALL_TIER_META.get(self.tier_code, {})
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "inducted_year": self.inducted_year,
            "path_code": self.path_code,
            "tier_code": self.tier_code,
            "tier_name": tier_meta.get("name", ""),
            "title": tier_meta.get("title", ""),
            "badge": tier_meta.get("badge", ""),
            "color": tier_meta.get("color", "gold"),
            "role_key": self.role_key,
            "role_label": self.role_label,
            "fishing_method": self.fishing_method,
            "fish_species": self.fish_species,
            "catch_id": self.catch_id,
            "weight": float(self.weight) if self.weight is not None else None,
            "reason": self.reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        # 判断附带用户
        if include_user and self.user is not None:
            result["user_nickname"] = self.user.nickname
            result["user_avatar"] = self.user.avatar
        return result
