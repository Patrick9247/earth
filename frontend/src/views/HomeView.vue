<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { gempyApi } from '@/api'
import { useGeothermalStore } from '@/stores/geothermal'
import Mini3DViewer from '@/components/Mini3DViewer.vue'
import TemperatureMonitor from '@/components/TemperatureMonitor.vue'

const router = useRouter()
const store = useGeothermalStore()

const stats = computed(() => ({
  layers: store.layers.length,
  drillHoles: store.drillHoles.length,
  calculations: store.calculationResults.length,
  models: store.modelCreated ? 1 : 0
}))

const quickCalcForm = ref({
  volume: 100000000,  // 1e8 m³
  temperature: 150,
  porosity: 0.15
})

const volumeOptions = [
  { label: '100万 m³ (小型)', value: 1000000 },
  { label: '1000万 m³ (中型)', value: 10000000 },
  { label: '1亿 m³ (大型)', value: 100000000 },
  { label: '10亿 m³ (超大型)', value: 1000000000 },
  { label: '100亿 m³ (巨型)', value: 10000000000 }
]

const quickResult = ref<any>(null)
const loading = ref(false)

const handleQuickCalc = async () => {
  loading.value = true
  try {
    const res = await gempyApi.quickCalc({
      reservoir_volume: quickCalcForm.value.volume,
      avg_temperature: quickCalcForm.value.temperature,
      porosity: quickCalcForm.value.porosity
    })
    quickResult.value = res.data
  } catch (error) {
    console.error('快速计算失败:', error)
  } finally {
    loading.value = false
  }
}

// 格式化热量显示
const formatHeat = (joules: number) => {
  if (!joules) return '0'
  if (joules >= 1e18) {
    return `${(joules / 1e18).toFixed(2)} EJ (艾焦)`
  } else if (joules >= 1e15) {
    return `${(joules / 1e15).toFixed(2)} PJ (拍焦)`
  } else if (joules >= 1e12) {
    return `${(joules / 1e12).toFixed(2)} TJ (太焦)`
  } else {
    return `${(joules / 1e9).toFixed(2)} GJ (吉焦)`
  }
}

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

    <!-- 地温网格监控 -->
    <TemperatureMonitor />

    <!-- 快速计算 -->
    <div class="card">
      <h2 class="card-title">⚡ 快速资源估算</h2>
      <el-form :model="quickCalcForm" label-width="120px" inline class="quick-calc-form">
        <el-form-item label="储层体积">
          <el-select v-model="quickCalcForm.volume" style="width: 220px">
            <el-option
              v-for="opt in volumeOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="平均温度(°C)">
          <el-input-number 
            v-model="quickCalcForm.temperature" 
            :min="50" 
            :max="400"
            :step="10"
          />
        </el-form-item>
        <el-form-item label="孔隙度">
          <div class="porosity-input">
            <el-slider 
              v-model="quickCalcForm.porosity" 
              :min="0" 
              :max="0.5" 
              :step="0.01" 
              style="width: 200px" 
            />
            <span class="porosity-value">{{ (quickCalcForm.porosity * 100).toFixed(0) }}%</span>
          </div>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleQuickCalc" :loading="loading">
            <el-icon><Cpu /></el-icon>
            开始计算
          </el-button>
        </el-form-item>
      </el-form>

      <div v-if="quickResult" class="result-panel">
        <el-alert type="success" :closable="false">
          <template #title>
            <span style="font-size: 16px; font-weight: 600;">{{ quickResult.data?.summary }}</span>
          </template>
          <div class="result-details">
            <div class="result-item">
              <span class="label">总热含量:</span>
              <span class="value">{{ formatHeat(quickResult.data?.total_heat_joules) }}</span>
            </div>
            <div class="result-item">
              <span class="label">可采热量:</span>
              <span class="value">{{ formatHeat(quickResult.data?.extractable_heat_joules) }}</span>
            </div>
            <div class="result-item">
              <span class="label">发电潜力:</span>
              <span class="value highlight">{{ quickResult.data?.power_potential_mw?.toFixed(2) }} MW</span>
            </div>
          </div>
        </el-alert>
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

.monitor-panel {
  margin-bottom: 24px;
}

.quick-calc-form {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
}

.porosity-input {
  display: flex;
  align-items: center;
  gap: 12px;
}

.porosity-value {
  min-width: 45px;
  font-weight: 600;
  color: #409eff;
}

.result-panel {
  margin-top: 20px;
}

.result-details {
  display: flex;
  flex-wrap: wrap;
  gap: 32px;
  margin-top: 12px;
}

.result-item {
  display: flex;
  gap: 8px;
}

.result-item .label {
  color: #606266;
}

.result-item .value {
  font-weight: 600;
}

.result-item .value.highlight {
  color: #409eff;
  font-size: 18px;
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
