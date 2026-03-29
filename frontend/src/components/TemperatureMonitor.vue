<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { useGeothermalStore } from '@/stores/geothermal'

const store = useGeothermalStore()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

// 地温范围分类
const temperatureRanges = [
  { name: '低温 (<100°C)', min: 0, max: 100, color: '#4CAF50' },
  { name: '中低温 (100-150°C)', min: 100, max: 150, color: '#FFC107' },
  { name: '中高温 (150-200°C)', min: 150, max: 200, color: '#FF9800' },
  { name: '高温 (>200°C)', min: 200, max: 500, color: '#F44336' }
]

// 计算网格数据
const gridData = computed(() => {
  const { xMin, xMax, yMin, yMax, zMin, zMax } = store.extent
  const resolution = store.modelConfig.grid_resolution || 20
  
  // 计算网格数量
  const nx = resolution
  const ny = resolution
  const nz = Math.max(1, Math.round(resolution * Math.abs(zMin - zMax) / Math.max(xMax - xMin, yMax - yMin)))
  
  // 每个网格单元的体积
  const dx = (xMax - xMin) / nx
  const dy = (yMax - yMin) / ny
  const dz = Math.abs(zMin - zMax) / nz
  const cellVolume = dx * dy * dz
  
  // 总网格数和总体积
  const totalCells = nx * ny * nz
  const totalVolume = (xMax - xMin) * (yMax - yMin) * Math.abs(zMin - zMax)
  
  // 模拟不同温度范围的网格分布（基于钻孔温度数据）
  const holes = store.drillHoles
  const tempCounts = [0, 0, 0, 0]
  
  if (holes.length > 0) {
    // 根据钻孔温度分布计算网格
    holes.forEach((hole: any) => {
      const temp = hole.temperature || 100 + Math.random() * 100
      if (temp < 100) tempCounts[0]++
      else if (temp < 150) tempCounts[1]++
      else if (temp < 200) tempCounts[2]++
      else tempCounts[3]++
    })
    
    // 按比例分配网格
    const totalHoles = tempCounts.reduce((a, b) => a + b, 0) || 1
    const distributedCells = tempCounts.map(count => Math.round(count / totalHoles * totalCells))
    
    // 确保总数正确
    const diff = totalCells - distributedCells.reduce((a, b) => a + b, 0)
    distributedCells[0] += diff
    
    return {
      nx, ny, nz,
      totalCells,
      totalVolume,
      cellVolume,
      temperatureDistribution: distributedCells.map((count, index) => ({
        name: temperatureRanges[index].name,
        value: count,
        color: temperatureRanges[index].color,
        volume: count * cellVolume
      }))
    }
  }
  
  // 默认分布（无钻孔数据时）
  const defaultDistribution = [
    Math.round(totalCells * 0.15),
    Math.round(totalCells * 0.35),
    Math.round(totalCells * 0.30),
    Math.round(totalCells * 0.20)
  ]
  const diff = totalCells - defaultDistribution.reduce((a, b) => a + b, 0)
  defaultDistribution[0] += diff
  
  return {
    nx, ny, nz,
    totalCells,
    totalVolume,
    cellVolume,
    temperatureDistribution: defaultDistribution.map((count, index) => ({
      name: temperatureRanges[index].name,
      value: count,
      color: temperatureRanges[index].color,
      volume: count * cellVolume
    }))
  }
})

// 计算资源量（简化估算）
const resourceData = computed(() => {
  const data = gridData.value
  
  // 每个温度范围的资源量估算（简化公式：体积 * 温度系数 * 孔隙度）
  const porosity = 0.15 // 平均孔隙度
  const waterDensity = 1000 // kg/m³
  const specificHeat = 4186 // J/(kg·K)
  const refTemp = 25 // 参考温度
  
  const resources = data.temperatureDistribution.map((item, index) => {
    // 平均温度估算
    let avgTemp = 75 // 低温
    if (index === 1) avgTemp = 125
    if (index === 2) avgTemp = 175
    if (index === 3) avgTemp = 250
    
    const deltaT = avgTemp - refTemp
    const waterVolume = item.volume * porosity
    const waterMass = waterVolume * waterDensity
    const heatContent = waterMass * specificHeat * deltaT // 焦耳
    
    return {
      ...item,
      avgTemp,
      heatContent,
      heatContentEJ: heatContent / 1e18
    }
  })
  
  const totalHeat = resources.reduce((sum, r) => sum + r.heatContent, 0)
  
  return {
    byTemperature: resources,
    totalHeat,
    totalHeatEJ: totalHeat / 1e18
  }
})

// 格式化数字
const formatNumber = (num: number, decimals: number = 2): string => {
  if (num >= 1e9) return (num / 1e9).toFixed(decimals) + ' × 10⁹'
  if (num >= 1e6) return (num / 1e6).toFixed(decimals) + ' × 10⁶'
  if (num >= 1e3) return (num / 1e3).toFixed(decimals) + ' × 10³'
  return num.toFixed(decimals)
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  updateChart()
}

// 更新图表
const updateChart = () => {
  if (!chart) return
  
  const data = gridData.value.temperatureDistribution
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const item = data[params.dataIndex]
        return `
          <div style="font-weight:600;margin-bottom:4px">${params.name}</div>
          <div>网格数量: ${formatNumber(item.value, 0)} 个</div>
          <div>体积: ${formatNumber(item.volume)} m³</div>
          <div>占比: ${params.percent}%</div>
        `
      }
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: {
        color: '#606266',
        fontSize: 13
      }
    },
    series: [
      {
        name: '地温分布',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{c}格',
          fontSize: 12,
          color: '#606266'
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 10
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold'
          },
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)'
          }
        },
        data: data.map(item => ({
          name: item.name,
          value: item.value,
          itemStyle: { color: item.color }
        }))
      }
    ]
  }
  
  chart.setOption(option)
}

// 处理窗口大小变化
const handleResize = () => {
  chart?.resize()
}

// 监听数据变化
watch(() => [store.extent, store.modelConfig.grid_resolution, store.drillHoles], () => {
  updateChart()
}, { deep: true })

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})
</script>

<template>
  <div class="monitor-panel">
    <h3 class="panel-title">🌡️ 地温网格监控</h3>
    
    <div class="monitor-content">
      <!-- 饼图区域 -->
      <div class="chart-container" ref="chartRef"></div>
      
      <!-- 统计信息 -->
      <div class="stats-container">
        <!-- 总体统计 -->
        <div class="stat-group">
          <h4>📊 总体统计</h4>
          <div class="stat-item">
            <span class="stat-label">总网格数</span>
            <span class="stat-value">{{ formatNumber(gridData.totalCells, 0) }} 个</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">总体积</span>
            <span class="stat-value">{{ formatNumber(gridData.totalVolume) }} m³</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">单格体积</span>
            <span class="stat-value">{{ formatNumber(gridData.cellVolume) }} m³</span>
          </div>
        </div>
        
        <!-- 资源量统计 -->
        <div class="stat-group highlight">
          <h4>⚡ 总资源量</h4>
          <div class="stat-item big">
            <span class="stat-value">{{ resourceData.totalHeatEJ.toFixed(2) }}</span>
            <span class="stat-unit">EJ</span>
          </div>
          <p class="stat-desc">（艾焦耳 = 10¹⁸焦耳）</p>
        </div>
        
        <!-- 各温度范围资源 -->
        <div class="stat-group">
          <h4>🌡️ 分类资源量</h4>
          <div 
            v-for="(item, index) in resourceData.byTemperature" 
            :key="index"
            class="resource-item"
            :style="{ borderLeftColor: item.color }"
          >
            <div class="resource-header">
              <span class="dot" :style="{ background: item.color }"></span>
              <span class="resource-name">{{ item.name }}</span>
            </div>
            <div class="resource-stats">
              <span>{{ formatNumber(item.value, 0) }} 格</span>
              <span>{{ item.heatContentEJ.toFixed(3) }} EJ</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 图例说明 -->
    <div class="legend-section">
      <img src="/temperature-legend.png" alt="温度分类图例" class="legend-image" />
    </div>
  </div>
</template>

<style scoped>
.monitor-panel {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.panel-title {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.monitor-content {
  display: flex;
  gap: 24px;
}

.chart-container {
  width: 350px;
  height: 300px;
  flex-shrink: 0;
}

.stats-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stat-group {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 12px 16px;
}

.stat-group.highlight {
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  color: #fff;
}

.stat-group.highlight h4 {
  color: rgba(255, 255, 255, 0.9);
}

.stat-group h4 {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 10px;
  color: #606266;
}

.stat-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
}

.stat-item.big {
  justify-content: center;
  gap: 8px;
  padding: 12px 0;
}

.stat-item.big .stat-value {
  font-size: 32px;
  font-weight: 700;
}

.stat-label {
  color: #909399;
  font-size: 13px;
}

.stat-value {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}

.stat-group.highlight .stat-value,
.stat-group.highlight .stat-unit,
.stat-group.highlight .stat-desc {
  color: #fff;
}

.stat-unit {
  font-size: 16px;
  font-weight: 500;
}

.stat-desc {
  text-align: center;
  font-size: 12px;
  opacity: 0.8;
  margin: 0;
}

.resource-item {
  background: #fff;
  border-radius: 6px;
  padding: 10px 12px;
  margin-bottom: 8px;
  border-left: 4px solid;
}

.resource-item:last-child {
  margin-bottom: 0;
}

.resource-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.resource-name {
  font-size: 13px;
  font-weight: 500;
  color: #303133;
}

.resource-stats {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #909399;
}

.legend-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
  text-align: center;
}

.legend-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
</style>
