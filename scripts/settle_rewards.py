"""
@file settle_rewards.py
@description 命令行手动触发月榜 / 年榜结算
@module scripts.settle_rewards
@author fishing-ranking
@created 2026-08-14
@version 1.0.0

用法：
  cd backend
  python -m scripts.settle_rewards --month 2026-08
  python -m scripts.settle_rewards --year 2025
  python -m scripts.settle_rewards --previous-month
  python -m scripts.settle_rewards --previous-year
"""

import argparse
import json
import sys

from app.database import SessionLocal
from app.services.reward_settlement import (
    previous_month,
    previous_year,
    settle_month,
    settle_year,
)
from app.utils.schema import ensure_schema


def main(argv=None):
    """
    main - 解析参数并执行结算
    """
    parser = argparse.ArgumentParser(description="野钓记录榜 · 奖励结算")
    parser.add_argument("--month", help="结算指定月，格式 YYYY-MM")
    parser.add_argument("--year", type=int, help="结算指定年，格式 YYYY")
    parser.add_argument("--previous-month", action="store_true", help="结算上个月")
    parser.add_argument("--previous-year", action="store_true", help="结算上一年")
    parser.add_argument("--force", action="store_true", help="强制重算")
    args = parser.parse_args(argv)

    ensure_schema()
    database = SessionLocal()
    try:
        result = None
        # 判断结算指定月
        if args.month:
            year_text, month_text = args.month.split("-")
            result = settle_month(
                database, int(year_text), int(month_text), force=args.force
            )
        # 判断结算指定年
        elif args.year:
            result = settle_year(database, args.year, force=args.force)
        # 判断结算上月
        elif args.previous_month:
            year_number, month_number = previous_month()
            result = settle_month(database, year_number, month_number, force=args.force)
        # 判断结算上年
        elif args.previous_year:
            result = settle_year(database, previous_year(), force=args.force)
        else:
            parser.print_help()
            return 1

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        database.close()


if __name__ == "__main__":
    sys.exit(main())
