"""
@file user_title.py
@description 用户称号表
@module app.models.user_title
@author fishing-ranking
@created 2026-08-14
@version 1.0.0
"""

from datetime import datetime

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.constants import TITLE_DEFINITIONS
from app.database import Base


class UserTitle(Base):
    """
    用户已获得称号
    """

    __tablename__ = "user_titles"
    __table_args__ = (
        UniqueConstraint("user_id", "title_code", name="uq_user_title_code"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title_code = Column(String(40), nullable=False, index=True)
    # 1 有效 / 0 失效（如纪录被超越）
    is_active = Column(Integer, nullable=False, default=1, index=True)
    # 次数等附加信息，如月度上榜次数
    count = Column(Integer, nullable=False, default=1)
    # 附加说明，如鱼种名
    extra = Column(String(80), nullable=True)
    granted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship("User")

    def to_dict(self):
        """
        to_dict - 称号字典（含元数据）
        """
        meta = TITLE_DEFINITIONS.get(self.title_code, {})
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title_code": self.title_code,
            "name": meta.get("name", self.title_code),
            "color": meta.get("color", "gold"),
            "icon": meta.get("icon", ""),
            "display": meta.get("display", "wall"),
            "priority": meta.get("priority", 0),
            "description": meta.get("description", ""),
            "is_active": self.is_active,
            "count": self.count,
            "extra": self.extra,
            "granted_at": self.granted_at.isoformat() if self.granted_at else None,
        }


class FirstSpeciesRecord(Base):
    """
    首个纪录墙：每个鱼种第一条通过审核的记录（永不覆盖）
    """

    __tablename__ = "first_species_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fish_species = Column(String(20), unique=True, nullable=False, index=True)
    catch_id = Column(Integer, ForeignKey("catches.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    weight = Column(Numeric(6, 2), nullable=False)
    fishing_method = Column(String(20), nullable=False)
    caught_at = Column(Date, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    catch = relationship("Catch")
    user = relationship("User")

    def to_dict(self):
        """
        to_dict - 首个纪录字典
        """
        return {
            "fish_species": self.fish_species,
            "catch_id": self.catch_id,
            "user_id": self.user_id,
            "user_nickname": self.user.nickname if self.user else None,
            "weight": float(self.weight),
            "fishing_method": self.fishing_method,
            "caught_at": self.caught_at.isoformat() if self.caught_at else None,
            "status_label": "首个纪录",
        }
