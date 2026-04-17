<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

const settings = ref({
  // 数据库配置
  mysql_host: 'localhost',
  mysql_port: 3306,
  mysql_database: 'geothermal_db',
  
  // 计算参数默认值
  default_porosity: 0.15,
  default_recovery_factor: 0.25,
  default_utilization_efficiency: 0.1,
  default_lifetime_years: 30,
  
  // 模型配置
  default_grid_resolution: 50,
  
  // 物理常数
  water_density: 1000,
  rock_density: 2600,
  water_specific_heat: 4186,
  rock_specific_heat: 880
})

const saveSettings = () => {
  localStorage.setItem('geothermal_settings', JSON.stringify(settings.value))
  ElMessage.success('设置已保存')
}

const resetSettings = () => {
  settings.value = {
    mysql_host: 'localhost',
    mysql_port: 3306,
    mysql_database: 'geothermal_db',
    default_porosity: 0.15,
    default_recovery_factor: 0.25,
    default_utilization_efficiency: 0.1,
    default_lifetime_years: 30,
    default_grid_resolution: 50,
    water_density: 1000,
    rock_density: 2600,
    water_specific_heat: 4186,
    rock_specific_heat: 880
  }
  localStorage.removeItem('geothermal_settings')
  ElMessage.success('设置已重置')
}

onMounted(() => {
  const saved = localStorage.getItem('geothermal_settings')
  if (saved) {
    try {
      settings.value = { ...settings.value, ...JSON.parse(saved) }
    } catch (e) {
      console.error('Failed to load settings:', e)
    }
  }
})
</script>

<template>
  <div class="settings-view">
    <h1 class="page-title">系统设置</h1>
    
    <!-- 计算参数设置 -->
    <div class="card">
      <h3 class="card-title">默认计算参数</h3>
      <el-form :model="settings" label-width="160px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="默认孔隙度">
              <el-slider v-model="settings.default_porosity" :min="0" :max="0.5" :step="0.01" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认采收率">
              <el-slider v-model="settings.default_recovery_factor" :min="0.1" :max="0.5" :step="0.01" show-input />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="默认利用效率">
              <el-slider v-model="settings.default_utilization_efficiency" :min="0.05" :max="0.2" :step="0.01" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="默认开采年限">
              <el-input-number v-model="settings.default_lifetime_years" :min="10" :max="50" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <!-- 物理常数 -->
    <div class="card">
      <h3 class="card-title">物理常数</h3>
      <el-form :model="settings" label-width="160px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="水密度(kg/m³)">
              <el-input-number v-model="settings.water_density" :min="900" :max="1200" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="岩石密度(kg/m³)">
              <el-input-number v-model="settings.rock_density" :min="2000" :max="3000" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="水比热容(J/kg·K)">
              <el-input-number v-model="settings.water_specific_heat" :min="4000" :max="4500" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="岩石比热容(J/kg·K)">
              <el-input-number v-model="settings.rock_specific_heat" :min="700" :max="1000" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </div>

    <!-- 操作按钮 -->
    <div class="card">
      <el-button type="primary" @click="saveSettings">
        <el-icon><Check /></el-icon>
        保存设置
      </el-button>
      <el-button @click="resetSettings">
        <el-icon><RefreshLeft /></el-icon>
        重置默认
      </el-button>
    </div>

  </div>
</template>

<style scoped>
.settings-view {
  max-width: 1000px;
}
</style>
