"""
@file auth.py
@description 用户认证相关 Pydantic 模型
@module app.schemas.auth
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.0.0
"""

import re
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import NICKNAME_MAX_LENGTH, PASSWORD_MIN_LENGTH


# 手机号：1 开头 11 位
PHONE_PATTERN = re.compile(r"^1\d{10}$")


class RegisterRequest(BaseModel):
    """
    RegisterRequest - 用户注册请求体
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")
    nickname: str = Field(..., description="昵称")
    province: Optional[str] = Field(default=None, description="省份")
    city: Optional[str] = Field(default=None, description="城市")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """
        validate_phone - 校验手机号格式
        """
        # 判断手机号是否为空
        if not value:
            raise ValueError("手机号不能为空")
        # 判断手机号格式
        if not PHONE_PATTERN.match(value):
            raise ValueError("手机号格式不正确")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        validate_password - 校验密码长度
        """
        # 判断密码是否为空
        if not value:
            raise ValueError("密码不能为空")
        # 判断密码长度
        if len(value) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"密码长度不能少于{PASSWORD_MIN_LENGTH}位")
        return value

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        """
        validate_nickname - 校验昵称
        """
        # 判断昵称是否为空
        if not value:
            raise ValueError("昵称不能为空")
        # 判断昵称长度
        if len(value) > NICKNAME_MAX_LENGTH:
            raise ValueError(f"昵称不能超过{NICKNAME_MAX_LENGTH}个字符")
        return value

    @field_validator("province", "city")
    @classmethod
    def empty_to_none(cls, value: Optional[str]) -> Optional[str]:
        """
        empty_to_none - 空字符串转为 None
        """
        # 判断空串
        if value is None or value == "":
            return None
        return value


class LoginRequest(BaseModel):
    """
    LoginRequest - 用户登录请求体
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    phone: str = Field(..., description="手机号")
    password: str = Field(..., description="密码")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        """
        validate_phone - 校验手机号格式
        """
        # 判断手机号是否为空
        if not value:
            raise ValueError("手机号不能为空")
        # 判断手机号格式
        if not PHONE_PATTERN.match(value):
            raise ValueError("手机号格式不正确")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        validate_password - 校验密码非空
        """
        # 判断密码是否填写
        if not value:
            raise ValueError("密码不能为空")
        return value


class UpdateProfileRequest(BaseModel):
    """
    UpdateProfileRequest - 更新资料请求体
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    nickname: str = Field(..., description="昵称")
    province: Optional[str] = Field(default=None, description="省份")
    city: Optional[str] = Field(default=None, description="城市")

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        """
        validate_nickname - 校验昵称
        """
        # 判断昵称是否为空
        if not value:
            raise ValueError("昵称不能为空")
        # 判断昵称长度
        if len(value) > NICKNAME_MAX_LENGTH:
            raise ValueError(f"昵称不能超过{NICKNAME_MAX_LENGTH}个字符")
        return value

    @field_validator("province", "city")
    @classmethod
    def empty_to_none(cls, value: Optional[str]) -> Optional[str]:
        """
        empty_to_none - 空字符串转为 None
        """
        # 判断空串
        if value is None or value == "":
            return None
        return value


class UpdateAvatarRequest(BaseModel):
    """
    UpdateAvatarRequest - 更新头像请求体
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    avatar: str = Field(..., description="头像 URL")

    @field_validator("avatar")
    @classmethod
    def validate_avatar(cls, value: str) -> str:
        """
        validate_avatar - 校验为本站上传路径
        """
        # 判断头像 URL
        if not value:
            raise ValueError("请先上传头像图片")
        # 判断是否为本站上传路径
        if not value.startswith("/uploads/"):
            raise ValueError("头像地址不合法")
        return value


class ChangePasswordRequest(BaseModel):
    """
    ChangePasswordRequest - 修改密码请求体
    """

    old_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., description="新密码")

    @field_validator("old_password")
    @classmethod
    def validate_old_password(cls, value: str) -> str:
        """
        validate_old_password - 校验当前密码非空
        """
        # 判断旧密码
        if not value:
            raise ValueError("请输入当前密码")
        return value

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        """
        validate_new_password - 校验新密码长度
        """
        # 判断密码是否为空
        if not value:
            raise ValueError("密码不能为空")
        # 判断密码长度
        if len(value) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"密码长度不能少于{PASSWORD_MIN_LENGTH}位")
        return value
