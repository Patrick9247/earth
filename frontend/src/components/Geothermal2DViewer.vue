<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'

interface Props {
  layers?: any[]
  drillHoles?: any[]
  extent?: {
    xMin: number
    xMax: number
    yMin: number
    yMax: number
    zMin: number
    zMax: number
  }
}

const props = withDefaults(defineProps<Props>(), {
  layers: () => [],
  drillHoles: () => [],
  extent: () => ({
    xMin: 0,
    xMax: 1000,
    yMin: 0,
    yMax: 1000,
    zMin: -2000,
    zMax: 0
  })
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
const ctx = ref<CanvasRenderingContext2D | null>(null)

// 剖面位置控制
const sectionType = ref<'x' | 'y'>('x')  // X剖面 或 Y剖面
const sectionPosition = ref(500)  // 剖面位置
const showDrillHoles = ref(true)

// 计算数据
const computedLayers = computed(() => {
  if (props.layers.length > 0) return props.layers
  return [
    { name: '地表', depth_top: 0, depth_bottom: 100, color: '#4CAF50' },
    { name: '沉积层', depth_top: 100, depth_bottom: 500, color: '#FFC107' },
    { name: '储层', depth_top: 500, depth_bottom: 1200, color: '#FF9800' },
    { name: '基底', depth_top: 1200, depth_bottom: 2000, color: '#E91E63' }
  ]
})

const computedDrillHoles = computed(() => {
  if (props.drillHoles.length > 0) return props.drillHoles
  return [
    { name: 'ZK-001', location_x: 200, location_y: 300, depth: 800, temperature: 120 },
    { name: 'ZK-002', location_x: 500, location_y: 600, depth: 1200, temperature: 160 },
    { name: 'ZK-003', location_x: 800, location_y: 400, depth: 600, temperature: 95 },
    { name: 'ZK-004', location_x: 350, location_y: 700, depth: 1000, temperature: 140 },
    { name: 'ZK-005', location_x: 650, location_y: 200, depth: 900, temperature: 135 }
  ]
})

// 绘制剖面图
const draw = () => {
  if (!canvasRef.value || !ctx.value) return
  
  const canvas = canvasRef.value
  const context = ctx.value
  
  // 清空画布
  context.clearRect(0, 0, canvas.width, canvas.height)
  
  const padding = { top: 60, right: 60, bottom: 80, left: 80 }
  const width = canvas.width - padding.left - padding.right
  const height = canvas.height - padding.top - padding.bottom
  
  const { xMin, xMax, yMin, yMax, zMin } = props.extent
  const maxDepth = Math.abs(zMin)
  
  // 坐标转换函数
  const toX = (val: number) => padding.left + ((val - (sectionType.value === 'x' ? xMin : yMin)) / (sectionType.value === 'x' ? (xMax - xMin) : (yMax - yMin))) * width
  const toY = (depth: number) => padding.top + (depth / maxDepth) * height
  
  // 绘制背景
  context.fillStyle = '#1a1a2e'
  context.fillRect(0, 0, canvas.width, canvas.height)
  
  // 绘制地层
  computedLayers.value.forEach((layer: any) => {
    const topDepth = Math.abs(layer.depth_top ?? 0)
    const bottomDepth = Math.abs(layer.depth_bottom ?? 500)
    
    // 地层矩形
    context.fillStyle = layer.color || '#409eff'
    context.globalAlpha = 0.7
    context.fillRect(padding.left, toY(topDepth), width, toY(bottomDepth) - toY(topDepth))
    context.globalAlpha = 1
    
    // 地层边界
    context.strokeStyle = '#ffffff'
    context.lineWidth = 1
    context.strokeRect(padding.left, toY(topDepth), width, toY(bottomDepth) - toY(topDepth))
    
    // 地层名称标签
    context.fillStyle = '#ffffff'
    context.font = 'bold 14px Arial'
    context.textAlign = 'center'
    const labelY = (toY(topDepth) + toY(bottomDepth)) / 2
    context.fillText(layer.name, padding.left + width / 2, labelY + 5)
  })
  
  // 绘制钻孔（如果开启且在剖面线上）
  if (showDrillHoles.value) {
    computedDrillHoles.value.forEach((hole: any) => {
      const pos = sectionType.value === 'x' ? hole.location_x : hole.location_y
      const otherPos = sectionType.value === 'x' ? hole.location_y : hole.location_x
      
      // 检查钻孔是否在剖面附近（±50m）
      if (Math.abs(pos - sectionPosition.value) < 100) {
        const x = toX(otherPos)
        const depth = hole.depth || 500
        
        // 钻孔线
        context.strokeStyle = '#ffffff'
        context.lineWidth = 3
        context.beginPath()
        context.moveTo(x, toY(0))
        context.lineTo(x, toY(depth))
        context.stroke()
        
        // 钻孔顶部标记
        context.fillStyle = getTemperatureColor(hole.temperature)
        context.beginPath()
        context.arc(x, toY(0), 8, 0, Math.PI * 2)
        context.fill()
        
        // 钻孔标签
        context.fillStyle = '#ffffff'
        context.font = '12px Arial'
        context.textAlign = 'center'
        context.fillText(hole.name, x, toY(0) - 15)
        context.fillText(`${hole.temperature}°C`, x, toY(depth) + 15)
      }
    })
  }
  
  // 绘制坐标轴
  drawAxes(context, padding, width, height, maxDepth)
  
  // 绘制剖面线指示
  context.fillStyle = '#ffffff'
  context.font = 'bold 16px Arial'
  context.textAlign = 'center'
  context.fillText(
    `${sectionType.value === 'x' ? 'X' : 'Y'} = ${sectionPosition.value}m 剖面`,
    canvas.width / 2,
    30
  )
}

// 绘制坐标轴
const drawAxes = (context: CanvasRenderingContext2D, padding: any, width: number, height: number, maxDepth: number) => {
  const { xMin, xMax, yMin, yMax } = props.extent
  
  context.strokeStyle = '#666666'
  context.lineWidth = 1
  context.fillStyle = '#aaaaaa'
  context.font = '12px Arial'
  
  // Y轴（深度）
  context.beginPath()
  context.moveTo(padding.left, padding.top)
  context.lineTo(padding.left, padding.top + height)
  context.stroke()
  
  // Y轴刻度
  for (let d = 0; d <= maxDepth; d += 200) {
    const y = padding.top + (d / maxDepth) * height
    context.beginPath()
    context.moveTo(padding.left - 5, y)
    context.lineTo(padding.left, y)
    context.stroke()
    context.textAlign = 'right'
    context.fillText(`${d}m`, padding.left - 10, y + 4)
  }
  
  // X轴
  const xRange = sectionType.value === 'x' ? (yMax - yMin) : (xMax - xMin)
  const xStart = sectionType.value === 'x' ? yMin : xMin
  
  context.beginPath()
  context.moveTo(padding.left, padding.top + height)
  context.lineTo(padding.left + width, padding.top + height)
  context.stroke()
  
  // X轴刻度
  for (let i = 0; i <= 5; i++) {
    const val = xStart + (xRange * i / 5)
    const x = padding.left + (width * i / 5)
    context.beginPath()
    context.moveTo(x, padding.top + height)
    context.lineTo(x, padding.top + height + 5)
    context.stroke()
    context.textAlign = 'center'
    context.fillText(`${Math.round(val)}m`, x, padding.top + height + 20)
  }
  
  // 轴标签
  context.fillStyle = '#ffffff'
  context.font = 'bold 14px Arial'
  context.textAlign = 'center'
  context.fillText(
    sectionType.value === 'x' ? 'Y方向 (m)' : 'X方向 (m)',
    padding.left + width / 2,
    padding.top + height + 50
  )
  
  // Y轴标签（深度）
  context.save()
  context.translate(25, padding.top + height / 2)
  context.rotate(-Math.PI / 2)
  context.fillText('深度 (m)', 0, 0)
  context.restore()
}

// 获取温度颜色
const getTemperatureColor = (temp: number): string => {
  if (temp < 100) return '#4CAF50'
  if (temp < 150) return '#FFC107'
  if (temp < 200) return '#FF9800'
  return '#F44336'
}

// 剖面位置范围
const positionMin = computed(() => sectionType.value === 'x' ? props.extent.xMin : props.extent.yMin)
const positionMax = computed(() => sectionType.value === 'x' ? props.extent.xMax : props.extent.yMax)

// 切换剖面类型
const handleSectionTypeChange = () => {
  sectionPosition.value = (positionMin.value + positionMax.value) / 2
  draw()
}

// 导出图片
const exportImage = () => {
  if (!canvasRef.value) return
  const link = document.createElement('a')
  link.download = `地质剖面_${sectionType.value}=${sectionPosition.value}.png`
  link.href = canvasRef.value.toDataURL('image/png')
  link.click()
}

// 初始化
onMounted(() => {
  if (canvasRef.value) {
    const canvas = canvasRef.value
    // 设置画布大小
    canvas.width = canvas.parentElement?.clientWidth || 800
    canvas.height = 500
    ctx.value = canvas.getContext('2d')
    draw()
  }
  
  window.addEventListener('resize', () => {
    if (canvasRef.value) {
      canvasRef.value.width = canvasRef.value.parentElement?.clientWidth || 800
      draw()
    }
  })
})

// 监听数据变化
watch(() => [props.layers, props.drillHoles, props.extent], draw, { deep: true })
watch(sectionPosition, draw)
watch(showDrillHoles, draw)

defineExpose({ exportImage })
</script>

<template>
  <div class="viewer-2d">
    <!-- 控制面板 -->
    <div class="control-panel">
      <div class="control-group">
        <label>剖面方向：</label>
        <el-radio-group v-model="sectionType" @change="handleSectionTypeChange">
          <el-radio-button value="x">X 剖面</el-radio-button>
          <el-radio-button value="y">Y 剖面</el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="control-group">
        <label>剖面位置：</label>
        <el-slider
          v-model="sectionPosition"
          :min="positionMin"
          :max="positionMax"
          :step="10"
          show-input
          style="width: 300px;"
        />
      </div>
      
      <div class="control-group">
        <el-checkbox v-model="showDrillHoles">显示钻孔</el-checkbox>
      </div>
      
      <el-button type="primary" size="small" @click="exportImage">
        <el-icon><Download /></el-icon>
        导出图片
      </el-button>
    </div>
    
    <!-- 画布容器 -->
    <div class="canvas-container">
      <canvas ref="canvasRef"></canvas>
    </div>
    
    <!-- 图例 -->
    <div class="legend-panel">
      <div class="legend-title">地质层图例</div>
      <div class="legend-items">
        <div class="legend-item" v-for="layer in computedLayers" :key="layer.name">
          <span class="color-box" :style="{ background: layer.color }"></span>
          <span class="layer-name">{{ layer.name }}</span>
          <span class="layer-depth">{{ layer.depth_top }}-{{ layer.depth_bottom }}m</span>
        </div>
      </div>
      <div class="legend-title" style="margin-top: 12px;">温度图例</div>
      <div class="legend-items">
        <div class="legend-item"><span class="color-box" style="background:#4CAF50"></span><span>&lt;100°C</span></div>
        <div class="legend-item"><span class="color-box" style="background:#FFC107"></span><span>100-150°C</span></div>
        <div class="legend-item"><span class="color-box" style="background:#FF9800"></span><span>150-200°C</span></div>
        <div class="legend-item"><span class="color-box" style="background:#F44336"></span><span>&gt;200°C</span></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.viewer-2d {
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
}

.control-panel {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group label {
  color: #aaaaaa;
  font-size: 14px;
}

.canvas-container {
  width: 100%;
  min-height: 500px;
}

.canvas-container canvas {
  width: 100%;
  display: block;
}

.legend-panel {
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
}

.legend-title {
  color: #ffffff;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #cccccc;
  font-size: 13px;
}

.color-box {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.layer-name {
  font-weight: 500;
  color: #ffffff;
}

.layer-depth {
  color: #888888;
  font-size: 12px;
}
</style>
