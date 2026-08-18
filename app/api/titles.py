"""
@file titles.py
@description 称号查询接口
@module app.api.titles
@author fishing-ranking
@created 2026-08-14
@version 1.0.0
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import TITLE_DEFINITIONS
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.services.title_service import evaluate_user_titles, list_user_titles
from app.utils.response import success


router = APIRouter(prefix="/api/titles", tags=["titles"])


@router.get("/catalog")
def title_catalog():
    """
    title_catalog - 全部称号定义
    """
    items = []
    for code, meta in TITLE_DEFINITIONS.items():
        items.append(
            {
                "title_code": code,
                "name": meta["name"],
                "color": meta["color"],
                "icon": meta["icon"],
                "display": meta["display"],
                "priority": meta["priority"],
                "description": meta["description"],
            }
        )
    items.sort(key=lambda item: item["priority"], reverse=True)
    return success({"list": items})


@router.get("/me")
def my_titles(
    refresh: bool = Query(default=False),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    my_titles - 当前用户称号墙
    """
    # 判断需要刷新评定
    if refresh:
        evaluate_user_titles(db, user.id)
        db.commit()
    return success({"list": list_user_titles(db, user.id, active_only=True)})


@router.get("/users/{user_id}")
def user_titles(user_id: int, db: Session = Depends(get_db)):
    """
    user_titles - 指定用户称号墙
    """
    return success({"list": list_user_titles(db, user_id, active_only=True)})
