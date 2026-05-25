<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { ElLoading } from 'element-plus'
import { Plus, Upload, Download, Delete, Cpu } from '@element-plus/icons-vue'
import { gempyApi, gridCalcApi } from '@/api/get-api.ts'

const loading = ref(false)
const result = ref<any>(null)
let loadingInstance: any = null

// 图表相关
const chartRef = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null

// 页签状态
const activeTab = ref('calculation')

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
    // 确保每个网格都有热力学参数，没有则设置默认值
    gridData.value = (gridsRes.data || []).map((grid: any) => ({
      ...grid,
      grid_count: grid.grid_count ?? 1,  // 确保有网格数默认值
      liquid_specific_heat: grid.liquid_specific_heat ?? 4.18,
      gas_specific_heat: grid.gas_specific_heat ?? 2.0,
      latent_heat: grid.latent_heat ?? 2257
    }))
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
        liquid_specific_heat: 4.18,  // 默认液体比热容 kJ/(kg·°C)
        gas_specific_heat: 2.0,      // 默认气体比热容 kJ/(kg·°C)
        latent_heat: 2257,           // 默认气化潜热 kJ/kg
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

// 下载CSV模板
const downloadCsvTemplate = () => {
  const headers = ['网格数', '孔隙度', '体积(m³)', '温度(°C)', '压力(kPa)', '液体比热容(kJ/(kg·°C))', '气体比热容(kJ/(kg·°C))', '气化潜热(kJ/kg)']
  const csvContent = headers.join(',') + '\n'
  
  // 添加示例数据行
  const exampleRow = ['10', '0.2', '1000', '150', '500', '4.18', '2.0', '2257']
  const fullContent = csvContent + exampleRow.join(',')
  
  const blob = new Blob(['\ufeff' + fullContent], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '网格数据模板.csv'
  link.click()
  window.URL.revokeObjectURL(url)
  ElMessage.success('模板已下载')
}

// 解析CSV文件
const parseCsvLine = (line: string): string[] => {
  const result: string[] = []
  let current = ''
  let inQuotes = false
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    if (char === '"') {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim())
      current = ''
    } else {
      current += char
    }
  }
  result.push(current.trim())
  return result
}

// 导入CSV文件
const handleCsvUpload = async (file: File) => {
  console.log('[CSV导入] 文件信息:', file.name, file.type, file.size)
  
  const loading = ElLoading.service({ lock: true, text: '正在导入CSV文件...' })
  
  try {
    if (!currentFormId.value) {
      await createNewForm()
    }
    
    // 直接读取File对象
    const text = await file.text()
    console.log('[CSV导入] 文件内容长度:', text.length)
    
    const lines = text.split(/\r?\n/).filter(line => line.trim() && !line.startsWith('#'))
    console.log('[CSV导入] 有效行数:', lines.length)
    
    // 跳过表头行
    const dataLines = lines.slice(1)
    let successCount = 0
    let errorCount = 0
    
    // 检查是否有有效的表单ID
    if (!currentFormId.value) {
      loading.close()
      ElMessage.error('请先创建或选择一个计算表单')
      return false
    }
    
    for (const line of dataLines) {
      if (!line.trim()) continue
      
      const values = parseCsvLine(line)
      console.log('[CSV导入] 解析行:', values)
      
      if (values.length >= 5) {
        try {
          const res = await gridCalcApi.addGrid(currentFormId.value!, {
            calc_id: currentFormId.value!,
            grid_count: parseInt(values[0]) || 1,
            porosity: parseFloat(values[1]) || null,
            volume: parseFloat(values[2]) || null,
            temperature: parseFloat(values[3]) || null,
            pressure: parseFloat(values[4]) || null,
            liquid_specific_heat: parseFloat(values[5]) || 4.18,
            gas_specific_heat: parseFloat(values[6]) || 2.0,
            latent_heat: parseFloat(values[7]) || 2257,
            sort_order: gridData.value.length
          })
          gridData.value.push(res.data)
          successCount++
        } catch (e) {
          console.error('[CSV导入] 添加网格失败:', e)
          errorCount++
        }
      } else {
        errorCount++
      }
    }
    
    loading.close()
    if (successCount > 0) {
      ElMessage.success(`成功导入 ${successCount} 条数据${errorCount > 0 ? `，${errorCount} 条失败` : ''}`)
    } else {
      ElMessage.warning('没有有效数据被导入')
    }
  } catch (error) {
    console.error('[CSV导入] 读取文件失败:', error)
    loading.close()
    ElMessage.error('读取文件失败，请检查文件格式')
  }
  
  return false  // 阻止默认上传行为
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
        grid_count: item.grid_count || 1,
        porosity: item.porosity,
        volume: item.volume,
        temperature: item.temperature,
        pressure: item.pressure,
        liquid_specific_heat: item.liquid_specific_heat,
        gas_specific_heat: item.gas_specific_heat,
        latent_heat: item.latent_heat
      })
    } catch (error) {
      console.error('更新网格失败:', error)
    }
  }
}

// 计算饱和温度（分段公式，P 单位: kPa）
// P_i ≤ 101.325 kPa: T_isat = 0.95 × P_i + 26.44
// P_i > 101.325 kPa: T_isat = 0.04 × P_i + 132.01
const calculateBoilingPoint = (pressure: number): number => {
  if (pressure <= 0) return 100.0
  if (pressure <= 101.325) {
    return 0.95 * pressure + 26.44
  } else {
    return 0.04 * pressure + 132.01
  }
}

// 根据温度和压力自动判断相态
// T < T_sat: 液态水; T ≈ T_sat: 气液共存; T > T_sat: 气态
const determinePhase = (temperature: number, pressure: number): string => {
  const boilingPoint = calculateBoilingPoint(pressure)
  const tolerance = 0.1  // 温度容差
  if (temperature < boilingPoint - tolerance) {
    return 'liquid'  // 液态水
  } else if (temperature >= boilingPoint - tolerance && temperature <= boilingPoint + tolerance) {
    return 'two_phase'  // 气液共存
  } else {
    return 'gas'  // 气态
  }
}

// 获取相态标签
const getPhaseLabel = (phase: string): string => {
  return phase === 'liquid' ? '液态水' : phase === 'two_phase' ? '气液共存' : '气态'
}

// 获取相态标签类型
const getPhaseTagType = (phase: string): string => {
  return phase === 'liquid' ? 'success' : phase === 'two_phase' ? 'warning' : 'danger'
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  if (gridData.value.length === 0) return

  // 销毁旧实例
  if (myChart) {
    myChart.dispose()
    myChart = null
  }

  // 准备图表数据
  const xData = gridData.value.map((_, idx) => `网格${idx + 1}`)
  const yData = gridData.value.map(d => d.grid_count || 1)

  // 初始化图表
  myChart = echarts.init(chartRef.value)

  const option = {
    title: {
      text: '网格数量分布',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const idx = params[0].dataIndex
        const grid = gridData.value[idx]
        if (!grid) return ''
        const boilingPoint = calculateBoilingPoint(grid.pressure || 0.1)
        const phase = determinePhase(grid.temperature || 0, grid.pressure || 0.1)
        return `
          <div style="font-weight:bold;margin-bottom:5px;">${params[0].axisValue}</div>
          <div style="margin:3px 0;">孔隙度: <b>${(grid.porosity || 0).toFixed(4)}</b></div>
          <div style="margin:3px 0;">体积: <b>${(grid.volume || 0).toFixed(2)}</b> m³</div>
          <div style="margin:3px 0;">温度: <b>${(grid.temperature || 0).toFixed(2)}</b> °C</div>
          <div style="margin:3px 0;">压力: <b>${(grid.pressure || 0).toFixed(2)}</b> kPa</div>
          <div style="margin:3px 0;">沸点温度: <b>${boilingPoint.toFixed(2)}</b> °C</div>
          <div style="margin:3px 0;">相态: <b>${getPhaseLabel(phase)}</b></div>
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '60px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: {
        interval: 0,
        rotate: 30
      },
      name: '编号'
    },
    yAxis: {
      type: 'value',
      name: '网格数'
    },
    series: [
      {
        name: '网格数',
        type: 'bar',
        data: yData,
        itemStyle: {
          color: (params: any) => {
            const grid = gridData.value[params.dataIndex]
            const phase = determinePhase(grid?.temperature || 0, grid?.pressure || 0.1)
            return phase === 'liquid' ? '#67C23A' : phase === 'two_phase' ? '#E6A23C' : '#F56565'
          }
        },
        label: {
          show: true,
          position: 'top',
          formatter: '{c}'
        }
      }
    ]
  }

  myChart.setOption(option)
}

// 监听页签切换，更新图表
watch(activeTab, (newTab) => {
  if (newTab === 'visualization') {
    setTimeout(() => initChart(), 100)
  }
})

// 窗口变化自适应
const resizeChart = () => {
  myChart?.resize()
}

onMounted(() => {
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  if (myChart) {
    myChart.dispose()
    myChart = null
  }
})

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
    // 直接传递网格数据，后端会根据 phase 字段使用对应公式计算
    const grids = gridData.value.map((grid: any) => ({
      grid_count: grid.grid_count || 0,
      porosity: grid.porosity,
      volume: grid.volume,
      temperature: grid.temperature,
      pressure: grid.pressure,
      phase: determinePhase(grid.temperature || 0, grid.pressure || 0.1),  // 根据温度压力计算相态
      liquid_specific_heat: grid.liquid_specific_heat,
      gas_specific_heat: grid.gas_specific_heat,
      latent_heat: grid.latent_heat
    }))
    
    // 计算总网格数用于显示
    const totalGrids = grids.reduce((sum: number, g: any) => sum + (g.grid_count || 1), 0)
    console.log(`[网格计算] 准备计算 ${grids.length} 条记录，共 ${totalGrids} 个网格...`)
    console.log('[网格计算] 发送的数据:', JSON.stringify(grids, null, 2))
    
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
      ElMessage.success(`网格计算完成！共 ${totalGrids} 个网格`)
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

// 格式化体积
const formatVolume = (vol: number, decimals: number = 2): string => {
  if (!vol && vol !== 0) return '0'
  if (vol >= 1e9) return (vol / 1e9).toFixed(decimals) + ' km³'
  if (vol >= 1e6) return (vol / 1e6).toFixed(decimals) + ' Mm³'
  if (vol >= 1e3) return (vol / 1e3).toFixed(decimals) + ' 千m³'
  return vol.toFixed(decimals) + ' m³'
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

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- 网格资源计算 -->
      <el-tab-pane label="网格资源计算" name="calculation">
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
            <el-upload
              ref="csvUploadRef"
              :show-file-list="false"
              :before-upload="handleCsvUpload"
              accept=".csv"
              style="display: inline-block; margin-left: 10px;"
            >
              <el-button type="warning">
                <el-icon><Upload /></el-icon>
                导入CSV
              </el-button>
            </el-upload>
            <el-button type="info" @click="downloadCsvTemplate">
              <el-icon><Download /></el-icon>
              下载模板
            </el-button>
            <el-button type="success" @click="handleGridCalculate" :loading="loading">
              <el-icon><Cpu /></el-icon>
              计算网格资源
            </el-button>
          </div>

          <el-table :data="gridData" border stripe style="width: 100%" table-layout="auto">
            <el-table-column label="编号" type="index" width="50" />
            <el-table-column label="网格数" min-width="120">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.grid_count" :min="1" :max="10000" :step="1" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="孔隙度" min-width="110">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.porosity" :min="0" :max="1" :step="0.001" :precision="4" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="体积(m³)" min-width="120">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.volume" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="温度(°C)" min-width="110">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.temperature" :min="0" :max="1000" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="压力(kPa)" min-width="110">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.pressure" :min="0.1" :max="500000" :step="100" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="液体比热容" min-width="100">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.liquid_specific_heat" :min="0.1" :max="10" :step="0.01" :precision="2" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="气体比热容" min-width="100">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.gas_specific_heat" :min="0.1" :max="5" :step="0.01" :precision="2" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="气化潜热" min-width="100">
              <template #default="{ row, $index }">
                <el-input-number v-model="row.latent_heat" :min="100" :max="3000" :step="10" :precision="0" size="small" controls-position="right" @change="updateGridData($index)" />
              </template>
            </el-table-column>
            <el-table-column label="沸点(°C)" min-width="80">
              <template #default="{ row }">
                {{ calculateBoilingPoint(row.pressure || 0.1).toFixed(1) }}
              </template>
            </el-table-column>
            <el-table-column label="相态" min-width="90">
              <template #default="{ row }">
                <el-tag :type="getPhaseTagType(determinePhase(row.temperature || 0, row.pressure || 0.1))" size="small">
                  {{ getPhaseLabel(determinePhase(row.temperature || 0, row.pressure || 0.1)) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="60" fixed="right">
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
            <el-col :span="6">
              <div class="result-item">
                <div class="result-label">总网格体积</div>
                <div class="result-value">{{ formatVolume(result.total_volume) }}</div>
              </div>
            </el-col>
          </el-row>
          
          <el-divider />
          
          <!-- 总热量构成 -->
          <h4 style="margin: 16px 0 12px;">热量构成</h4>
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="result-item">
                <div class="result-label">地热流体热量</div>
                <div class="result-value">{{ formatNumber(result.fluid_resource_joules) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="result-item">
                <div class="result-label">岩石热量</div>
                <div class="result-value">{{ formatNumber(result.rock_heat_joules) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="result-item highlight">
                <div class="result-label">总地热资源量 Q<sub>总</sub></div>
                <div class="result-value">{{ formatNumber(result.total_resource_joules) }}</div>
              </div>
            </el-col>
          </el-row>
          
          <el-divider />
          
          <!-- 资源量分类 -->
          <h4 style="margin: 16px 0 12px;">流体资源量分类（按相态）</h4>
          <el-row :gutter="20">
            <el-col :span="6">
              <div class="result-item">
                <div class="result-label">液态资源量 Q<sub>1</sub></div>
                <div class="result-value">{{ formatNumber(result.liquid_resource_joules) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="result-item">
                <div class="result-label">气液共存资源量 Q<sub>4</sub></div>
                <div class="result-value">{{ formatNumber(result.reservoir_resource_joules) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="result-item">
                <div class="result-label">气态资源量 Q<sub>5</sub></div>
                <div class="result-value">{{ formatNumber(result.gas_resource_joules || 0) }}</div>
              </div>
            </el-col>
          </el-row>
          
          <el-row :gutter="20" style="margin-top: 12px;">
            <el-col :span="6">
              <div class="result-item">
                <div class="result-label">├ 气液共存液态 Q<sub>2</sub></div>
                <div class="result-value">{{ formatNumber(result.two_phase_liquid_resource_joules) }}</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="result-item">
                <div class="result-label">├ 气液共存蒸汽 Q<sub>3</sub></div>
                <div class="result-value">{{ formatNumber(result.steam_resource_joules) }}</div>
              </div>
            </el-col>
          </el-row>
          
          <el-divider />
          
          <!-- 网格分类统计 -->
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="液态水网格" :value="result.liquid_grid_count || 0">
                <template #suffix>
                  <span style="font-size: 14px; color: #67c23a;">个</span>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="8">
              <el-statistic title="气液共存网格" :value="result.two_phase_grid_count || 0">
                <template #suffix>
                  <span style="font-size: 14px; color: #e6a23c;">个</span>
                </template>
              </el-statistic>
            </el-col>
            <el-col :span="8">
              <el-statistic title="气态网格" :value="result.gas_grid_count || 0">
                <template #suffix>
                  <span style="font-size: 14px; color: #f56c6c;">个</span>
                </template>
              </el-statistic>
            </el-col>
          </el-row>
        </div>
      </el-tab-pane>

      <!-- 数据可视化 -->
      <el-tab-pane label="数据可视化" name="visualization">
        <div class="card">
          <h3 class="card-title">网格数据可视化</h3>
          <div class="chart-section" v-if="gridData.length > 0">
            <div ref="chartRef" class="grid-chart"></div>
          </div>
          <el-empty v-else description="暂无网格数据，请先添加网格" />
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
@import "@/styles/calculation-view.css";
</style>
