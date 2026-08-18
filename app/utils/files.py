"""
@file files.py
@description 上传文件名安全处理
@module app.utils.files
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.0.0
"""

import re


def secure_filename(filename: str) -> str:
    """
    secure_filename - 清洗上传文件名

    @description 去掉路径分隔与危险字符，仅保留安全文件名

    @param {str} filename - 原始文件名

    @returns {str} 安全文件名
    """
    # 去掉目录部分
    name_text = filename.replace("\\", "/").split("/")[-1]
    # 仅保留字母数字、点、下划线、短横线
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", name_text).strip("._")
    # 判断清洗后为空
    if not cleaned:
        return "file"
    return cleaned
