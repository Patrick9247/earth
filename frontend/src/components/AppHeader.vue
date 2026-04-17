<script setup lang="ts">
const navItems = [
  { path: '/', icon: 'HomeFilled', label: '系统首页' },
  { path: '/layers', icon: 'Document', label: '地质层管理' },
  { path: '/drill-data', icon: 'Aim', label: '钻孔数据' },
  { path: '/model', icon: 'DataAnalysis', label: '地质建模' },
  { path: '/calculation', icon: 'Cpu', label: '资源计算' },
  { path: '/results', icon: 'TrendCharts', label: '计算结果' },
  { path: '/settings', icon: 'Setting', label: '系统设置' }
]
</script>

<template>
  <header class="app-header">
    <div class="logo">
      <el-icon :size="28" color="#409eff"><Histogram /></el-icon>
      <span class="title">地热流体资源建模系统</span>
    </div>
    <nav class="nav-menu">
      <router-link 
        v-for="item in navItems" 
        :key="item.path"
        :to="item.path"
        class="nav-item"
        :class="{ active: $route.path === item.path }"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </router-link>
    </nav>
  </header>
</template>

<style scoped>
@import "@/styles/app-header.css";
</style>
