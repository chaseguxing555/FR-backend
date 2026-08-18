"""
@file auth.py
@description 用户认证接口：注册、登录、资料、头像、改密
@module app.api.auth
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.1.0
"""

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import USER_STATUS_DISABLED, USER_STATUS_NORMAL
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UpdateAvatarRequest,
    UpdateProfileRequest,
)
from app.utils.response import raise_error, success
from app.utils.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _user_with_join_days(user: User) -> Dict[str, Any]:
    """
    _user_with_join_days - 用户字典附加加入天数

    @param {User} user - 用户

    @returns {dict} 用户信息
    """
    user_data = user.to_dict(mask_phone=True)
    join_days = (datetime.utcnow().date() - user.created_at.date()).days + 1
    user_data["join_days"] = join_days
    return user_data


@router.post("/register")
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    register - 用户注册
    """
    existing_user = db.query(User).filter_by(phone=payload.phone).first()
    # 判断是否已注册
    if existing_user is not None:
        raise_error("该手机号已注册")

    user = User(
        phone=payload.phone,
        password=hash_password(payload.password),
        nickname=payload.nickname,
        province=payload.province,
        city=payload.city,
        total_catches=0,
        status=USER_STATUS_NORMAL,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(identity=f"user:{user.id}", role="user")
    return success(
        {"token": access_token, "user": user.to_dict(mask_phone=True)},
        message="注册成功",
    )


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    login - 用户登录
    """
    user = db.query(User).filter_by(phone=payload.phone).first()
    # 判断用户或密码
    if user is None or not verify_password(payload.password, user.password):
        raise_error("手机号或密码错误", http_status=401)
    # 判断是否禁用
    if user.status == USER_STATUS_DISABLED:
        raise_error("账号已被禁用", http_status=403)

    access_token = create_access_token(identity=f"user:{user.id}", role="user")
    return success(
        {"token": access_token, "user": user.to_dict(mask_phone=True)},
        message="登录成功",
    )


@router.get("/me")
def get_current_user_info(user: User = Depends(get_current_user)):
    """
    get_current_user_info - 获取当前用户
    """
    return success(_user_with_join_days(user))


@router.put("/me")
def update_current_user(
    payload: UpdateProfileRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    update_current_user - 更新资料
    """
    # 判断选了城市但未选省份
    if payload.city and not payload.province:
        raise_error("请先选择省份")

    user.nickname = payload.nickname
    user.province = payload.province
    user.city = payload.city
    db.commit()
    db.refresh(user)
    return success(_user_with_join_days(user), message="资料已更新")


@router.put("/me/avatar")
def update_avatar(
    payload: UpdateAvatarRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    update_avatar - 更新头像
    """
    user.avatar = payload.avatar
    db.commit()
    db.refresh(user)
    return success(_user_with_join_days(user), message="头像已更新")


@router.put("/me/password")
def change_password(
    payload: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    change_password - 修改密码
    """
    # 判断旧密码是否正确
    if not verify_password(payload.old_password, user.password):
        raise_error("当前密码不正确")
    # 判断新旧相同
    if payload.old_password == payload.new_password:
        raise_error("新密码不能与当前密码相同")

    user.password = hash_password(payload.new_password)
    db.commit()
    return success(None, message="密码已修改")
