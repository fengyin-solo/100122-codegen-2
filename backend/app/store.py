"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.seed import SEED_ROWS

# 看板模块元数据：顺序、名称、路径都与左侧导航一一对应，
# 看板下钻跳转直接使用这里的 path，避免两边各写一份对不上。
MODULES: list[dict[str, str]] = [
    {"key": "fleet", "name": "车辆档案", "path": "/fleet"},
    {"key": "driver", "name": "司机管理", "path": "/driver"},
    {"key": "order", "name": "运输委托", "path": "/order"},
    {"key": "dispatch3", "name": "运力调度", "path": "/dispatch3"},
    {"key": "temp", "name": "温控监测", "path": "/temp"},
    {"key": "door", "name": "门到门配送", "path": "/door"},
    {"key": "returntrip", "name": "回单管理", "path": "/returntrip"},
    {"key": "abnormal2", "name": "异常处置", "path": "/abnormal2"},
    {"key": "renew", "name": "续运中转", "path": "/renew"},
    {"key": "refriger", "name": "制冷机组", "path": "/refriger"},
    {"key": "box", "name": "温控箱体", "path": "/box"},
    {"key": "route", "name": "运输路线", "path": "/route"},
    {"key": "sensor", "name": "温感器管理", "path": "/sensor"},
    {"key": "cost", "name": "运输费用", "path": "/cost"},
    {"key": "client2", "name": "委托方管理", "path": "/client2"},
    {"key": "checkin", "name": "出车检查", "path": "/checkin"},
    {"key": "accident", "name": "事故记录", "path": "/accident"},
    {"key": "roadcheck", "name": "途中核查", "path": "/roadcheck"},
    {"key": "clean2", "name": "车厢清洗", "path": "/clean2"},
    {"key": "contract2", "name": "合作合同", "path": "/contract2"},
]

# 统计区间：days 为从今天往前推的天数（含今天）；全部则不过滤。
RANGE_OPTIONS: list[dict[str, Any]] = [
    {"key": "today", "label": "今日", "days": 0},
    {"key": "7d", "label": "近7天", "days": 6},
    {"key": "30d", "label": "近30天", "days": 29},
    {"key": "all", "label": "全部", "days": None},
]
DEFAULT_RANGE = "30d"
_RANGE_MAP = {option["key"]: option for option in RANGE_OPTIONS}


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {
            name: [dict(row) for row in rows] for name, rows in SEED_ROWS.items()
        }

    def module_names(self) -> list[str]:
        return sorted(self._tables)

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def record_time(self, position: int, row: dict[str, Any]) -> date | None:
        """取一条记录最近的业务日期。

        多数模块本身带日期字段（记录时间、发生时间、签约日期等），直接解析其中最晚的一天；
        少数档案类模块没有日期列，按模块位次与记录 id 补一个稳定的登记日期，
        这样看板的「最近一条记录」始终有值，且同一行每次算出来都一致。
        """
        candidates: list[date] = []
        for value in row.values():
            if isinstance(value, str) and len(value) >= 10:
                try:
                    candidates.append(datetime.strptime(value[:10], "%Y-%m-%d").date())
                except ValueError:
                    continue
        if candidates:
            return max(candidates)
        entry_no = max(int(row.get("id", 1)) - 1, 0)
        days_ago = 25 - (position % 7) - entry_no
        return date.today() - timedelta(days=max(days_ago, 0))

    def overview(self, range_key: str = DEFAULT_RANGE) -> dict[str, object]:
        """运营概览：按统计区间汇总各模块新增/待处理/异常量，并给出最近记录时间。"""
        option = _RANGE_MAP.get(range_key)
        if option is None:
            valid = "、".join(item["key"] for item in RANGE_OPTIONS)
            raise ValueError(f"不支持的统计区间「{range_key}」，可选：{valid}")

        today = date.today()
        start = None if option["days"] is None else today - timedelta(days=int(option["days"]))

        modules: list[dict[str, object]] = []
        for position, meta in enumerate(MODULES):
            timed_rows = [
                (row, self.record_time(position, row))
                for row in self.rows(meta["key"])
            ]
            if start is None:
                in_range = timed_rows
            else:
                in_range = [
                    (row, recorded)
                    for row, recorded in timed_rows
                    if recorded is not None and start <= recorded <= today
                ]
            created = len(in_range)
            pending = sum(1 for row, _ in in_range if row.get("pending"))
            abnormal = sum(1 for row, _ in in_range if row.get("abnormal"))
            latest = max((recorded for _, recorded in in_range if recorded), default=None)
            modules.append({
                **meta,
                "created": created,
                "pending": pending,
                "abnormal": abnormal,
                "total": len(timed_rows),
                "last_record": latest.isoformat() if latest else None,
                "empty": created == 0,
            })

        # 积压多的排前面：待处理降序，其次异常量，再次模块名兜底，保证顺序稳定。
        modules.sort(key=lambda item: (-int(item["pending"]), -int(item["abnormal"]), str(item["name"])))

        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules), "drilldown": False},
            {
                "key": "created",
                "label": f"{option['label']}新增",
                "value": sum(int(item["created"]) for item in modules),
                "drilldown": True,
            },
            {
                "key": "pending",
                "label": "待处理",
                "value": sum(int(item["pending"]) for item in modules),
                "drilldown": True,
            },
            {
                "key": "abnormal",
                "label": "异常量",
                "value": sum(int(item["abnormal"]) for item in modules),
                "drilldown": True,
            },
        ]
        return {
            "range": range_key,
            "range_label": option["label"],
            "ranges": [{"key": item["key"], "label": item["label"]} for item in RANGE_OPTIONS],
            "cards": cards,
            "modules": modules,
        }


store = Store()
