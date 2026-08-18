"""
@file upload.py
@description 图片 / 视频上传接口
@module app.api.upload
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-13
@version 2.1.0
"""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, UploadFile

from app.config import settings
from app.deps import get_current_user
from app.models.user import User
from app.utils.files import secure_filename
from app.utils.response import raise_error, success


router = APIRouter(prefix="/api/upload", tags=["upload"])


def is_allowed_image(filename: str) -> bool:
    """
    is_allowed_image - 判断图片扩展名是否允许

    @param {str} filename - 原始文件名

    @returns {bool}
    """
    # 判断文件名是否包含扩展名
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in settings.ALLOWED_EXTENSIONS


def is_allowed_video(filename: str) -> bool:
    """
    is_allowed_video - 判断视频扩展名是否允许

    @param {str} filename - 原始文件名

    @returns {bool}
    """
    # 判断文件名是否包含扩展名
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in settings.ALLOWED_VIDEO_EXTENSIONS


async def _save_upload_file(file: UploadFile, max_bytes: int, type_label: str) -> str:
    """
    _save_upload_file - 保存上传文件并返回访问路径

    @param {UploadFile} file - 上传文件
    @param {int} max_bytes - 大小上限
    @param {str} type_label - 类型文案（用于报错）

    @returns {str} /uploads/... 路径
    """
    original_name = secure_filename(file.filename)
    extension = original_name.rsplit(".", 1)[1].lower()
    date_folder = datetime.utcnow().strftime("%Y%m%d")
    save_dir = os.path.join(settings.UPLOAD_FOLDER, date_folder)
    os.makedirs(save_dir, exist_ok=True)

    saved_filename = f"{uuid.uuid4().hex}.{extension}"
    save_path = os.path.join(save_dir, saved_filename)

    content = await file.read()
    # 判断大小
    if len(content) > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise_error(f"{type_label}不能超过 {max_mb}MB")

    with open(save_path, "wb") as output_file:
        output_file.write(content)

    return f"/uploads/{date_folder}/{saved_filename}"


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    upload_image - 上传图片

    @description 登录用户上传单张 jpg/png，返回可访问 URL
    """
    # 判断文件名
    if not file.filename:
        raise_error("请选择要上传的图片")
    # 判断扩展名
    if not is_allowed_image(file.filename):
        raise_error("仅支持 jpg/png 格式图片")

    image_url = await _save_upload_file(
        file,
        settings.MAX_CONTENT_LENGTH,
        "图片",
    )
    return success({"url": image_url}, message="上传成功")


@router.post("/video")
async def upload_video(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """
    upload_video - 上传视频

    @description 登录用户上传单个 mp4/webm/mov，返回可访问 URL
    """
    # 判断文件名
    if not file.filename:
        raise_error("请选择要上传的视频")
    # 判断扩展名
    if not is_allowed_video(file.filename):
        raise_error("仅支持 mp4/webm/mov 格式视频")

    video_url = await _save_upload_file(
        file,
        settings.MAX_VIDEO_CONTENT_LENGTH,
        "视频",
    )
    return success({"url": video_url}, message="上传成功")
