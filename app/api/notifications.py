"""
@file notifications.py
@description 站内消息接口
@module app.api.notifications
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.constants import NOTIFICATION_READ, NOTIFICATION_UNREAD, RANKING_PER_PAGE
from app.database import get_db
from app.deps import get_current_user, paginate_query
from app.models.notification import Notification
from app.models.user import User
from app.utils.response import raise_error, success


router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    page: int = Query(default=1),
    per_page: int = Query(default=RANKING_PER_PAGE),
    unread_only: Optional[str] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    list_notifications - 消息列表
    """
    # 判断分页
    if page < 1 or per_page < 1:
        raise_error("分页参数不正确")

    query = db.query(Notification).filter_by(user_id=user.id)
    # 判断是否只看未读
    if unread_only in ("1", "true", "True"):
        query = query.filter_by(is_read=NOTIFICATION_UNREAD)

    query = query.order_by(Notification.created_at.desc())
    items, total = paginate_query(query, page, per_page)
    return success(
        {
            "list": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.get("/unread-count")
def unread_count(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    unread_count - 未读数量
    """
    count_value = (
        db.query(Notification)
        .filter_by(user_id=user.id, is_read=NOTIFICATION_UNREAD)
        .count()
    )
    return success({"count": count_value})


@router.put("/{notification_id}/read")
def mark_read(
    notification_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    mark_read - 单条已读
    """
    notification = (
        db.query(Notification)
        .filter_by(id=notification_id, user_id=user.id)
        .first()
    )
    # 判断消息是否存在
    if notification is None:
        raise_error("消息不存在", http_status=404)

    notification.is_read = NOTIFICATION_READ
    db.commit()
    db.refresh(notification)
    return success(notification.to_dict(), message="已标为已读")


@router.put("/read-all")
def mark_all_read(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    mark_all_read - 全部已读
    """
    updated_count = (
        db.query(Notification)
        .filter_by(user_id=user.id, is_read=NOTIFICATION_UNREAD)
        .update({"is_read": NOTIFICATION_READ})
    )
    db.commit()
    return success({"updated": updated_count}, message="已全部标为已读")
