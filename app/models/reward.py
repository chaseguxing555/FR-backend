"""
@file reward.py
@description 奖励结算记录表（月榜 / 年榜冠军）
@module app.models.reward
@author fishing-ranking
@created 2026-08-14
@updated 2026-08-14
@version 1.0.0
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class RewardAward(Base):
    """
    奖励结算记录

    @description 每月/每年结算一次，幂等写入；用于发通知与首页荣耀展示
    """

    __tablename__ = "reward_awards"
    __table_args__ = (
        UniqueConstraint(
            "period_type",
            "period_key",
            "award_type",
            "fishing_method",
            name="uq_reward_period_award_method",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # month / year
    period_type = Column(String(10), nullable=False, index=True)
    # 2026-07 / 2026
    period_key = Column(String(10), nullable=False, index=True)
    # monthly_method / monthly_overall / yearly_method / yearly_overall
    award_type = Column(String(32), nullable=False, index=True)
    # 钓法冠军时有值；总冠军为空字符串（唯一约束需要非 NULL）
    fishing_method = Column(String(20), nullable=False, default="", index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    catch_id = Column(Integer, ForeignKey("catches.id"), nullable=False, index=True)
    weight = Column(Numeric(6, 2), nullable=False)
    fish_species = Column(String(20), nullable=False)
    title = Column(String(80), nullable=False)
    prizes = Column(String(200), nullable=False)
    # 是否已发站内通知：0 否 1 是
    notified = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User")
    catch = relationship("Catch")

    def to_dict(self, include_user=True):
        """
        to_dict - 转为字典

        @param {bool} [include_user=True] - 是否带用户昵称
        @returns {dict}
        """
        result = {
            "id": self.id,
            "period_type": self.period_type,
            "period_key": self.period_key,
            "award_type": self.award_type,
            "fishing_method": self.fishing_method or None,
            "user_id": self.user_id,
            "catch_id": self.catch_id,
            "weight": float(self.weight),
            "fish_species": self.fish_species,
            "title": self.title,
            "prizes": self.prizes,
            "notified": self.notified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        # 判断附带用户信息
        if include_user and self.user is not None:
            result["user_nickname"] = self.user.nickname
        return result

    def __repr__(self):
        return (
            f"<RewardAward id={self.id} {self.period_key} "
            f"{self.award_type} user={self.user_id}>"
        )
