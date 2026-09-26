<template>
  <div class="app-shell">
    <aside class="app-side">
      <h1 class="app-title">冷链物流运输管理平台</h1>
      <nav class="nav-list">
        <RouterLink :to="dashboard.path" class="nav-item">{{ dashboard.label }}</RouterLink>
        <RouterLink v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item">
          {{ item.label }}
        </RouterLink>
      </nav>
    </aside>
    <main class="app-main">
      <header class="app-head">
        <span class="head-desc">面向冷链运输全程温控、车辆调度、门到门配送、温度异常处置、签收回单与运力结算的冷链运输管理后台。</span>
        <span class="head-user">当前值班：{{ store.operator }} · {{ store.shiftLabel }}</span>
      </header>
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSessionStore } from '@/stores/session'
import { NAV_ENTRIES as navItems } from '@/config/nav'

const store = useSessionStore()

const dashboard = { label: '运营概览', path: '/' }
</script>
