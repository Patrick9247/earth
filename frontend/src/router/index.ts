import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
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
    path: '/drill-holes',
    name: 'drill-holes',
    component: () => import('@/views/DrillHolesView.vue'),
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
  next()
})

export default router
