"""
@file hall.py
@description 名人堂：四条入堂路径成员展示
@module app.api.hall
@author fishing-ranking
@created 2026-08-14
@updated 2026-08-14
@version 2.0.0
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.hall_member import HallMember
from app.services.hall_induction import (
    evaluate_hall_of_fame,
    hall_stats,
    list_hall_members,
)
from app.utils.response import success


router = APIRouter(prefix="/api/hall", tags=["hall"])


@router.get("")
def get_hall(
    year: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    get_hall - 名人堂按年度成员 + 汇总数据

    @description 按 inducted_year 展示；永久路径成员归入入堂当年
    """
    today = date.today()
    year_number = year or today.year
    members = list_hall_members(db, year=year_number)
    stats = hall_stats(db)
    # 可选年份：成员表有的年份 + 近 6 年
    year_rows = db.query(HallMember.inducted_year).distinct().all()
    year_set = {row[0] for row in year_rows}
    for offset in range(6):
        year_set.add(today.year - offset)
    available_years = sorted(year_set, reverse=True)

    return success(
        {
            "year": year_number,
            "members": members,
            "stats": stats,
            "available_years": available_years,
            "paths": [
                {
                    "code": "annual_champion",
                    "name": "年度总冠军",
                    "tier": "record",
                    "desc": "全榜冠军 + 三大钓法冠军（同年不重复占位）",
                },
                {
                    "code": "record_keeper",
                    "name": "全国纪录保持者",
                    "tier": "record",
                    "desc": "鱼种全国纪录连续保持 ≥ 6 个月",
                },
                {
                    "code": "legend_angler",
                    "name": "传奇钓手",
                    "tier": "legend",
                    "desc": "同一鱼种连续 3 年进入年度 TOP 3",
                },
                {
                    "code": "dominate_master",
                    "name": "全鱼种制霸",
                    "tier": "master",
                    "desc": "任一钓法下全部鱼种均有上榜记录",
                },
            ],
        }
    )


@router.post("/evaluate")
def post_evaluate_hall(
    year: Optional[int] = Query(default=None),
    include_annual: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    """
    post_evaluate_hall - 手动触发名人堂四条路径评定（运维/回填）
    """
    result = evaluate_hall_of_fame(
        db,
        year=year,
        notify=True,
        include_annual=include_annual,
        do_commit=True,
    )
    return success(result, message="名人堂评定完成")
