<script setup lang="ts">
interface User {
  id: number
  username: string
  role: string
  full_name?: string
  email?: string
  phone?: string
}

defineProps<{
  user: User | null
}>()

const emit = defineEmits<{
  (e: 'logout'): void
  (e: 'go-to-users'): void
}>()

const navItems = [
  { path: '/', icon: 'HomeFilled', label: '系统首页' },
  { path: '/layers', icon: 'Document', label: '地质层管理' },
  { path: '/drill-data', icon: 'Aim', label: '钻孔数据' },
  { path: '/model', icon: 'DataAnalysis', label: '地质建模' },
  { path: '/calculation', icon: 'Cpu', label: '资源计算' },
  { path: '/results', icon: 'TrendCharts', label: '计算结果' },
  { path: '/users', icon: 'User', label: '用户管理' },
  { path: '/settings', icon: 'Setting', label: '系统设置' }
]

const handleCommand = (command: string) => {
  switch (command) {
    case 'profile':
      emit('go-to-users')
      break
    case 'logout':
      emit('logout')
      break
  }
}

const getRoleText = (role: string) => {
  return role === 'SUPER' ? '超级管理员' : '普通管理员'
}

const getRoleTagType = (role: string) => {
  return role === 'SUPER' ? 'danger' : 'primary'
}
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
    <div class="user-section">
      <el-dropdown @command="handleCommand" trigger="click">
        <div class="user-info">
          <el-avatar :size="32" style="background-color: #409eff;">
            {{ user?.username?.charAt(0).toUpperCase() || 'U' }}
          </el-avatar>
          <div class="user-details">
            <span class="username">{{ user?.full_name || user?.username }}</span>
            <el-tag :type="getRoleTagType(user?.role || 'ADMIN')" size="small">
              {{ getRoleText(user?.role || 'ADMIN') }}
            </el-tag>
          </div>
          <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="profile">
              <el-icon><User /></el-icon>
              个人信息管理
            </el-dropdown-item>
            <el-dropdown-item command="logout" divided>
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </header>
</template>

<style scoped>
@import "@/styles/app-header.css";

.user-section {
  margin-left: auto;
  margin-right: 10px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: rgba(64, 158, 255, 0.1);
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.username {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.dropdown-icon {
  font-size: 12px;
  color: #909399;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
