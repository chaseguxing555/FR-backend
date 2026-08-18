"""
@file rewards.py
@description 奖励查询接口（公开：近期冠军；管理结算走 admin）
@module app.api.rewards
@author fishing-ranking
@created 2026-08-14
@updated 2026-08-14
@version 1.0.0
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import (
    REWARD_AWARD_MONTHLY_OVERALL,
    REWARD_AWARD_YEARLY_OVERALL,
    REWARD_PERIOD_MONTH,
    REWARD_PERIOD_YEAR,
)
from app.database import get_db
from app.models.reward import RewardAward
from app.utils.response import success


router = APIRouter(prefix="/api/rewards", tags=["rewards"])


@router.get("")
def list_rewards(
    period_type: Optional[str] = Query(default=None),
    period_key: Optional[str] = Query(default=None),
    award_type: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    list_rewards - 奖励结算列表
    """
    query = db.query(RewardAward).order_by(RewardAward.created_at.desc())
    # 判断周期类型
    if period_type:
        query = query.filter(RewardAward.period_type == period_type.strip())
    # 判断周期键
    if period_key:
        query = query.filter(RewardAward.period_key == period_key.strip())
    # 判断奖项类型
    if award_type:
        query = query.filter(RewardAward.award_type == award_type.strip())

    items = query.limit(limit).all()
    return success({"list": [item.to_dict() for item in items]})


@router.get("/highlights")
def reward_highlights(db: Session = Depends(get_db)):
    """
    reward_highlights - 首页奖励高亮：最近月榜总冠军 + 最近年榜总冠军
    """
    monthly = (
        db.query(RewardAward)
        .filter_by(
            period_type=REWARD_PERIOD_MONTH,
            award_type=REWARD_AWARD_MONTHLY_OVERALL,
        )
        .order_by(RewardAward.period_key.desc())
        .first()
    )
    yearly = (
        db.query(RewardAward)
        .filter_by(
            period_type=REWARD_PERIOD_YEAR,
            award_type=REWARD_AWARD_YEARLY_OVERALL,
        )
        .order_by(RewardAward.period_key.desc())
        .first()
    )
    return success(
        {
            "monthly_overall": monthly.to_dict() if monthly else None,
            "yearly_overall": yearly.to_dict() if yearly else None,
        }
    )
