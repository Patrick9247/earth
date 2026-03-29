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
const containerRef = ref<HTMLDivElement | null>(null)

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
  if (!canvasRef.value || !containerRef.value) return
  
  const canvas = canvasRef.value
  const container = containerRef.value
  
  // 高分辨率支持
  const dpr = window.devicePixelRatio || 1
  const displayWidth = container.clientWidth
  const displayHeight = 600
  
  // 设置 canvas 实际大小（高分辨率）
  canvas.width = displayWidth * dpr
  canvas.height = displayHeight * dpr
  canvas.style.width = displayWidth + 'px'
  canvas.style.height = displayHeight + 'px'
  
  const ctx = canvas.getContext('2d')
  if (!ctx) return
  
  // 缩放上下文以匹配高分辨率
  ctx.scale(dpr, dpr)
  
  // 清空画布
  ctx.clearRect(0, 0, displayWidth, displayHeight)
  
  const padding = { top: 60, right: 100, bottom: 80, left: 60 }
  const width = displayWidth - padding.left - padding.right
  const height = displayHeight - padding.top - padding.bottom
  
  const { xMin, xMax, yMin, yMax, zMin } = props.extent
  const maxDepth = Math.abs(zMin)
  
  // 剖面方向的范围
  const horizontalMin = sectionType.value === 'x' ? yMin : xMin
  const horizontalMax = sectionType.value === 'x' ? yMax : xMax
  
  // 坐标转换函数
  const toX = (val: number) => padding.left + ((val - horizontalMin) / (horizontalMax - horizontalMin)) * width
  const toY = (depth: number) => padding.top + (depth / maxDepth) * height
  
  // 绘制背景
  ctx.fillStyle = '#1a1a2e'
  ctx.fillRect(0, 0, displayWidth, displayHeight)
  
  // 绘制地层
  computedLayers.value.forEach((layer: any, index: number) => {
    const topDepth = Math.abs(layer.depth_top ?? index * 500)
    const bottomDepth = Math.abs(layer.depth_bottom ?? (index + 1) * 500)
    
    const y1 = toY(topDepth)
    const y2 = toY(bottomDepth)
    
    // 地层矩形
    ctx.fillStyle = layer.color || '#409eff'
    ctx.globalAlpha = 0.75
    ctx.fillRect(padding.left, y1, width, y2 - y1)
    ctx.globalAlpha = 1
    
    // 地层边界
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)'
    ctx.lineWidth = 1
    ctx.strokeRect(padding.left, y1, width, y2 - y1)
    
    // 地层名称标签
    ctx.fillStyle = '#ffffff'
    ctx.font = 'bold 16px Arial'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    const labelY = (y1 + y2) / 2
    ctx.fillText(layer.name, padding.left + width / 2, labelY)
    
    // 深度标签（右侧）
    ctx.font = '12px Arial'
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'middle'
    ctx.fillText(`${topDepth}m`, padding.left + width + 12, y1)
  })
  
  // 绘制钻孔
  if (showDrillHoles.value) {
    computedDrillHoles.value.forEach((hole: any) => {
      // 钻孔在剖面方向的位置
      const sectionPos = sectionType.value === 'x' ? hole.location_x : hole.location_y
      // 钻孔在剖面横向的位置（显示在图上的位置）
      const horizontalPos = sectionType.value === 'x' ? hole.location_y : hole.location_x
      
      const x = toX(horizontalPos)
      const depth = hole.depth || 500
      
      // 判断钻孔是否在剖面线上（距离小于150m）
      const distanceToSection = Math.abs(sectionPos - sectionPosition.value)
      const isOnSection = distanceToSection < 150
      
      // 钻孔线
      ctx.strokeStyle = isOnSection ? '#ffffff' : 'rgba(255, 255, 255, 0.3)'
      ctx.lineWidth = isOnSection ? 3 : 1
      ctx.beginPath()
      ctx.moveTo(x, toY(0))
      ctx.lineTo(x, toY(depth))
      ctx.stroke()
      
      // 钻孔顶部标记
      ctx.fillStyle = getTemperatureColor(hole.temperature)
      ctx.globalAlpha = isOnSection ? 1 : 0.5
      ctx.beginPath()
      ctx.arc(x, toY(0), isOnSection ? 10 : 6, 0, Math.PI * 2)
      ctx.fill()
      ctx.globalAlpha = 1
      
      // 只显示在剖面线上的钻孔标签
      if (isOnSection) {
        // 钻孔标签背景
        ctx.fillStyle = 'rgba(0, 0, 0, 0.7)'
        ctx.fillRect(x - 35, toY(0) - 45, 70, 30)
        
        // 钻孔名称
        ctx.fillStyle = '#ffffff'
        ctx.font = 'bold 12px Arial'
        ctx.textAlign = 'center'
        ctx.fillText(hole.name, x, toY(0) - 30)
        
        // 温度标签
        ctx.fillStyle = getTemperatureColor(hole.temperature)
        ctx.font = '11px Arial'
        ctx.fillText(`${hole.temperature}°C`, x, toY(depth) + 18)
      }
    })
  }
  
  // 绘制坐标轴
  drawAxes(ctx, padding, width, height, maxDepth, horizontalMin, horizontalMax)
  
  // 绘制剖面标题
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 18px Arial'
  ctx.textAlign = 'center'
  ctx.fillText(
    `${sectionType.value === 'x' ? 'X' : 'Y'} = ${sectionPosition.value}m 地质剖面图`,
    displayWidth / 2,
    35
  )
}

// 绘制坐标轴
const drawAxes = (
  ctx: CanvasRenderingContext2D, 
  padding: any, 
  width: number, 
  height: number, 
  maxDepth: number,
  horizontalMin: number,
  horizontalMax: number
) => {
  // 坐标轴样式
  ctx.strokeStyle = '#888888'
  ctx.lineWidth = 1
  ctx.fillStyle = '#aaaaaa'
  ctx.font = '12px Arial'
  
  // Y轴（深度）- 右侧
  ctx.beginPath()
  ctx.moveTo(padding.left + width, padding.top)
  ctx.lineTo(padding.left + width, padding.top + height)
  ctx.stroke()
  
  // Y轴刻度和网格线
  for (let d = 0; d <= maxDepth; d += 200) {
    const y = padding.top + (d / maxDepth) * height
    
    // 网格线
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(padding.left + width, y)
    ctx.stroke()
    
    // 刻度线
    ctx.strokeStyle = '#666666'
    ctx.beginPath()
    ctx.moveTo(padding.left + width, y)
    ctx.lineTo(padding.left + width + 8, y)
    ctx.stroke()
    
    // 刻度值（右侧）
    ctx.fillStyle = '#aaaaaa'
    ctx.textAlign = 'left'
    ctx.textBaseline = 'middle'
    ctx.fillText(`${d}`, padding.left + width + 12, y)
  }
  
  // X轴
  ctx.beginPath()
  ctx.moveTo(padding.left, padding.top + height)
  ctx.lineTo(padding.left + width, padding.top + height)
  ctx.stroke()
  
  // X轴刻度
  const xRange = horizontalMax - horizontalMin
  for (let i = 0; i <= 5; i++) {
    const val = horizontalMin + (xRange * i / 5)
    const x = padding.left + (width * i / 5)
    
    // 网格线
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)'
    ctx.beginPath()
    ctx.moveTo(x, padding.top)
    ctx.lineTo(x, padding.top + height)
    ctx.stroke()
    
    // 刻度线
    ctx.strokeStyle = '#666666'
    ctx.beginPath()
    ctx.moveTo(x, padding.top + height)
    ctx.lineTo(x, padding.top + height + 8)
    ctx.stroke()
    
    // 刻度值
    ctx.fillStyle = '#aaaaaa'
    ctx.textAlign = 'center'
    ctx.fillText(`${Math.round(val)}`, x, padding.top + height + 22)
  }
  
  // 轴标签
  ctx.fillStyle = '#ffffff'
  ctx.font = 'bold 14px Arial'
  ctx.textAlign = 'center'
  ctx.fillText(
    sectionType.value === 'x' ? 'Y 方向 (m)' : 'X 方向 (m)',
    padding.left + width / 2,
    padding.top + height + 55
  )
  
  // Y轴标签（深度）- 右侧
  ctx.save()
  ctx.translate(padding.left + width + 70, padding.top + height / 2)
  ctx.rotate(-Math.PI / 2)
  ctx.fillText('深度 (m)', 0, 0)
  ctx.restore()
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
  sectionPosition.value = Math.round((positionMin.value + positionMax.value) / 2)
  draw()
}

// 导出图片
const exportImage = () => {
  if (!canvasRef.value) return
  const link = document.createElement('a')
  link.download = `地质剖面_${sectionType.value}=${sectionPosition.value}.png`
  link.href = canvasRef.value.toDataURL('image/png', 1.0)
  link.click()
}

// 初始化
onMounted(() => {
  draw()
  window.addEventListener('resize', draw)
})

// 清理
import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('resize', draw)
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
    <div class="canvas-container" ref="containerRef">
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
  min-height: 600px;
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
