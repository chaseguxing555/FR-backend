"""
@file rankings.py
@description 排行榜接口（对齐：钓法×鱼种×年榜/月榜）
@module app.api.rankings
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-14
@version 3.0.0
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import (
    CATCH_STATUS_APPROVED,
    DEFAULT_FISHING_METHOD,
    FISHING_METHOD_LIST,
    FISHING_METHOD_SPECIES_MAP,
    MONTHLY_HOT_SPECIES,
    MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG,
    RANKING_PER_PAGE,
)
from app.database import get_db
from app.deps import get_optional_user, paginate_query
from app.models.catch import Catch
from app.models.user import User
from app.utils.response import raise_error, success


router = APIRouter(prefix="/api/rankings", tags=["rankings"])

# 榜单周期：年榜（当年） / 月榜（当月）
RANKING_PERIOD_MONTH = "month"
RANKING_PERIOD_YEAR = "year"
RANKING_PERIOD_LIST = (
    RANKING_PERIOD_MONTH,
    RANKING_PERIOD_YEAR,
)
RANKING_PERIOD_DEFAULT = RANKING_PERIOD_YEAR


def _species_list_for_period(method_text: str, period_text: str):
    """
    _species_list_for_period - 按周期返回可选鱼种

    @description 月榜仅保留设计文档 10 个热门鱼种与当前钓法的交集
    """
    method_species = FISHING_METHOD_SPECIES_MAP[method_text]
    # 判断是否月度精选榜
    if period_text != RANKING_PERIOD_MONTH:
        return list(method_species)
    return [name for name in method_species if name in MONTHLY_HOT_SPECIES]


def _build_board_query(
    db: Session,
    method_text: str,
    species_text: str,
    period_text: str,
    province_text: str,
    city_text: str,
):
    """
    _build_board_query - 构造当前分榜查询（含月榜门槛）
    """
    query = db.query(Catch).filter_by(
        status=CATCH_STATUS_APPROVED,
        fishing_method=method_text,
        fish_species=species_text,
    )
    # 判断是否按省份筛选
    if province_text:
        query = query.filter(Catch.province == province_text)
    # 判断是否按城市筛选
    if city_text:
        query = query.filter(Catch.city == city_text)

    today = date.today()
    # 判断月榜：仅当月钓获 + 最低重量门槛
    if period_text == RANKING_PERIOD_MONTH:
        month_start = today.replace(day=1)
        # 下月 1 日作为半开区间上界
        if today.month == 12:
            month_end = date(today.year + 1, 1, 1)
        else:
            month_end = date(today.year, today.month + 1, 1)
        query = query.filter(
            Catch.caught_at >= month_start,
            Catch.caught_at < month_end,
        )
        min_weight = MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG.get(species_text)
        # 判断该鱼种是否配置了月榜门槛
        if min_weight is not None:
            query = query.filter(Catch.weight >= min_weight)
    # 判断年榜：仅当年钓获
    else:
        year_start = date(today.year, 1, 1)
        year_end = date(today.year + 1, 1, 1)
        query = query.filter(
            Catch.caught_at >= year_start,
            Catch.caught_at < year_end,
        )

    return query.order_by(Catch.weight.desc(), Catch.created_at.desc())


@router.get("")
def get_rankings(
    fishing_method: Optional[str] = Query(default=None),
    fish_species: Optional[str] = Query(default=None),
    province: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    period: Optional[str] = Query(default=RANKING_PERIOD_DEFAULT),
    page: int = Query(default=1),
    per_page: int = Query(default=RANKING_PER_PAGE),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
):
    """
    get_rankings - 按钓法 + 鱼种分榜的排行榜列表

    @description 仅支持当年年榜 / 当月月榜；固定按重量降序
    """
    # 判断页码
    if page < 1:
        raise_error("页码必须大于等于1")
    # 判断每页条数
    if per_page < 1:
        raise_error("每页条数必须大于等于1")

    method_text = (fishing_method or "").strip() or DEFAULT_FISHING_METHOD
    # 判断钓法是否合法
    if method_text not in FISHING_METHOD_LIST:
        raise_error("钓法不合法")

    period_text = (period or "").strip() or RANKING_PERIOD_DEFAULT
    # 兼容旧链接：历史总榜已取消，统一落到年榜
    if period_text == "all":
        period_text = RANKING_PERIOD_YEAR
    # 判断周期是否合法
    if period_text not in RANKING_PERIOD_LIST:
        raise_error("榜单周期不合法")

    species_options = _species_list_for_period(method_text, period_text)
    # 判断月榜下当前钓法是否有热门鱼种
    if not species_options:
        raise_error("当前钓法本月暂无精选鱼种")

    default_species = species_options[0]
    species_text = (fish_species or "").strip() or default_species
    # 判断鱼种是否可进入当前周期榜单
    if species_text not in species_options:
        raise_error("该鱼种不属于当前榜单周期可选范围")

    province_text = (province or "").strip()
    city_text = (city or "").strip()
    query = _build_board_query(
        db,
        method_text,
        species_text,
        period_text,
        province_text,
        city_text,
    )

    items, total = paginate_query(query, page, per_page)
    start_rank = (page - 1) * per_page + 1

    from app.services.title_service import primary_title_for_user

    ranking_list = []
    for index, catch in enumerate(items):
        item = catch.to_dict(include_user=True)
        item["rank"] = start_rank + index
        item["primary_title"] = primary_title_for_user(db, catch.user_id)
        ranking_list.append(item)

    # 全国/当前分榜纪录保持者（第 1 名）
    record_holder = None
    # 判断是否有上榜记录
    if total > 0:
        top_catch = query.first()
        # 判断第一名是否存在
        if top_catch is not None:
            top_item = top_catch.to_dict(include_user=True)
            top_item["rank"] = 1
            record_holder = top_item

    # 当前登录用户在本榜的排名（可选）
    my_rank = None
    # 判断已登录则计算我的最佳名次
    if current_user is not None:
        my_best = (
            query.filter(Catch.user_id == current_user.id)
            .order_by(Catch.weight.desc(), Catch.created_at.desc())
            .first()
        )
        # 判断本人是否有上榜记录
        if my_best is not None:
            better_count = query.filter(Catch.weight > my_best.weight).count()
            same_weight_earlier = query.filter(
                Catch.weight == my_best.weight,
                Catch.created_at > my_best.created_at,
            ).count()
            my_rank = {
                "rank": better_count + same_weight_earlier + 1,
                "weight": float(my_best.weight),
                "catch_id": my_best.id,
            }

    today = date.today()
    return success(
        {
            "list": ranking_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "fishing_method": method_text,
            "fish_species": species_text,
            "fish_species_list": species_options,
            "fishing_method_list": FISHING_METHOD_LIST,
            "province": province_text or None,
            "city": city_text or None,
            "period": period_text,
            "record_holder": record_holder,
            "my_rank": my_rank,
            "board_year": today.year,
            "board_month": today.month,
            "monthly_hot_species": MONTHLY_HOT_SPECIES,
            "monthly_min_weight_kg": MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG.get(
                species_text
            ),
        }
    )
