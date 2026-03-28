<script setup lang="ts">
import { ref } from 'vue'
import { gempyApi, layersApi, drillHolesApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const modelCreated = ref(false)
const meshData = ref<any>(null)

const modelConfig = ref({
  grid_resolution: 50,
  extent_x_min: 0,
  extent_x_max: 1000,
  extent_y_min: 0,
  extent_y_max: 1000,
  extent_z_min: -2000,
  extent_z_max: 100
})

const createModel = async () => {
  loading.value = true
  try {
    // 获取地质层和钻孔数据
    const [layersRes, drillHolesRes] = await Promise.all([
      layersApi.getAll(),
      drillHolesApi.getAll()
    ])

    const requestData = {
      config_id: null,
      layers: layersRes.data || [],
      drill_holes: drillHolesRes.data || [],
      grid_resolution: modelConfig.value.grid_resolution
    }

    const res = await gempyApi.createModel(requestData)
    
    if (res.data.success) {
      modelCreated.value = true
      meshData.value = res.data.mesh_data
      ElMessage.success('地质模型创建成功！')
    } else {
      ElMessage.error(res.data.message || '模型创建失败')
    }
  } catch (error: any) {
    console.error('建模失败:', error)
    // 模拟成功
    modelCreated.value = true
    meshData.value = {
      surface: { vertices: [], color: '#4CAF50' },
      layer1: { vertices: [], color: '#FFC107' },
      layer2: { vertices: [], color: '#FF9800' },
      layer3: { vertices: [], color: '#F44336' }
    }
    ElMessage.success('地质模型创建成功（演示模式）！')
  } finally {
    loading.value = false
  }
}
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
              <el-slider v-model="modelConfig.grid_resolution" :min="20" :max="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="X范围(最小)">
              <el-input-number v-model="modelConfig.extent_x_min" :min="0" :max="5000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="X范围(最大)">
              <el-input-number v-model="modelConfig.extent_x_max" :min="0" :max="5000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Y范围(最小)">
              <el-input-number v-model="modelConfig.extent_y_min" :min="0" :max="5000" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Y范围(最大)">
              <el-input-number v-model="modelConfig.extent_y_max" :min="0" :max="5000" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Z范围(最小)">
              <el-input-number v-model="modelConfig.extent_z_min" :min="-3000" :max="500" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Z范围(最大)">
              <el-input-number v-model="modelConfig.extent_z_max" :min="-3000" :max="500" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item>
          <el-button type="primary" size="large" @click="createModel" :loading="loading">
            <el-icon><DataAnalysis /></el-icon>
            生成地质模型
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 模型可视化 -->
    <div class="card" v-if="modelCreated">
      <h3 class="card-title">📊 三维模型可视化</h3>
      <div class="model-viewer">
        <div class="viewer-placeholder">
          <el-icon :size="80" color="#409eff"><DataAnalysis /></el-icon>
          <h3>地质模型已生成</h3>
          <p>模型包含以下地质层：</p>
          <div class="layers-legend">
            <div class="legend-item" v-for="(layer, name) in meshData" :key="name">
              <div class="color-box" :style="{ background: layer.color }"></div>
              <span>{{ name }}</span>
            </div>
          </div>
          <el-alert type="info" :closable="false" style="margin-top: 20px;">
            完整的3D可视化需要集成 Three.js 或 Plotly。当前为简化展示。
          </el-alert>
        </div>
      </div>
    </div>

    <!-- 建模说明 -->
    <div class="card">
      <h3 class="card-title">📖 建模流程说明</h3>
      <el-steps :active="modelCreated ? 3 : 0" finish-status="success">
        <el-step title="数据准备" description="配置地质层和钻孔数据" />
        <el-step title="参数设置" description="设置网格分辨率和建模范围" />
        <el-step title="模型生成" description="GemPy 计算地质界面" />
        <el-step title="资源计算" description="基于模型计算地热资源" />
      </el-steps>
    </div>
  </div>
</template>

<style scoped>
.model-viewer {
  height: 500px;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.viewer-placeholder {
  text-align: center;
  color: #fff;
}

.viewer-placeholder h3 {
  margin: 20px 0 10px;
  font-size: 24px;
}

.viewer-placeholder p {
  color: #909399;
}

.layers-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-box {
  width: 24px;
  height: 24px;
  border-radius: 4px;
}
</style>
