<template>
  <section class="page">
    <header class="page-head">
      <div>
        <h2>运营概览</h2>
        <p class="page-desc">汇总各业务模块的关键指标，点击卡片可下钻查看积压模块，模块名与左侧导航一一对应。</p>
      </div>
      <div class="range-switch" role="group" aria-label="统计区间">
        <button
          v-for="item in store.data?.ranges ?? rangeFallback"
          :key="item.key"
          type="button"
          class="range-btn"
          :class="{ active: item.key === store.range }"
          :disabled="store.loading"
          @click="store.switchRange(item.key)"
        >
          {{ item.label }}
        </button>
      </div>
    </header>

    <div v-if="store.errorMessage" class="board-error">
      <span>{{ store.errorMessage }}</span>
      <button class="btn" type="button" @click="store.load()">重试</button>
    </div>

    <div class="stat-row">
      <article
        v-for="card in cards"
        :key="card.key"
        class="stat-card board-card"
        :class="{ clickable: card.drilldown, active: card.drilldown && activeCard === card.key }"
        role="button"
        :tabindex="card.drilldown ? 0 : undefined"
        :aria-expanded="card.drilldown ? activeCard === card.key : undefined"
        @click="card.drilldown && toggle(card.key)"
        @keydown.enter.prevent="card.drilldown && toggle(card.key)"
        @keydown.space.prevent="card.drilldown && toggle(card.key)"
      >
        <span class="stat-label">
          {{ card.label }}
          <em v-if="card.drilldown" class="drill-hint">{{ activeCard === card.key ? '收起明细' : '查看下钻' }}</em>
        </span>
        <strong class="stat-value">{{ card.value }}</strong>
      </article>
    </div>

    <!-- 卡片下钻：列出该指标下的模块待处理量/异常量，按待处理量排列 -->
    <transition name="expand">
      <section v-if="activePanel" class="drill-panel">
        <header class="drill-head">
          <h3>{{ activePanel.title }}</h3>
          <span class="drill-sub">统计区间：{{ store.data?.range_label ?? '—' }} · 共 {{ activePanel.rows.length }} 个模块有积压</span>
        </header>
        <table v-if="activePanel.rows.length" class="data-table">
          <thead>
            <tr><th>业务模块</th><th>待处理量</th><th>异常量</th><th>最近一条记录</th><th>入口</th></tr>
          </thead>
          <tbody>
            <tr v-for="row in activePanel.rows" :key="row.key">
              <td>{{ row.name }}</td>
              <td :class="{ 'num-pending': row.pending > 0 }">{{ row.pending }}</td>
              <td :class="{ 'num-abnormal': row.abnormal > 0 }">{{ row.abnormal }}</td>
              <td>{{ row.last_record ?? '暂无记录' }}</td>
              <td><RouterLink class="link" :to="row.path">进入模块 →</RouterLink></td>
            </tr>
          </tbody>
        </table>
        <p v-else class="empty-state drill-empty">{{ activePanel.emptyText }}</p>
      </section>
    </transition>

    <!-- 全量模块看板：顺序随统计区间变化，点击行直接进入对应模块 -->
    <section class="module-board">
      <header class="drill-head">
        <h3>各模块积压明细</h3>
        <span class="drill-sub">按待处理量降序排列，切换统计区间后顺序自动调整</span>
      </header>
      <table class="data-table">
        <thead>
          <tr>
            <th>业务模块</th>
            <th>区间新增</th>
            <th>待处理</th>
            <th>异常量</th>
            <th>最近一条记录</th>
            <th>入口</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in modules" :key="row.key">
            <td>
              <RouterLink class="module-name" :to="row.path">{{ row.name }}</RouterLink>
              <span v-if="row.empty" class="empty-inline">暂无：当前区间内没有记录</span>
            </td>
            <td v-if="row.empty" colspan="3" class="muted-cell">暂无数据</td>
            <template v-else>
              <td>{{ row.created }}</td>
              <td :class="{ 'num-pending': row.pending > 0 }">{{ row.pending }}</td>
              <td :class="{ 'num-abnormal': row.abnormal > 0 }">{{ row.abnormal }}</td>
            </template>
            <td>{{ row.last_record ?? '暂无记录' }}</td>
            <td><RouterLink class="link" :to="row.path">进入模块 →</RouterLink></td>
          </tr>
          <tr v-if="!modules.length">
            <td colspan="6" class="empty-state">
              {{ store.loading ? '看板数据加载中…' : '暂无模块数据，请确认服务是否正常启动' }}
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { useDashboardStore, type OverviewCard, type OverviewModule } from '@/stores/dashboard'

const store = useDashboardStore()

// 默认展开「待处理」，让积压情况进页面就能看见；展开状态不持久化，只有统计区间需要记住。
const activeCard = ref<string>('pending')

const rangeFallback = [
  { key: 'today', label: '今日' },
  { key: '7d', label: '近7天' },
  { key: '30d', label: '近30天' },
  { key: 'all', label: '全部' },
]

const cards = computed<OverviewCard[]>(() => store.data?.cards ?? [])
const modules = computed<OverviewModule[]>(() => store.data?.modules ?? [])

function toggle(key: string) {
  activeCard.value = activeCard.value === key ? '' : key
}

const PANEL_META: Record<string, { title: string; emptyText: string }> = {
  created: {
    title: '区间新增模块下钻',
    emptyText: '当前统计区间内没有新增记录，暂无模块需要关注',
  },
  pending: {
    title: '待处理积压模块下钻',
    emptyText: '当前统计区间内没有待处理任务，所有模块均已清空积压',
  },
  abnormal: {
    title: '异常模块下钻',
    emptyText: '当前统计区间内没有异常记录，各模块运行正常',
  },
}

const activePanel = computed(() => {
  const key = activeCard.value
  if (!key || !PANEL_META[key]) return null
  const meta = PANEL_META[key]
  // 下钻清单同样按待处理量降序；created 卡片下钻取区间内有记录的模块。
  const metric: (row: OverviewModule) => number =
    key === 'created' ? (row) => row.created : key === 'abnormal' ? (row) => row.abnormal : (row) => row.pending
  const rows = modules.value
    .filter((row) => metric(row) > 0)
    .slice()
    .sort((a, b) => b.pending - a.pending || b.abnormal - a.abnormal || a.name.localeCompare(b.name))
  return { ...meta, rows }
})

// 每次进入看板都重新拉取：在模块里执行过状态流转后，返回看到的数字与模块列表保持一致。
onMounted(() => {
  void store.load()
})
</script>

<style scoped>
.range-switch { display: flex; gap: 6px; }
.range-btn {
  border: 1px solid var(--border);
  background: #fff;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
}
.range-btn.active { background: var(--brand); border-color: var(--brand); color: #fff; }
.range-btn:disabled { opacity: 0.6; cursor: wait; }

.board-card { user-select: none; transition: box-shadow 0.15s ease, border-color 0.15s ease; }
.board-card.clickable { cursor: pointer; }
.board-card.clickable:hover { border-color: var(--brand); box-shadow: 0 2px 8px rgba(31, 111, 235, 0.15); }
.board-card.active { border-color: var(--brand); box-shadow: 0 0 0 1px var(--brand) inset; }
.drill-hint { font-style: normal; font-size: 11px; color: var(--brand); margin-left: 6px; }

.drill-panel,
.module-board {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}
.drill-head { display: flex; align-items: baseline; gap: 12px; margin-bottom: 8px; }
.drill-head h3 { font-size: 14px; margin: 0; }
.drill-sub { color: var(--muted); font-size: 12px; }
.drill-empty { padding: 20px 0; margin: 0; }

.module-name { font-weight: 600; color: #1f2937; text-decoration: none; }
.module-name:hover { color: var(--brand); text-decoration: underline; }
.empty-inline { display: block; color: var(--muted); font-size: 12px; margin-top: 2px; }
.muted-cell { color: var(--muted); }
.num-pending { font-weight: 600; color: #b45309; }
.num-abnormal { font-weight: 600; color: #b42318; }

.board-error {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fef3f2;
  border: 1px solid #fda29b;
  border-radius: 8px;
  color: #b42318;
  font-size: 13px;
  padding: 8px 12px;
  margin-bottom: 12px;
}

.expand-enter-active, .expand-leave-active { transition: opacity 0.15s ease; }
.expand-enter-from, .expand-leave-to { opacity: 0; }
</style>
