<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ElLoading } from 'element-plus'
import { gempyApi, gridCalcApi } from '@/api/get-api.ts'

const loading = ref(false)
const result = ref<any>(null)
let loadingInstance: any = null

// 当前编辑的表单ID
const currentFormId = ref<number | null>(null)
const currentFormName = ref('未命名')

// 网格计算表单参数
const gridForm = ref({
  reference_temperature: 25,
  recovery_factor: 0.25,
  utilization_efficiency: 0.1,
  lifetime_years: 30
})

// 网格数据列表
const gridData = ref<any[]>([])

// 加载表单列表
const loadFormList = async () => {
  try {
    const res = await gridCalcApi.getAll()
    return res.data || []
  } catch (error) {
    console.error('加载表单列表失败:', error)
    return []
  }
}

// 加载指定表单
const loadForm = async (formId: number) => {
  try {
    // 加载表单信息
    const formRes = await gridCalcApi.getOne(formId)
    const form = formRes.data
    currentFormId.value = form.id
    currentFormName.value = form.name
    gridForm.value = {
      reference_temperature: form.reference_temperature,
      recovery_factor: form.recovery_factor,
      utilization_efficiency: form.utilization_efficiency,
      lifetime_years: form.lifetime_years
    }
    
    // 加载网格数据
    const gridsRes = await gridCalcApi.getGrids(formId)
    gridData.value = gridsRes.data || []
  } catch (error) {
    console.error('加载表单失败:', error)
    ElMessage.error('加载表单失败')
  }
}

// 新建表单
const createNewForm = async () => {
  try {
    const res = await gridCalcApi.create({
      name: `计算方案_${Date.now()}`,
      reference_temperature: 25,
      recovery_factor: 0.25,
      utilization_efficiency: 0.1,
      lifetime_years: 30
    })
    currentFormId.value = res.data.id
    currentFormName.value = res.data.name
    gridData.value = []
    ElMessage.success('已创建新表单')
  } catch (error) {
    console.error('创建表单失败:', error)
    ElMessage.error('创建表单失败')
  }
}

// 添加网格
const addGrid = async () => {
  if (!currentFormId.value) {
    await createNewForm()
  }
  
  if (currentFormId.value) {
    try {
      const res = await gridCalcApi.addGrid(currentFormId.value, {
        calc_id: currentFormId.value,
        grid_count: 1,
        porosity: null,
        volume: null,
        temperature: null,
        pressure: null,
        sort_order: gridData.value.length
      })
      gridData.value.push(res.data)
      ElMessage.success('已添加网格')
    } catch (error) {
      console.error('添加网格失败:', error)
      ElMessage.error('添加网格失败')
    }
  }
}

// 删除网格
const removeGrid = async (index: number) => {
  const item = gridData.value[index]
  if (item && item.id) {
    try {
      await gridCalcApi.deleteGrid(currentFormId.value!, item.id)
    } catch (error) {
      console.error('删除网格失败:', error)
    }
  }
  gridData.value.splice(index, 1)
}

// 更新网格数据
const updateGridData = async (index: number) => {
  const item = gridData.value[index]
  if (item && item.id && currentFormId.value) {
    try {
      await gridCalcApi.updateGrid(currentFormId.value, item.id, {
        grid_count: item.grid_count,
        porosity: item.porosity,
        volume: item.volume,
        temperature: item.temperature,
        pressure: item.pressure
      })
    } catch (error) {
      console.error('更新网格失败:', error)
    }
  }
}

// 计算沸点温度 T_boil = 26.12 * ln(P) - 8.97
const calculateBoilingPoint = (pressure: number): number => {
  const pressureKpa = pressure * 1000  // MPa 转 kPa
  if (pressureKpa <= 0) return 100.0
  return 26.12 * Math.log(pressureKpa) - 8.97
}

// 根据温度和压力自动判断相态
const determinePhase = (temperature: number, pressure: number): string => {
  const boilingPoint = calculateBoilingPoint(pressure)
  return temperature >= boilingPoint ? 'two_phase' : 'liquid'
}

// 网格计算
const handleGridCalculate = async () => {
  // 验证数据
  if (gridData.value.length === 0) {
    ElMessage.warning('请先添加网格数据')
    return
  }
  
  for (let i = 0; i < gridData.value.length; i++) {
    const grid = gridData.value[i]
    if (!grid.porosity || !grid.volume || !grid.temperature || !grid.pressure) {
      ElMessage.warning(`第 ${i + 1} 行网格数据不完整，请填写所有字段`)
      return
    }
  }
  
  loading.value = true
  result.value = null  // 清除之前的结果
  // 显示加载遮罩
  loadingInstance = ElLoading.service({
    lock: true,
    text: '正在计算，请稍候...',
    background: 'rgba(0, 0, 0, 0.7)'
  })
  
  try {
    // 转换为后端API格式
    const grids = gridData.value.flatMap((grid: any) => {
      const count = grid.grid_count || 1
      return Array.from({ length: count }, () => ({
        porosity: grid.porosity,
        volume: grid.volume / count, // 每个网格的体积
        temperature: grid.temperature,
        pressure: grid.pressure
      }))
    })
    
    console.log(`[网格计算] 准备计算 ${grids.length} 个网格...`)
    
    // 调用后端API计算并保存
    const res = await gempyApi.calculateGrid({
      grids,
      reference_temperature: gridForm.value.reference_temperature,
      recovery_factor: gridForm.value.recovery_factor,
      utilization_efficiency: gridForm.value.utilization_efficiency,
      lifetime_years: gridForm.value.lifetime_years
    })
    
    console.log('[网格计算] API响应:', res.data)
    
    if (res.data.success) {
      result.value = res.data.data
      ElMessage.success(`网格计算完成！共 ${grids.length} 个网格`)
    } else {
      ElMessage.error(res.data.message || '计算失败')
    }
  } catch (error: any) {
    console.error('网格计算失败:', error)
    // 详细错误信息
    if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请减少网格数量或稍后重试')
    } else if (error.response) {
      ElMessage.error(error.response.data?.detail || error.response.data?.message || '服务器错误')
    } else if (error.request) {
      ElMessage.error('无法连接服务器，请检查网络')
    } else {
      ElMessage.error(error.message || '计算失败，请重试')
    }
  } finally {
    loading.value = false
    // 关闭加载遮罩
    if (loadingInstance) {
      loadingInstance.close()
      loadingInstance = null
    }
  }
}

// 格式化数字
const formatNumber = (num: number, decimals: number = 2): string => {
  if (!num && num !== 0) return '0'
  if (num >= 1e18) return (num / 1e18).toFixed(decimals) + ' EJ'
  if (num >= 1e15) return (num / 1e15).toFixed(decimals) + ' PJ'
  if (num >= 1e12) return (num / 1e12).toFixed(decimals) + ' TJ'
  if (num >= 1e9) return (num / 1e9).toFixed(decimals) + ' GJ'
  if (num >= 1e6) return (num / 1e6).toFixed(decimals) + ' MJ'
  return num.toFixed(decimals) + ' J'
}

// 智能格式化功率单位
const formatPower = (mw: number): string => {
  if (!mw && mw !== 0) return '0'
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

// 页面加载时初始化
onMounted(async () => {
  // 加载表单列表，如果有则加载最新的
  const forms = await loadFormList()
  if (forms.length > 0) {
    await loadForm(forms[0].id)
  } else {
    // 没有表单则创建新表单
    await createNewForm()
  }
})
</script>

<template>
  <div class="calculation-view">
    <h1 class="page-title">地热资源计算</h1>
    
    <!-- 网格资源计算 -->
    <div class="card">
      <h3 class="card-title">网格资源计算</h3>
      <p class="description">
        基于一种不规则热储层多相态地热流体资源量计算方法，对每个网格进行相态判定后分别计算资源量。
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
        <el-table-column label="编号" type="index" width="60" />
        <el-table-column label="网格数" width="150">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.grid_count" :min="1" :max="1000" :step="1" size="small" @change="updateGridData($index)" />
          </template>
        </el-table-column>
        <el-table-column label="孔隙度" width="150">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.porosity" :min="0" :max="1" :step="0.01" :precision="4" size="small" @change="updateGridData($index)" />
          </template>
        </el-table-column>
        <el-table-column label="体积(m³)" width="150">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.volume" size="small" @change="updateGridData($index)" />
          </template>
        </el-table-column>
        <el-table-column label="温度(°C)" width="150">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.temperature" :min="50" :max="400" size="small" @change="updateGridData($index)" />
          </template>
        </el-table-column>
        <el-table-column label="压力(MPa)" width="150">
          <template #default="{ row, $index }">
            <el-input-number v-model="row.pressure" :min="0.1" :max="100" :step="0.5" size="small" @change="updateGridData($index)" />
          </template>
        </el-table-column>
        <el-table-column label="沸点温度(°C)" width="120">
          <template #default="{ row }">
            {{ calculateBoilingPoint(row.pressure || 0.1).toFixed(1) }}
          </template>
        </el-table-column>
        <el-table-column label="相态" width="120">
          <template #default="{ row }">
            <el-tag :type="determinePhase(row.temperature || 0, row.pressure || 0.1) === 'liquid' ? 'success' : 'warning'" size="small">
              {{ determinePhase(row.temperature || 0, row.pressure || 0.1) === 'liquid' ? '液态水' : '气液共存' }}
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
    </div>

    <!-- 计算结果 -->
    <div class="card" v-if="result">
      <h3 class="card-title">✅ 计算结果</h3>
      
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
  </div>
</template>

<style scoped>
@import "@/styles/calculation-view.css";
</style>
