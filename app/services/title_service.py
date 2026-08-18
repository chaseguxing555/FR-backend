"""
@file title_service.py
@description 称号评定、发放与被超越通知
@module app.services.title_service
@author fishing-ranking
@created 2026-08-14
@version 1.0.0
"""

from calendar import monthrange
from datetime import date, datetime, timedelta
from typing import List, Optional, Set

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.constants import (
    CATCH_STATUS_APPROVED,
    DOMINATE_TITLE_MAP,
    FISHING_METHOD_SPECIES_MAP,
    NOTIFICATION_TYPE_SURPASSED,
    NOTIFICATION_TYPE_TITLE,
    SPECIES_RECORD_TITLE_MAP,
    TITLE_CRUCIAN_SAINT,
    TITLE_CARP_KING,
    TITLE_DEFINITIONS,
    TITLE_DOMINATE_BOTTOM,
    TITLE_DOMINATE_HAND,
    TITLE_DOMINATE_LURE,
    TITLE_FOUNDING_ELDER,
    TITLE_HUNDRED_JIN,
    TITLE_HUNDRED_JIN_KG,
    TITLE_MONTHLY_TOP10,
    TITLE_STREAK_3,
    TITLE_STREAK_6,
    TITLE_THOUSAND_JIN,
    TITLE_THOUSAND_JIN_KG,
    TITLE_YEARLY_CELEBRITY,
)
from app.models.catch import Catch
from app.models.notification import Notification
from app.models.system_setting import get_all_settings_map
from app.models.user import User
from app.models.user_title import FirstSpeciesRecord, UserTitle


def _launch_date(db: Session) -> date:
    """
    _launch_date - 站点上线日（系统配置，默认用户最早注册日）
    """
    settings_map = get_all_settings_map(db)
    raw_value = settings_map.get("launch_date")
    # 判断配置了上线日
    if isinstance(raw_value, str) and raw_value:
        try:
            return date.fromisoformat(raw_value[:10])
        except ValueError:
            pass
    first_user = db.query(User).order_by(User.created_at.asc()).first()
    # 判断有用户
    if first_user and first_user.created_at:
        return first_user.created_at.date()
    return date.today()


def _grant_title(
    db: Session,
    user_id: int,
    title_code: str,
    *,
    extra: Optional[str] = None,
    count: int = 1,
    notify: bool = True,
) -> Optional[UserTitle]:
    """
    _grant_title - 发放或激活称号（首次发放发通知）
    """
    # 判断称号是否定义
    if title_code not in TITLE_DEFINITIONS:
        return None
    existing = (
        db.query(UserTitle).filter_by(user_id=user_id, title_code=title_code).first()
    )
    title_name = TITLE_DEFINITIONS[title_code]["name"]
    # 判断已有称号
    if existing is not None:
        was_inactive = existing.is_active == 0
        existing.is_active = 1
        existing.count = max(existing.count, count)
        # 判断有附加信息
        if extra:
            existing.extra = extra
        existing.updated_at = datetime.utcnow()
        db.add(existing)
        # 判断重新激活则通知
        if was_inactive and notify:
            _notify_title(db, user_id, title_name, "重新获得")
        return existing

    row = UserTitle(
        user_id=user_id,
        title_code=title_code,
        is_active=1,
        count=count,
        extra=extra,
    )
    db.add(row)
    db.flush()
    # 判断首次发放通知
    if notify:
        _notify_title(db, user_id, title_name, "获得")
    return row


def _deactivate_title(db: Session, title_code: str, except_user_id: Optional[int] = None):
    """
    _deactivate_title - 使某称号对其他用户失效（纪录类）
    """
    query = db.query(UserTitle).filter_by(title_code=title_code, is_active=1)
    # 判断排除新纪录保持者
    if except_user_id is not None:
        query = query.filter(UserTitle.user_id != except_user_id)
    for row in query.all():
        row.is_active = 0
        row.updated_at = datetime.utcnow()
        db.add(row)


def _notify_title(db: Session, user_id: int, title_name: str, action_text: str):
    """
    _notify_title - 称号站内通知
    """
    db.add(
        Notification(
            user_id=user_id,
            type=NOTIFICATION_TYPE_TITLE,
            title=f"获得称号 · {title_name}",
            content=(
                f"恭喜！你{action_text}了【{title_name}】称号，"
                f"已展示在你的个人主页。"
            ),
            catch_id=None,
            is_read=0,
        )
    )


def ensure_first_species_record(db: Session, catch: Catch):
    """
    ensure_first_species_record - 若该鱼种尚无首个纪录则写入（永不覆盖）
    """
    existing = (
        db.query(FirstSpeciesRecord)
        .filter_by(fish_species=catch.fish_species)
        .first()
    )
    # 判断已有首个纪录
    if existing is not None:
        return existing
    row = FirstSpeciesRecord(
        fish_species=catch.fish_species,
        catch_id=catch.id,
        user_id=catch.user_id,
        weight=catch.weight,
        fishing_method=catch.fishing_method,
        caught_at=catch.caught_at,
    )
    db.add(row)
    return row


def notify_surpassed(db: Session, new_catch: Catch):
    """
    notify_surpassed - 同钓法同鱼种全国总榜被超越时通知原保持者
    """
    previous = (
        db.query(Catch)
        .filter(
            Catch.status == CATCH_STATUS_APPROVED,
            Catch.fishing_method == new_catch.fishing_method,
            Catch.fish_species == new_catch.fish_species,
            Catch.id != new_catch.id,
            Catch.weight < new_catch.weight,
        )
        .order_by(Catch.weight.desc(), Catch.created_at.desc())
        .first()
    )
    # 判断无人原第一且不是同一人
    if previous is None or previous.user_id == new_catch.user_id:
        return

    # 仅当新纪录确实成为榜一才通知旧榜一
    top = (
        db.query(Catch)
        .filter_by(
            status=CATCH_STATUS_APPROVED,
            fishing_method=new_catch.fishing_method,
            fish_species=new_catch.fish_species,
        )
        .order_by(Catch.weight.desc(), Catch.created_at.desc())
        .first()
    )
    # 判断新纪录不是榜一
    if top is None or top.id != new_catch.id:
        return

    # 计算原保持者当前名次
    better_count = (
        db.query(Catch)
        .filter(
            Catch.status == CATCH_STATUS_APPROVED,
            Catch.fishing_method == previous.fishing_method,
            Catch.fish_species == previous.fish_species,
            Catch.weight > previous.weight,
        )
        .count()
    )
    total = (
        db.query(Catch)
        .filter_by(
            status=CATCH_STATUS_APPROVED,
            fishing_method=previous.fishing_method,
            fish_species=previous.fish_species,
        )
        .count()
    )
    new_user = db.get(User, new_catch.user_id)
    nick = new_user.nickname if new_user else "钓友"
    db.add(
        Notification(
            user_id=previous.user_id,
            type=NOTIFICATION_TYPE_SURPASSED,
            title="你的纪录被超越了！",
            content=(
                f"你在【{previous.fish_species}·{previous.fishing_method}全国总榜】中的纪录"
                f"（{float(previous.weight)}kg）已被钓友【{nick}】以 "
                f"{float(new_catch.weight)}kg 超越。"
                f"你的当前排名：第 {better_count + 1} 位（共 {total} 条记录）"
            ),
            catch_id=new_catch.id,
            is_read=0,
        )
    )


def _sync_species_record_titles(db: Session):
    """
    _sync_species_record_titles - 同步鲤王 / 鲫圣给当前全国纪录保持者
    """
    for species_name, title_code in SPECIES_RECORD_TITLE_MAP.items():
        top = (
            db.query(Catch)
            .filter_by(status=CATCH_STATUS_APPROVED, fish_species=species_name)
            .order_by(Catch.weight.desc(), Catch.created_at.desc())
            .first()
        )
        # 判断无纪录则全部失效
        if top is None:
            _deactivate_title(db, title_code)
            continue
        _deactivate_title(db, title_code, except_user_id=top.user_id)
        _grant_title(db, top.user_id, title_code, extra=species_name, notify=True)


def _check_weight_club(db: Session, user_id: int):
    """
    _check_weight_club - 百斤 / 千斤俱乐部
    """
    total_weight = (
        db.query(func.coalesce(func.sum(Catch.weight), 0))
        .filter_by(user_id=user_id, status=CATCH_STATUS_APPROVED)
        .scalar()
    )
    total_value = float(total_weight or 0)
    # 判断百斤
    if total_value >= TITLE_HUNDRED_JIN_KG:
        _grant_title(db, user_id, TITLE_HUNDRED_JIN)
    # 判断千斤
    if total_value >= TITLE_THOUSAND_JIN_KG:
        _grant_title(db, user_id, TITLE_THOUSAND_JIN)


def _check_founding_elder(db: Session, user_id: int):
    """
    _check_founding_elder - 开榜元老
    """
    user = db.get(User, user_id)
    # 判断用户不存在
    if user is None or user.created_at is None:
        return
    launch = _launch_date(db)
    # 判断注册晚于上线日 7 天后
    if user.created_at.date() > launch + timedelta(days=7):
        return
    first_catch = (
        db.query(Catch)
        .filter_by(user_id=user_id, status=CATCH_STATUS_APPROVED)
        .order_by(Catch.created_at.asc())
        .first()
    )
    # 判断无通过记录
    if first_catch is None or first_catch.created_at is None:
        return
    # 判断首条在上线 7 天内
    if first_catch.created_at.date() <= launch + timedelta(days=7):
        _grant_title(db, user_id, TITLE_FOUNDING_ELDER)


def _check_dominate(db: Session, user_id: int):
    """
    _check_dominate - 全鱼种制霸
    """
    for method_name, title_code in DOMINATE_TITLE_MAP.items():
        required = set(FISHING_METHOD_SPECIES_MAP.get(method_name) or [])
        # 判断无鱼种列表
        if not required:
            continue
        owned = {
            row[0]
            for row in db.query(Catch.fish_species)
            .filter_by(
                user_id=user_id,
                status=CATCH_STATUS_APPROVED,
                fishing_method=method_name,
            )
            .distinct()
            .all()
        }
        # 判断全部覆盖
        if required.issubset(owned):
            _grant_title(db, user_id, title_code, extra=method_name)


def _user_on_board_in_month(
    db: Session,
    user_id: int,
    species: str,
    method: str,
    year: int,
    month: int,
) -> bool:
    """
    _user_on_board_in_month - 用户该月该分榜是否有通过记录（视为上榜）
    """
    start = date(year, month, 1)
    # 判断月末
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)
    exists = (
        db.query(Catch.id)
        .filter(
            Catch.user_id == user_id,
            Catch.status == CATCH_STATUS_APPROVED,
            Catch.fish_species == species,
            Catch.fishing_method == method,
            Catch.caught_at >= start,
            Catch.caught_at < end,
        )
        .first()
    )
    return exists is not None


def _check_streak(db: Session, user_id: int):
    """
    _check_streak - 连冠王者 3/6 个月（同钓法同鱼种连续自然月有上榜记录）
    """
    pairs = (
        db.query(Catch.fish_species, Catch.fishing_method)
        .filter_by(user_id=user_id, status=CATCH_STATUS_APPROVED)
        .distinct()
        .all()
    )
    today = date.today()
    best_streak = 0
    best_extra = ""
    for species, method in pairs:
        streak = 0
        cursor_year, cursor_month = today.year, today.month
        # 连续往前查最多 12 个月
        for _ in range(12):
            # 判断当月在榜
            if _user_on_board_in_month(
                db, user_id, species, method, cursor_year, cursor_month
            ):
                streak += 1
            else:
                break
            # 回退一个月
            if cursor_month == 1:
                cursor_year -= 1
                cursor_month = 12
            else:
                cursor_month -= 1
        # 判断刷新最佳
        if streak > best_streak:
            best_streak = streak
            best_extra = f"{method}·{species}"
    # 判断 6 连
    if best_streak >= 6:
        _grant_title(db, user_id, TITLE_STREAK_6, extra=best_extra)
    # 判断 3 连
    if best_streak >= 3:
        _grant_title(db, user_id, TITLE_STREAK_3, extra=best_extra)


def _check_monthly_top10(db: Session, user_id: int):
    """
    _check_monthly_top10 - 当月任意分榜 TOP10
    """
    today = date.today()
    start = today.replace(day=1)
    if today.month == 12:
        end = date(today.year + 1, 1, 1)
    else:
        end = date(today.year, today.month + 1, 1)

    user_catches = (
        db.query(Catch)
        .filter(
            Catch.user_id == user_id,
            Catch.status == CATCH_STATUS_APPROVED,
            Catch.caught_at >= start,
            Catch.caught_at < end,
        )
        .all()
    )
    hit_count = 0
    for catch in user_catches:
        # 同钓法同鱼种当月榜按重量排序取前 10
        board = (
            db.query(Catch)
            .filter(
                Catch.status == CATCH_STATUS_APPROVED,
                Catch.fishing_method == catch.fishing_method,
                Catch.fish_species == catch.fish_species,
                Catch.caught_at >= start,
                Catch.caught_at < end,
            )
            .order_by(Catch.weight.desc(), Catch.created_at.desc())
            .limit(10)
            .all()
        )
        board_ids = {item.id for item in board}
        # 判断本人记录在 TOP10
        if catch.id in board_ids:
            hit_count += 1
    # 判断有上榜
    if hit_count > 0:
        _grant_title(db, user_id, TITLE_MONTHLY_TOP10, count=hit_count)


def _check_yearly_celebrity(db: Session, user_id: int):
    """
    _check_yearly_celebrity - 本年度任意鱼种 TOP3
    """
    today = date.today()
    start = date(today.year, 1, 1)
    end = date(today.year + 1, 1, 1)
    pairs = (
        db.query(Catch.fish_species, Catch.fishing_method)
        .filter(
            Catch.user_id == user_id,
            Catch.status == CATCH_STATUS_APPROVED,
            Catch.caught_at >= start,
            Catch.caught_at < end,
        )
        .distinct()
        .all()
    )
    for species, method in pairs:
        board = (
            db.query(Catch)
            .filter(
                Catch.status == CATCH_STATUS_APPROVED,
                Catch.fish_species == species,
                Catch.fishing_method == method,
                Catch.caught_at >= start,
                Catch.caught_at < end,
            )
            .order_by(Catch.weight.desc(), Catch.created_at.desc())
            .limit(3)
            .all()
        )
        # 判断用户在 TOP3
        if any(item.user_id == user_id for item in board):
            _grant_title(
                db,
                user_id,
                TITLE_YEARLY_CELEBRITY,
                extra=f"{today.year}·{method}·{species}",
            )
            return


def evaluate_user_titles(db: Session, user_id: int):
    """
    evaluate_user_titles - 评定用户全部可累计 / 条件称号
    """
    _check_founding_elder(db, user_id)
    _check_weight_club(db, user_id)
    _check_dominate(db, user_id)
    _check_streak(db, user_id)
    _check_monthly_top10(db, user_id)
    _check_yearly_celebrity(db, user_id)


def sync_all_record_titles(db: Session):
    """
    sync_all_record_titles - 对外同步鲤王 / 鲫圣
    """
    _sync_species_record_titles(db)


def on_catch_approved(db: Session, catch: Catch):
    """
    on_catch_approved - 审核通过后：首个纪录、被超越通知、称号评定、名人堂路径二/三/四
    """
    ensure_first_species_record(db, catch)
    notify_surpassed(db, catch)
    _sync_species_record_titles(db)
    evaluate_user_titles(db, catch.user_id)
    # 名人堂：纪录保持 / 传奇 / 制霸（不含年度冠军，年结时评定）
    from app.services.hall_induction import evaluate_hall_of_fame

    evaluate_hall_of_fame(db, include_annual=False, notify=True, do_commit=False)

def list_user_titles(db: Session, user_id: int, active_only: bool = True) -> List[dict]:
    """
    list_user_titles - 用户称号列表（按优先级）
    """
    query = db.query(UserTitle).filter_by(user_id=user_id)
    # 判断仅有效
    if active_only:
        query = query.filter_by(is_active=1)
    rows = query.all()
    items = [row.to_dict() for row in rows]
    items.sort(key=lambda item: item.get("priority", 0), reverse=True)
    return items


def primary_title_for_user(db: Session, user_id: int) -> Optional[dict]:
    """
    primary_title_for_user - 昵称旁展示的主称号（仅 nickname 位）
    """
    items = list_user_titles(db, user_id, active_only=True)
    # 仅取昵称旁展示位
    for item in items:
        # 判断昵称旁展示
        if item.get("display") == "nickname":
            return item
    return None


def titles_map_for_users(db: Session, user_ids: Set[int]) -> dict:
    """
    titles_map_for_users - 批量取用户主称号
    """
    result = {}
    # 判断空集合
    if not user_ids:
        return result
    for user_id in user_ids:
        result[user_id] = primary_title_for_user(db, user_id)
    return result
