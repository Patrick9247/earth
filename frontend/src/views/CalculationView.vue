<script setup lang="ts">
import { ref } from 'vue'
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
  { gridCount: 10, porosity: 0.15, volume: 1e7, temperature: 120, pressure: 0.3 },
  { gridCount: 8, porosity: 0.12, volume: 1e7, temperature: 150, pressure: 0.5 },
  { gridCount: 5, porosity: 0.10, volume: 1e7, temperature: 180, pressure: 0.8 },
  { gridCount: 3, porosity: 0.08, volume: 1e7, temperature: 200, pressure: 1.2 }
])

// 基于 IAPWS-IF97 标准的密度计算公式
const calculateDensity = (T: number, P: number): number => {
  // T: 温度(°C), P: 压力(MPa) -> 转换为 kPa
  const Ti = T
  const Pi = P * 1000  // MPa 转 kPa
  
  // 参数A和B
  const A = -Math.pow(Pi - 163278.7315, 2) / (6.613e10)
  const B = -Math.pow(Ti - 4.1171, 2) / 29947.659
  
  // 密度计算 (kg/m³)
  const density = 137.1358 * Math.exp(A) + 139.3560 * Math.exp(B) + 769.9024
  
  // 确保密度在合理范围内
  return Math.max(600, Math.min(density, 1100))
}

// 计算沸点温度 T_boil = 26.12 * ln(P) - 8.97
const calculateBoilingPoint = (pressure: number): number => {
  const pressureKpa = pressure * 1000  // MPa 转 kPa
  if (pressureKpa <= 0) return 100.0
  return 26.12 * Math.log(pressureKpa) - 8.97
}

// 物理常数
const WATER_SPECIFIC_HEAT = 4186      // 地热水比热容 J/(kg·K)
const STEAM_SPECIFIC_HEAT = 2080       // 气体比热容 J/(kg·K)
const LATENT_HEAT_VAPORIZATION = 2260000  // 气化潜热 J/kg
const WATER_SPECIFIC_VOLUME = 0.001    // 水的比容 m³/kg (100°C)
const STEAM_SPECIFIC_VOLUME = 1.673    // 水蒸气比容 m³/kg (100°C, 1atm)

// 计算液态地热流体资源量
// Q₁ = Σ(φᵢ × Vᵢ × ρᵢ × Cw × (Tᵢ - T₀))
const calculateLiquidResource = (
  porosity: number,
  volume: number,
  density: number,
  temperature: number,
  referenceTemp: number
): number => {
  return porosity * volume * density * WATER_SPECIFIC_HEAT * (temperature - referenceTemp)
}

// 计算气液共存时液态地热流体资源量
// Q₂ = Σ(φᵢ × Vᵢ × (1 - ρᵢ × vg) / (vp - vg) × Cw × (T_boil - T₀))
const calculateTwoPhaseLiquidResource = (
  porosity: number,
  volume: number,
  density: number,
  boilingPoint: number,
  referenceTemp: number
): number => {
  const vg = STEAM_SPECIFIC_VOLUME
  const vp = WATER_SPECIFIC_VOLUME
  const factor = (1 - density * vg) / (vp - vg)
  return porosity * volume * factor * WATER_SPECIFIC_HEAT * (boilingPoint - referenceTemp)
}

// 计算气液共存时水蒸汽资源量
// Q₃ = Σ(φᵢ × Vᵢ × (ρᵢ - (1 - ρᵢ × vg) / (vp - vg)) × [Cw × (T_boil - T₀) + Lv + Cv × (Tᵢ - T_boil)])
const calculateSteamResource = (
  porosity: number,
  volume: number,
  density: number,
  temperature: number,
  boilingPoint: number,
  referenceTemp: number
): number => {
  const vg = STEAM_SPECIFIC_VOLUME
  const vp = WATER_SPECIFIC_VOLUME
  const factor1 = (1 - density * vg) / (vp - vg)
  const factor2 = density - factor1
  const latentHeat = WATER_SPECIFIC_HEAT * (boilingPoint - referenceTemp) + LATENT_HEAT_VAPORIZATION + STEAM_SPECIFIC_HEAT * (temperature - boilingPoint)
  return porosity * volume * factor2 * latentHeat
}

// 根据温度和压力自动判断相态
const determinePhase = (temperature: number, pressure: number): string => {
  const boilingPoint = calculateBoilingPoint(pressure)
  return temperature >= boilingPoint ? 'two_phase' : 'liquid'
}

// 前端计算网格资源（基于专利方法）
const calculateGridResource = () => {
  let totalLiquidResource = 0  // Q₁
  let totalTwoPhaseLiquidResource = 0  // Q₂
  let totalSteamResource = 0  // Q₃
  let totalResource = 0  // Q₄ = Q₂ + Q₃
  let liquidGridCount = 0
  let twoPhaseGridCount = 0
  let totalGridCount = 0
  
  gridData.value.forEach((grid: any) => {
    const gridCount = Number(grid.gridCount) || 1
    const porosity = Number(grid.porosity) || 0
    const volume = Number(grid.volume) || 0
    const temperature = Number(grid.temperature) || 0
    const pressure = Number(grid.pressure) || 0.1
    const phase = determinePhase(temperature, pressure)
    const boilingPoint = calculateBoilingPoint(pressure)
    const referenceTemp = gridForm.value.reference_temperature
    const density = calculateDensity(temperature, pressure)
    
    totalGridCount += gridCount
    
    if (porosity <= 0 || volume <= 0) {
      return
    }
    
    if (phase === 'two_phase') {
      // 气液共存网格
      twoPhaseGridCount += gridCount
      
      // Q₂: 气液共存时液态地热流体资源量
      const q2 = calculateTwoPhaseLiquidResource(porosity, volume, density, boilingPoint, referenceTemp)
      // Q₃: 气液共存时水蒸汽资源量
      const q3 = calculateSteamResource(porosity, volume, density, temperature, boilingPoint, referenceTemp)
      
      totalTwoPhaseLiquidResource += q2 * gridCount
      totalSteamResource += q3 * gridCount
      totalResource += (q2 + q3) * gridCount
    } else {
      // 液态水网格
      liquidGridCount += gridCount
      
      // Q₁: 液态地热流体资源量
      const q1 = calculateLiquidResource(porosity, volume, density, temperature, referenceTemp)
      totalLiquidResource += q1 * gridCount
      totalResource += q1 * gridCount
    }
  })
  
  const recovery_factor = Number(gridForm.value.recovery_factor) || 0.25
  const utilization_efficiency = Number(gridForm.value.utilization_efficiency) || 0.1
  const lifetime_years = Number(gridForm.value.lifetime_years) || 30
  
  const extractable = totalResource * recovery_factor
  const annual = lifetime_years > 0 ? extractable * utilization_efficiency / lifetime_years : 0
  const power_mw = annual > 0 ? annual / (365.25 * 24 * 3600) / 1e6 : 0
  
  console.log('计算参数:', { totalResource, extractable, annual, power_mw, totalLiquidResource, totalTwoPhaseLiquidResource, totalSteamResource })
  
  return {
    total_resource_joules: totalResource || 0,
    liquid_resource_joules: totalLiquidResource || 0,
    two_phase_liquid_resource_joules: totalTwoPhaseLiquidResource || 0,
    steam_resource_joules: totalSteamResource || 0,
    total_grid_count: totalGridCount,
    liquid_grid_count: liquidGridCount,
    two_phase_grid_count: twoPhaseGridCount,
    extractable_heat: extractable || 0,
    power_potential_mw: power_mw || 0,
    parameters: { ...gridForm.value }
  }
}

// 网格计算
const handleGridCalculate = async () => {
  loading.value = true
  try {
    // 直接使用前端计算，不依赖后端API（确保gridCount生效）
    result.value = calculateGridResource()
    ElMessage.success('网格计算完成！')
  } catch (error) {
    console.error('网格计算失败:', error)
    ElMessage.error('计算失败，请重试')
  } finally {
    loading.value = false
  }
}

// 添加网格
const addGrid = () => {
  gridData.value.push({
    gridCount: 5,
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

// 智能格式化功率单位
const formatPower = (mw: number): string => {
  if (mw >= 1e6) return (mw / 1e6).toFixed(4) + ' TW'    // 太瓦
  if (mw >= 1e3) return (mw / 1e3).toFixed(4) + ' GW'    // 吉瓦
  if (mw >= 1) return mw.toFixed(4) + ' MW'               // 兆瓦
  if (mw >= 1e-3) return (mw * 1e3).toFixed(4) + ' kW'    // 千瓦
  if (mw >= 1e-6) return (mw * 1e6).toFixed(4) + ' W'    // 瓦
  if (mw >= 1e-9) return (mw * 1e9).toFixed(4) + ' mW'   // 毫瓦
  if (mw >= 1e-12) return (mw * 1e12).toFixed(4) + ' μW'  // 微瓦
  if (mw >= 1e-15) return (mw * 1e15).toFixed(4) + ' nW'  // 纳瓦
  return mw.toExponential(4) + ' W'                       // 科学计数法
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
        <el-table-column label="网格数" width="100">
          <template #default="{ row }">
            <el-input-number v-model="row.gridCount" :min="1" :max="1000" :step="1" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="孔隙度" width="130">
          <template #default="{ row }">
            <el-input-number v-model="row.porosity" :min="0" :step="0.01" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="体积(m³)" width="140">
          <template #default="{ row }">
            <el-input-number v-model="row.volume" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="温度(°C)" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.temperature" :min="50" :max="400" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="压力(MPa)" width="110">
          <template #default="{ row }">
            <el-input-number v-model="row.pressure" :min="0.1" :max="100" :step="0.5" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="沸点温度(°C)" width="120">
          <template #default="{ row }">
            {{ calculateBoilingPoint(row.pressure).toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column label="相态" width="120">
          <template #default="{ row }">
            <el-tag :type="determinePhase(row.temperature, row.pressure) === 'liquid' ? 'success' : 'warning'" size="small">
              {{ determinePhase(row.temperature, row.pressure) === 'liquid' ? '液态水' : '气液共存' }}
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
      
      <!-- 调试信息 -->
      <el-alert type="warning" :closable="false" style="margin-bottom: 16px;">
        <template #title>调试信息：发电潜力={{ formatPower(result.power_potential_mw) }}, 总资源Q₄={{ formatNumber(result.total_resource_joules) }}</template>
      </el-alert>
      
      <!-- 网格计算结果 -->
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="result-item highlight">
            <div class="result-label">发电潜力</div>
            <div class="result-value">{{ formatPower(result.power_potential_mw) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="result-item">
            <div class="result-label">地热资源总量 Q₄</div>
            <div class="result-value">{{ formatNumber(result.total_resource_joules) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="result-item">
            <div class="result-label">可采热量</div>
            <div class="result-value">{{ formatNumber(result.extractable_heat) }}</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="result-item">
            <div class="result-label">总网格数</div>
            <div class="result-value">{{ result.total_grid_count || 0 }} 个</div>
          </div>
        </el-col>
      </el-row>
      
      <el-divider />
      
      <!-- 资源量分类 -->
      <h4 style="margin: 16px 0 12px;">资源量分类</h4>
      <el-row :gutter="20">
        <el-col :span="8">
          <div class="result-item">
            <div class="result-label">液态资源量 Q₁</div>
            <div class="result-value">{{ formatNumber(result.liquid_resource_joules) }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="result-item">
            <div class="result-label">气液共存液态资源量 Q₂</div>
            <div class="result-value">{{ formatNumber(result.two_phase_liquid_resource_joules) }}</div>
          </div>
        </el-col>
        <el-col :span="8">
          <div class="result-item">
            <div class="result-label">蒸汽资源量 Q₃</div>
            <div class="result-value">{{ formatNumber(result.steam_resource_joules) }}</div>
          </div>
        </el-col>
      </el-row>
      
      <el-divider />
      
      <!-- 网格分类统计 -->
      <el-row :gutter="20">
        <el-col :span="12">
          <el-statistic title="液态水网格" :value="result.liquid_grid_count || 0">
            <template #suffix>
              <span style="font-size: 14px; color: #67c23a;">个</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="12">
          <el-statistic title="气液共存网格" :value="result.two_phase_grid_count || 0">
            <template #suffix>
              <span style="font-size: 14px; color: #e6a23c;">个</span>
            </template>
          </el-statistic>
        </el-col>
      </el-row>
    </div>

    <!-- 计算公式说明 -->
    <div class="card">
      <h3 class="card-title">📖 计算公式说明（基于专利）</h3>
      <div class="formula-section">
        <el-collapse>
          <el-collapse-item title="相态选择说明" name="1">
            <div class="formula">
              <p><strong>相态判断规则：</strong></p>
              <ul>
                <li>当 Tᵢ &lt; T<sub>boil</sub>：液态水网格集</li>
                <li>当 Tᵢ ≥ T<sub>boil</sub>：气液共存网格集</li>
              </ul>
              <p><strong>沸点温度计算：</strong>T<sub>boil</sub> = 26.12 × ln(Pᵢ) - 8.97</p>
              <p>其中 Pᵢ 为压力(kPa)</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="密度校正公式（IAPWS-IF97）" name="2">
            <div class="formula">
              <p><strong>地热流体密度：</strong></p>
              <p>ρᵢ = 137.1358 × e<sup>A</sup> + 139.3560 × e<sup>B</sup> + 769.9024</p>
              <p><strong>参数A：</strong>A = -(Pᵢ - 163278.7315)<sup>2</sup> / (6.613 × 10<sup>10</sup>)</p>
              <p><strong>参数B：</strong>B = -(Tᵢ - 4.1171)<sup>2</sup> / 29947.659</p>
              <p>其中：Tᵢ 为温度(°C)，Pᵢ 为压力(kPa)</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="液态资源量公式 Q₁" name="3">
            <div class="formula">
              <p><strong>液态地热流体资源量：</strong></p>
              <p>Q₁ = Σ(φᵢ × Vᵢ × ρᵢ × C<sub>w</sub> × (Tᵢ - T₀))</p>
              <p>其中：φᵢ 为孔隙度，Vᵢ 为体积，ρᵢ 为密度，C<sub>w</sub> 为地热水比热容，T₀ 为参考温度</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="气液共存液态资源量公式 Q₂" name="4">
            <div class="formula">
              <p><strong>气液共存时液态地热流体资源量：</strong></p>
              <p>Q₂ = Σ(φᵢ × Vᵢ × (1 - ρᵢ × v<sub>g</sub>) / (v<sub>p</sub> - v<sub>g</sub>) × C<sub>w</sub> × (T<sub>boil</sub> - T₀))</p>
              <p>其中：v<sub>g</sub> 为水蒸气比容，v<sub>p</sub> 为水的比容</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="气液共存蒸汽资源量公式 Q₃" name="5">
            <div class="formula">
              <p><strong>气液共存时水蒸汽资源量：</strong></p>
              <p>Q₃ = Σ(φᵢ × Vᵢ × (ρᵢ - (1 - ρᵢ × v<sub>g</sub>) / (v<sub>p</sub> - v<sub>g</sub>)) × [Cw × (T<sub>boil</sub> - T₀) + L<sub>v</sub> + C<sub>v</sub> × (Tᵢ - T<sub>boil</sub>)])</p>
              <p>其中：L<sub>v</sub> 为气化潜热，C<sub>v</sub> 为气体比热容</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="地热资源总量 Q₄" name="6">
            <div class="formula">
              <p><strong>热储层的地热资源总量：</strong></p>
              <p>Q₄ = Q₂ + Q₃</p>
              <p>注：液态水网格只计算 Q₁，气液共存网格计算 Q₂ + Q₃</p>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>
</template>

<style scoped>
.result-item {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  text-align: center;
}

.result-item.highlight {
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  color: #fff;
}

.result-item.highlight .result-label {
  color: rgba(255, 255, 255, 0.9);
}

.result-label {
  font-size: 14px;
  color: #909399;
  margin-bottom: 8px;
}

.result-value {
  font-size: 24px;
  font-weight: 700;
  color: #303133;
}

.result-item.highlight .result-value {
  color: #fff;
}

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
