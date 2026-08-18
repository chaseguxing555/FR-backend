"""
@file validators.py
@description 请求参数校验工具
@module app.utils.validators
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-11
@version 1.0.0
"""

import re
from datetime import date, datetime

from app.constants import (
    DESCRIPTION_MAX_LENGTH,
    FISH_SPECIES_LIST,
    LOCATION_DETAIL_MAX_LENGTH,
    NICKNAME_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    WEIGHT_MAX,
    WEIGHT_MIN,
)


# 手机号正则：1 开头的 11 位数字
PHONE_PATTERN = re.compile(r"^1\d{10}$")


def validate_phone(phone):
    """
    validate_phone - 校验手机号格式

    @description 校验是否为 1 开头的 11 位数字

    @param {str} phone - 手机号

    @returns {str|None} 校验失败返回错误信息，成功返回 None
    """
    # 判断手机号是否为空
    if not phone:
        return "手机号不能为空"
    # 判断手机号格式
    if not PHONE_PATTERN.match(str(phone)):
        return "手机号格式不正确"
    return None


def validate_password(password):
    """
    validate_password - 校验密码长度

    @description 密码长度须 ≥ 6 位

    @param {str} password - 密码

    @returns {str|None} 校验失败返回错误信息，成功返回 None
    """
    # 判断密码是否为空
    if not password:
        return "密码不能为空"
    # 判断密码长度
    if len(password) < PASSWORD_MIN_LENGTH:
        return f"密码长度不能少于{PASSWORD_MIN_LENGTH}位"
    return None


def validate_nickname(nickname):
    """
    validate_nickname - 校验昵称

    @description 昵称必填且长度 ≤ 20

    @param {str} nickname - 昵称

    @returns {str|None} 校验失败返回错误信息，成功返回 None
    """
    # 判断昵称是否为空
    if not nickname:
        return "昵称不能为空"
    # 判断昵称长度
    if len(nickname) > NICKNAME_MAX_LENGTH:
        return f"昵称不能超过{NICKNAME_MAX_LENGTH}个字符"
    return None


def validate_catch_payload(payload):
    """
    validate_catch_payload - 校验上传鱼获请求体

    @description 按 PRD FR-04 校验鱼种、重量、省市、日期、照片、备注等字段

    @param {dict} payload - 上传请求 JSON

    @returns {str|None} 校验失败返回错误信息，成功返回 None
    """
    # 判断请求体是否存在
    if not payload:
        return "请求体不能为空"

    fish_species = payload.get("fish_species")
    # 判断鱼种是否合法
    if fish_species not in FISH_SPECIES_LIST:
        return "鱼种不合法"

    weight = payload.get("weight")
    # 判断重量是否为数字且在合法区间
    try:
        weight_value = float(weight)
    except (TypeError, ValueError):
        return "重量必须为数字"
    # 判断重量是否大于 0
    if weight_value <= WEIGHT_MIN:
        return "重量必须大于0"
    # 判断重量是否超过上限
    if weight_value > WEIGHT_MAX:
        return f"重量不能超过{WEIGHT_MAX}kg"

    province = payload.get("province")
    # 判断省份是否填写
    if not province:
        return "省份不能为空"

    city = payload.get("city")
    # 判断城市是否填写
    if not city:
        return "城市不能为空"

    location_detail = payload.get("location_detail")
    # 判断具体钓点长度
    if location_detail and len(location_detail) > LOCATION_DETAIL_MAX_LENGTH:
        return f"具体钓点不能超过{LOCATION_DETAIL_MAX_LENGTH}个字符"

    caught_at = payload.get("caught_at")
    # 判断钓获日期是否填写
    if not caught_at:
        return "钓获日期不能为空"
    # 解析日期并判断是否晚于今天
    try:
        caught_date = datetime.strptime(caught_at, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return "钓获日期格式不正确，应为 YYYY-MM-DD"
    # 判断日期不能晚于今天
    if caught_date > date.today():
        return "钓获日期不能晚于今天"

    image_urls = payload.get("image_urls")
    # 判断照片是否为列表且至少 1 张
    if not isinstance(image_urls, list) or len(image_urls) < 1:
        return "至少上传1张照片"
    # 判断照片数量不超过 3 张
    if len(image_urls) > 3:
        return "最多上传3张照片"

    description = payload.get("description")
    # 判断备注长度
    if description and len(description) > DESCRIPTION_MAX_LENGTH:
        return f"备注不能超过{DESCRIPTION_MAX_LENGTH}个字符"

    return None
