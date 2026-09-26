"""内存数据仓库：给每个业务模块准备一份可筛选、可流转的示例数据。

真实项目里这里会换成数据库访问层；当前实现只依赖标准库，保证克隆下来就能起。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from app.modules_meta import MODULE_KEYS, MODULE_LABELS, MODULE_TIME_FIELDS, MODULES
from app.seed import SEED_ROWS

# 概览看板支持的统计区间：today 当天、7d/30d 近 N 天、all 不限。
RANGE_DAYS: dict[str, int | None] = {"today": 0, "7d": 7, "30d": 30, "all": None}
DEFAULT_RANGE = "30d"

# 没有业务时间字段的模块，示例数据用一个固定基准日补出记录时间，
# 保证这些模块在近 30 天区间内也能看到“最近一条记录”。
_SEED_BASE = date(2026, 9, 1)


def _parse_date(value: Any) -> datetime | None:
    """尽量把记录上的时间值解析成 datetime；解析不了就当作没有时间。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _format_time(value: datetime | None) -> str | None:
    """概览只展示到分钟；记录上只有日期时不带 00:00，避免误导。"""
    if value is None:
        return None
    if value.hour == 0 and value.minute == 0 and value.second == 0:
        return value.strftime("%Y-%m-%d")
    return value.strftime("%Y-%m-%d %H:%M")


class Store:
    def __init__(self) -> None:
        self._tables: dict[str, list[dict[str, Any]]] = {}
        for index, meta in enumerate(MODULES):
            rows = [dict(row) for row in SEED_ROWS.get(meta.key, [])]
            self._tables[meta.key] = rows
            for row in rows:
                row["created_at"] = self._seed_time(meta, row, index)

    @staticmethod
    def _seed_time(meta: tuple[str, str, str | None], row: dict[str, Any], module_index: int) -> str:
        """示例记录的时间：优先取模块的业务时间字段，没有就按基准日补一个。"""
        time_field = MODULE_TIME_FIELDS.get(meta[0])
        parsed = _parse_date(row.get(time_field)) if time_field else None
        if parsed is None:
            parsed = datetime.combine(_SEED_BASE + timedelta(days=module_index), datetime.min.time())
        return parsed.strftime("%Y-%m-%d %H:%M:%S")

    def module_names(self) -> list[str]:
        """按左侧导航顺序返回模块 key。"""
        return [key for key in MODULE_KEYS if key in self._tables]

    def rows(self, module: str) -> list[dict[str, Any]]:
        return self._tables.setdefault(module, [])

    def add_row(self, module: str, entry: dict[str, Any]) -> dict[str, Any]:
        """登记新记录时统一补上 created_at，概览的“最近记录时间”才有依据。"""
        entry["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.rows(module).append(entry)
        return entry

    def find(self, module: str, entry_id: int) -> dict[str, Any] | None:
        for row in self.rows(module):
            if int(row.get("id", 0)) == entry_id:
                return row
        return None

    def overview(self, range_key: str = DEFAULT_RANGE) -> dict[str, object]:
        """按统计区间汇总各模块：待处理量、异常量、区间新增与最近记录时间。

        区间内一条记录都没有的模块，各项指标返回 None，由前端显示“暂无”，
        而不是一律显示成 0。
        """
        days = RANGE_DAYS.get(range_key)
        cutoff: datetime | None = None
        if days is not None:
            today = datetime.now().date()
            cutoff = datetime.combine(today - timedelta(days=days), datetime.min.time())

        modules: list[dict[str, object]] = []
        for order, key in enumerate(self.module_names()):
            rows = self.rows(key)
            scoped = [row for row in rows if self._in_range(row, cutoff)]
            if scoped:
                created = len(scoped)
                pending = sum(1 for row in scoped if row.get("pending"))
                abnormal = sum(1 for row in scoped if row.get("abnormal"))
                latest = max(
                    (parsed for parsed in (self._record_time(key, row) for row in scoped) if parsed),
                    default=None,
                )
                last_time = _format_time(latest)
            else:
                created = pending = abnormal = None
                last_time = None
            modules.append({
                "key": key,
                "name": MODULE_LABELS.get(key, key),
                "path": f"/{key}",
                "order": order,
                "created": created,
                "pending": pending,
                "abnormal": abnormal,
                "lastTime": last_time,
                "hasData": bool(scoped),
            })

        def present(value: object) -> int:
            return int(value) if value is not None else 0

        cards = [
            {"key": "modules", "label": "业务模块", "value": len(modules)},
            {"key": "created", "label": "区间新增", "value": sum(present(item["created"]) for item in modules)},
            {"key": "pending", "label": "待处理", "value": sum(present(item["pending"]) for item in modules)},
            {"key": "abnormal", "label": "异常量", "value": sum(present(item["abnormal"]) for item in modules)},
        ]
        return {"range": range_key, "cards": cards, "modules": modules}

    @staticmethod
    def _in_range(row: dict[str, Any], cutoff: datetime | None) -> bool:
        if cutoff is None:
            return True
        record_time = _parse_date(row.get("created_at"))
        return record_time is not None and record_time >= cutoff

    @staticmethod
    def _record_time(module: str, row: dict[str, Any]) -> datetime | None:
        """最近记录时间优先用业务时间字段，其次用 created_at。"""
        time_field = MODULE_TIME_FIELDS.get(module)
        if time_field:
            parsed = _parse_date(row.get(time_field))
            if parsed is not None:
                return parsed
        return _parse_date(row.get("created_at"))


store = Store()
