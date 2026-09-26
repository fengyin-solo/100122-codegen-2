import { defineStore } from 'pinia'

import { fetchJson } from '@/api/client'

export type OverviewCard = {
  key: string
  label: string
  value: number
  drilldown: boolean
}

export type OverviewModule = {
  key: string
  name: string
  path: string
  created: number
  pending: number
  abnormal: number
  total: number
  last_record: string | null
  empty: boolean
}

export type Overview = {
  range: string
  range_label: string
  ranges: { key: string; label: string }[]
  cards: OverviewCard[]
  modules: OverviewModule[]
}

const STORAGE_KEY = 'dashboard.range'

function loadRange(): string {
  try {
    return sessionStorage.getItem(STORAGE_KEY) ?? '30d'
  } catch {
    return '30d'
  }
}

/**
 * 看板状态独立成 store：统计区间是用户的会话级选择，
 * 从看板跳进模块再返回时（Dashboard 重新挂载）沿用上次区间，
 * 而不是每次回到看板都跳回默认的近 30 天。
 */
export const useDashboardStore = defineStore('dashboard', {
  state: () => ({
    range: loadRange(),
    data: null as Overview | null,
    loading: false,
    errorMessage: '',
  }),
  actions: {
    persistRange() {
      try {
        sessionStorage.setItem(STORAGE_KEY, this.range)
      } catch {
        /* 隐私模式等场景下 sessionStorage 不可用时静默退化为内存态 */
      }
    },
    async load() {
      this.loading = true
      this.errorMessage = ''
      try {
        this.data = await fetchJson<Overview>(`/api/overview?range=${encodeURIComponent(this.range)}`)
        // 以服务端认可的区间为准，防止本地存了历史版本已不支持的值。
        this.range = this.data.range
        this.persistRange()
      } catch (error) {
        this.errorMessage = error instanceof Error ? error.message : '运营概览读取失败'
      } finally {
        this.loading = false
      }
    },
    async switchRange(range: string) {
      if (range === this.range) return
      this.range = range
      this.persistRange()
      await this.load()
    },
  },
})
