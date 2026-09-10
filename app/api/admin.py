"""
@file admin.py
@description 审核后台接口（FastAPI）
@module app.api.admin
@author fishing-ranking
@created 2026-08-11
@updated 2026-09-10
@version 3.2.0
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.config import settings
from app.constants import (
    AUDIT_ACTION_APPROVE,
    CATCH_STATUS_APPROVED,
    CATCH_STATUS_PENDING,
    CATCH_STATUS_REJECTED,
    RANKING_PER_PAGE,
    USER_STATUS_NORMAL,
)
from app.database import get_db
from app.deps import get_current_admin, paginate_query
from app.models.admin import Admin
from app.models.audit_log import AuditLog
from app.models.catch import Catch
from app.models.hall_member import HallMember
from app.models.notification import build_audit_notification
from app.models.reward import RewardAward
from app.models.system_setting import (
    DEFAULT_SETTINGS,
    SystemSetting,
    get_all_settings_map,
)
from app.models.user import User
from app.models.user_title import FirstSpeciesRecord, UserTitle
from app.schemas.admin import (
    AdminChangePasswordRequest,
    AdminLoginRequest,
    AuditCatchRequest,
    UpdateSettingsRequest,
    UpdateUserStatusRequest,
)
from app.utils.logging_setup import read_log_tail
from app.utils.response import raise_error, success
from app.utils.security import create_access_token, hash_password, verify_password


router = APIRouter(prefix="/api/admin", tags=["admin"])


def _parse_page(page: int, per_page: int, db: Session):
    """
    _parse_page - 校验分页并套用默认每页条数

    @returns {tuple} (page, per_page)
    """
    # 判断未指定有效 per_page 时用配置
    if per_page < 1:
        settings_map = get_all_settings_map(db)
        per_page = int(settings_map.get("list_per_page") or RANKING_PER_PAGE)
    # 判断页码
    if page < 1 or per_page < 1:
        raise_error("分页参数不正确")
    # 限制单页上限
    if per_page > 100:
        per_page = 100
    return page, per_page


def _collect_referenced_upload_paths(db: Session):
    """
    _collect_referenced_upload_paths - 收集 DB 引用的上传路径

    @returns {set[str]}
    """
    referenced = set()
    for catch_item in db.query(Catch).all():
        for image_url in catch_item.get_image_url_list():
            # 判断是否为站内上传路径
            if image_url and image_url.startswith("/uploads/"):
                referenced.add(image_url.lstrip("/"))
        # 判断是否有视频
        if catch_item.video_url and catch_item.video_url.startswith("/uploads/"):
            referenced.add(catch_item.video_url.lstrip("/"))
    for user_item in db.query(User).filter(User.avatar.isnot(None)).all():
        # 判断头像是否为站内路径
        if user_item.avatar and user_item.avatar.startswith("/uploads/"):
            referenced.add(user_item.avatar.lstrip("/"))
    return referenced


def _walk_upload_files(upload_folder: str):
    """
    _walk_upload_files - 遍历上传目录

    @returns {list[tuple]}
    """
    file_rows = []
    # 判断目录是否存在
    if not os.path.isdir(upload_folder):
        return file_rows
    for root_dir, _dir_names, file_names in os.walk(upload_folder):
        for file_name in file_names:
            absolute_path = os.path.join(root_dir, file_name)
            relative_path = os.path.relpath(absolute_path, upload_folder)
            relative_key = f"uploads/{relative_path.replace(os.sep, '/')}"
            try:
                size_bytes = os.path.getsize(absolute_path)
            except OSError:
                size_bytes = 0
            file_rows.append((relative_key, absolute_path, size_bytes))
    return file_rows


@router.post("/login")
def admin_login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    """
    admin_login - 管理员登录
    """
    admin = db.query(Admin).filter_by(username=payload.username).first()
    # 判断账号或密码
    if admin is None or not verify_password(payload.password, admin.password):
        raise_error("用户名或密码错误", http_status=401)

    access_token = create_access_token(identity=f"admin:{admin.id}", role="admin")
    return success(
        {"token": access_token, "admin": admin.to_dict()},
        message="登录成功",
    )


@router.get("/stats")
def get_admin_stats(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_admin_stats - 概览统计
    """
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    return success(
        {
            "user_total": db.query(User).count(),
            "catch_total": db.query(Catch).count(),
            "pending_count": db.query(Catch).filter_by(status=CATCH_STATUS_PENDING).count(),
            "approved_count": db.query(Catch).filter_by(status=CATCH_STATUS_APPROVED).count(),
            "rejected_count": db.query(Catch).filter_by(status=CATCH_STATUS_REJECTED).count(),
            "today_users": db.query(User).filter(User.created_at >= today_start).count(),
            "today_catches": db.query(Catch).filter(Catch.created_at >= today_start).count(),
            "today_audits": db.query(AuditLog).filter(AuditLog.created_at >= today_start).count(),
            "hall_entry_count": db.query(HallMember).count(),
            "title_active_count": db.query(UserTitle).filter_by(is_active=1).count(),
            "reward_award_count": db.query(RewardAward).count(),
        }
    )


@router.get("/catches/pending")
def get_pending_catches(
    page: int = Query(default=1),
    per_page: int = Query(default=0),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_pending_catches - 待审核列表
    """
    page, per_page = _parse_page(page, per_page, db)
    query = (
        db.query(Catch)
        .filter_by(status=CATCH_STATUS_PENDING)
        .order_by(Catch.created_at.desc())
    )
    items, total = paginate_query(query, page, per_page)
    return success(
        {
            "list": [catch.to_dict(include_user=True) for catch in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.get("/catches")
def get_all_catches(
    page: int = Query(default=1),
    per_page: int = Query(default=0),
    status: Optional[str] = Query(default=None),
    fish_species: Optional[str] = Query(default=None),
    province: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_all_catches - 全部记录
    """
    page, per_page = _parse_page(page, per_page, db)
    query = db.query(Catch)

    # 判断是否按状态筛选
    if status is not None and status != "" and status != "all":
        try:
            status_value = int(status)
        except ValueError:
            raise_error("状态参数不正确")
        query = query.filter_by(status=status_value)

    fish_text = (fish_species or "").strip()
    # 判断鱼种
    if fish_text:
        query = query.filter_by(fish_species=fish_text)

    province_text = (province or "").strip()
    # 判断省份
    if province_text:
        query = query.filter_by(province=province_text)

    keyword_text = (keyword or "").strip()
    # 判断关键词
    if keyword_text:
        query = query.join(User, Catch.user_id == User.id).filter(
            or_(
                User.nickname.contains(keyword_text),
                Catch.location_detail.contains(keyword_text),
                Catch.description.contains(keyword_text),
            )
        )

    query = query.order_by(Catch.created_at.desc())
    items, total = paginate_query(query, page, per_page)
    return success(
        {
            "list": [catch.to_dict(include_user=True) for catch in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.put("/catches/{catch_id}/audit")
def audit_catch(
    catch_id: int,
    payload: AuditCatchRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    audit_catch - 审核通过/拒绝
    """
    catch = db.get(Catch, catch_id)
    # 判断记录
    if catch is None:
        raise_error("记录不存在", http_status=404)
    # 判断是否仍待审
    if catch.status != CATCH_STATUS_PENDING:
        raise_error("该记录已审核，不能重复操作")

    # 判断通过或拒绝
    if payload.action == AUDIT_ACTION_APPROVE:
        catch.status = CATCH_STATUS_APPROVED
        message = "审核通过"
    else:
        catch.status = CATCH_STATUS_REJECTED
        message = "已拒绝"

    db.add(
        AuditLog(
            catch_id=catch.id,
            admin_id=admin.id,
            action=payload.action,
            reason=payload.reason,
        )
    )
    db.add(
        build_audit_notification(
            user_id=catch.user_id,
            catch=catch,
            action=payload.action,
            reason=payload.reason,
        )
    )
    # 判断审核通过：称号评定 + 被超越通知 + 首个纪录
    if payload.action == AUDIT_ACTION_APPROVE:
        from app.services.title_service import on_catch_approved

        on_catch_approved(db, catch)

    db.commit()
    db.refresh(catch)
    result = catch.to_dict(include_user=True)
    result["audit_reason"] = payload.reason
    return success(result, message=message)


@router.get("/users")
def get_admin_users(
    page: int = Query(default=1),
    per_page: int = Query(default=0),
    status: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_admin_users - 用户列表
    """
    page, per_page = _parse_page(page, per_page, db)
    query = db.query(User)

    # 判断状态筛选
    if status is not None and status != "" and status != "all":
        try:
            status_value = int(status)
        except ValueError:
            raise_error("状态参数不正确")
        query = query.filter_by(status=status_value)

    keyword_text = (keyword or "").strip()
    # 判断关键词
    if keyword_text:
        query = query.filter(
            or_(
                User.nickname.contains(keyword_text),
                User.phone.contains(keyword_text),
                User.province.contains(keyword_text),
                User.city.contains(keyword_text),
            )
        )

    query = query.order_by(User.created_at.desc())
    items, total = paginate_query(query, page, per_page)
    from app.services.title_service import titles_map_for_users

    user_ids = {user_item.id for user_item in items}
    title_map = titles_map_for_users(db, user_ids)
    user_list = []
    # 附带昵称旁主称号
    for user_item in items:
        row = user_item.to_dict(mask_phone=True)
        row["primary_title"] = title_map.get(user_item.id)
        user_list.append(row)
    return success(
        {
            "list": user_list,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UpdateUserStatusRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    update_user_status - 启用/禁用用户
    """
    user = db.get(User, user_id)
    # 判断用户
    if user is None:
        raise_error("用户不存在", http_status=404)

    user.status = payload.status
    db.commit()
    db.refresh(user)
    return success(
        user.to_dict(mask_phone=True),
        message="已启用" if payload.status == USER_STATUS_NORMAL else "已禁用",
    )


@router.get("/audit-logs")
def get_audit_logs(
    page: int = Query(default=1),
    per_page: int = Query(default=0),
    action: Optional[str] = Query(default=None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_audit_logs - 审核日志
    """
    page, per_page = _parse_page(page, per_page, db)
    query = db.query(AuditLog)

    # 判断动作筛选
    if action is not None and action != "" and action != "all":
        try:
            action_value = int(action)
        except ValueError:
            raise_error("动作参数不正确")
        query = query.filter_by(action=action_value)

    query = query.order_by(AuditLog.created_at.desc())
    items, total = paginate_query(query, page, per_page)

    log_list = []
    for log_item in items:
        row = log_item.to_dict()
        catch_item = db.get(Catch, log_item.catch_id)
        admin_item = db.get(Admin, log_item.admin_id)
        # 判断关联鱼获
        if catch_item is not None:
            row["fish_species"] = catch_item.fish_species
            row["weight"] = float(catch_item.weight) if catch_item.weight is not None else None
            row["user_nickname"] = (
                catch_item.user.nickname if catch_item.user is not None else None
            )
        else:
            row["fish_species"] = None
            row["weight"] = None
            row["user_nickname"] = None
        row["admin_username"] = admin_item.username if admin_item is not None else None
        log_list.append(row)

    return success(
        {
            "list": log_list,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.get("/system")
def get_system_info(
    request: Request,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_system_info - 系统监控
    """
    upload_folder = settings.UPLOAD_FOLDER
    file_rows = _walk_upload_files(upload_folder)
    upload_file_count = len(file_rows)
    upload_bytes = sum(size for _key, _path, size in file_rows)

    db_uri = settings.SQLALCHEMY_DATABASE_URI or ""
    # 判断数据库驱动
    if db_uri.startswith("sqlite"):
        db_driver = "sqlite"
    elif "postgresql" in db_uri:
        db_driver = "postgresql"
    else:
        db_driver = db_uri.split(":", 1)[0] if ":" in db_uri else "unknown"

    started_at = getattr(request.app.state, "started_at", None) or datetime.utcnow()
    pending_count = db.query(Catch).filter_by(status=CATCH_STATUS_PENDING).count()

    return success(
        {
            "env": settings.ENV,
            "debug": bool(settings.DEBUG),
            "db_driver": db_driver,
            "upload_folder": upload_folder,
            "upload_file_count": upload_file_count,
            "upload_bytes": upload_bytes,
            "pending_count": pending_count,
            "started_at": started_at.isoformat() if started_at else None,
            "server_time": datetime.utcnow().isoformat(),
        }
    )


@router.post("/system/clear-orphan-uploads")
def clear_orphan_uploads(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    clear_orphan_uploads - 清理未引用上传
    """
    upload_folder = settings.UPLOAD_FOLDER
    referenced = _collect_referenced_upload_paths(db)
    file_rows = _walk_upload_files(upload_folder)

    deleted_count = 0
    freed_bytes = 0
    for relative_key, absolute_path, size_bytes in file_rows:
        # 判断是否仍被引用
        if relative_key in referenced:
            continue
        try:
            os.remove(absolute_path)
            deleted_count += 1
            freed_bytes += size_bytes
        except OSError:
            continue

    for root_dir, dir_names, file_names in os.walk(upload_folder, topdown=False):
        # 判断空目录
        if root_dir == upload_folder:
            continue
        if not dir_names and not file_names:
            try:
                os.rmdir(root_dir)
            except OSError:
                continue

    return success(
        {"deleted_count": deleted_count, "freed_bytes": freed_bytes},
        message=f"已清理 {deleted_count} 个未引用文件",
    )


@router.get("/system/logs")
def get_system_logs(
    lines: int = Query(default=200),
    admin: Admin = Depends(get_current_admin),
):
    """
    get_system_logs - 错误日志尾部
    """
    log_lines = read_log_tail(lines)
    return success({"lines": log_lines, "count": len(log_lines)})


@router.get("/settings")
def get_settings(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_settings - 读取配置
    """
    return success(get_all_settings_map(db))


@router.put("/settings")
def update_settings(
    payload: UpdateSettingsRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    update_settings - 更新配置
    """
    allowed_keys = set(DEFAULT_SETTINGS.keys())
    # 仅更新请求中实际传入的字段
    for key_name, raw_value in payload.model_dump(exclude_unset=True).items():
        # 判断是否允许的键
        if key_name not in allowed_keys:
            continue

        setting = db.get(SystemSetting, key_name)
        # 判断是否新建
        if setting is None:
            setting = SystemSetting(key=key_name)
            db.add(setting)
        setting.set_parsed_value(raw_value)

    db.commit()
    return success(get_all_settings_map(db), message="配置已保存")


@router.put("/password")
def change_admin_password(
    payload: AdminChangePasswordRequest,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    change_admin_password - 修改管理员密码
    """
    # 判断旧密码正确
    if not verify_password(payload.old_password, admin.password):
        raise_error("当前密码不正确")
    # 判断新旧相同
    if payload.old_password == payload.new_password:
        raise_error("新密码不能与当前密码相同")

    admin.password = hash_password(payload.new_password)
    db.commit()
    return success(None, message="密码已修改")


@router.post("/rewards/settle-month")
def admin_settle_month(
    year: Optional[int] = Query(default=None),
    month: Optional[int] = Query(default=None),
    force: bool = Query(default=False),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    admin_settle_month - 手动结算月榜（默认上月）并发送站内通知
    """
    from app.services.reward_settlement import previous_month, settle_month

    # 判断未指定则结算上月
    if year is None or month is None:
        year, month = previous_month()
    try:
        result = settle_month(db, year, month, force=force)
    except ValueError as error:
        raise_error(str(error))
    return success(result, message="月榜结算完成")


@router.post("/rewards/settle-year")
def admin_settle_year(
    year: Optional[int] = Query(default=None),
    force: bool = Query(default=False),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    admin_settle_year - 手动结算年榜（默认上年）并发送站内通知
    """
    from app.services.reward_settlement import previous_year, settle_year

    # 判断未指定则结算上年
    if year is None:
        year = previous_year()
    result = settle_year(db, year, force=force)
    return success(result, message="年榜结算完成")


@router.get("/rewards")
def admin_list_rewards(
    period_type: Optional[str] = Query(default=None),
    period_key: Optional[str] = Query(default=None),
    page: int = Query(default=1),
    per_page: int = Query(default=20),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    admin_list_rewards - 管理端查看奖励结算记录
    """
    from app.models.reward import RewardAward

    page, per_page = _parse_page(page, per_page, db)
    query = db.query(RewardAward).order_by(RewardAward.created_at.desc())
    # 判断周期类型
    if period_type:
        query = query.filter(RewardAward.period_type == period_type.strip())
    # 判断周期键
    if period_key:
        query = query.filter(RewardAward.period_key == period_key.strip())

    items, total = paginate_query(query, page, per_page)
    return success(
        {
            "list": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.get("/hall")
def get_admin_hall(
    year: Optional[int] = Query(default=None),
    page: int = Query(default=1),
    per_page: int = Query(default=0),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_admin_hall - 名人堂成员列表
    """
    from datetime import date
    from app.services.hall_induction import hall_stats

    page, per_page = _parse_page(page, per_page, db)
    query = db.query(HallMember)
    # 判断按年筛选
    if year is not None:
        query = query.filter(HallMember.inducted_year == year)
    query = query.order_by(HallMember.inducted_year.desc(), HallMember.id.desc())
    items, total = paginate_query(query, page, per_page)

    year_rows = db.query(HallMember.inducted_year).distinct().all()
    year_set = {row[0] for row in year_rows}
    today = date.today()
    for offset in range(6):
        year_set.add(today.year - offset)
    available_years = sorted(year_set, reverse=True)

    return success(
        {
            "list": [item.to_dict() for item in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "year": year,
            "stats": hall_stats(db),
            "available_years": available_years,
        }
    )


@router.post("/hall/evaluate")
def admin_evaluate_hall(
    year: Optional[int] = Query(default=None),
    include_annual: bool = Query(default=True),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    admin_evaluate_hall - 手动触发名人堂四条路径评定
    """
    from app.services.hall_induction import evaluate_hall_of_fame

    result = evaluate_hall_of_fame(
        db,
        year=year,
        notify=True,
        include_annual=include_annual,
        do_commit=True,
    )
    return success(result, message="名人堂评定完成")


@router.get("/titles")
def get_admin_titles(
    page: int = Query(default=1),
    per_page: int = Query(default=0),
    title_code: Optional[str] = Query(default=None),
    is_active: Optional[str] = Query(default=None),
    keyword: Optional[str] = Query(default=None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_admin_titles - 用户称号列表
    """
    page, per_page = _parse_page(page, per_page, db)
    query = db.query(UserTitle, User).join(User, UserTitle.user_id == User.id)

    title_code_text = (title_code or "").strip()
    # 判断称号编码筛选
    if title_code_text and title_code_text != "all":
        query = query.filter(UserTitle.title_code == title_code_text)

    # 判断有效状态筛选
    if is_active is not None and is_active != "" and is_active != "all":
        try:
            active_value = int(is_active)
        except ValueError:
            raise_error("状态参数不正确")
        query = query.filter(UserTitle.is_active == active_value)

    keyword_text = (keyword or "").strip()
    # 判断昵称关键词
    if keyword_text:
        query = query.filter(User.nickname.contains(keyword_text))

    query = query.order_by(UserTitle.granted_at.desc())
    items, total = paginate_query(query, page, per_page)
    title_list = []
    # 拼接用户昵称
    for title_item, user_item in items:
        row = title_item.to_dict()
        row["user_nickname"] = user_item.nickname
        title_list.append(row)
    return success(
        {
            "list": title_list,
            "total": total,
            "page": page,
            "per_page": per_page,
        }
    )


@router.post("/titles/evaluate")
def admin_evaluate_titles(
    user_id: Optional[int] = Query(default=None),
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    admin_evaluate_titles - 评定称号：指定用户或全量
    """
    from app.services.title_service import (
        evaluate_all_user_titles,
        evaluate_user_titles,
        sync_all_record_titles,
    )

    # 判断指定用户
    if user_id is not None:
        user_item = db.get(User, user_id)
        # 判断用户存在
        if user_item is None:
            raise_error("用户不存在", http_status=404)
        evaluate_user_titles(db, user_id)
        sync_all_record_titles(db)
        db.commit()
        return success({"user_id": user_id}, message="该用户称号已评定")

    result = evaluate_all_user_titles(db)
    db.commit()
    return success(result, message="全量称号评定完成")


@router.get("/first-records")
def get_admin_first_records(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    get_admin_first_records - 首个纪录墙
    """
    rows = (
        db.query(FirstSpeciesRecord)
        .order_by(FirstSpeciesRecord.caught_at.asc())
        .all()
    )
    return success({"list": [row.to_dict() for row in rows]})
