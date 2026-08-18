"""
@file hall_induction.py
@description 名人堂四条入堂路径自动评定
@module app.services.hall_induction
@author fishing-ranking
@created 2026-08-14
@version 1.0.0
"""

from calendar import monthrange
from datetime import date, datetime
from typing import Dict, List, Optional, Set

from sqlalchemy.orm import Session

from app.constants import (
    CATCH_STATUS_APPROVED,
    FISHING_METHOD_LIST,
    FISHING_METHOD_SPECIES_MAP,
    HALL_LEGEND_STREAK_YEARS,
    HALL_LEGEND_TOP_N,
    HALL_PATH_ANNUAL,
    HALL_PATH_DOMINATE,
    HALL_PATH_LEGEND,
    HALL_PATH_RECORD,
    HALL_RECORD_HOLD_MONTHS,
    HALL_TIER_LEGEND,
    HALL_TIER_MASTER,
    HALL_TIER_META,
    HALL_TIER_RECORD,
    NOTIFICATION_TYPE_HALL,
    RANKING_SPECIES_LIST,
)
from app.models.catch import Catch
from app.models.hall_member import HallMember
from app.models.notification import Notification


def _year_bounds(year: int):
    """
    _year_bounds - 自然年半开区间
    """
    return date(year, 1, 1), date(year + 1, 1, 1)


def _months_ago(base_date: date, months: int) -> date:
    """
    _months_ago - 往前推 N 个月（按日对齐到当月最大日）
    """
    total_month = base_date.year * 12 + (base_date.month - 1) - months
    year_number = total_month // 12
    month_number = total_month % 12 + 1
    day_number = min(base_date.day, monthrange(year_number, month_number)[1])
    return date(year_number, month_number, day_number)


# 永久路径：同一 path+role 终身只入一次
_PERMANENT_PATHS = {HALL_PATH_RECORD, HALL_PATH_LEGEND, HALL_PATH_DOMINATE}


def _find_top_catch(
    db: Session,
    start_date: date,
    end_date: date,
    fishing_method: Optional[str] = None,
    fish_species: Optional[str] = None,
) -> Optional[Catch]:
    """
    _find_top_catch - 区间内最重鱼获
    """
    query = db.query(Catch).filter(
        Catch.status == CATCH_STATUS_APPROVED,
        Catch.caught_at >= start_date,
        Catch.caught_at < end_date,
    )
    # 判断限定钓法
    if fishing_method:
        query = query.filter(Catch.fishing_method == fishing_method)
    # 判断限定鱼种
    if fish_species:
        query = query.filter(Catch.fish_species == fish_species)
    return query.order_by(Catch.weight.desc(), Catch.created_at.desc()).first()


def _upsert_member(
    db: Session,
    *,
    user_id: int,
    inducted_year: int,
    path_code: str,
    tier_code: str,
    role_key: str,
    role_label: str,
    reason: str,
    fishing_method: Optional[str] = None,
    fish_species: Optional[str] = None,
    catch: Optional[Catch] = None,
    notify: bool = True,
) -> Optional[HallMember]:
    """
    _upsert_member - 幂等写入名人堂成员并可选发通知
    """
    # 判断永久路径：同人同角色终身只入一次
    if path_code in _PERMANENT_PATHS:
        existing = (
            db.query(HallMember)
            .filter_by(user_id=user_id, path_code=path_code, role_key=role_key)
            .first()
        )
    else:
        existing = (
            db.query(HallMember)
            .filter_by(
                user_id=user_id,
                inducted_year=inducted_year,
                path_code=path_code,
                role_key=role_key,
            )
            .first()
        )
    # 判断已入堂：幂等，不视为新建
    if existing is not None:
        return None

    member = HallMember(
        user_id=user_id,
        inducted_year=inducted_year,
        path_code=path_code,
        tier_code=tier_code,
        role_key=role_key,
        role_label=role_label,
        fishing_method=fishing_method,
        fish_species=fish_species,
        catch_id=catch.id if catch else None,
        weight=catch.weight if catch else None,
        reason=reason,
    )
    db.add(member)
    db.flush()

    # 判断发入堂通知
    if notify:
        tier_title = HALL_TIER_META.get(tier_code, {}).get("title", "名人堂成员")
        db.add(
            Notification(
                user_id=user_id,
                type=NOTIFICATION_TYPE_HALL,
                title=f"入选名人堂 · {tier_title}",
                content=(
                    f"恭喜！你因「{role_label}」入选 {inducted_year} 名人堂"
                    f"（{tier_title}）。{reason}"
                ),
                catch_id=catch.id if catch else None,
                is_read=0,
            )
        )
    return member


def induct_annual_champions(db: Session, year: int, notify: bool = True) -> List[HallMember]:
    """
    induct_annual_champions - 路径一：年度全榜总冠军 + 三大钓法总冠军

    @description 同一人同年不重复占位（全榜优先保留，钓法冠军合并标注）
    """
    start_date, end_date = _year_bounds(year)
    created: List[HallMember] = []
    # user_id -> 已占角色说明（含库中已有席位，避免重跑重复占位）
    occupied: Dict[int, str] = {}
    for existing_row in (
        db.query(HallMember)
        .filter_by(inducted_year=year, path_code=HALL_PATH_ANNUAL)
        .all()
    ):
        occupied[existing_row.user_id] = existing_row.role_label

    overall = _find_top_catch(db, start_date, end_date)
    # 判断有全榜冠军
    if overall is not None:
        member = _upsert_member(
            db,
            user_id=overall.user_id,
            inducted_year=year,
            path_code=HALL_PATH_ANNUAL,
            tier_code=HALL_TIER_RECORD,
            role_key="overall",
            role_label="全榜冠军",
            reason=f"{year} 年全国单尾最重（{float(overall.weight)}kg）",
            fishing_method=overall.fishing_method,
            fish_species=overall.fish_species,
            catch=overall,
            notify=notify,
        )
        # 判断新建
        if member is not None:
            created.append(member)
        # 全榜用户始终占位，避免与钓法冠军重复
        occupied[overall.user_id] = "全榜冠军"

    for method_name in FISHING_METHOD_LIST:
        top = _find_top_catch(db, start_date, end_date, fishing_method=method_name)
        # 判断无该钓法冠军
        if top is None:
            continue
        # 判断该用户本年已有年度席位：不重复占位，仅补充角色说明
        if top.user_id in occupied:
            existing = (
                db.query(HallMember)
                .filter(
                    HallMember.user_id == top.user_id,
                    HallMember.inducted_year == year,
                    HallMember.path_code == HALL_PATH_ANNUAL,
                )
                .first()
            )
            # 判断已有记录则合并标签
            if existing is not None and method_name not in (existing.role_label or ""):
                existing.role_label = f"{existing.role_label}（兼{method_name}）"
                existing.reason = (
                    f"{existing.reason}；同时为{method_name}年度总冠军"
                )
                db.add(existing)
            continue

        member = _upsert_member(
            db,
            user_id=top.user_id,
            inducted_year=year,
            path_code=HALL_PATH_ANNUAL,
            tier_code=HALL_TIER_RECORD,
            role_key=f"method:{method_name}",
            role_label=f"{method_name}冠军",
            reason=f"{year} 年{method_name}单尾最重（{float(top.weight)}kg）",
            fishing_method=method_name,
            fish_species=top.fish_species,
            catch=top,
            notify=notify,
        )
        # 判断新建
        if member is not None:
            created.append(member)
            occupied[top.user_id] = f"{method_name}冠军"

    return created


def induct_record_keepers(db: Session, as_of: Optional[date] = None, notify: bool = True) -> List[HallMember]:
    """
    induct_record_keepers - 路径二：某鱼种全国纪录保持 ≥ 6 个月
    """
    today = as_of or date.today()
    threshold = _months_ago(today, HALL_RECORD_HOLD_MONTHS)
    created: List[HallMember] = []
    species_names = list(RANKING_SPECIES_LIST)

    for species_name in species_names:
        top = (
            db.query(Catch)
            .filter_by(status=CATCH_STATUS_APPROVED, fish_species=species_name)
            .order_by(Catch.weight.desc(), Catch.created_at.desc())
            .first()
        )
        # 判断无纪录
        if top is None or top.created_at is None:
            continue
        hold_since = top.created_at.date()
        # 判断保持不足 6 个月
        if hold_since > threshold:
            continue

        inducted_year = today.year
        member = _upsert_member(
            db,
            user_id=top.user_id,
            inducted_year=inducted_year,
            path_code=HALL_PATH_RECORD,
            tier_code=HALL_TIER_RECORD,
            role_key=f"species:{species_name}",
            role_label=f"{species_name}纪录",
            reason=(
                f"保持{species_name}全国纪录 ≥ {HALL_RECORD_HOLD_MONTHS} 个月"
                f"（{float(top.weight)}kg）"
            ),
            fishing_method=top.fishing_method,
            fish_species=species_name,
            catch=top,
            notify=notify,
        )
        # 判断写入
        if member is not None:
            created.append(member)

    return created


def _yearly_species_top_user_ids(
    db: Session, year: int, species_name: str
) -> Set[int]:
    """
    _yearly_species_top_user_ids - 某年某鱼种年度榜 TOP N 用户
    """
    start_date, end_date = _year_bounds(year)
    rows = (
        db.query(Catch)
        .filter(
            Catch.status == CATCH_STATUS_APPROVED,
            Catch.fish_species == species_name,
            Catch.caught_at >= start_date,
            Catch.caught_at < end_date,
        )
        .order_by(Catch.weight.desc(), Catch.created_at.desc())
        .limit(HALL_LEGEND_TOP_N)
        .all()
    )
    return {row.user_id for row in rows}


def induct_legend_anglers(db: Session, end_year: Optional[int] = None, notify: bool = True) -> List[HallMember]:
    """
    induct_legend_anglers - 路径三：同一鱼种连续 3 年进入年度 TOP 3
    """
    last_year = end_year or date.today().year
    created: List[HallMember] = []
    years = [last_year - 2, last_year - 1, last_year]

    for species_name in RANKING_SPECIES_LIST:
        top_by_year = {
            year_value: _yearly_species_top_user_ids(db, year_value, species_name)
            for year_value in years
        }
        # 三年交集用户
        common_users = set.intersection(*(top_by_year[year_value] for year_value in years))
        for user_id in common_users:
            member = _upsert_member(
                db,
                user_id=user_id,
                inducted_year=last_year,
                path_code=HALL_PATH_LEGEND,
                tier_code=HALL_TIER_LEGEND,
                role_key=f"legend:{species_name}",
                role_label=f"传奇·{species_name}",
                reason=(
                    f"{years[0]}-{years[2]} 连续 {HALL_LEGEND_STREAK_YEARS} 年"
                    f"进入{species_name}年度榜 TOP {HALL_LEGEND_TOP_N}"
                ),
                fish_species=species_name,
                catch=None,
                notify=notify,
            )
            # 判断写入
            if member is not None:
                created.append(member)

    return created


def induct_dominate_masters(db: Session, as_of: Optional[date] = None, notify: bool = True) -> List[HallMember]:
    """
    induct_dominate_masters - 路径四：任一钓法下全部鱼种均有上榜记录
    """
    today = as_of or date.today()
    created: List[HallMember] = []
    user_ids = [row[0] for row in db.query(Catch.user_id).filter_by(status=CATCH_STATUS_APPROVED).distinct().all()]

    for user_id in user_ids:
        for method_name, species_list in FISHING_METHOD_SPECIES_MAP.items():
            required = set(species_list)
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
            # 判断未制霸
            if not required.issubset(owned):
                continue
            member = _upsert_member(
                db,
                user_id=user_id,
                inducted_year=today.year,
                path_code=HALL_PATH_DOMINATE,
                tier_code=HALL_TIER_MASTER,
                role_key=f"dominate:{method_name}",
                role_label=f"全能·{method_name}",
                reason=f"{method_name}下全部 {len(required)} 个鱼种均有上榜记录",
                fishing_method=method_name,
                catch=None,
                notify=notify,
            )
            # 判断写入
            if member is not None:
                created.append(member)

    return created


def evaluate_hall_of_fame(
    db: Session,
    year: Optional[int] = None,
    notify: bool = True,
    include_annual: bool = True,
    do_commit: bool = False,
) -> dict:
    """
    evaluate_hall_of_fame - 扫描四条入堂路径

    @param {Session} db - 会话
    @param {int} [year] - 年度路径所用年份，默认当前年
    @param {bool} [notify=True] - 新入堂是否发通知
    @param {bool} [include_annual=True] - 是否评定路径一（年结时打开）
    @param {bool} [do_commit=False] - 是否自行 commit
    """
    year_number = year or date.today().year
    annual: List[HallMember] = []
    # 判断评定年度冠军路径
    if include_annual:
        annual = induct_annual_champions(db, year_number, notify=notify)
    records = induct_record_keepers(db, notify=notify)
    legends = induct_legend_anglers(db, end_year=year_number, notify=notify)
    masters = induct_dominate_masters(db, notify=notify)
    # 判断自行提交
    if do_commit:
        db.commit()
    else:
        db.flush()
    return {
        "year": year_number,
        "annual": [item.to_dict() for item in annual],
        "records": [item.to_dict() for item in records],
        "legends": [item.to_dict() for item in legends],
        "masters": [item.to_dict() for item in masters],
        "evaluated_at": datetime.utcnow().isoformat(),
    }


def list_hall_members(db: Session, year: Optional[int] = None) -> List[dict]:
    """
    list_hall_members - 按年份列出名人堂成员（含永久路径该年入堂者）
    """
    query = db.query(HallMember).order_by(
        HallMember.tier_code.asc(),
        HallMember.created_at.asc(),
    )
    # 判断按年筛选
    if year is not None:
        query = query.filter(HallMember.inducted_year == year)
    rows = query.all()
    # 层级展示顺序：传奇 > 纪录 > 大师
    tier_order = {HALL_TIER_LEGEND: 0, HALL_TIER_RECORD: 1, HALL_TIER_MASTER: 2}
    items = [row.to_dict() for row in rows]
    items.sort(key=lambda item: (tier_order.get(item["tier_code"], 9), item["id"]))
    return items


def hall_stats(db: Session) -> dict:
    """
    hall_stats - 名人堂汇总数据
    """
    members = db.query(HallMember).all()
    user_ids = {row.user_id for row in members}
    species_set = {row.fish_species for row in members if row.fish_species}
    return {
        "member_count": len(user_ids),
        "entry_count": len(members),
        "species_count": len(species_set),
    }
