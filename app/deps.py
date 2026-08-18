"""
@file deps.py
@description FastAPI 依赖：数据库会话、当前用户/管理员
@module app.deps
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.0.0
"""

from typing import Optional

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin import Admin
from app.models.user import User
from app.constants import USER_STATUS_DISABLED
from app.utils.response import raise_error
from app.utils.security import decode_access_token


def _extract_bearer(authorization: Optional[str]) -> str:
    """
    _extract_bearer - 从 Authorization 头取出 Token

    @param {str|None} authorization - 请求头

    @returns {str} Token
    """
    # 判断是否携带 Authorization
    if not authorization:
        raise_error("未登录或 Token 失效", code=401, http_status=401)
    parts = authorization.split()
    # 判断 Bearer 格式
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise_error("未登录或 Token 失效", code=401, http_status=401)
    return parts[1]


def get_token_payload(authorization: Optional[str] = Header(default=None)):
    """
    get_token_payload - 解析 JWT payload

    @param {str|None} authorization - Authorization 头

    @returns {dict} payload
    """
    token = _extract_bearer(authorization)
    try:
        return decode_access_token(token)
    except Exception:
        raise_error("未登录或 Token 失效", code=401, http_status=401)


def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    get_optional_user - 可选登录用户（无 Token 时返回 None）

    @returns {User|None} 用户实体或空
    """
    # 判断是否携带 Authorization
    if not authorization:
        return None
    parts = authorization.split()
    # 判断 Bearer 格式
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    try:
        payload = decode_access_token(parts[1])
    except Exception:
        return None
    # 判断角色
    if payload.get("role") != "user":
        return None
    identity = payload.get("sub") or ""
    # 判断 identity 格式
    if not str(identity).startswith("user:"):
        return None
    user_id = int(str(identity).split(":")[1])
    user = db.get(User, user_id)
    # 判断用户是否存在或禁用
    if user is None or user.status == USER_STATUS_DISABLED:
        return None
    return user


def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    """
    get_current_user - 当前登录普通用户

    @returns {User} 用户实体
    """
    # 判断角色
    if payload.get("role") != "user":
        raise_error("无权限访问", code=403, http_status=403)

    identity = payload.get("sub") or ""
    # 判断 identity 格式
    if not str(identity).startswith("user:"):
        raise_error("未登录或 Token 失效", code=401, http_status=401)

    user_id = int(str(identity).split(":")[1])
    user = db.get(User, user_id)
    # 判断用户是否存在
    if user is None:
        raise_error("用户不存在", http_status=404)
    # 判断是否禁用
    if user.status == USER_STATUS_DISABLED:
        raise_error("账号已被禁用", http_status=403)
    return user


def get_current_admin(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> Admin:
    """
    get_current_admin - 当前登录管理员

    @returns {Admin} 管理员实体
    """
    # 判断角色
    if payload.get("role") != "admin":
        raise_error("无权限访问", code=403, http_status=403)

    identity = payload.get("sub") or ""
    # 判断 identity 格式
    if not str(identity).startswith("admin:"):
        raise_error("未登录或 Token 失效", code=401, http_status=401)

    admin_id = int(str(identity).split(":")[1])
    admin = db.get(Admin, admin_id)
    # 判断管理员是否存在
    if admin is None:
        raise_error("管理员不存在", http_status=404)
    return admin


def paginate_query(query, page: int, per_page: int):
    """
    paginate_query - 简单分页

    @param {Query} query - SQLAlchemy Query
    @param {int} page - 页码
    @param {int} per_page - 每页条数

    @returns {tuple} (items, total)
    """
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    return items, total
