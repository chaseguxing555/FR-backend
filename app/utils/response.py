"""
@file response.py
@description 统一 API 响应与业务异常（兼容原 {code,message,data}）
@module app.utils.response
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.0.0
"""

from typing import Any, Optional


class AppError(Exception):
    """
    业务错误：由全局异常处理器转为 JSON
    """

    def __init__(self, message="error", code=1, http_status=400):
        """
        @param {str} message - 错误说明
        @param {int} code - 业务错误码
        @param {int} http_status - HTTP 状态码
        """
        self.message = message
        self.code = code
        self.http_status = http_status
        super().__init__(message)


def success(data: Any = None, message: str = "ok"):
    """
    success - 成功响应体

    @param {*} [data=None] - 业务数据
    @param {str} [message="ok"] - 提示

    @returns {dict} { code, message, data }
    """
    return {"code": 0, "message": message, "data": data}


def error(message: str = "error", code: int = 1, http_status: int = 400):
    """
    error - 构造业务错误对象（配合 raise 使用）

    @param {str} message - 错误说明
    @param {int} code - 业务码
    @param {int} http_status - HTTP 状态

    @returns {AppError}
    """
    return AppError(message=message, code=code, http_status=http_status)


def raise_error(message: str = "error", code: int = 1, http_status: int = 400):
    """
    raise_error - 直接抛出业务错误

    @param {str} message - 错误说明
    @param {int} code - 业务码
    @param {int} http_status - HTTP 状态
    """
    raise AppError(message=message, code=code, http_status=http_status)
