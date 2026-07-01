<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGeothermalStore } from '@/stores/geothermal'
const router = useRouter()
const store = useGeothermalStore()
const stats = computed(() => ({
  layers: store.layerCount,
  drillHoles: store.gridItemCount,
  calculations: store.resourceCount,
  models: store.modelCreated ? 1 : 0
}))
// 导航到对应页面
const navigateTo = (path: string) => {
  router.push(path)
}
onMounted(async () => {
  // 从 store 初始化数据（会自动同步）
  await store.initializeData()
})
</script>
<template>
  <div class="home-view">
    <h1 class="page-title">系统首页</h1>
    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <el-icon :size="32"><Document /></el-icon>
        <div class="stat-value">{{ stats.layers }}</div>
        <div class="stat-label">地质层</div>
      </div>
      <div class="stat-card success">
        <el-icon :size="32"><Aim /></el-icon>
        <div class="stat-value">{{ stats.drillHoles }}</div>
        <div class="stat-label">网格资源数</div>
      </div>
      <div class="stat-card warning">
        <el-icon :size="32"><Cpu /></el-icon>
        <div class="stat-value">{{ stats.calculations }}</div>
        <div class="stat-label">资源计算</div>
      </div>
    </div>
    <!-- 系统介绍 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <div class="card" style="margin-bottom: 0;">
          <h2 class="card-title">系统功能</h2>
          <div class="feature-card clickable" @click="navigateTo('/calculation')">
            <el-icon :size="40" color="#67c23a"><Cpu /></el-icon>
            <h3>资源计算</h3>
            <p>精确计算地热储层的热含量、可采资源和发电潜力</p>
          </div>
          <div class="feature-card clickable" @click="navigateTo('/results')">
            <el-icon :size="40" color="#e6a23c"><TrendCharts /></el-icon>
            <h3>数据管理</h3>
            <p>管理钻孔数据、地质层信息和计算结果，支持 CSV/JSON 导出</p>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>
<style scoped>
@import "@/styles/home-view.css";
</style>
