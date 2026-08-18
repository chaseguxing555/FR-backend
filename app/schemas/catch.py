"""
@file catch.py
@description 鱼获相关 Pydantic 模型
@module app.schemas.catch
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.0.0
"""

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.constants import (
    BAIT_MAX_LENGTH,
    DESCRIPTION_MAX_LENGTH,
    FISHING_METHOD_LIST,
    LOCATION_DETAIL_MAX_LENGTH,
    UPLOAD_METHOD_SPECIES_MAP,
    WEIGHT_MAX,
    WEIGHT_MIN,
)


class CreateCatchRequest(BaseModel):
    """
    CreateCatchRequest - 上传鱼获请求体
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    fishing_method: str = Field(..., description="钓法")
    fish_species: str = Field(..., description="鱼种")
    weight: float = Field(..., description="重量（公斤）")
    province: str = Field(..., description="省份")
    city: str = Field(..., description="城市")
    location_detail: Optional[str] = Field(default=None, description="具体钓点")
    bait: str = Field(..., description="饵料")
    caught_at: str = Field(..., description="钓获日期 YYYY-MM-DD")
    image_urls: List[str] = Field(..., description="照片 URL 列表")
    video_url: Optional[str] = Field(default=None, description="视频 URL")
    description: Optional[str] = Field(default=None, description="备注")

    @field_validator("fishing_method")
    @classmethod
    def validate_method(cls, value: str) -> str:
        """
        validate_method - 校验钓法是否合法
        """
        # 判断钓法是否在列表中
        if value not in FISHING_METHOD_LIST:
            raise ValueError("钓法不合法")
        return value

    @field_validator("fish_species")
    @classmethod
    def validate_species(cls, value: str, info) -> str:
        """
        validate_species - 校验鱼种属于当前钓法
        """
        method_text = info.data.get("fishing_method")
        # 判断钓法是否已通过校验
        if method_text not in UPLOAD_METHOD_SPECIES_MAP:
            raise ValueError("请先选择合法钓法")
        allowed_species = UPLOAD_METHOD_SPECIES_MAP[method_text]
        # 判断鱼种是否属于该钓法（含可上传但不进榜的鱼种）
        if value not in allowed_species:
            raise ValueError("该鱼种不属于所选钓法")
        return value

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: float) -> float:
        """
        validate_weight - 校验重量区间
        """
        # 判断重量是否大于 0
        if value <= WEIGHT_MIN:
            raise ValueError("重量必须大于0")
        # 判断重量上限
        if value > WEIGHT_MAX:
            raise ValueError(f"重量不能超过{WEIGHT_MAX}kg")
        return round(float(value), 1)

    @field_validator("province")
    @classmethod
    def validate_province(cls, value: str) -> str:
        """
        validate_province - 校验省份非空
        """
        # 判断省份是否填写
        if not value:
            raise ValueError("省份不能为空")
        return value

    @field_validator("city")
    @classmethod
    def validate_city(cls, value: str) -> str:
        """
        validate_city - 校验城市非空
        """
        # 判断城市是否填写
        if not value:
            raise ValueError("城市不能为空")
        return value

    @field_validator("location_detail")
    @classmethod
    def validate_location_detail(cls, value: Optional[str]) -> Optional[str]:
        """
        validate_location_detail - 校验具体钓点长度
        """
        # 判断空串
        if value is None or value == "":
            return None
        # 判断具体钓点长度
        if len(value) > LOCATION_DETAIL_MAX_LENGTH:
            raise ValueError(f"具体钓点不能超过{LOCATION_DETAIL_MAX_LENGTH}个字符")
        return value

    @field_validator("bait")
    @classmethod
    def validate_bait(cls, value: str) -> str:
        """
        validate_bait - 校验饵料必填与长度
        """
        bait_text = (value or "").strip()
        # 判断饵料是否填写
        if not bait_text:
            raise ValueError("请填写饵料")
        # 判断饵料长度
        if len(bait_text) > BAIT_MAX_LENGTH:
            raise ValueError(f"饵料不能超过{BAIT_MAX_LENGTH}个字符")
        return bait_text

    @field_validator("caught_at")
    @classmethod
    def validate_caught_at(cls, value: str) -> str:
        """
        validate_caught_at - 校验日期格式且不晚于今天
        """
        # 判断钓获日期是否填写
        if not value:
            raise ValueError("钓获日期不能为空")
        try:
            caught_date = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("钓获日期格式不正确，应为 YYYY-MM-DD") from exc
        # 判断日期不能晚于今天
        if caught_date > date.today():
            raise ValueError("钓获日期不能晚于今天")
        return value

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        """
        validate_description - 校验备注长度
        """
        # 判断空串
        if value is None or value == "":
            return None
        # 判断备注长度
        if len(value) > DESCRIPTION_MAX_LENGTH:
            raise ValueError(f"备注不能超过{DESCRIPTION_MAX_LENGTH}个字符")
        return value

    @field_validator("image_urls")
    @classmethod
    def validate_images(cls, value: List[str]) -> List[str]:
        """
        validate_images - 校验照片列表
        """
        # 判断照片是否为列表且至少 1 张
        if not isinstance(value, list) or len(value) < 1:
            raise ValueError("至少上传1张照片")
        cleaned = [item.strip() for item in value if item and str(item).strip()]
        # 判断清洗后至少 1 张
        if not cleaned:
            raise ValueError("至少上传1张照片")
        # 判断照片数量不超过 3 张
        if len(cleaned) > 3:
            raise ValueError("最多上传3张照片")
        return cleaned

    @field_validator("video_url")
    @classmethod
    def validate_video_url(cls, value: Optional[str]) -> Optional[str]:
        """
        validate_video_url - 校验可选视频地址
        """
        # 判断空串
        if value is None or value == "":
            return None
        video_text = value.strip()
        # 判断必须为站内上传路径
        if not video_text.startswith("/uploads/"):
            raise ValueError("视频地址不合法")
        return video_text
