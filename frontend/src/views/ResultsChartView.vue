<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { gempyApi } from '@/api/get-api.ts'

// 注册 ECharts 组件
use([LineChart, GridComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const router = useRouter()

// 结果数据
const results = ref<any[]>([])
const loading = ref(false)

// 选中的结果用于图表展示
const selectedResults = ref<number[]>([])
const selectionMode = ref(false)

// 加载计算结果
const loadResults = async () => {
  loading.value = true
  try {
    const res = await gempyApi.getResults()
    results.value = res.data || []
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载计算结果失败')
    results.value = []
  } finally {
    loading.value = false
  }
}

// 切换选择模式
const toggleSelectionMode = () => {
  selectionMode.value = !selectionMode.value
  if (!selectionMode.value) {
    selectedResults.value = []
  }
}

// 判断是否选中
const isSelected = (id: number) => selectedResults.value.includes(id)

// 清除选择
const clearSelection = () => {
  selectedResults.value = []
}

// 全选
const selectAll = () => {
  selectedResults.value = results.value.map(r => r.id)
}

// 选中反转
const toggleSelectAll = () => {
  if (selectedResults.value.length === results.value.length) {
    selectedResults.value = []
  } else {
    selectAll()
  }
}

// 生成图表数据
const chartOption = computed(() => {
  if (selectedResults.value.length === 0) {
    return {
      title: {
        text: '请选择要展示的计算结果',
        left: 'center',
        top: 'center',
        textStyle: { color: '#999', fontSize: 16 }
      },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value', name: '发电潜力 (MW)' },
      series: []
    }
  }

  const selectedData = results.value.filter(r => selectedResults.value.includes(r.id))
  
  // 横轴为计算结果名称
  const xAxisData = selectedData.map((r, index) => `${index + 1}. ${r.name}`)
  
  // 纵轴为发电潜力
  const powerData = selectedData.map(r => r.power_potential || 0)

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      formatter: (params: any) => {
        if (!params || params.length === 0) return ''
        const param = params[0]
        const dataIndex = param.dataIndex
        const data = selectedData[dataIndex]
        
        return `
          <div style="font-weight: bold; margin-bottom: 5px;">${data.name}</div>
          <div>储层体积: ${formatVolume(data.volume)}</div>
          <div>平均温度: ${data.temperature_avg?.toFixed(4) || '0'} °C</div>
          <div>可采热量: ${formatHeat(data.extractable_heat)}</div>
          <div style="color: #67c23a; font-weight: bold;">发电潜力: ${formatPower(data.power_potential)}</div>
        `
      }
    },
    legend: {
      data: ['发电潜力'],
      top: 10
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xAxisData,
      name: '计算结果',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: {
        rotate: 0,
        fontSize: 11,
        interval: 0
      }
    },
    yAxis: {
      type: 'value',
      name: '发电潜力 (MW)',
      nameLocation: 'middle',
      nameGap: 50,
      axisLabel: {
        formatter: (value: number) => formatPower(value)
      }
    },
    series: [
      {
        name: '发电潜力',
        type: 'line',
        data: powerData,
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: {
          width: 3,
          color: '#409eff'
        },
        itemStyle: {
          color: '#409eff',
          borderColor: '#fff',
          borderWidth: 2
        },
        emphasis: {
          scale: true,
          scaleSize: 12
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
              { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
            ]
          }
        },
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => formatPower(params.value),
          fontSize: 10
        }
      }
    ],
    animationDuration: 1000,
    animationEasing: 'cubicOut' as const
  }
})

// 格式化发电潜力
const formatPower = (mw: number): string => {
  if (!mw) return '0'
  if (mw >= 1e6) return (mw / 1e6).toFixed(2) + ' TW'
  if (mw >= 1e3) return (mw / 1e3).toFixed(2) + ' GW'
  if (mw >= 1) return mw.toFixed(4) + ' MW'
  if (mw >= 1e-3) return (mw * 1e3).toFixed(4) + ' kW'
  return mw.toExponential(2) + ' W'
}

// 格式化体积
const formatVolume = (vol: number | null | undefined): string => {
  if (!vol) return '0 m³'
  if (vol >= 1e12) return (vol / 1e12).toFixed(2) + ' × 10¹² m³'
  if (vol >= 1e9) return (vol / 1e9).toFixed(2) + ' × 10⁹ m³'
  if (vol >= 1e6) return (vol / 1e6).toFixed(2) + ' × 10⁶ m³'
  if (vol >= 1e3) return (vol / 1e3).toFixed(2) + ' × 10³ m³'
  return vol.toFixed(2) + ' m³'
}

// 格式化热量
const formatHeat = (heat: number | null | undefined): string => {
  if (!heat) return '0 J'
  if (heat >= 1e18) return (heat / 1e18).toFixed(2) + ' EJ'
  if (heat >= 1e15) return (heat / 1e15).toFixed(2) + ' PJ'
  if (heat >= 1e12) return (heat / 1e12).toFixed(2) + ' TJ'
  if (heat >= 1e9) return (heat / 1e9).toFixed(2) + ' GJ'
  return heat.toExponential(2) + ' J'
}

// 返回列表页
const goBack = () => {
  router.push('/results')
}

onMounted(() => {
  loadResults()
})
</script>

<template>
  <div class="results-chart-view">
    <div class="page-header">
      <div class="header-left">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回列表
        </el-button>
        <h1 class="page-title">数据可视化</h1>
      </div>
      <div class="header-actions">
        <el-button 
          :type="selectionMode ? 'primary' : 'default'"
          @click="toggleSelectionMode"
        >
          <el-icon><Select /></el-icon>
          {{ selectionMode ? '退出选择' : '选择数据' }}
        </el-button>
        <template v-if="selectionMode">
          <el-button @click="selectAll">全选</el-button>
          <el-button @click="toggleSelectAll">
            {{ selectedResults.length === results.length ? '取消全选' : '反选' }}
          </el-button>
          <el-button @click="clearSelection" :disabled="selectedResults.length === 0">
            清除选择
          </el-button>
        </template>
      </div>
    </div>

    <!-- 选择提示 -->
    <div v-if="selectionMode" class="selection-tip">
      <el-alert
        title="选择模式已开启"
        type="info"
        :closable="false"
        show-icon
      >
        <template #default>
          请在下方表格中勾选要展示的数据（已选择 {{ selectedResults.length }} 条），
          或点击「生成图表」按钮查看选中数据的可视化效果。
        </template>
      </el-alert>
    </div>

    <!-- 数据选择表格 -->
    <el-card class="selection-card">
      <template #header>
        <div class="card-header">
          <span>计算结果列表</span>
          <span class="selection-count">已选择 {{ selectedResults.length }} / {{ results.length }} 条</span>
        </div>
      </template>
      
      <el-table 
        :data="results" 
        v-loading="loading" 
        stripe 
        @selection-change="(val: any) => selectedResults = val.map((v: any) => v.id)"
        :row-class-name="({ row }: any) => isSelected(row.id) ? 'selected-row' : ''"
      >
        <el-table-column v-if="selectionMode" type="selection" width="55" />
        <el-table-column prop="name" label="名称" width="180" />
        <el-table-column prop="volume" label="储层体积(m³)" width="150">
          <template #default="{ row }">
            {{ formatVolume(row.volume) }}
          </template>
        </el-table-column>
        <el-table-column prop="temperature_avg" label="平均温度(°C)" width="120">
          <template #default="{ row }">
            <el-tag :type="row.temperature_avg > 150 ? 'danger' : 'success'" size="small">
              {{ row.temperature_avg?.toFixed(2) }} °C
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="extractable_heat" label="可采热量" width="140">
          <template #default="{ row }">
            {{ formatHeat(row.extractable_heat) }}
          </template>
        </el-table-column>
        <el-table-column prop="power_potential" label="发电潜力" width="140">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: 600;">
              {{ formatPower(row.power_potential) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column v-if="!selectionMode" label="操作" width="100">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              text
              @click="selectedResults = [row.id]; selectionMode = true"
            >
              查看图表
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 图表区域 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>发电潜力折线图</span>
          <el-tag v-if="selectedResults.length > 0" type="primary">
            {{ selectedResults.length }} 条数据
          </el-tag>
        </div>
      </template>
      
      <div class="chart-container">
        <v-chart 
          :option="chartOption" 
          autoresize 
          style="height: 450px; width: 100%;"
        />
      </div>
      
      <div v-if="selectedResults.length === 0" class="chart-placeholder">
        <el-empty description="请先选择要展示的数据">
          <el-button type="primary" @click="toggleSelectionMode">
            立即选择
          </el-button>
        </el-empty>
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.results-chart-view {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.page-title {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.selection-tip {
  margin-bottom: 20px;
}

.selection-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selection-count {
  font-size: 13px;
  color: #909399;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  min-height: 450px;
  position: relative;
}

.chart-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.9);
}

:deep(.selected-row) {
  background-color: #ecf5ff !important;
}

:deep(.el-table .selected-row td) {
  background-color: #ecf5ff !important;
}
</style>
