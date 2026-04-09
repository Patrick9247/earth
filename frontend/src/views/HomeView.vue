<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGeothermalStore } from '@/stores/geothermal'
import Mini3DViewer from '@/components/Mini3DViewer.vue'

const router = useRouter()
const store = useGeothermalStore()

const stats = computed(() => ({
  layers: store.layers.length,
  drillHoles: store.drillHoles.length,
  calculations: store.calculationResults.length,
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
        <div class="stat-label">钻孔数据</div>
      </div>
      <div class="stat-card warning">
        <el-icon :size="32"><Cpu /></el-icon>
        <div class="stat-value">{{ stats.calculations }}</div>
        <div class="stat-label">资源计算</div>
      </div>
      <div class="stat-card info">
        <el-icon :size="32"><DataAnalysis /></el-icon>
        <div class="stat-value">{{ stats.models }}</div>
        <div class="stat-label">地质模型</div>
      </div>
    </div>

    <!-- 系统介绍 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <div class="card" style="margin-bottom: 0;">
          <h2 class="card-title">📖 系统功能</h2>
          <div class="feature-card clickable" @click="navigateTo('/modeling')">
            <el-icon :size="40" color="#409eff"><DataAnalysis /></el-icon>
            <h3>三维地质建模</h3>
            <p>基于 GemPy + Three.js 构建三维地质结构模型，实时交互式可视化展示地层分布</p>
          </div>
          <div class="feature-card clickable" @click="navigateTo('/calculation')">
            <el-icon :size="40" color="#67c23a"><Cpu /></el-icon>
            <h3>资源计算</h3>
            <p>精确计算地热储层的热含量、可采资源和发电潜力</p>
          </div>
          <div class="feature-card clickable" @click="navigateTo('/layers')">
            <el-icon :size="40" color="#e6a23c"><TrendCharts /></el-icon>
            <h3>数据管理</h3>
            <p>管理钻孔数据、地质层信息和计算结果，支持 CSV/JSON 导出</p>
          </div>
          
          <!-- 同步状态提示 -->
          <div class="sync-status">
            <el-tag :type="store.modelCreated ? 'success' : 'info'" size="small">
              {{ store.modelCreated ? '✓ 已同步建模数据' : '待建模' }}
            </el-tag>
            <span class="sync-hint">
              首页 3D 预览与 <router-link to="/modeling">地质建模</router-link> 页面数据实时同步
            </span>
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <!-- 使用 store 数据同步显示 -->
        <Mini3DViewer 
          :layers="store.layers"
          :drill-holes="store.drillHoles"
          :extent="store.extent"
        />
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.home-view {
  max-width: 1400px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 24px;
}

.feature-card {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: #f5f7fa;
  transition: all 0.3s;
  margin-bottom: 16px;
}

.feature-card.clickable {
  cursor: pointer;
}

.feature-card.clickable:hover {
  background: #e8f4ff;
  border: 1px solid #409eff;
}

.feature-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.feature-card h3 {
  margin: 12px 0 6px;
  font-size: 15px;
}

.feature-card p {
  color: #909399;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
}

.sync-status {
  margin-top: 16px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.sync-hint {
  font-size: 13px;
  color: #606266;
}

.sync-hint a {
  color: #409eff;
  text-decoration: none;
}

.sync-hint a:hover {
  text-decoration: underline;
}
</style>
