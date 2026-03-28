<script setup lang="ts">
const navItems = [
  { path: '/', icon: 'HomeFilled', label: '系统首页' },
  { path: '/layers', icon: 'Document', label: '地质层管理' },
  { path: '/drill-holes', icon: 'Aim', label: '钻孔数据' },
  { path: '/model', icon: 'DataAnalysis', label: '地质建模' },
  { path: '/calculation', icon: 'Cpu', label: '资源计算' },
  { path: '/results', icon: 'TrendCharts', label: '计算结果' },
  { path: '/settings', icon: 'Setting', label: '系统设置' }
]
</script>

<template>
  <header class="app-header">
    <div class="logo">
      <el-icon :size="28" color="#409eff"><DataAnalysis /></el-icon>
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
.app-header {
  height: 60px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.nav-menu {
  display: flex;
  margin-left: 40px;
  gap: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 6px;
  text-decoration: none;
  color: #606266;
  transition: all 0.3s;
}

.nav-item:hover {
  background: #ecf5ff;
  color: #409eff;
}

.nav-item.active {
  background: #409eff;
  color: #fff;
}
</style>
