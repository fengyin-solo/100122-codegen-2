"""业务模块元数据：概览看板与左侧导航共用同一份模块清单。

key 为后端表名/路由前缀，label 为左侧导航里的中文模块名，
time_field 指向该模块记录上最能代表“最近一条记录时间”的业务字段；
个别模块没有时间字段（如司机管理、运输委托），记为 None，
由 store 在写入时统一补 created_at。
"""
from __future__ import annotations

from typing import NamedTuple


class ModuleMeta(NamedTuple):
    key: str
    label: str
    time_field: str | None


# 顺序即左侧导航的排列顺序，也是概览数据的默认顺序。
MODULES: tuple[ModuleMeta, ...] = (
    ModuleMeta("fleet", "车辆档案", "购置日期"),
    ModuleMeta("driver", "司机管理", None),
    ModuleMeta("order", "运输委托", None),
    ModuleMeta("dispatch3", "运力调度", None),
    ModuleMeta("temp", "温控监测", "记录时间"),
    ModuleMeta("door", "门到门配送", "计划时段"),
    ModuleMeta("returntrip", "回单管理", "签收日期"),
    ModuleMeta("abnormal2", "异常处置", "发生时间"),
    ModuleMeta("renew", "续运中转", "中转时间"),
    ModuleMeta("refriger", "制冷机组", None),
    ModuleMeta("box", "温控箱体", "出库日期"),
    ModuleMeta("route", "运输路线", None),
    ModuleMeta("sensor", "温感器管理", "校准日期"),
    ModuleMeta("cost", "运输费用", "费用日期"),
    ModuleMeta("client2", "委托方管理", "签约日期"),
    ModuleMeta("checkin", "出车检查", "检查日期"),
    ModuleMeta("accident", "事故记录", "发生时间"),
    ModuleMeta("roadcheck", "途中核查", "核查时间"),
    ModuleMeta("clean2", "车厢清洗", "清洗日期"),
    ModuleMeta("contract2", "合作合同", "签约日期"),
)

MODULE_KEYS: tuple[str, ...] = tuple(item.key for item in MODULES)
MODULE_LABELS: dict[str, str] = {item.key: item.label for item in MODULES}
MODULE_TIME_FIELDS: dict[str, str | None] = {item.key: item.time_field for item in MODULES}
