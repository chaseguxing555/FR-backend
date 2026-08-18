"""
@file meta.py
@description 元数据接口：鱼种、钓法（上榜 / 上传分流）
@module app.api.meta
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-14
@version 2.2.0
"""

from fastapi import APIRouter

from app.constants import (
    FISH_SPECIES_LIST,
    FISHING_METHOD_LIST,
    FISHING_METHOD_SPECIES_MAP,
    MONTHLY_HOT_SPECIES,
    MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG,
    PERSONAL_ONLY_SPECIES,
    RANKING_SPECIES_LIST,
    UPLOAD_METHOD_SPECIES_MAP,
)
from app.utils.response import success


router = APIRouter(prefix="/api/meta", tags=["meta"])


@router.get("/fish-species")
def get_fish_species():
    """
    get_fish_species - 获取全部鱼种列表（含不设榜鱼种）
    """
    return success(
        {
            "list": FISH_SPECIES_LIST,
            "ranking_list": RANKING_SPECIES_LIST,
            "personal_only_list": PERSONAL_ONLY_SPECIES,
            "monthly_hot_list": MONTHLY_HOT_SPECIES,
        }
    )


@router.get("/fishing-methods")
def get_fishing_methods():
    """
    get_fishing_methods - 获取钓法及对应鱼种

    @description method_species_map 为上榜鱼种；upload_method_species_map 含不设榜鱼种
    """
    method_list = []
    for method_name in FISHING_METHOD_LIST:
        method_list.append(
            {
                "name": method_name,
                "species_list": FISHING_METHOD_SPECIES_MAP[method_name],
                "upload_species_list": UPLOAD_METHOD_SPECIES_MAP[method_name],
            }
        )
    return success(
        {
            "list": method_list,
            "method_species_map": FISHING_METHOD_SPECIES_MAP,
            "upload_method_species_map": UPLOAD_METHOD_SPECIES_MAP,
            "personal_only_species": PERSONAL_ONLY_SPECIES,
            "monthly_hot_species": MONTHLY_HOT_SPECIES,
            "monthly_hot_min_weight_kg": MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG,
        }
    )
