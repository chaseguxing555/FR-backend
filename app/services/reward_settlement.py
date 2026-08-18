"""
@file reward_settlement.py
@description 月榜 / 年榜奖励自动结算与通知发放
@module app.services.reward_settlement
@author fishing-ranking
@created 2026-08-14
@updated 2026-08-14
@version 1.0.0
"""

from calendar import monthrange
from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.constants import (
    CATCH_STATUS_APPROVED,
    FISHING_METHOD_LIST,
    MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG,
    NOTIFICATION_TYPE_REWARD_MONTHLY,
    NOTIFICATION_TYPE_REWARD_YEARLY,
    REWARD_AWARD_META,
    REWARD_AWARD_MONTHLY_METHOD,
    REWARD_AWARD_MONTHLY_OVERALL,
    REWARD_AWARD_YEARLY_METHOD,
    REWARD_AWARD_YEARLY_OVERALL,
    REWARD_PERIOD_MONTH,
    REWARD_PERIOD_YEAR,
)
from app.models.catch import Catch
from app.models.notification import Notification
from app.models.reward import RewardAward


def previous_month(reference: Optional[date] = None):
    """
    previous_month - 取上一个月的年月

    @param {date} [reference] - 参考日，默认今天
    @returns {tuple} (year, month)
    """
    today = reference or date.today()
    # 判断是否 1 月
    if today.month == 1:
        return today.year - 1, 12
    return today.year, today.month - 1


def previous_year(reference: Optional[date] = None):
    """
    previous_year - 取上一年年份

    @param {date} [reference] - 参考日，默认今天
    @returns {int} year
    """
    today = reference or date.today()
    return today.year - 1


def _month_bounds(year: int, month: int):
    """
    _month_bounds - 自然月半开区间 [start, end)

    @returns {tuple} (start_date, end_date)
    """
    start_date = date(year, month, 1)
    # 判断是否 12 月
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return start_date, end_date


def _year_bounds(year: int):
    """
    _year_bounds - 自然年半开区间 [start, end)

    @returns {tuple} (start_date, end_date)
    """
    return date(year, 1, 1), date(year + 1, 1, 1)


def _format_period_label(period_type: str, period_key: str) -> str:
    """
    _format_period_label - 周期展示文案
    """
    # 判断月榜
    if period_type == REWARD_PERIOD_MONTH:
        year_text, month_text = period_key.split("-")
        return f"{year_text}年{int(month_text)}月"
    return f"{period_key}年"


def _build_title(award_type: str, period_type: str, period_key: str, method: str = "") -> str:
    """
    _build_title - 生成奖项标题
    """
    meta = REWARD_AWARD_META[award_type]
    period_label = _format_period_label(period_type, period_key)
    return meta["title_template"].format(period=period_label, method=method)


def _monthly_species_filter():
    """
    _monthly_species_filter - 月榜热门鱼种 + 最低重量门槛条件
    """
    condition_list = []
    for species_name, min_weight in MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG.items():
        condition_list.append(
            and_(
                Catch.fish_species == species_name,
                Catch.weight >= min_weight,
            )
        )
    return or_(*condition_list)


def find_top_catch(
    db: Session,
    start_date: date,
    end_date: date,
    fishing_method: Optional[str] = None,
    apply_monthly_rules: bool = False,
) -> Optional[Catch]:
    """
    find_top_catch - 区间内重量最大的已通过鱼获

    @param {Session} db - 会话
    @param {date} start_date - 含
    @param {date} end_date - 不含
    @param {str} [fishing_method] - 限定钓法
    @param {bool} [apply_monthly_rules=False] - 是否套用月榜热门门槛
    @returns {Catch|None}
    """
    query = db.query(Catch).filter(
        Catch.status == CATCH_STATUS_APPROVED,
        Catch.caught_at >= start_date,
        Catch.caught_at < end_date,
    )
    # 判断限定钓法
    if fishing_method:
        query = query.filter(Catch.fishing_method == fishing_method)
    # 判断月榜规则
    if apply_monthly_rules:
        query = query.filter(_monthly_species_filter())

    return query.order_by(Catch.weight.desc(), Catch.created_at.desc()).first()


def _get_existing_award(
    db: Session,
    period_type: str,
    period_key: str,
    award_type: str,
    fishing_method: str = "",
) -> Optional[RewardAward]:
    """
    _get_existing_award - 查询是否已结算
    """
    return (
        db.query(RewardAward)
        .filter_by(
            period_type=period_type,
            period_key=period_key,
            award_type=award_type,
            fishing_method=fishing_method or "",
        )
        .first()
    )


def _create_award_and_notify(
    db: Session,
    *,
    period_type: str,
    period_key: str,
    award_type: str,
    catch: Catch,
    fishing_method: str = "",
    force: bool = False,
) -> Optional[RewardAward]:
    """
    _create_award_and_notify - 写入奖项并发站内通知（幂等）

    @returns {RewardAward|None} 新建或已存在的奖项；无冠军时 None
    """
    method_key = fishing_method or ""
    existing = _get_existing_award(db, period_type, period_key, award_type, method_key)
    # 判断已结算且不强制
    if existing is not None and not force:
        # 判断漏发通知则补发
        if existing.notified == 0:
            _send_reward_notification(db, existing)
            existing.notified = 1
            db.add(existing)
        return existing

    # 判断强制重算：删除旧记录后重建
    if existing is not None and force:
        db.delete(existing)
        db.flush()

    title = _build_title(award_type, period_type, period_key, method_key)
    prizes = REWARD_AWARD_META[award_type]["prizes"]
    award = RewardAward(
        period_type=period_type,
        period_key=period_key,
        award_type=award_type,
        fishing_method=method_key,
        user_id=catch.user_id,
        catch_id=catch.id,
        weight=catch.weight,
        fish_species=catch.fish_species,
        title=title,
        prizes=prizes,
        notified=0,
    )
    db.add(award)
    db.flush()
    _send_reward_notification(db, award)
    award.notified = 1
    db.add(award)
    return award


def _send_reward_notification(db: Session, award: RewardAward):
    """
    _send_reward_notification - 向冠军用户发站内消息
    """
    # 判断月榜 / 年榜消息类型
    if award.period_type == REWARD_PERIOD_MONTH:
        notice_type = NOTIFICATION_TYPE_REWARD_MONTHLY
    else:
        notice_type = NOTIFICATION_TYPE_REWARD_YEARLY

    weight_text = f"{float(award.weight)}kg"
    content = (
        f"恭喜你荣获「{award.title}」！"
        f"鱼种 {award.fish_species}，重量 {weight_text}。"
        f"奖励：{award.prizes}。"
    )
    db.add(
        Notification(
            user_id=award.user_id,
            type=notice_type,
            title=award.title,
            content=content,
            catch_id=award.catch_id,
            is_read=0,
        )
    )


def settle_month(
    db: Session,
    year: int,
    month: int,
    force: bool = False,
) -> dict:
    """
    settle_month - 结算指定月份：各钓法月冠军 + 月榜总冠军，并发通知

    @param {Session} db - 会话
    @param {int} year - 年
    @param {int} month - 月
    @param {bool} [force=False] - 是否强制重算
    @returns {dict} 结算结果摘要
    """
    # 判断月份合法
    if month < 1 or month > 12:
        raise ValueError("月份不合法")
    # 判断日期天数合法（顺带校验年月）
    monthrange(year, month)

    period_key = f"{year:04d}-{month:02d}"
    start_date, end_date = _month_bounds(year, month)
    created_list: List[RewardAward] = []
    skipped_list = []

    # 各钓法月冠军
    for method_name in FISHING_METHOD_LIST:
        top_catch = find_top_catch(
            db,
            start_date,
            end_date,
            fishing_method=method_name,
            apply_monthly_rules=True,
        )
        # 判断无冠军
        if top_catch is None:
            skipped_list.append(
                {
                    "award_type": REWARD_AWARD_MONTHLY_METHOD,
                    "fishing_method": method_name,
                    "reason": "无达标记录",
                }
            )
            continue
        award = _create_award_and_notify(
            db,
            period_type=REWARD_PERIOD_MONTH,
            period_key=period_key,
            award_type=REWARD_AWARD_MONTHLY_METHOD,
            catch=top_catch,
            fishing_method=method_name,
            force=force,
        )
        # 判断写入成功
        if award is not None:
            created_list.append(award)

    # 月榜总冠军（全钓法最重）
    overall_catch = find_top_catch(
        db,
        start_date,
        end_date,
        fishing_method=None,
        apply_monthly_rules=True,
    )
    # 判断有总冠军
    if overall_catch is None:
        skipped_list.append(
            {
                "award_type": REWARD_AWARD_MONTHLY_OVERALL,
                "fishing_method": None,
                "reason": "无达标记录",
            }
        )
    else:
        award = _create_award_and_notify(
            db,
            period_type=REWARD_PERIOD_MONTH,
            period_key=period_key,
            award_type=REWARD_AWARD_MONTHLY_OVERALL,
            catch=overall_catch,
            fishing_method="",
            force=force,
        )
        # 判断写入成功
        if award is not None:
            created_list.append(award)

    db.commit()
    return {
        "period_type": REWARD_PERIOD_MONTH,
        "period_key": period_key,
        "awards": [item.to_dict() for item in created_list],
        "skipped": skipped_list,
        "settled_at": datetime.utcnow().isoformat(),
    }


def settle_year(db: Session, year: int, force: bool = False) -> dict:
    """
    settle_year - 结算指定年份：各钓法年度总冠军 + 年度全榜总冠军，并发通知

    @param {Session} db - 会话
    @param {int} year - 年
    @param {bool} [force=False] - 是否强制重算
    @returns {dict} 结算结果摘要
    """
    period_key = f"{year:04d}"
    start_date, end_date = _year_bounds(year)
    created_list: List[RewardAward] = []
    skipped_list = []

    # 各钓法年度总冠军
    for method_name in FISHING_METHOD_LIST:
        top_catch = find_top_catch(
            db,
            start_date,
            end_date,
            fishing_method=method_name,
            apply_monthly_rules=False,
        )
        # 判断无冠军
        if top_catch is None:
            skipped_list.append(
                {
                    "award_type": REWARD_AWARD_YEARLY_METHOD,
                    "fishing_method": method_name,
                    "reason": "无达标记录",
                }
            )
            continue
        award = _create_award_and_notify(
            db,
            period_type=REWARD_PERIOD_YEAR,
            period_key=period_key,
            award_type=REWARD_AWARD_YEARLY_METHOD,
            catch=top_catch,
            fishing_method=method_name,
            force=force,
        )
        # 判断写入成功
        if award is not None:
            created_list.append(award)

    # 年度全榜总冠军
    overall_catch = find_top_catch(
        db,
        start_date,
        end_date,
        fishing_method=None,
        apply_monthly_rules=False,
    )
    # 判断有总冠军
    if overall_catch is None:
        skipped_list.append(
            {
                "award_type": REWARD_AWARD_YEARLY_OVERALL,
                "fishing_method": None,
                "reason": "无达标记录",
            }
        )
    else:
        award = _create_award_and_notify(
            db,
            period_type=REWARD_PERIOD_YEAR,
            period_key=period_key,
            award_type=REWARD_AWARD_YEARLY_OVERALL,
            catch=overall_catch,
            fishing_method="",
            force=force,
        )
        # 判断写入成功
        if award is not None:
            created_list.append(award)

    # 名人堂路径一：年度全榜 + 三大钓法总冠军（同年不重复占位）
    from app.services.hall_induction import evaluate_hall_of_fame

    hall_result = evaluate_hall_of_fame(
        db,
        year=year,
        notify=True,
        include_annual=True,
        do_commit=False,
    )

    db.commit()
    return {
        "period_type": REWARD_PERIOD_YEAR,
        "period_key": period_key,
        "awards": [item.to_dict() for item in created_list],
        "skipped": skipped_list,
        "hall": hall_result,
        "settled_at": datetime.utcnow().isoformat(),
    }


def settle_previous_month(db: Session, force: bool = False) -> dict:
    """
    settle_previous_month - 结算上个月（定时任务入口）
    """
    year_number, month_number = previous_month()
    return settle_month(db, year_number, month_number, force=force)


def settle_previous_year(db: Session, force: bool = False) -> dict:
    """
    settle_previous_year - 结算上一年（定时任务入口）
    """
    return settle_year(db, previous_year(), force=force)
