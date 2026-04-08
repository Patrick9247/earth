<script setup lang="ts">
import { ref } from 'vue'
import { gempyApi } from '@/api'
import { ElMessage } from 'element-plus'

const loading = ref(false)
const result = ref<any>(null)

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

// 计算水密度（专利公式）
const calculateDensity = (T: number): number => {
  const A = 0.99987 + 6.0e-5 * T
  const B = 2.0e-4 + 1.0e-5 * T
  const density = A * (1 - B * T) * 1000
  return Math.max(600, Math.min(density, 1050))
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

// 删除网格
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
    
    <!-- 网格资源计算 -->
    <div class="card">
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
    </div>

    <!-- 计算结果 -->
    <div class="card" v-if="result">
      <h3 class="card-title">✅ 计算结果</h3>
      
      <!-- 网格计算结果 -->
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
