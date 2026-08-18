"""
@file security.py
@description 密码与 JWT 工具
@module app.utils.security
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import bcrypt
import jwt

from app.config import settings


def hash_password(plain_password):
    """
    hash_password - 对明文密码进行 bcrypt 加密

    @param {str} plain_password - 明文密码

    @returns {str} 加密后的密码字符串
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_bytes.decode("utf-8")


def verify_password(plain_password, hashed_password):
    """
    verify_password - 校验明文密码与哈希是否匹配

    @param {str} plain_password - 明文密码
    @param {str} hashed_password - 库中存储的哈希密码

    @returns {bool} 匹配返回 True，否则 False
    """
    plain_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_bytes, hashed_bytes)


def create_access_token(identity: str, role: str, expires_delta: Optional[timedelta] = None):
    """
    create_access_token - 签发 JWT

    @description sub=identity（如 user:1 / admin:1），附加 role

    @param {str} identity - 主体标识
    @param {str} role - user / admin
    @param {timedelta} [expires_delta] - 过期时间

    @returns {str} JWT 字符串
    """
    expire = datetime.utcnow() + (expires_delta or settings.JWT_ACCESS_TOKEN_EXPIRES)
    payload = {
        "sub": identity,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    decode_access_token - 解析 JWT

    @param {str} token - Bearer Token

    @returns {dict} payload

    @throws {jwt.PyJWTError} 无效或过期
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
