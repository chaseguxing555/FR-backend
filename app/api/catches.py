"""
@file catches.py
@description 鱼获上传与详情接口
@module app.api.catches
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.1.0
"""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import CATCH_STATUS_APPROVED, CATCH_STATUS_PENDING
from app.database import get_db
from app.deps import get_current_user
from app.models.catch import Catch
from app.models.user import User
from app.schemas.catch import CreateCatchRequest
from app.utils.response import raise_error, success


router = APIRouter(prefix="/api/catches", tags=["catches"])


@router.post("")
def create_catch(
    payload: CreateCatchRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    create_catch - 上传鱼获
    """
    caught_date = datetime.strptime(payload.caught_at, "%Y-%m-%d").date()

    catch = Catch(
        user_id=user.id,
        fishing_method=payload.fishing_method,
        fish_species=payload.fish_species,
        weight=payload.weight,
        province=payload.province,
        city=payload.city,
        location_detail=payload.location_detail,
        bait=payload.bait,
        caught_at=caught_date,
        description=payload.description,
        status=CATCH_STATUS_PENDING,
    )
    catch.set_image_url_list(payload.image_urls)
    catch.video_url = payload.video_url

    user.total_catches = user.total_catches + 1
    db.add(catch)
    db.commit()
    db.refresh(catch)
    return success(catch.to_dict(include_user=True), message="提交成功，等待审核")


@router.get("/{catch_id}")
def get_catch_detail(catch_id: int, db: Session = Depends(get_db)):
    """
    get_catch_detail - 公开详情（仅已通过）
    """
    catch = db.get(Catch, catch_id)
    # 判断是否存在
    if catch is None:
        raise_error("记录不存在", http_status=404)
    # 公开详情仅展示已通过
    if catch.status != CATCH_STATUS_APPROVED:
        raise_error("记录不存在或未通过审核", http_status=404)
    from app.services.title_service import primary_title_for_user

    result = catch.to_dict(include_user=True)
    result["primary_title"] = primary_title_for_user(db, catch.user_id)
    return success(result)
