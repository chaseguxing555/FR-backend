"""
@file users.py
@description 用户相关业务接口：我的记录
@module app.api.users
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import RANKING_PER_PAGE
from app.database import get_db
from app.deps import get_current_user, paginate_query
from app.models.catch import Catch
from app.models.user import User
from app.utils.response import raise_error, success


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me/catches")
def get_my_catches(
    page: int = Query(default=1),
    per_page: int = Query(default=RANKING_PER_PAGE),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    get_my_catches - 我的鱼获列表
    """
    # 判断分页
    if page < 1 or per_page < 1:
        raise_error("分页参数不正确")

    query = (
        db.query(Catch)
        .filter_by(user_id=user.id)
        .order_by(Catch.created_at.desc())
    )
    items, total = paginate_query(query, page, per_page)
    catch_list = [catch.to_dict(include_user=False) for catch in items]
    return success(
        {
            "list": catch_list,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.get("/me/catches/{catch_id}")
def get_my_catch_detail(
    catch_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    get_my_catch_detail - 本人单条鱼获
    """
    catch = db.query(Catch).filter_by(id=catch_id, user_id=user.id).first()
    # 判断记录是否存在
    if catch is None:
        raise_error("记录不存在", http_status=404)
    return success(catch.to_dict(include_user=False))
