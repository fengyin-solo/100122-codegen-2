/** 左侧导航与概览看板共用的模块入口清单。
 *  key/path 必须与后端 /api/overview 返回的模块 key 及路由一一对应，
 *  这样从看板点进模块、再从左侧导航进入，看到的是同一个页面。
 */
export interface NavEntry {
  /** 后端模块 key，与概览接口 modules[].key 一致 */
  key: string
  /** 左侧导航与下钻列表里显示的中文名 */
  label: string
  /** 前端路由路径，与 router/index.ts 对应 */
  path: string
}

export const NAV_ENTRIES: NavEntry[] = [
  { key: 'fleet', label: '车辆档案', path: '/fleet' },
  { key: 'driver', label: '司机管理', path: '/driver' },
  { key: 'order', label: '运输委托', path: '/order' },
  { key: 'dispatch3', label: '运力调度', path: '/dispatch3' },
  { key: 'temp', label: '温控监测', path: '/temp' },
  { key: 'door', label: '门到门配送', path: '/door' },
  { key: 'returntrip', label: '回单管理', path: '/returntrip' },
  { key: 'abnormal2', label: '异常处置', path: '/abnormal2' },
  { key: 'renew', label: '续运中转', path: '/renew' },
  { key: 'refriger', label: '制冷机组', path: '/refriger' },
  { key: 'box', label: '温控箱体', path: '/box' },
  { key: 'route', label: '运输路线', path: '/route' },
  { key: 'sensor', label: '温感器管理', path: '/sensor' },
  { key: 'cost', label: '运输费用', path: '/cost' },
  { key: 'client2', label: '委托方管理', path: '/client2' },
  { key: 'checkin', label: '出车检查', path: '/checkin' },
  { key: 'accident', label: '事故记录', path: '/accident' },
  { key: 'roadcheck', label: '途中核查', path: '/roadcheck' },
  { key: 'clean2', label: '车厢清洗', path: '/clean2' },
  { key: 'contract2', label: '合作合同', path: '/contract2' },
]

/** 路由里没有业务页面的模块仍会在导航中展示；这里的映射用于下钻跳转兜底。 */
export const MODULE_PATH: Record<string, string> = Object.fromEntries(
  NAV_ENTRIES.map((entry) => [entry.key, entry.path]),
)
