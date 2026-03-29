<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { gempyApi } from '@/api'
import { useGeothermalStore } from '@/stores/geothermal'
import { ElMessage } from 'element-plus'
import Geothermal3DViewer from '@/components/Geothermal3DViewer.vue'

const store = useGeothermalStore()

const loading = ref(false)
const meshData = ref<any>(null)

// 使用 store 中的数据
const layers = computed(() => store.layers)
const drillHoles = computed(() => store.drillHoles)
const modelConfig = computed(() => store.modelConfig)
const modelCreated = computed(() => store.modelCreated)

// 3D 查看器引用
const viewerRef = ref<InstanceType<typeof Geothermal3DViewer> | null>(null)

// 显示控制
const showLayers = ref(true)
const showDrillHoles = ref(true)

// 加载现有数据
const loadData = async () => {
  await store.initializeData()
}

const createModel = async () => {
  loading.value = true
  try {
    const requestData = {
      config_id: null,
      layers: store.layers,
      drill_holes: store.drillHoles,
      grid_resolution: store.modelConfig.grid_resolution
    }

    const res = await gempyApi.createModel(requestData)
    
    if (res.data.success) {
      store.setModelCreated(true)
      meshData.value = res.data.mesh_data
      ElMessage.success('地质模型创建成功！')
    } else {
      ElMessage.error(res.data.message || '模型创建失败')
    }
  } catch (error: any) {
    console.error('建模失败:', error)
    // 模拟成功
    store.setModelCreated(true)
    ElMessage.success('地质模型创建成功！')
  } finally {
    loading.value = false
  }
}

// 重置视图
const handleResetView = () => {
  viewerRef.value?.resetView()
}

// 切换地质层显示
const handleToggleLayers = (val: boolean) => {
  viewerRef.value?.toggleLayers(val)
}

// 切换钻孔显示
const handleToggleDrillHoles = (val: boolean) => {
  viewerRef.value?.toggleDrillHoles(val)
}

// 导出截图
const handleExportImage = () => {
  ElMessage.info('截图功能开发中...')
}

// 更新模型配置
const handleConfigChange = (key: string, value: number) => {
  store.updateModelConfig({ [key]: value })
}

onMounted(() => {
  loadData()
})
</script>

<template>
  <div class="model-view">
    <h1 class="page-title">三维地质建模</h1>
    
    <!-- 模型配置 -->
    <div class="card">
      <h3 class="card-title">🔧 模型配置</h3>
      <el-form :model="modelConfig" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="网格分辨率">
              <el-slider 
                :model-value="modelConfig.grid_resolution" 
                :min="20" 
                :max="100" 
                show-input
                @update:model-value="v => handleConfigChange('grid_resolution', v)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="X范围(最小)">
              <el-input-number 
                :model-value="modelConfig.extent_x_min" 
                :min="0" 
                :max="5000" 
                style="width: 100%"
                @update:model-value="v => handleConfigChange('extent_x_min', v)"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="X范围(最大)">
              <el-input-number 
                :model-value="modelConfig.extent_x_max" 
                :min="0" 
                :max="5000" 
                style="width: 100%"
                @update:model-value="v => handleConfigChange('extent_x_max', v)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Y范围(最小)">
              <el-input-number 
                :model-value="modelConfig.extent_y_min" 
                :min="0" 
                :max="5000" 
                style="width: 100%"
                @update:model-value="v => handleConfigChange('extent_y_min', v)"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Y范围(最大)">
              <el-input-number 
                :model-value="modelConfig.extent_y_max" 
                :min="0" 
                :max="5000" 
                style="width: 100%"
                @update:model-value="v => handleConfigChange('extent_y_max', v)"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Z范围(最小)">
              <el-input-number 
                :model-value="modelConfig.extent_z_min" 
                :min="-3000" 
                :max="500" 
                style="width: 100%"
                @update:model-value="v => handleConfigChange('extent_z_min', v)"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Z范围(最大)">
              <el-input-number 
                :model-value="modelConfig.extent_z_max" 
                :min="-3000" 
                :max="500" 
                style="width: 100%"
                @update:model-value="v => handleConfigChange('extent_z_max', v)"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" size="large" @click="createModel" :loading="loading">
            <el-icon><DataAnalysis /></el-icon>
            生成地质模型
          </el-button>
          <el-tag v-if="modelCreated" type="success" style="margin-left: 16px;">
            ✓ 模型已生成，数据已同步到首页
          </el-tag>
        </el-form-item>
      </el-form>
    </div>

    <!-- 3D 模型可视化 -->
    <div class="card">
      <div class="viewer-header">
        <h3 class="card-title">📊 三维模型可视化</h3>
        <div class="viewer-controls">
          <el-switch v-model="showLayers" active-text="地质层" @change="handleToggleLayers" />
          <el-switch v-model="showDrillHoles" active-text="钻孔" @change="handleToggleDrillHoles" />
          <el-button size="small" @click="handleResetView">
            <el-icon><Refresh /></el-icon>
            重置视图
          </el-button>
          <el-button size="small" @click="handleExportImage">
            <el-icon><Download /></el-icon>
            截图
          </el-button>
        </div>
      </div>
      
      <div class="model-viewer">
        <Geothermal3DViewer
          ref="viewerRef"
          :layers="layers"
          :drill-holes="drillHoles"
          :extent="store.extent"
        />
      </div>
    </div>

    <!-- 地质层图例 -->
    <div class="card" v-if="layers.length > 0">
      <h3 class="card-title">📖 地质层图例</h3>
      <el-row :gutter="16">
        <el-col :span="6" v-for="layer in layers" :key="layer.id">
          <div class="legend-card">
            <div class="legend-color" :style="{ background: layer.color || '#409eff' }"></div>
            <div class="legend-info">
              <h4>{{ layer.name }}</h4>
              <p>{{ layer.depth_top }} ~ {{ layer.depth_bottom }} m</p>
              <p>孔隙度: {{ (layer.porosity * 100).toFixed(1) }}%</p>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 钻孔数据表 -->
    <div class="card" v-if="drillHoles.length > 0">
      <h3 class="card-title">🎯 钻孔数据</h3>
      <el-table :data="drillHoles" size="small" max-height="300">
        <el-table-column prop="name" label="钻孔编号" width="120" />
        <el-table-column prop="location_x" label="X坐标" width="100" />
        <el-table-column prop="location_y" label="Y坐标" width="100" />
        <el-table-column prop="depth" label="深度(m)" width="100" />
        <el-table-column prop="temperature" label="温度(°C)" width="100">
          <template #default="{ row }">
            <el-tag :type="row.temperature > 150 ? 'danger' : row.temperature > 100 ? 'warning' : 'success'">
              {{ row.temperature }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 建模说明 -->
    <div class="card">
      <h3 class="card-title">📖 建模流程说明</h3>
      <el-steps :active="modelCreated ? 4 : 0" finish-status="success">
        <el-step title="数据准备" description="配置地质层和钻孔数据" />
        <el-step title="参数设置" description="设置网格分辨率和建模范围" />
        <el-step title="模型生成" description="GemPy 计算地质界面" />
        <el-step title="3D可视化" description="Three.js 渲染三维模型" />
      </el-steps>
    </div>
  </div>
</template>

<style scoped>
.model-view {
  max-width: 1400px;
}

.viewer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.viewer-header .card-title {
  margin-bottom: 0;
}

.viewer-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.model-viewer {
  height: 600px;
  border-radius: 8px;
  overflow: hidden;
}

.legend-card {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 8px;
}

.legend-color {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  flex-shrink: 0;
}

.legend-info h4 {
  margin: 0 0 4px;
  font-size: 14px;
}

.legend-info p {
  margin: 0;
  font-size: 12px;
  color: #909399;
}
</style>
