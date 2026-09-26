import { defineStore } from 'pinia'

import { fetchJson } from '@/api/client'

/** 统计区间，与后端 store.RANGE_DAYS 的 key 保持一致。 */
export type RangeKey = 'today' | '7d' | '30d' | 'all'

export const RANGE_OPTIONS: { key: RangeKey; label: string }[] = [
  { key: 'today', label: '今日' },
  { key: '7d', label: '近7天' },
  { key: '30d', label: '近30天' },
  { key: 'all', label: '全部' },
]

export type CardKey = 'modules' | 'created' | 'pending' | 'abnormal'

export interface OverviewCard {
  key: CardKey
  label: string
  value: number
}

export interface ModuleStat {
  key: string
  /** 模块中文名，与左侧导航一致 */
  name: string
  /** 模块路由，与左侧导航入口一致 */
  path: string
  order: number
  /** 区间新增：区间内没有记录时为 null，前端显示“暂无”而不是 0 */
  created: number | null
  /** 待处理量：区间内没有记录时为 null */
  pending: number | null
  /** 异常量：区间内没有记录时为 null */
  abnormal: number | null
  /** 最近一条记录的时间 */
  lastTime: string | null
  hasData: boolean
}

interface OverviewPayload {
  range: RangeKey
  cards: OverviewCard[]
  modules: ModuleStat[]
}

const RANGE_STORAGE_KEY = 'dashboard.range'
const CARD_STORAGE_KEY = 'dashboard.activeCard'

function readStoredRange(): RangeKey {
  const saved = sessionStorage.getItem(RANGE_STORAGE_KEY)
  return RANGE_OPTIONS.some((item) => item.key === saved) ? (saved as RangeKey) : '30d'
}

function readStoredCard(): CardKey {
  const saved = sessionStorage.getItem(CARD_STORAGE_KEY)
  const valid: CardKey[] = ['modules', 'created', 'pending', 'abnormal']
  return (valid as string[]).includes(saved ?? '') ? (saved as CardKey) : 'pending'
}

interface State {
  range: RangeKey
  activeCard: CardKey
  /** 每个区间各缓存一份：从模块返回时数字与离开前保持一致，不重新拉取。 */
  cache: Partial<Record<RangeKey, OverviewPayload>>
  loading: boolean
  errorMessage: string
}

export const useDashboardStore = defineStore('dashboard', {
  state: (): State => ({
    range: readStoredRange(),
    activeCard: readStoredCard(),
    cache: {},
    loading: false,
    errorMessage: '',
  }),
  getters: {
    overview(state): OverviewPayload | null {
      return state.cache[state.range] ?? null
    },
    cards(state): OverviewCard[] {
      return state.cache[state.range]?.cards ?? []
    },
  },
  actions: {
    setRange(range: RangeKey) {
      if (range === this.range) return
      this.range = range
      sessionStorage.setItem(RANGE_STORAGE_KEY, range)
      void this.ensureLoaded()
    },
    setActiveCard(card: CardKey) {
      this.activeCard = card
      sessionStorage.setItem(CARD_STORAGE_KEY, card)
    },
    /**
     * 进入看板时拉取当前区间的数据：
     * - 已有缓存（从模块页返回）时先用缓存渲染，再后台静默刷新，
     *   用户在模块里做过状态流转也能让卡片数字与模块页保持一致；
     * - 没有缓存时进入加载态；force 用于“刷新数据”按钮。
     * 区间与当前下钻卡片存在 sessionStorage，不会随拉取跳回默认。
     */
    async ensureLoaded(force = false) {
      const hadCache = !force && !!this.cache[this.range]
      if (!hadCache) {
        this.loading = true
        this.errorMessage = ''
      }
      try {
        const payload = await fetchJson<OverviewPayload>(`/api/overview?range=${this.range}`)
        this.cache[payload.range] = payload
      } catch (error) {
        if (!hadCache) {
          this.errorMessage = error instanceof Error ? error.message : '运营概览读取失败'
        }
      } finally {
        if (!hadCache) {
          this.loading = false
        }
      }
    },
  },
})
