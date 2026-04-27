<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { gempyApi } from '@/api/get-api.ts'
import { ElMessage } from 'element-plus'
import { formatDate } from '@/utils/utils.ts'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { ElTable } from 'element-plus'

// 注册 ECharts 组件
use([LineChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])

const results = ref<any[]>([])
const loading = ref(false)
const selectedResult = ref<any>(null)
const tableRef = ref<InstanceType<typeof ElTable>>()
const dialogVisible = computed({
  get: () => selectedResult.value !== null,
  set: () => { selectedResult.value = null }
})

// 分页配置
const currentPage = ref(1)
const pageSize = ref(10)
const total = computed(() => results.value.length)

// 分页后的数据
const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return results.value.slice(start, end)
})

// 分页变化
const handlePageChange = (page: number) => {
  currentPage.value = page
}

// 每页条数变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

// 选中的用于图表展示的数据
const selectedChartData = ref<number[]>([])

const loadResults = async () => {
  loading.value = true
  try {
    const res = await gempyApi.getResults()
    console.log('API返回数据:', res.data)
    results.value = res.data || []
    currentPage.value = 1 // 重置分页
    selectedChartData.value = [] // 清空选择
    tableRef.value?.clearSelection() // 清空表格选择
  } catch (error) {
    console.error('加载失败:', error)
    ElMessage.error('加载计算结果失败，请检查网络连接')
    results.value = []
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id: number) => {
  const index = results.value.findIndex(r => r.id === id)
  if (index !== -1) {
    results.value.splice(index, 1)
  }
  
  try {
    await gempyApi.deleteResult(id)
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('API删除失败，但已从本地删除:', error)
  }
}

const viewDetail = async (row: any) => {
  selectedResult.value = row
  if (row.parameters && row.parameters.original_grids) {
    selectedResult.value.grids = row.parameters.original_grids
  }
}

// 全选/取消全选图表数据
const toggleSelectAll = () => {
  if (selectedChartData.value.length === results.value.length) {
    tableRef.value?.clearSelection()
  } else {
    results.value.forEach(row => {
      tableRef.value?.toggleRowSelection(row, true)
    })
  }
}

// 清除选择
const clearSelection = () => {
  tableRef.value?.clearSelection()
}

// 监听表格选择变化
const handleSelectionChange = (val: any[]) => {
  selectedChartData.value = val.map(v => v.id)
}

// 格式化数字显示
const formatNumber = (num: number): string => {
  if (!num) return '0'
  if (num >= 1e18) return (num / 1e18).toFixed(2) + ' EJ'
  if (num >= 1e15) return (num / 1e15).toFixed(2) + ' PJ'
  if (num >= 1e12) return (num / 1e12).toFixed(2) + ' TJ'
  if (num >= 1e9) return (num / 1e9).toFixed(2) + ' GJ'
  if (num >= 1e6) return (num / 1e6).toFixed(2) + ' MJ'
  if (num >= 1e3) return (num / 1e3).toFixed(2) + ' kJ'
  return num.toFixed(2) + ' J'
}

// 格式化功率显示
const formatPower = (mw: number): string => {
  if (!mw) return '0'
  if (mw >= 1e6) return (mw / 1e6).toFixed(4) + ' TW'
  if (mw >= 1e3) return (mw / 1e3).toFixed(4) + ' GW'
  if (mw >= 1) return mw.toFixed(4) + ' MW'
  if (mw >= 1e-3) return (mw * 1e3).toFixed(4) + ' kW'
  if (mw >= 1e-6) return (mw * 1e6).toFixed(4) + ' W'
  if (mw >= 1e-9) return (mw * 1e9).toFixed(4) + ' mW'
  if (mw >= 1e-12) return (mw * 1e12).toFixed(4) + ' μW'
  return mw.toExponential(4) + ' W'
}

// 格式化体积显示
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

// 导出为 CSV
const exportToCSV = () => {
  if (results.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  const headers = ['名称', '储层体积(m³)', '平均温度(°C)', '热含量(J)', '可采热量(J)', '发电潜力(MW)', '创建时间']
  
  const rows = results.value.map(row => [
    row.name,
    row.volume?.toFixed(2) || '0.00',
    row.temperature_avg?.toFixed(2) || '0.00',
    row.heat_content?.toFixed(2) || '0.00',
    row.extractable_heat?.toFixed(2) || '0.00',
    row.power_potential?.toFixed(6) || '0.000000',
    row.created_at
  ])

  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `计算结果_${new Date().toISOString().slice(0, 10)}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('导出成功')
}

// 图表配置
const chartOption = computed(() => {
  if (selectedChartData.value.length === 0) {
    return {
      title: {
        text: '请勾选表格中的数据进行图表展示',
        left: 'center',
        top: 'center',
        textStyle: { color: '#999', fontSize: 14 }
      },
      xAxis: { type: 'category', data: [] },
      yAxis: { type: 'value', name: '发电潜力 (MW)' },
      series: []
    }
  }

  const selectedData = results.value.filter(r => selectedChartData.value.includes(r.id))
  const xAxisData = selectedData.map((r, index) => `${index + 1}. ${r.name}`)
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
      nameGap: 65,
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

onMounted(() => {
  loadResults()
})
</script>

<template>
  <div class="results-view">
    <h1 class="page-title">计算结果管理</h1>
    
    <div class="card">
      <div class="btn-group">
        <el-button @click="loadResults">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="toggleSelectAll">
          {{ selectedChartData.length === results.length ? '取消全选' : '全选图表' }}
        </el-button>
        <el-button @click="clearSelection" :disabled="selectedChartData.length === 0">
          清除选择
        </el-button>
        <el-button type="success" @click="exportToCSV">
          <el-icon><Download /></el-icon>
          导出 CSV
        </el-button>
      </div>

      <el-table 
        ref="tableRef"
        :data="paginatedData" 
        v-loading="loading" 
        stripe 
        row-key="id"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="volume" label="储层体积(m³)" width="150">
          <template #default="{ row }">
            <span v-if="row.volume >= 1e9">{{ (row.volume / 1e9).toFixed(2) }} × 10⁹</span>
            <span v-else-if="row.volume >= 1e6">{{ (row.volume / 1e6).toFixed(2) }} × 10⁶</span>
            <span v-else-if="row.volume >= 1e3">{{ (row.volume / 1e3).toFixed(2) }} × 10³</span>
            <span v-else>{{ row.volume?.toFixed(2) || '0.00' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="temperature_avg" label="平均温度(°C)" width="120">
          <template #default="{ row }">
            <el-tag :type="row.temperature_avg > 150 ? 'danger' : 'success'">{{ row.temperature_avg?.toFixed(4) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="heat_content" label="热含量(J)" width="140">
          <template #default="{ row }">{{ formatNumber(row.heat_content) }}</template>
        </el-table-column>
        <el-table-column prop="extractable_heat" label="可采热量(J)" width="140">
          <template #default="{ row }">{{ formatNumber(row.extractable_heat) }}</template>
        </el-table-column>
        <el-table-column prop="power_potential" label="发电潜力" width="120">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: 600;">{{ formatPower(row.power_potential) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="120">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页组件 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 结果统计 -->
    <el-row :gutter="20">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ results.length }}</div>
          <div class="stat-label">计算记录</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card success">
          <div class="stat-value">{{ formatPower(results.reduce((sum: number, r: any) => sum + (r.power_potential || 0), 0)) }}</div>
          <div class="stat-label">总发电潜力</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card info">
          <div class="stat-value">{{ formatNumber(results.reduce((sum: number, r: any) => sum + (r.extractable_heat || 0), 0)) }}</div>
          <div class="stat-label">总可采热量</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card success">
          <div class="stat-value">{{ formatVolume(results.reduce((sum: number, r: any) => sum + (r.volume || 0), 0)) }}</div>
          <div class="stat-label">总储层体积</div>
        </div>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>发电潜力折线图</span>
          <el-tag v-if="selectedChartData.length > 0" type="primary">
            已选择 {{ selectedChartData.length }} 条数据
          </el-tag>
        </div>
      </template>
      <div class="chart-container">
        <v-chart 
          :option="chartOption" 
          autoresize 
          style="height: 400px; width: 100%;"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="dialogVisible" title="计算结果详情" width="900px" @close="selectedResult = null">
      <el-descriptions :column="2" border v-if="selectedResult">
        <el-descriptions-item label="名称">{{ selectedResult.name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDate(selectedResult.created_at)}}</el-descriptions-item>
        <el-descriptions-item label="储层体积">{{ formatVolume(selectedResult.volume) }}</el-descriptions-item>
        <el-descriptions-item label="平均温度">{{ selectedResult.temperature_avg }} °C</el-descriptions-item>
        <el-descriptions-item label="热含量">{{ formatNumber(selectedResult.heat_content) }}</el-descriptions-item>
        <el-descriptions-item label="可采热量">{{ formatNumber(selectedResult.extractable_heat) }}</el-descriptions-item>
        <el-descriptions-item label="发电潜力" :span="2">
          <el-tag type="success" size="large">{{ formatPower(selectedResult.power_potential) }}</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <!-- 网格数据表格 -->
      <div v-if="selectedResult?.grids?.length" style="margin-top: 20px;">
        <h4>网格数据 ({{ selectedResult.grids.length }} 个)</h4>
        <el-table :data="selectedResult.grids" size="small" max-height="300" border stripe>
          <el-table-column type="index" label="编号" width="60" />
          <el-table-column prop="porosity" label="孔隙度" width="100">
            <template #default="{ row }">{{ row.porosity?.toFixed(4) }}</template>
          </el-table-column>
          <el-table-column prop="volume" label="体积(m³)" width="120">
            <template #default="{ row }">{{ row.volume?.toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="temperature" label="温度(°C)" width="100" />
          <el-table-column prop="pressure" label="压力(MPa)" width="100" />
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.stat-card {
  text-align: center;
  padding: 24px;
  border-radius: 8px;
  color: #fff;
  margin-top: 20px;
}

.btn-group {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.chart-card {
  margin-top: 20px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  min-height: 400px;
}
</style>
