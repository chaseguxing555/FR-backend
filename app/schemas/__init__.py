"""
@file __init__.py
@description Pydantic 请求/响应模型包
@module app.schemas
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.0.0
"""

from app.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    UpdateAvatarRequest,
    UpdateProfileRequest,
)
from app.schemas.catch import CreateCatchRequest
from app.schemas.admin import (
    AdminChangePasswordRequest,
    AdminLoginRequest,
    AuditCatchRequest,
    UpdateSettingsRequest,
    UpdateUserStatusRequest,
)

__all__ = [
    "RegisterRequest",
    "LoginRequest",
    "UpdateProfileRequest",
    "UpdateAvatarRequest",
    "ChangePasswordRequest",
    "CreateCatchRequest",
    "AdminLoginRequest",
    "AuditCatchRequest",
    "UpdateUserStatusRequest",
    "UpdateSettingsRequest",
    "AdminChangePasswordRequest",
]
