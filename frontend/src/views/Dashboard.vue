<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，点击卡片可下钻查看各模块的待处理量与异常量。</p>
      </div>
      <div class="page-actions">
        <div class="range-switch" role="group" aria-label="统计区间">
          <button
            v-for="option in rangeOptions"
            :key="option.key"
            type="button"
            class="range-btn"
            :class="{ active: option.key === store.range }"
            @click="store.setRange(option.key)"
          >
            {{ option.label }}
          </button>
        </div>
        <button class="btn" type="button" :disabled="store.loading" @click="refresh">
          {{ store.loading ? '刷新中…' : '刷新数据' }}
        </button>
      </div>
    </header>

    <div class="stat-row">
      <article
        v-for="card in store.cards"
        :key="card.key"
        class="stat-card stat-card-btn"
        :class="{ active: card.key === store.activeCard }"
        role="button"
        tabindex="0"
        @click="store.setActiveCard(card.key)"
        @keydown.enter="store.setActiveCard(card.key)"
        @keydown.space.prevent="store.setActiveCard(card.key)"
      >
        <span class="stat-label">{{ card.label }}</span>
        <strong class="stat-value">{{ card.value }}</strong>
        <span class="stat-hint">点击查看模块明细</span>
      </article>
    </div>

    <section class="drill-panel">
      <header class="drill-head">
        <h3>{{ activeTitle }}</h3>
        <span class="drill-sub">按待处理量排列，模块名后标注该模块最近一条记录的时间</span>
      </header>
      <table class="data-table">
        <thead>
          <tr>
            <th>业务模块（最近记录时间）</th>
            <th>待处理量</th>
            <th>异常量</th>
            <th v-if="showCreated">区间新增</th>
            <th>模块入口</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in panelRows" :key="row.key" :class="{ 'is-empty': !row.hasData }">
            <td>
              <RouterLink class="module-link" :to="row.path">{{ row.name }}</RouterLink>
              <span class="last-time">{{ row.lastTime ? `最近记录 ${row.lastTime}` : '暂无记录' }}</span>
            </td>
            <td>{{ display(row.pending) }}</td>
            <td>{{ display(row.abnormal) }}</td>
            <td v-if="showCreated">{{ display(row.created) }}</td>
            <td>
              <RouterLink class="link" :to="row.path">进入模块</RouterLink>
            </td>
          </tr>
          <tr v-if="!panelRows.length">
            <td :colspan="showCreated ? 5 : 4" class="empty-state">
              {{ store.loading ? '数据加载中…' : emptyHint }}
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="store.errorMessage" class="error-text">{{ store.errorMessage }}</p>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'

import {
  RANGE_OPTIONS as rangeOptions,
  useDashboardStore,
  type CardKey,
  type ModuleStat,
} from '@/stores/dashboard'

const store = useDashboardStore()

const CARD_TITLES: Record<CardKey, string> = {
  modules: '各业务模块明细',
  created: '区间新增下钻：模块新增情况',
  pending: '待处理下钻：各模块积压情况',
  abnormal: '异常下钻：各模块异常情况',
}

const activeTitle = computed(() => CARD_TITLES[store.activeCard])
const showCreated = computed(() => store.activeCard === 'created')

/** 待处理量降序优先；异常量、区间新增、导航顺序依次兜底，保证切换区间后顺序跟着变。 */
function compareModules(a: ModuleStat, b: ModuleStat): number {
  if (a.hasData !== b.hasData) return a.hasData ? -1 : 1
  const pendingDiff = (b.pending ?? 0) - (a.pending ?? 0)
  if (pendingDiff) return pendingDiff
  const abnormalDiff = (b.abnormal ?? 0) - (a.abnormal ?? 0)
  if (abnormalDiff) return abnormalDiff
  const createdDiff = (b.created ?? 0) - (a.created ?? 0)
  if (createdDiff) return createdDiff
  return a.order - b.order
}

/** 下钻列出全部模块，待处理量降序排列；区间内没有记录的模块沉底并显示“暂无”。 */
const panelRows = computed<ModuleStat[]>(() => {
  const modules = store.overview?.modules ?? []
  return [...modules].sort(compareModules)
})

const emptyHint = computed(() => '当前统计区间内暂无模块数据')

/** 没有数据时显示“暂无”，有数据但数量为 0 时仍显示 0，二者不混淆。 */
function display(value: number | null): string {
  return value === null ? '暂无' : String(value)
}

function refresh() {
  void store.ensureLoaded(true)
}

onMounted(() => {
  void store.ensureLoaded()
})
</script>
