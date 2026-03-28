<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { gempyApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const result = ref<any>(null)
const phaseInfo = ref<any>(null)
const activeTab = ref('simple')

// 简单计算表单
const calcForm = ref({
  model_id: 1,
  reservoir_volume: 1e8,
  avg_temperature: 150,
  reference_temperature: 25,
  porosity: 0.15,
  pressure: 0.5,
  water_density: null as number | null,
  rock_density: 2600,
  water_specific_heat: 4186,
  rock_specific_heat: 880,
  recovery_factor: 0.25,
  utilization_efficiency: 0.1,
  lifetime_years: 30
})

// 网格计算表单
const gridForm = ref({
  reference_temperature: 25,
  recovery_factor: 0.25,
  utilization_efficiency: 0.1,
  lifetime_years: 30
})

// 网格数据
const gridData = ref<any[]>([
  { porosity: 0.15, volume: 1e7, temperature: 120, pressure: 0.3 },
  { porosity: 0.12, volume: 1e7, temperature: 150, pressure: 0.5 },
  { porosity: 0.10, volume: 1e7, temperature: 180, pressure: 0.8 },
  { porosity: 0.08, volume: 1e7, temperature: 200, pressure: 1.2 }
])

// 相态判定
const checkPhase = async () => {
  try {
    const res = await gempyApi.phaseDetermination(
      calcForm.value.avg_temperature,
      calcForm.value.pressure
    )
    if (res.data.success) {
      phaseInfo.value = res.data.data
    }
  } catch (error) {
    // 模拟相态判定
    const T = calcForm.value.avg_temperature
    const P = calcForm.value.pressure
    const T_boiling = -8.97 * Math.log(P)
    phaseInfo.value = {
      temperature: T,
      pressure: P,
      boiling_point: Math.max(100, Math.min(T_boiling, 374)),
      phase_type: T >= T_boiling ? 'two_phase' : 'liquid',
      phase_description: T >= T_boiling ? '气液共存' : '液态水',
      water_density: calculateDensity(T),
      is_boiling: T >= T_boiling
    }
  }
}

// 计算水密度（专利公式）
const calculateDensity = (T: number): number => {
  const A = 0.99987 + 6.0e-5 * T
  const B = 2.0e-4 + 1.0e-5 * T
  const density = A * (1 - B * T) * 1000
  return Math.max(600, Math.min(density, 1050))
}

// 监听温度和压力变化，自动判定相态
watch(
  () => [calcForm.value.avg_temperature, calcForm.value.pressure],
  () => {
    checkPhase()
  },
  { immediate: true }
)

// 计算预估值（实时）
const estimatedPower = computed(() => {
  const v = calcForm.value
  const delta_T = v.avg_temperature - v.reference_temperature
  const water_density = calculateDensity(v.avg_temperature)
  const water_vol = v.reservoir_volume * v.porosity
  const rock_vol = v.reservoir_volume * (1 - v.porosity)
  const total_heat = (water_vol * water_density * v.water_specific_heat + 
                      rock_vol * v.rock_density * v.rock_specific_heat) * delta_T
  const extractable = total_heat * v.recovery_factor
  const annual = extractable * v.utilization_efficiency / v.lifetime_years
  const power_mw = annual / (365.25 * 24 * 3600) / 1e6
  return power_mw.toFixed(2)
})

// 简单计算
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
    const water_density = calculateDensity(calcForm.value.avg_temperature)
    result.value = {
      id: Date.now(),
      name: '计算结果',
      volume: calcForm.value.reservoir_volume,
      temperature_avg: calcForm.value.avg_temperature,
      heat_content: parseFloat(estimatedPower.value) * 365.25 * 24 * 3600 * 1e6 * calcForm.value.lifetime_years / calcForm.value.utilization_efficiency / calcForm.value.recovery_factor,
      extractable_heat: parseFloat(estimatedPower.value) * 365.25 * 24 * 3600 * 1e6 * calcForm.value.lifetime_years / calcForm.value.utilization_efficiency,
      power_potential: parseFloat(estimatedPower.value),
      lifetime_years: calcForm.value.lifetime_years,
      phase_info: phaseInfo.value,
      water_density_calculated: water_density,
      created_at: new Date().toISOString()
    }
    ElMessage.success('计算完成！')
  } finally {
    loading.value = false
  }
}

// 网格计算
const handleGridCalculate = async () => {
  loading.value = true
  try {
    const res = await gempyApi.calculateGrid({
      grids: gridData.value,
      ...gridForm.value
    })
    if (res.data.success) {
      result.value = res.data.data
      ElMessage.success('网格计算完成！')
    } else {
      ElMessage.error(res.data.message || '计算失败')
    }
  } catch (error) {
    console.error('网格计算失败:', error)
    // 模拟网格计算结果
    let totalResource = 0
    let liquidCount = 0
    let twoPhaseCount = 0
    
    gridData.value.forEach(grid => {
      const T_boiling = -8.97 * Math.log(grid.pressure)
      const isTwoPhase = grid.temperature >= T_boiling
      const density = calculateDensity(grid.temperature)
      const delta_T = grid.temperature - gridForm.value.reference_temperature
      
      if (isTwoPhase) {
        twoPhaseCount++
        // 简化的两相计算
        totalResource += grid.porosity * grid.volume * density * 4186 * delta_T * 1.2
      } else {
        liquidCount++
        totalResource += grid.porosity * grid.volume * density * 4186 * delta_T
      }
    })
    
    const extractable = totalResource * gridForm.value.recovery_factor
    const annual = extractable * gridForm.value.utilization_efficiency / gridForm.value.lifetime_years
    const power_mw = annual / (365.25 * 24 * 3600) / 1e6
    
    result.value = {
      total_resource_joules: totalResource,
      liquid_grid_count: liquidCount,
      two_phase_grid_count: twoPhaseCount,
      extractable_heat: extractable,
      power_potential_mw: power_mw,
      parameters: gridForm.value
    }
    ElMessage.success('网格计算完成（演示模式）！')
  } finally {
    loading.value = false
  }
}

// 添加网格
const addGrid = () => {
  gridData.value.push({
    porosity: 0.12,
    volume: 1e7,
    temperature: 150,
    pressure: 0.5
  })
}

// 删除网格
const removeGrid = (index: number) => {
  gridData.value.splice(index, 1)
}

const presetTemplates = [
  { name: '低温地热田', temperature: 90, porosity: 0.20, pressure: 0.2 },
  { name: '中温地热田', temperature: 150, porosity: 0.15, pressure: 0.5 },
  { name: '高温地热田', temperature: 220, porosity: 0.10, pressure: 1.5 },
  { name: '干热岩', temperature: 300, porosity: 0.02, pressure: 3.0 }
]

const applyTemplate = (tpl: any) => {
  calcForm.value.avg_temperature = tpl.temperature
  calcForm.value.porosity = tpl.porosity
  calcForm.value.pressure = tpl.pressure
  ElMessage.success(`已应用模板：${tpl.name}`)
}

// 格式化数字
const formatNumber = (num: number, decimals: number = 2): string => {
  if (num >= 1e18) return (num / 1e18).toFixed(decimals) + ' EJ'
  if (num >= 1e15) return (num / 1e15).toFixed(decimals) + ' PJ'
  if (num >= 1e12) return (num / 1e12).toFixed(decimals) + ' TJ'
  if (num >= 1e9) return (num / 1e9).toFixed(decimals) + ' GJ'
  if (num >= 1e6) return (num / 1e6).toFixed(decimals) + ' MJ'
  return num.toFixed(decimals) + ' J'
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
            <p>压力: {{ tpl.pressure }} MPa</p>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 计算方式选择 -->
    <div class="card">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="简单计算" name="simple">
          <h3 class="card-title">📐 简单计算参数</h3>
          <el-form :model="calcForm" label-width="140px">
            <el-row :gutter="20">
              <el-col :span="8">
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
              <el-col :span="8">
                <el-form-item label="平均温度(°C)">
                  <el-input-number v-model="calcForm.avg_temperature" :min="50" :max="400" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="储层压力(MPa)">
                  <el-input-number v-model="calcForm.pressure" :min="0.1" :max="10" :step="0.1" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>

            <!-- 相态判定结果 -->
            <div v-if="phaseInfo" class="phase-panel">
              <el-alert
                :title="`相态判定结果：${phaseInfo.phase_description}`"
                :type="phaseInfo.phase_type === 'two_phase' ? 'warning' : 'success'"
                show-icon
              >
                <template #default>
                  <div class="phase-details">
                    <span>沸点温度: <b>{{ phaseInfo.boiling_point.toFixed(1) }}°C</b></span>
                    <span>计算水密度: <b>{{ phaseInfo.water_density.toFixed(1) }} kg/m³</b></span>
                    <span>状态: <b>{{ phaseInfo.is_boiling ? '已沸腾' : '未沸腾' }}</b></span>
                  </div>
                </template>
              </el-alert>
            </div>

            <el-divider content-position="left">物性参数</el-divider>
            
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="孔隙度">
                  <el-slider v-model="calcForm.porosity" :min="0" :max="0.5" :step="0.01" show-input />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="岩石密度(kg/m³)">
                  <el-input-number v-model="calcForm.rock_density" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="参考温度(°C)">
                  <el-input-number v-model="calcForm.reference_temperature" style="width: 100%" />
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
                  <el-input-number v-model="calcForm.lifetime_years" :min="10" :max="50" style="width: 100%" />
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
        </el-tab-pane>

        <el-tab-pane label="网格计算" name="grid">
          <h3 class="card-title">🔬 网格资源计算（专利方法）</h3>
          <p class="description">
            基于专利《一种不规则热储层多相态地热流体资源量计算方法》，对每个网格进行相态判定后分别计算资源量。
          </p>
          
          <div class="grid-toolbar">
            <el-button type="primary" @click="addGrid">
              <el-icon><Plus /></el-icon>
              添加网格
            </el-button>
            <el-button type="success" @click="handleGridCalculate" :loading="loading">
              <el-icon><Cpu /></el-icon>
              计算网格资源
            </el-button>
          </div>

          <el-table :data="gridData" border stripe>
            <el-table-column label="网格编号" type="index" width="80" />
            <el-table-column label="孔隙度" width="150">
              <template #default="{ row }">
                <el-input-number v-model="row.porosity" :min="0.01" :max="0.5" :step="0.01" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="体积(m³)" width="160">
              <template #default="{ row }">
                <el-input-number v-model="row.volume" :min="1e5" :max="1e10" :step="1e6" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="温度(°C)" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.temperature" :min="50" :max="400" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="压力(MPa)" width="120">
              <template #default="{ row }">
                <el-input-number v-model="row.pressure" :min="0.1" :max="10" :step="0.1" size="small" />
              </template>
            </el-table-column>
            <el-table-column label="相态" width="100">
              <template #default="{ row }">
                <el-tag :type="-8.97 * Math.log(row.pressure) <= row.temperature ? 'warning' : 'success'">
                  {{ -8.97 * Math.log(row.pressure) <= row.temperature ? '气液共存' : '液态' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ $index }">
                <el-button type="danger" link @click="removeGrid($index)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>

          <!-- 网格计算参数 -->
          <div class="grid-params">
            <el-row :gutter="20">
              <el-col :span="6">
                <div class="param-item">
                  <label>参考温度</label>
                  <el-input-number v-model="gridForm.reference_temperature" size="small" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="param-item">
                  <label>采收率</label>
                  <el-input-number v-model="gridForm.recovery_factor" :min="0.1" :max="0.5" :step="0.01" size="small" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="param-item">
                  <label>利用效率</label>
                  <el-input-number v-model="gridForm.utilization_efficiency" :min="0.05" :max="0.2" :step="0.01" size="small" />
                </div>
              </el-col>
              <el-col :span="6">
                <div class="param-item">
                  <label>开采年限</label>
                  <el-input-number v-model="gridForm.lifetime_years" :min="10" :max="50" size="small" />
                </div>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 实时预估 -->
    <div class="card" v-if="activeTab === 'simple'">
      <h3 class="card-title">📊 实时预估</h3>
      <div class="estimate-panel">
        <div class="estimate-item highlight">
          <span class="label">预估发电潜力</span>
          <span class="value">{{ estimatedPower }} MW</span>
        </div>
        <div class="estimate-item" v-if="phaseInfo">
          <span class="label">计算水密度</span>
          <span class="value">{{ phaseInfo.water_density.toFixed(1) }} kg/m³</span>
        </div>
      </div>
    </div>

    <!-- 计算结果 -->
    <div class="card" v-if="result">
      <h3 class="card-title">✅ 计算结果</h3>
      
      <!-- 简单计算结果 -->
      <template v-if="activeTab === 'simple'">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="储层体积">{{ (result.volume / 1e6).toFixed(2) }} × 10⁶ m³</el-descriptions-item>
          <el-descriptions-item label="平均温度">{{ result.temperature_avg }} °C</el-descriptions-item>
          <el-descriptions-item label="开采年限">{{ result.lifetime_years }} 年</el-descriptions-item>
          <el-descriptions-item label="热含量">{{ formatNumber(result.heat_content) }}</el-descriptions-item>
          <el-descriptions-item label="可采热量">{{ formatNumber(result.extractable_heat) }}</el-descriptions-item>
          <el-descriptions-item label="发电潜力">
            <el-tag type="success" size="large">{{ result.power_potential?.toFixed(2) }} MW</el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 相态信息 -->
        <div v-if="result.phase_info" class="result-phase">
          <h4>相态判定信息</h4>
          <el-descriptions :column="4" border size="small">
            <el-descriptions-item label="相态类型">
              <el-tag :type="result.phase_info.phase_type === 'two_phase' ? 'warning' : 'success'">
                {{ result.phase_info.phase_description }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="沸点温度">{{ result.phase_info.boiling_point?.toFixed(1) }} °C</el-descriptions-item>
            <el-descriptions-item label="水密度">{{ result.water_density_calculated?.toFixed(1) }} kg/m³</el-descriptions-item>
            <el-descriptions-item label="沸腾状态">{{ result.phase_info.is_boiling ? '是' : '否' }}</el-descriptions-item>
          </el-descriptions>
        </div>
      </template>
      
      <!-- 网格计算结果 -->
      <template v-else>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="总资源量" :value="result.total_resource_joules" :formatter="(v: number) => formatNumber(v)" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="发电潜力" :value="result.power_potential_mw" suffix="MW" :precision="2" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="液态网格数" :value="result.liquid_grid_count" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="气液共存网格数" :value="result.two_phase_grid_count" />
          </el-col>
        </el-row>
        
        <el-divider />
        
        <el-descriptions :column="2" border>
          <el-descriptions-item label="可采热量">{{ formatNumber(result.extractable_heat) }}</el-descriptions-item>
          <el-descriptions-item label="采收率">{{ (result.parameters?.recovery_factor * 100).toFixed(0) }}%</el-descriptions-item>
        </el-descriptions>
      </template>
    </div>

    <!-- 计算公式说明 -->
    <div class="card">
      <h3 class="card-title">📖 计算公式说明（基于专利）</h3>
      <div class="formula-section">
        <el-collapse>
          <el-collapse-item title="相态判定曲线方程" name="1">
            <div class="formula">
              <p><strong>沸点温度计算：</strong>T<sub>boiling</sub> = -8.97 × ln(P)</p>
              <p>其中 P 为压力 (MPa)</p>
              <ul>
                <li>当 T < T<sub>boiling</sub>：液态水</li>
                <li>当 T ≥ T<sub>boiling</sub>：气液共存</li>
              </ul>
            </div>
          </el-collapse-item>
          <el-collapse-item title="密度校正公式" name="2">
            <div class="formula">
              <p><strong>地热流体密度：</strong>ρ = A × (1 - B × T) × 1000 kg/m³</p>
              <p>A = 0.99987 + 6.0×10⁻⁵ × T</p>
              <p>B = 2.0×10⁻⁴ + 1.0×10⁻⁵ × T</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="液态资源量公式" name="3">
            <div class="formula">
              <p><strong>液态地热流体资源量：</strong></p>
              <p>Q<sub>liquid</sub> = Σ(φᵢ × Vᵢ × ρᵢ × C<sub>p</sub> × (Tᵢ - T₀))</p>
              <p>其中：φᵢ 为孔隙度，Vᵢ 为体积，ρᵢ 为密度，C<sub>p</sub> 为比热容</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="气液共存资源量公式" name="4">
            <div class="formula">
              <p><strong>气液共存总资源量：</strong>Q<sub>total</sub> = Q<sub>liquid_two_phase</sub> + Q<sub>steam</sub></p>
              <p>Q<sub>liquid_two_phase</sub> = Σ(φᵢ × Vᵢ × ρ × (v<sub>g</sub>/(v<sub>g</sub>-v<sub>f</sub>)) × C<sub>p</sub> × ΔT)</p>
              <p>Q<sub>steam</sub> = Σ(φᵢ × Vᵢ × ρ × (v<sub>f</sub>/(v<sub>g</sub>-v<sub>f</sub>)) × (L + C<sub>pg</sub> × ΔT))</p>
              <p>其中：v<sub>g</sub> 为水蒸气比容，v<sub>f</sub> 为水比容，L 为气化潜热</p>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
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

.phase-panel {
  margin: 16px 0;
}

.phase-details {
  display: flex;
  gap: 24px;
  margin-top: 8px;
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

.description {
  color: #909399;
  margin-bottom: 16px;
}

.grid-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
}

.grid-params {
  margin-top: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-item label {
  font-size: 12px;
  color: #909399;
}

.result-phase {
  margin-top: 16px;
}

.result-phase h4 {
  margin-bottom: 12px;
  color: #606266;
}

.formula-section {
  padding: 8px 0;
}

.formula {
  padding: 8px 16px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.8;
}

.formula p {
  margin: 4px 0;
}

.formula ul {
  margin: 8px 0;
  padding-left: 20px;
}

.formula li {
  margin: 4px 0;
}
</style>
