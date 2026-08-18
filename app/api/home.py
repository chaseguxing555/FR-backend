"""
@file home.py
@description 首页聚合数据接口（榜单按钓法 × 单鱼种展示）
@module app.api.home
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.2.0
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import (
    CATCH_STATUS_APPROVED,
    DEFAULT_FISHING_METHOD,
    FISHING_METHOD_LIST,
    FISHING_METHOD_SPECIES_MAP,
)
from app.database import get_db
from app.models.catch import Catch
from app.models.user import User
from app.utils.response import raise_error, success


router = APIRouter(prefix="/api/home", tags=["home"])


@router.get("")
def get_home_data(
    province: Optional[str] = Query(default=None),
    fishing_method: Optional[str] = Query(default=None),
    fish_species: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    get_home_data - 首页数据

    @description 全国/本省 TOP10 均按指定钓法 + 鱼种分榜
    """
    province_text = (province or "").strip()
    method_text = (fishing_method or "").strip() or DEFAULT_FISHING_METHOD
    # 判断钓法是否合法
    if method_text not in FISHING_METHOD_LIST:
        raise_error("钓法不合法")

    method_species_list = FISHING_METHOD_SPECIES_MAP[method_text]
    species_text = (fish_species or "").strip() or method_species_list[0]
    # 判断鱼种是否属于该钓法
    if species_text not in method_species_list:
        raise_error("该鱼种不属于所选钓法")

    total_catches = db.query(Catch).filter_by(status=CATCH_STATUS_APPROVED).count()
    total_users = db.query(User).count()
    # 当前钓法 + 鱼种最大单尾
    max_catch = (
        db.query(Catch)
        .filter_by(
            status=CATCH_STATUS_APPROVED,
            fishing_method=method_text,
            fish_species=species_text,
        )
        .order_by(Catch.weight.desc())
        .first()
    )

    national_top = (
        db.query(Catch)
        .filter_by(
            status=CATCH_STATUS_APPROVED,
            fishing_method=method_text,
            fish_species=species_text,
        )
        .order_by(Catch.weight.desc(), Catch.created_at.desc())
        .limit(10)
        .all()
    )
    national_list = []
    for index, catch in enumerate(national_top):
        item = catch.to_dict(include_user=True)
        item["rank"] = index + 1
        national_list.append(item)

    # 判断是否有省份参数：有则本省同钓法同鱼种榜，无则回退全国榜
    if province_text:
        province_top = (
            db.query(Catch)
            .filter_by(
                status=CATCH_STATUS_APPROVED,
                fishing_method=method_text,
                fish_species=species_text,
                province=province_text,
            )
            .order_by(Catch.weight.desc(), Catch.created_at.desc())
            .limit(10)
            .all()
        )
    else:
        province_top = national_top

    province_list = []
    for index, catch in enumerate(province_top):
        item = catch.to_dict(include_user=True)
        item["rank"] = index + 1
        province_list.append(item)

    latest_catches = (
        db.query(Catch)
        .filter_by(status=CATCH_STATUS_APPROVED)
        .order_by(Catch.created_at.desc())
        .limit(8)
        .all()
    )
    latest_list = [catch.to_dict(include_user=True) for catch in latest_catches]
    max_weight = float(max_catch.weight) if max_catch is not None else 0

    return success(
        {
            "stats": {
                "total_catches": total_catches,
                "total_users": total_users,
                "max_weight": max_weight,
            },
            "national_top10": national_list,
            "province_top10": province_list,
            "province": province_text or None,
            "fishing_method": method_text,
            "fish_species": species_text,
            "fish_species_list": method_species_list,
            "fishing_method_list": FISHING_METHOD_LIST,
            "latest": latest_list,
        }
    )
