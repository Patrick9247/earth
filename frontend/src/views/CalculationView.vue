<script setup lang="ts">
import { ref, computed } from 'vue'
import { gempyApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const result = ref<any>(null)

const calcForm = ref({
  model_id: 1,
  reservoir_volume: 1e8,
  avg_temperature: 150,
  reference_temperature: 25,
  porosity: 0.15,
  water_density: 1000,
  rock_density: 2600,
  water_specific_heat: 4186,
  rock_specific_heat: 880,
  recovery_factor: 0.25,
  utilization_efficiency: 0.1,
  lifetime_years: 30
})

// 计算预估值（实时）
const estimatedPower = computed(() => {
  const v = calcForm.value
  const delta_T = v.avg_temperature - v.reference_temperature
  const water_vol = v.reservoir_volume * v.porosity
  const rock_vol = v.reservoir_volume * (1 - v.porosity)
  const total_heat = (water_vol * v.water_density * v.water_specific_heat + 
                      rock_vol * v.rock_density * v.rock_specific_heat) * delta_T
  const extractable = total_heat * v.recovery_factor
  const annual = extractable * v.utilization_efficiency / v.lifetime_years
  const power_mw = annual / (365.25 * 24 * 3600) / 1e6
  return power_mw.toFixed(2)
})

const handleCalculate = async () => {
  loading.value = true
  try {
    const res = await gempyApi.calculate(calcForm.value)
    if (res.data.success) {
      result.value = res.data.result
      ElMessage.success('计算完成！')
    } else {
      ElMessage.error(res.data.message || '计算失败')
    }
  } catch (error) {
    console.error('计算失败:', error)
    // 模拟结果
    result.value = {
      id: Date.now(),
      name: '计算结果',
      volume: calcForm.value.reservoir_volume,
      temperature_avg: calcForm.value.avg_temperature,
      heat_content: parseFloat(estimatedPower.value) * 365.25 * 24 * 3600 * 1e6 * calcForm.value.lifetime_years / calcForm.value.utilization_efficiency / calcForm.value.recovery_factor,
      extractable_heat: parseFloat(estimatedPower.value) * 365.25 * 24 * 3600 * 1e6 * calcForm.value.lifetime_years / calcForm.value.utilization_efficiency,
      power_potential: parseFloat(estimatedPower.value),
      lifetime_years: calcForm.value.lifetime_years,
      created_at: new Date().toISOString()
    }
    ElMessage.success('计算完成（演示模式）！')
  } finally {
    loading.value = false
  }
}

const presetTemplates = [
  { name: '低温地热田', temperature: 90, porosity: 0.20 },
  { name: '中温地热田', temperature: 150, porosity: 0.15 },
  { name: '高温地热田', temperature: 220, porosity: 0.10 },
  { name: '干热岩', temperature: 300, porosity: 0.02 }
]

const applyTemplate = (tpl: any) => {
  calcForm.value.avg_temperature = tpl.temperature
  calcForm.value.porosity = tpl.porosity
  ElMessage.success(`已应用模板：${tpl.name}`)
}
</script>

<template>
  <div class="calculation-view">
    <h1 class="page-title">地热资源计算</h1>
    
    <!-- 快速模板 -->
    <div class="card">
      <h3 class="card-title">⚡ 快速模板</h3>
      <el-row :gutter="16">
        <el-col :span="6" v-for="tpl in presetTemplates" :key="tpl.name">
          <el-card shadow="hover" class="template-card" @click="applyTemplate(tpl)">
            <h4>{{ tpl.name }}</h4>
            <p>温度: {{ tpl.temperature }}°C</p>
            <p>孔隙度: {{ (tpl.porosity * 100).toFixed(0) }}%</p>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 计算参数 -->
    <div class="card">
      <h3 class="card-title">📐 计算参数</h3>
      <el-form :model="calcForm" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="储层体积(m³)">
              <el-input-number 
                v-model="calcForm.reservoir_volume" 
                :min="1e6" 
                :max="1e12"
                :step="1e7"
                :controls="false"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="平均温度(°C)">
              <el-input-number v-model="calcForm.avg_temperature" :min="50" :max="400" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">物性参数</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="孔隙度">
              <el-slider v-model="calcForm.porosity" :min="0" :max="0.5" :step="0.01" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="水密度(kg/m³)">
              <el-input-number v-model="calcForm.water_density" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="岩石密度(kg/m³)">
              <el-input-number v-model="calcForm.rock_density" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">经济参数</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="采收率">
              <el-slider v-model="calcForm.recovery_factor" :min="0.1" :max="0.5" :step="0.01" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="利用效率">
              <el-slider v-model="calcForm.utilization_efficiency" :min="0.05" :max="0.2" :step="0.01" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开采年限(年)">
              <el-input-number v-model="calcForm.lifetime_years" :min="10" :max="50" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" size="large" @click="handleCalculate" :loading="loading">
            <el-icon><Cpu /></el-icon>
            开始计算
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 实时预估 -->
    <div class="card">
      <h3 class="card-title">📊 实时预估</h3>
      <div class="estimate-panel">
        <div class="estimate-item highlight">
          <span class="label">预估发电潜力</span>
          <span class="value">{{ estimatedPower }} MW</span>
        </div>
      </div>
    </div>

    <!-- 计算结果 -->
    <div class="card" v-if="result">
      <h3 class="card-title">✅ 计算结果</h3>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="储层体积">{{ (result.volume / 1e6).toFixed(2) }} × 10⁶ m³</el-descriptions-item>
        <el-descriptions-item label="平均温度">{{ result.temperature_avg }} °C</el-descriptions-item>
        <el-descriptions-item label="开采年限">{{ result.lifetime_years }} 年</el-descriptions-item>
        <el-descriptions-item label="热含量">{{ (result.heat_content / 1e18).toFixed(2) }} EJ</el-descriptions-item>
        <el-descriptions-item label="可采热量">{{ (result.extractable_heat / 1e18).toFixed(2) }} EJ</el-descriptions-item>
        <el-descriptions-item label="发电潜力">
          <el-tag type="success" size="large">{{ result.power_potential?.toFixed(2) }} MW</el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<style scoped>
.template-card {
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
}

.template-card:hover {
  transform: translateY(-4px);
  border-color: #409eff;
}

.template-card h4 {
  margin-bottom: 8px;
  color: #409eff;
}

.template-card p {
  font-size: 12px;
  color: #909399;
  margin: 4px 0;
}

.estimate-panel {
  display: flex;
  gap: 40px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
}

.estimate-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.estimate-item .label {
  font-size: 14px;
  opacity: 0.9;
}

.estimate-item .value {
  font-size: 36px;
  font-weight: 700;
}
</style>
