"""
@file logging_setup.py
@description 应用文件日志：ERROR 及以上写入 instance/app.log
@module app.utils.logging_setup
@author fishing-ranking
@created 2026-08-13
@updated 2026-08-13
@version 1.1.0
"""

import logging
import os
from logging.handlers import RotatingFileHandler

from app.config import BASE_DIR


# 日志文件路径
APP_LOG_PATH = os.path.join(BASE_DIR, "instance", "app.log")


def setup_file_logging(logger_name: str = "fishing_ranking"):
    """
    setup_file_logging - 挂载滚动文件日志

    @param {str} [logger_name] - logger 名称

    @returns {Logger} logger 实例
    """
    os.makedirs(os.path.dirname(APP_LOG_PATH), exist_ok=True)
    app_logger = logging.getLogger(logger_name)

    # 判断是否已挂过同名 handler
    for handler in app_logger.handlers:
        # 判断是否为指向 app.log 的文件 handler
        if getattr(handler, "baseFilename", None) == APP_LOG_PATH:
            return app_logger

    file_handler = RotatingFileHandler(
        APP_LOG_PATH,
        maxBytes=2 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    )
    app_logger.addHandler(file_handler)
    app_logger.setLevel(logging.INFO)
    return app_logger


def read_log_tail(line_count=200):
    """
    read_log_tail - 读取日志文件尾部行

    @param {int} [line_count=200] - 行数

    @returns {list[str]} 日志行
    """
    # 判断文件是否存在
    if not os.path.isfile(APP_LOG_PATH):
        return []

    with open(APP_LOG_PATH, "r", encoding="utf-8", errors="replace") as log_file:
        lines = log_file.readlines()

    # 判断行数是否超过限制
    if line_count < 1:
        line_count = 200
    return [line.rstrip("\n") for line in lines[-line_count:]]
