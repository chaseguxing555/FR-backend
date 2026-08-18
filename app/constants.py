"""
@file constants.py
@description 业务常量：鱼种、记录状态、审核动作等（对齐设计.md 三层榜单）
@module app.constants
@author fishing-ranking
@created 2026-08-11
@updated 2026-08-14
@version 2.0.0
"""


# ---------- 第二层：按钓法独立的上榜鱼种（设计.md §二） ----------

# 手竿（7 种）
HAND_POLE_SPECIES = [
    "鲫鱼",
    "鲤鱼",
    "草鱼",
    "鳊鱼",
    "黄辣丁",
    "翘嘴",
    "鳜鱼",
]

# 路亚（6 种）
LURE_SPECIES = [
    "翘嘴",
    "鳜鱼",
    "鲈鱼",
    "黑鱼",
    "马口",
    "鳡鱼",
]

# 水底 / 远投·海竿（5 种）
BOTTOM_SPECIES = [
    "青鱼",
    "鲢鳙",
    "鲤鱼",
    "草鱼",
    "鲶鱼",
]

# 各钓法上榜鱼种（同鱼种在不同钓法下分榜，互不混排）
FISHING_METHOD_SPECIES_MAP = {
    "手竿": HAND_POLE_SPECIES,
    "路亚": LURE_SPECIES,
    "水底": BOTTOM_SPECIES,
}

# 不设榜单鱼种：可上传个人记录，不进入全国排名（设计.md §三）
PERSONAL_ONLY_SPECIES = [
    "白条",
    "麦穗鱼",
    "鳑鲏",
    "趴地虎",
    "泥鳅",
]

# 上传可选鱼种 = 上榜鱼种 + 不设榜鱼种
UPLOAD_METHOD_SPECIES_MAP = {
    method_name: list(species_list) + list(PERSONAL_ONLY_SPECIES)
    for method_name, species_list in FISHING_METHOD_SPECIES_MAP.items()
}

# 全部鱼种（上榜 + 个人，去重保序）
FISH_SPECIES_LIST = list(
    dict.fromkeys(
        HAND_POLE_SPECIES
        + LURE_SPECIES
        + BOTTOM_SPECIES
        + PERSONAL_ONLY_SPECIES
    )
)

# 上榜鱼种合计（去重）
RANKING_SPECIES_LIST = list(
    dict.fromkeys(HAND_POLE_SPECIES + LURE_SPECIES + BOTTOM_SPECIES)
)

# ---------- 月度精选榜：10 个热门鱼种 + 最低上榜门槛（公斤，由斤换算） ----------
# 设计文档门槛单位为斤，1 斤 = 0.5 kg
MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG = {
    "鲤鱼": 1.0,  # ≥ 2 斤
    "鲫鱼": 0.25,  # ≥ 0.5 斤
    "草鱼": 1.0,  # ≥ 2 斤
    "翘嘴": 0.5,  # ≥ 1 斤
    "青鱼": 2.5,  # ≥ 5 斤
    "鲢鳙": 2.5,  # ≥ 5 斤
    "鳜鱼": 0.5,  # ≥ 1 斤
    "黑鱼": 0.75,  # ≥ 1.5 斤
    "鲈鱼": 0.5,  # ≥ 1 斤
    "鳊鱼": 0.25,  # ≥ 0.5 斤
}

MONTHLY_HOT_SPECIES = list(MONTHLY_HOT_SPECIES_MIN_WEIGHT_KG.keys())

# 钓法列表：排行榜 / 上传按钓法分榜
FISHING_METHOD_LIST = [
    "手竿",
    "路亚",
    "水底",
]

# 默认钓法
DEFAULT_FISHING_METHOD = FISHING_METHOD_LIST[0]

# 用户状态：1 正常，0 禁用
USER_STATUS_NORMAL = 1
USER_STATUS_DISABLED = 0

# 鱼获记录状态：0 待审核，1 已通过，2 已拒绝
CATCH_STATUS_PENDING = 0
CATCH_STATUS_APPROVED = 1
CATCH_STATUS_REJECTED = 2

# 审核动作：1 通过，2 拒绝
AUDIT_ACTION_APPROVE = 1
AUDIT_ACTION_REJECT = 2

# 排行榜默认每页条数
RANKING_PER_PAGE = 20

# 重量校验：必须 > 0，最大不超过 200kg
WEIGHT_MIN = 0
WEIGHT_MAX = 200

# 昵称最大长度
NICKNAME_MAX_LENGTH = 20

# 密码最小长度
PASSWORD_MIN_LENGTH = 6

# 备注最大长度
DESCRIPTION_MAX_LENGTH = 200

# 具体钓点最大长度
LOCATION_DETAIL_MAX_LENGTH = 100

# 饵料最大长度
BAIT_MAX_LENGTH = 50

# 站内消息类型
NOTIFICATION_TYPE_AUDIT_PASS = "audit_pass"
NOTIFICATION_TYPE_AUDIT_REJECT = "audit_reject"
NOTIFICATION_TYPE_REWARD_MONTHLY = "reward_monthly"
NOTIFICATION_TYPE_REWARD_YEARLY = "reward_yearly"
NOTIFICATION_TYPE_TITLE = "title_grant"
NOTIFICATION_TYPE_SURPASSED = "record_surpassed"
NOTIFICATION_TYPE_HALL = "hall_induct"

# 消息已读状态：0 未读，1 已读
NOTIFICATION_UNREAD = 0
NOTIFICATION_READ = 1

# ---------- 名人堂（名人堂设计.md） ----------
# 路径
HALL_PATH_ANNUAL = "annual_champion"
HALL_PATH_RECORD = "record_keeper"
HALL_PATH_LEGEND = "legend_angler"
HALL_PATH_DOMINATE = "dominate_master"

# 层级
HALL_TIER_LEGEND = "legend"
HALL_TIER_RECORD = "record"
HALL_TIER_MASTER = "master"

HALL_TIER_META = {
    HALL_TIER_LEGEND: {
        "name": "传奇级",
        "title": "传奇钓手",
        "badge": "传奇",
        "color": "gold",
    },
    HALL_TIER_RECORD: {
        "name": "纪录级",
        "title": "纪录之王",
        "badge": "纪录",
        "color": "amber",
    },
    HALL_TIER_MASTER: {
        "name": "大师级",
        "title": "全能大师",
        "badge": "大师",
        "color": "silver",
    },
}

# 全国纪录保持入堂：连续保持月数
HALL_RECORD_HOLD_MONTHS = 6

# 传奇钓手：连续年数 TOP3
HALL_LEGEND_STREAK_YEARS = 3
HALL_LEGEND_TOP_N = 3

# ---------- 称号体系（荣誉系统设计.md） ----------
# 累计重量门槛：设计文档为斤，1 斤 = 0.5 kg
TITLE_HUNDRED_JIN_KG = 50.0
TITLE_THOUSAND_JIN_KG = 500.0

# 称号编码
TITLE_FOUNDING_ELDER = "founding_elder"
TITLE_CARP_KING = "carp_king"
TITLE_CRUCIAN_SAINT = "crucian_saint"
TITLE_MONTHLY_TOP10 = "monthly_top10"
TITLE_HUNDRED_JIN = "hundred_jin"
TITLE_THOUSAND_JIN = "thousand_jin"
TITLE_DOMINATE_HAND = "dominate_hand"
TITLE_DOMINATE_LURE = "dominate_lure"
TITLE_DOMINATE_BOTTOM = "dominate_bottom"
TITLE_STREAK_3 = "streak_3"
TITLE_STREAK_6 = "streak_6"
TITLE_YEARLY_CELEBRITY = "yearly_celebrity"

# 称号元数据：名称 / 颜色 / 图标文件 / 展示位 / 优先级（越大越优先昵称旁展示）
TITLE_DEFINITIONS = {
    TITLE_FOUNDING_ELDER: {
        "name": "开榜元老",
        "color": "gold",
        "icon": "title-founding-elder.png",
        "display": "nickname",
        "priority": 90,
        "description": "上线前注册并在上线 7 天内上传首条记录",
    },
    TITLE_CARP_KING: {
        "name": "鲤王",
        "color": "amber",
        "icon": "title-carp-king.png",
        "display": "nickname",
        "priority": 100,
        "description": "当前鲤鱼全国纪录保持者",
    },
    TITLE_CRUCIAN_SAINT: {
        "name": "鲫圣",
        "color": "amber",
        "icon": "title-crucian-saint.png",
        "display": "nickname",
        "priority": 100,
        "description": "当前鲫鱼全国纪录保持者",
    },
    TITLE_MONTHLY_TOP10: {
        "name": "月度上榜者",
        "color": "silver",
        "icon": "title-monthly-top10.png",
        "display": "wall",
        "priority": 40,
        "description": "当月进入任意鱼种 TOP 10",
    },
    TITLE_HUNDRED_JIN: {
        "name": "百斤俱乐部",
        "color": "gold",
        "icon": "title-hundred-jin.png",
        "display": "nickname",
        "priority": 70,
        "description": "累计上传总重量 ≥ 100 斤",
    },
    TITLE_THOUSAND_JIN: {
        "name": "千斤大神",
        "color": "gold_diamond",
        "icon": "title-thousand-jin.png",
        "display": "nickname",
        "priority": 95,
        "description": "累计上传总重量 ≥ 1000 斤",
    },
    TITLE_DOMINATE_HAND: {
        "name": "全鱼种制霸（手竿）",
        "color": "rainbow",
        "icon": "title-dominate.png",
        "display": "nickname",
        "priority": 80,
        "description": "手竿下全部鱼种均有上榜记录",
    },
    TITLE_DOMINATE_LURE: {
        "name": "全鱼种制霸（路亚）",
        "color": "rainbow",
        "icon": "title-dominate.png",
        "display": "nickname",
        "priority": 80,
        "description": "路亚下全部鱼种均有上榜记录",
    },
    TITLE_DOMINATE_BOTTOM: {
        "name": "全鱼种制霸（水底）",
        "color": "rainbow",
        "icon": "title-dominate.png",
        "display": "nickname",
        "priority": 80,
        "description": "水底下全部鱼种均有上榜记录",
    },
    TITLE_STREAK_3: {
        "name": "连冠王者（3个月）",
        "color": "silver",
        "icon": "title-streak-3.png",
        "display": "nickname",
        "priority": 60,
        "description": "连续 3 个月在同一鱼种榜上有名",
    },
    TITLE_STREAK_6: {
        "name": "连冠王者（6个月）",
        "color": "gold",
        "icon": "title-streak-6.png",
        "display": "nickname",
        "priority": 85,
        "description": "连续 6 个月在同一鱼种榜上有名",
    },
    TITLE_YEARLY_CELEBRITY: {
        "name": "年度名人",
        "color": "gold_year",
        "icon": "title-yearly-celebrity.png",
        "display": "wall",
        "priority": 75,
        "description": "进入年度任何鱼种 TOP 3",
    },
}

# 纪录称号：鱼种 → 称号编码
SPECIES_RECORD_TITLE_MAP = {
    "鲤鱼": TITLE_CARP_KING,
    "鲫鱼": TITLE_CRUCIAN_SAINT,
}

# 全鱼种制霸：钓法 → 称号
DOMINATE_TITLE_MAP = {
    "手竿": TITLE_DOMINATE_HAND,
    "路亚": TITLE_DOMINATE_LURE,
    "水底": TITLE_DOMINATE_BOTTOM,
}

# ---------- 奖励结算 ----------
REWARD_PERIOD_MONTH = "month"
REWARD_PERIOD_YEAR = "year"
REWARD_AWARD_MONTHLY_METHOD = "monthly_method"
REWARD_AWARD_MONTHLY_OVERALL = "monthly_overall"
REWARD_AWARD_YEARLY_METHOD = "yearly_method"
REWARD_AWARD_YEARLY_OVERALL = "yearly_overall"
REWARD_AWARD_META = {
    REWARD_AWARD_MONTHLY_METHOD: {
        "title_template": "{period}{method}月冠军",
        "prizes": "电子徽章 + 专区展示",
    },
    REWARD_AWARD_MONTHLY_OVERALL: {
        "title_template": "{period}月榜总冠军",
        "prizes": "定制纪念章 + 电子证书 + 首页荣耀展示",
    },
    REWARD_AWARD_YEARLY_METHOD: {
        "title_template": "{period}{method}年度总冠军",
        "prizes": "专属刻名鱼竿套装 + 永久名人堂",
    },
    REWARD_AWARD_YEARLY_OVERALL: {
        "title_template": "{period}年度全榜总冠军",
        "prizes": "竿套装任选一套 + 冠军戒指",
    },
}
