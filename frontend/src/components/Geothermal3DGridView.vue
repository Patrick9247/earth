<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch, nextTick } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

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
  gridResolution?: number
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
  }),
  gridResolution: 20
})

// Three.js 相关变量
const containerRef = ref<HTMLDivElement | null>(null)
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let gridGroup: THREE.Group
let animationId: number

// 显示控制
const showGridLines = ref(true)
const showGridCells = ref(true)
const showAxes = ref(true)

// 计算网格信息
const gridInfo = computed(() => {
  const { xMin, xMax, yMin, yMax, zMin, zMax } = props.extent
  const res = props.gridResolution
  
  // 计算每个方向的网格数量
  const nx = res
  const ny = res
  const nz = Math.max(1, Math.round(res * Math.abs(zMax - zMin) / Math.max(xMax - xMin, yMax - yMin)))
  
  // 计算每个网格单元的尺寸
  const dx = (xMax - xMin) / nx
  const dy = (yMax - yMin) / ny
  const dz = (zMax - zMin) / nz
  
  // 每个网格单元的体积（立方米）
  const cellVolume = dx * dy * Math.abs(dz)
  
  // 总网格数量
  const totalCells = nx * ny * nz
  
  // 总体积
  const totalVolume = (xMax - xMin) * (yMax - yMin) * Math.abs(zMin - zMax)
  
  return {
    nx, ny, nz,
    dx, dy, dz,
    cellVolume,
    totalCells,
    totalVolume,
    xMin, xMax,
    yMin, yMax,
    zMin, zMax
  }
})

// 格式化数字
const formatNumber = (num: number, decimals: number = 2): string => {
  if (num >= 1e9) return (num / 1e9).toFixed(decimals) + ' × 10⁹'
  if (num >= 1e6) return (num / 1e6).toFixed(decimals) + ' × 10⁶'
  if (num >= 1e3) return (num / 1e3).toFixed(decimals) + ' × 10³'
  return num.toFixed(decimals)
}

// 计算地层分界面
const layerInterfaces = computed(() => {
  if (props.layers.length === 0) {
    return [
      { name: '地表', depth: 0, color: '#4CAF50' },
      { name: '储层顶', depth: -500, color: '#FFC107' },
      { name: '储层底', depth: -1200, color: '#FF9800' },
      { name: '基底', depth: -2000, color: '#E91E63' }
    ]
  }
  
  return props.layers.map((layer: any) => ({
    name: layer.name,
    depth: layer.depth_top,
    color: layer.color || '#409eff'
  }))
})

// 初始化 Three.js 场景
const initScene = () => {
  if (!containerRef.value) return
  
  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight || 600
  
  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)
  
  // 创建相机
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 10000)
  camera.position.set(1500, 1500, 1500)
  camera.lookAt(0, 0, -500)
  
  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.appendChild(renderer.domElement)
  
  // 创建控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.target.set(0, 0, -500)
  
  // 创建网格组
  gridGroup = new THREE.Group()
  scene.add(gridGroup)
  
  // 添加环境光
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)
  
  // 添加方向光
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(1000, 1000, 1000)
  scene.add(directionalLight)
  
  // 绘制网格
  drawGrid()
  
  // 添加坐标轴
  if (showAxes.value) {
    addAxes()
  }
  
  // 开始动画循环
  animate()
}

// 绘制三维网格
const drawGrid = () => {
  // 清除现有网格
  while (gridGroup.children.length > 0) {
    const child = gridGroup.children[0]
    gridGroup.remove(child)
    if (child instanceof THREE.Mesh) {
      child.geometry.dispose()
      if (Array.isArray(child.material)) {
        child.material.forEach(m => m.dispose())
      } else {
        child.material.dispose()
      }
    } else if (child instanceof THREE.Line) {
      child.geometry.dispose()
      if (Array.isArray(child.material)) {
        child.material.forEach(m => m.dispose())
      } else {
        child.material.dispose()
      }
    }
  }
  
  const { nx, ny, nz, dx, dy, dz } = gridInfo.value
  
  // 绘制网格线
  if (showGridLines.value) {
    const lineMaterial = new THREE.LineBasicMaterial({ 
      color: 0x409eff, 
      transparent: true, 
      opacity: 0.3 
    })
    
    // X 方向网格线
    for (let i = 0; i <= nx; i++) {
      for (let j = 0; j <= ny; j++) {
        const points = [
          new THREE.Vector3(i * dx, j * dy, 0),
          new THREE.Vector3(i * dx, j * dy, nz * dz)
        ]
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        const line = new THREE.Line(geometry, lineMaterial)
        gridGroup.add(line)
      }
    }
    
    // Y 方向网格线
    for (let i = 0; i <= nx; i++) {
      for (let k = 0; k <= nz; k++) {
        const points = [
          new THREE.Vector3(i * dx, 0, k * dz),
          new THREE.Vector3(i * dx, ny * dy, k * dz)
        ]
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        const line = new THREE.Line(geometry, lineMaterial)
        gridGroup.add(line)
      }
    }
    
    // Z 方向网格线
    for (let j = 0; j <= ny; j++) {
      for (let k = 0; k <= nz; k++) {
        const points = [
          new THREE.Vector3(0, j * dy, k * dz),
          new THREE.Vector3(nx * dx, j * dy, k * dz)
        ]
        const geometry = new THREE.BufferGeometry().setFromPoints(points)
        const line = new THREE.Line(geometry, lineMaterial)
        gridGroup.add(line)
      }
    }
  }
  
  // 绘制地层分界面（半透明平面）
  layerInterfaces.value.forEach((layer: any) => {
    const z = layer.depth
    const color = new THREE.Color(layer.color)
    
    const geometry = new THREE.PlaneGeometry(nx * dx, ny * dy)
    const material = new THREE.MeshBasicMaterial({
      color: color,
      transparent: true,
      opacity: 0.3,
      side: THREE.DoubleSide
    })
    const plane = new THREE.Mesh(geometry, material)
    plane.rotation.x = -Math.PI / 2
    plane.position.set(nx * dx / 2, ny * dy / 2, z)
    gridGroup.add(plane)
    
    // 地层分界面边框
    const edges = new THREE.EdgesGeometry(geometry)
    const edgeMaterial = new THREE.LineBasicMaterial({ color: color, linewidth: 2 })
    const edgeLine = new THREE.LineSegments(edges, edgeMaterial)
    edgeLine.rotation.x = -Math.PI / 2
    edgeLine.position.set(nx * dx / 2, ny * dy / 2, z)
    gridGroup.add(edgeLine)
  })
  
  // 绘制网格单元（仅绘制边界框）
  if (showGridCells.value) {
    // 只绘制外边界框
    const boxGeometry = new THREE.BoxGeometry(nx * dx, ny * dy, nz * Math.abs(dz))
    const edges = new THREE.EdgesGeometry(boxGeometry)
    const edgeMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 2 })
    const edgeLine = new THREE.LineSegments(edges, edgeMaterial)
    edgeLine.position.set(nx * dx / 2, ny * dy / 2, nz * dz / 2)
    gridGroup.add(edgeLine)
  }
  
  // 绘制钻孔
  drawDrillHoles()
}

// 绘制钻孔
const drawDrillHoles = () => {
  if (props.drillHoles.length === 0) return
  
  const { xMin, yMin } = gridInfo.value
  
  props.drillHoles.forEach((hole: any) => {
    const x = (hole.location_x - xMin)
    const y = (hole.location_y - yMin)
    const depth = hole.total_depth || hole.depth || 500
    
    // 钻孔线
    const points = [
      new THREE.Vector3(x, y, 0),
      new THREE.Vector3(x, y, -depth)
    ]
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({ color: 0xffffff, linewidth: 3 })
    const line = new THREE.Line(geometry, material)
    gridGroup.add(line)
    
    // 钻孔顶部标记
    const sphereGeometry = new THREE.SphereGeometry(15, 16, 16)
    const color = getTemperatureColor(hole.temperature || 100)
    const sphereMaterial = new THREE.MeshBasicMaterial({ color })
    const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial)
    sphere.position.set(x, y, 0)
    gridGroup.add(sphere)
  })
}

// 获取温度颜色
const getTemperatureColor = (temp: number): number => {
  if (temp < 100) return 0x4CAF50
  if (temp < 150) return 0xFFC107
  if (temp < 200) return 0xFF9800
  return 0xF44336
}

// 添加坐标轴
const addAxes = () => {
  const { nx, ny, nz, dx, dy, dz } = gridInfo.value
  
  // X 轴（红色）
  const xAxisPoints = [
    new THREE.Vector3(-100, 0, 0),
    new THREE.Vector3(nx * dx + 100, 0, 0)
  ]
  const xAxisGeometry = new THREE.BufferGeometry().setFromPoints(xAxisPoints)
  const xAxisMaterial = new THREE.LineBasicMaterial({ color: 0xff0000, linewidth: 2 })
  const xAxis = new THREE.Line(xAxisGeometry, xAxisMaterial)
  scene.add(xAxis)
  
  // Y 轴（绿色）
  const yAxisPoints = [
    new THREE.Vector3(0, -100, 0),
    new THREE.Vector3(0, ny * dy + 100, 0)
  ]
  const yAxisGeometry = new THREE.BufferGeometry().setFromPoints(yAxisPoints)
  const yAxisMaterial = new THREE.LineBasicMaterial({ color: 0x00ff00, linewidth: 2 })
  const yAxis = new THREE.Line(yAxisGeometry, yAxisMaterial)
  scene.add(yAxis)
  
  // Z 轴（蓝色）
  const zAxisPoints = [
    new THREE.Vector3(0, 0, 100),
    new THREE.Vector3(0, 0, nz * dz - 100)
  ]
  const zAxisGeometry = new THREE.BufferGeometry().setFromPoints(zAxisPoints)
  const zAxisMaterial = new THREE.LineBasicMaterial({ color: 0x0000ff, linewidth: 2 })
  const zAxis = new THREE.Line(zAxisGeometry, zAxisMaterial)
  scene.add(zAxis)
}

// 动画循环
const animate = () => {
  animationId = requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

// 重置视图
const resetView = () => {
  camera.position.set(1500, 1500, 1500)
  camera.lookAt(0, 0, -500)
  controls.target.set(0, 0, -500)
  controls.update()
}

// 切换网格线显示
const toggleGridLines = (val: boolean) => {
  showGridLines.value = val
  drawGrid()
}

// 切换网格单元显示
const toggleGridCells = (val: boolean) => {
  showGridCells.value = val
  drawGrid()
}

// 处理窗口大小变化
const handleResize = () => {
  if (!containerRef.value) return
  
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight || 600
  
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// 生命周期
onMounted(() => {
  nextTick(() => {
    initScene()
    window.addEventListener('resize', handleResize)
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
  if (controls) {
    controls.dispose()
  }
})

// 监听数据变化
watch(() => [props.layers, props.drillHoles, props.extent, props.gridResolution], () => {
  if (scene && gridGroup) {
    drawGrid()
  }
}, { deep: true })

watch(showAxes, (val) => {
  // 移除旧的坐标轴
  scene.children
    .filter(child => child instanceof THREE.Line && 
            (child as THREE.Line).material instanceof THREE.LineBasicMaterial &&
            ['0xff0000', '0x00ff00', '0x0000ff'].includes(
              ((child as THREE.Line).material as THREE.LineBasicMaterial).color.getHex().toString()
            ))
    .forEach(child => scene.remove(child))
  
  if (val) {
    addAxes()
  }
})

defineExpose({ resetView, toggleGridLines, toggleGridCells })
</script>

<template>
  <div class="grid-viewer">
    <!-- 控制面板 -->
    <div class="control-panel">
      <div class="control-group">
        <el-checkbox v-model="showGridLines" @change="toggleGridLines">显示网格线</el-checkbox>
        <el-checkbox v-model="showGridCells" @change="toggleGridCells">显示边界框</el-checkbox>
        <el-checkbox v-model="showAxes">显示坐标轴</el-checkbox>
      </div>
      
      <el-button size="small" @click="resetView">
        <el-icon><Refresh /></el-icon>
        重置视图
      </el-button>
    </div>
    
    <!-- 网格信息面板 -->
    <div class="info-panel">
      <div class="info-title">📊 三维网格信息</div>
      <div class="info-grid">
        <div class="info-item">
          <span class="label">网格分辨率:</span>
          <span class="value">{{ gridInfo.nx }} × {{ gridInfo.ny }} × {{ gridInfo.nz }}</span>
        </div>
        <div class="info-item">
          <span class="label">网格单元尺寸:</span>
          <span class="value">{{ gridInfo.dx.toFixed(1) }} × {{ gridInfo.dy.toFixed(1) }} × {{ Math.abs(gridInfo.dz).toFixed(1) }} m</span>
        </div>
        <div class="info-item highlight">
          <span class="label">每格平均体积:</span>
          <span class="value">{{ formatNumber(gridInfo.cellVolume) }} m³</span>
        </div>
        <div class="info-item">
          <span class="label">总网格数量:</span>
          <span class="value">{{ formatNumber(gridInfo.totalCells, 0) }} 个</span>
        </div>
        <div class="info-item">
          <span class="label">总体积:</span>
          <span class="value">{{ formatNumber(gridInfo.totalVolume) }} m³</span>
        </div>
        <div class="info-item">
          <span class="label">建模范围 X:</span>
          <span class="value">{{ gridInfo.xMin }} ~ {{ gridInfo.xMax }} m</span>
        </div>
        <div class="info-item">
          <span class="label">建模范围 Y:</span>
          <span class="value">{{ gridInfo.yMin }} ~ {{ gridInfo.yMax }} m</span>
        </div>
        <div class="info-item">
          <span class="label">建模范围 Z:</span>
          <span class="value">{{ gridInfo.zMin }} ~ {{ gridInfo.zMax }} m</span>
        </div>
      </div>
    </div>
    
    <!-- Three.js 容器 -->
    <div class="canvas-container" ref="containerRef"></div>
    
    <!-- 地层图例 -->
    <div class="legend-panel">
      <div class="legend-title">地层分界面</div>
      <div class="legend-items">
        <div class="legend-item" v-for="layer in layerInterfaces" :key="layer.name">
          <span class="color-box" :style="{ background: layer.color }"></span>
          <span class="layer-name">{{ layer.name }}</span>
          <span class="layer-depth">{{ layer.depth }}m</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.grid-viewer {
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
}

.control-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  flex-wrap: wrap;
  gap: 16px;
}

.control-group {
  display: flex;
  gap: 20px;
}

.control-group :deep(.el-checkbox__label) {
  color: #cccccc;
}

.info-panel {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.info-title {
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
}

.info-item.highlight {
  background: rgba(64, 158, 255, 0.2);
  border: 1px solid rgba(64, 158, 255, 0.5);
}

.info-item .label {
  color: #aaaaaa;
  font-size: 13px;
}

.info-item .value {
  color: #ffffff;
  font-size: 14px;
  font-weight: 500;
}

.info-item.highlight .value {
  color: #409eff;
  font-size: 16px;
}

.canvas-container {
  width: 100%;
  height: 500px;
  min-height: 500px;
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
