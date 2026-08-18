"""
@file scheduler.py
@description 奖励结算定时任务：每月 1 日结上月，每年 1 月 1 日结上年（无第三方依赖）
@module app.scheduler
@author fishing-ranking
@created 2026-08-14
@updated 2026-08-14
@version 1.1.0
"""

import logging
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.database import SessionLocal
from app.services.reward_settlement import settle_previous_month, settle_previous_year


logger = logging.getLogger("fishing-ranking.scheduler")

# 上海时区
_TZ_SHANGHAI = ZoneInfo("Asia/Shanghai")

# 后台线程与停止信号
_worker_thread: threading.Thread | None = None
_stop_event = threading.Event()
# 已触发过的任务标记，避免同一分钟重复执行
_fired_keys: set[str] = set()
_lock = threading.Lock()


def _now_shanghai() -> datetime:
    """
    _now_shanghai - 当前上海时间
    """
    return datetime.now(_TZ_SHANGHAI)


def _run_month_settle():
    """
    _run_month_settle - 执行上月结算
    """
    database = SessionLocal()
    try:
        result = settle_previous_month(database, force=False)
        logger.info(
            "月榜结算完成 period=%s awards=%s skipped=%s",
            result.get("period_key"),
            len(result.get("awards") or []),
            len(result.get("skipped") or []),
        )
    except Exception:
        logger.exception("月榜结算失败")
        database.rollback()
    finally:
        database.close()


def _run_year_settle():
    """
    _run_year_settle - 执行上年结算
    """
    database = SessionLocal()
    try:
        result = settle_previous_year(database, force=False)
        logger.info(
            "年榜结算完成 period=%s awards=%s skipped=%s",
            result.get("period_key"),
            len(result.get("awards") or []),
            len(result.get("skipped") or []),
        )
    except Exception:
        logger.exception("年榜结算失败")
        database.rollback()
    finally:
        database.close()


def _maybe_fire_jobs(now_time: datetime):
    """
    _maybe_fire_jobs - 按上海时间触发结算

    @description 每月 1 日 01:10 结上月；每年 1 月 1 日 02:10 结上年
    """
    # 判断每月 1 日 01:10
    if now_time.day == 1 and now_time.hour == 1 and now_time.minute == 10:
        fire_key = f"month:{now_time.strftime('%Y-%m-%d')}"
        with _lock:
            # 判断本分钟是否已跑过
            if fire_key not in _fired_keys:
                _fired_keys.add(fire_key)
                threading.Thread(
                    target=_run_month_settle,
                    name="reward-month-settle",
                    daemon=True,
                ).start()

    # 判断每年 1 月 1 日 02:10
    if (
        now_time.month == 1
        and now_time.day == 1
        and now_time.hour == 2
        and now_time.minute == 10
    ):
        fire_key = f"year:{now_time.strftime('%Y')}"
        with _lock:
            # 判断本年是否已跑过
            if fire_key not in _fired_keys:
                _fired_keys.add(fire_key)
                threading.Thread(
                    target=_run_year_settle,
                    name="reward-year-settle",
                    daemon=True,
                ).start()


def _worker_loop():
    """
    _worker_loop - 每 20 秒检查一次是否到点
    """
    logger.info("奖励结算定时循环已启动")
    while not _stop_event.is_set():
        try:
            _maybe_fire_jobs(_now_shanghai())
        except Exception:
            logger.exception("定时检查异常")
        _stop_event.wait(20)
    logger.info("奖励结算定时循环已退出")


def start_scheduler():
    """
    start_scheduler - 启动后台定时线程
    """
    global _worker_thread
    # 判断已在运行
    if _worker_thread is not None and _worker_thread.is_alive():
        return
    _stop_event.clear()
    _worker_thread = threading.Thread(
        target=_worker_loop,
        name="reward-scheduler",
        daemon=True,
    )
    _worker_thread.start()
    logger.info("奖励结算定时任务已启动（每月1日01:10 / 每年1月1日02:10 Asia/Shanghai）")


def stop_scheduler():
    """
    stop_scheduler - 停止后台定时线程
    """
    global _worker_thread
    _stop_event.set()
    # 判断线程存在则等待退出
    if _worker_thread is not None and _worker_thread.is_alive():
        _worker_thread.join(timeout=2)
    _worker_thread = None
    logger.info("奖励结算定时任务已停止")
