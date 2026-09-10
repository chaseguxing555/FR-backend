"""
@file admin.py
@description 管理后台相关 Pydantic 模型
@module app.schemas.admin
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.0.0
"""

from datetime import date as date_type
from typing import List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.constants import (
    AUDIT_ACTION_APPROVE,
    AUDIT_ACTION_REJECT,
    PASSWORD_MIN_LENGTH,
    USER_STATUS_DISABLED,
    USER_STATUS_NORMAL,
)


class AdminLoginRequest(BaseModel):
    """
    AdminLoginRequest - 管理员登录
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """
        validate_username - 校验用户名非空
        """
        # 判断用户名
        if not value:
            raise ValueError("用户名不能为空")
        return value

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """
        validate_password - 校验密码非空
        """
        # 判断密码
        if not value:
            raise ValueError("密码不能为空")
        return value


class AuditCatchRequest(BaseModel):
    """
    AuditCatchRequest - 审核操作
    """

    action: int = Field(..., description="1 通过 / 2 拒绝")
    reason: Optional[str] = Field(default=None, description="拒绝原因")

    @field_validator("action")
    @classmethod
    def validate_action(cls, value: int) -> int:
        """
        validate_action - 校验审核动作
        """
        # 判断动作合法
        if value not in (AUDIT_ACTION_APPROVE, AUDIT_ACTION_REJECT):
            raise ValueError("审核动作不合法，应为 1(通过) 或 2(拒绝)")
        return value

    @field_validator("reason")
    @classmethod
    def empty_reason_to_none(cls, value: Optional[str]) -> Optional[str]:
        """
        empty_reason_to_none - 空原因转 None
        """
        # 判断空串
        if value is None:
            return None
        text = value.strip()
        # 判断裁剪后为空
        if not text:
            return None
        # 判断原因长度
        if len(text) > 200:
            raise ValueError("拒绝原因不能超过200个字符")
        return text

    @model_validator(mode="after")
    def require_reason_when_reject(self):
        """
        require_reason_when_reject - 拒绝时必须填写原因
        """
        # 拒绝必须有原因
        if self.action == AUDIT_ACTION_REJECT and not self.reason:
            raise ValueError("拒绝时请填写拒绝原因")
        return self


class UpdateUserStatusRequest(BaseModel):
    """
    UpdateUserStatusRequest - 启用/禁用用户
    """

    status: int = Field(..., description="1 正常 / 0 禁用")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: int) -> int:
        """
        validate_status - 校验用户状态
        """
        # 判断状态合法
        if value not in (USER_STATUS_NORMAL, USER_STATUS_DISABLED):
            raise ValueError("状态不合法，应为 1(正常) 或 0(禁用)")
        return value


class UpdateSettingsRequest(BaseModel):
    """
    UpdateSettingsRequest - 配置中心更新（字段均可选）
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    site_name: Optional[str] = Field(default=None, description="站点名称")
    audit_tip: Optional[str] = Field(default=None, description="审核提示")
    reject_reason_presets: Optional[Union[List[str], str]] = Field(
        default=None, description="拒绝原因预设"
    )
    list_per_page: Optional[int] = Field(default=None, description="每页条数")
    launch_date: Optional[str] = Field(default=None, description="上线日 YYYY-MM-DD")

    @field_validator("site_name")
    @classmethod
    def validate_site_name(cls, value: Optional[str]) -> Optional[str]:
        """
        validate_site_name - 站点名非空且长度限制
        """
        # 判断未传
        if value is None:
            return None
        # 判断站点名
        if not value:
            raise ValueError("站点名称不能为空")
        # 判断长度
        if len(value) > 40:
            raise ValueError("站点名称不能超过40个字符")
        return value

    @field_validator("audit_tip")
    @classmethod
    def validate_audit_tip(cls, value: Optional[str]) -> Optional[str]:
        """
        validate_audit_tip - 审核提示长度
        """
        # 判断未传
        if value is None:
            return None
        # 判断长度
        if len(value) > 300:
            raise ValueError("审核提示不能超过300个字符")
        return value

    @field_validator("list_per_page")
    @classmethod
    def validate_list_per_page(cls, value: Optional[int]) -> Optional[int]:
        """
        validate_list_per_page - 每页条数区间
        """
        # 判断未传
        if value is None:
            return None
        # 判断范围
        if value < 5 or value > 100:
            raise ValueError("每页条数须在 5–100 之间")
        return value

    @field_validator("launch_date")
    @classmethod
    def validate_launch_date(cls, value: Optional[str]) -> Optional[str]:
        """
        validate_launch_date - 上线日须为 YYYY-MM-DD
        """
        # 判断未传
        if value is None:
            return None
        # 判断空串
        if not value:
            raise ValueError("上线日不能为空")
        date_text = value[:10]
        try:
            date_type.fromisoformat(date_text)
        except ValueError as error:
            raise ValueError("上线日须为 YYYY-MM-DD") from error
        return date_text

    @field_validator("reject_reason_presets")
    @classmethod
    def normalize_presets(cls, value: Optional[Union[List[str], str]]):
        """
        normalize_presets - 字符串按行拆成列表
        """
        # 判断未传
        if value is None:
            return None
        # 判断是否字符串
        if isinstance(value, str):
            return [line.strip() for line in value.split("\n") if line.strip()]
        # 判断是否列表
        if not isinstance(value, list):
            raise ValueError("拒绝原因预设须为列表")
        return [str(item).strip() for item in value if str(item).strip()]


class AdminChangePasswordRequest(BaseModel):
    """
    AdminChangePasswordRequest - 管理员改密
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
