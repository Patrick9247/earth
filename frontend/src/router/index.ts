import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { title: '用户登录', requiresAuth: false }
  },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { title: '系统首页' }
  },
  {
    path: '/layers',
    name: 'layers',
    component: () => import('@/views/LayersView.vue'),
    meta: { title: '地质层管理' }
  },
  {
    path: '/drill-data',
    name: 'drill-data',
    component: () => import('@/views/DrillDataView.vue'),
    meta: { title: '钻孔数据' }
  },
  {
    path: '/model',
    name: 'model',
    component: () => import('@/views/ModelView.vue'),
    meta: { title: '地质建模' }
  },
  {
    path: '/calculation',
    name: 'calculation',
    component: () => import('@/views/CalculationView.vue'),
    meta: { title: '资源计算' }
  },
  {
    path: '/results',
    name: 'results',
    component: () => import('@/views/ResultsView.vue'),
    meta: { title: '计算结果' }
  },
  {
    path: '/results/chart',
    name: 'results-chart',
    component: () => import('@/views/ResultsChartView.vue'),
    meta: { title: '数据可视化' }
  },
  {
    path: '/users',
    name: 'users',
    component: () => import('@/views/UserManagementView.vue'),
    meta: { title: '用户管理' }
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('@/views/SettingsView.vue'),
    meta: { title: '系统设置' }
  },
  {
    path: '/guide',
    name: 'guide',
    component: () => import('@/views/GuideView.vue'),
    meta: { title: '使用指南' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  document.title = `${to.meta.title || '首页'} - 地热流体资源建模系统`
  
  // 检查是否需要登录
  const token = localStorage.getItem('token')
  const requiresAuth = to.meta.requiresAuth !== false && to.name !== 'login'
  
  if (requiresAuth && !token) {
    // 未登录，跳转到登录页面
    next({ name: 'login' })
  } else if (to.name === 'login' && token) {
    // 已登录，跳转到首页
    next({ name: 'home' })
  } else {
    next()
  }
})

export default router
