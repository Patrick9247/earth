<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
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
  gridResolution: 10
})

const containerRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)

// 网格控制
const showGrid = ref(false)
const showGridInfo = ref(true)

// 计算网格信息
const gridInfo = computed(() => {
  const { xMin, xMax, yMin, yMax, zMin, zMax } = props.extent
  const res = props.gridResolution
  
  // 计算每个方向的网格数量
  const nx = res
  const ny = res
  const nz = Math.max(1, Math.round(res * Math.abs(zMin - zMax) / Math.max(xMax - xMin, yMax - yMin)))
  
  // 计算每个网格单元的尺寸
  const dx = (xMax - xMin) / nx
  const dy = (yMax - yMin) / ny
  const dz = (zMin - zMax) / nz  // zMin是负数，zMax是0或正数
  
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

// 计算地质层图例
const computedLayerLegend = computed(() => {
  if (props.layers.length > 0) {
    return props.layers.map((layer: any) => ({
      name: layer.name,
      color: layer.color || '#409eff',
      depthRange: `${layer.depth_top ?? 0}~${layer.depth_bottom ?? 0}m`
    }))
  }
  return [
    { name: '地表', color: '#4CAF50', depthRange: '0~100m' },
    { name: '沉积层', color: '#FFC107', depthRange: '100~500m' },
    { name: '储层', color: '#FF9800', depthRange: '500~1200m' },
    { name: '基底', color: '#E91E63', depthRange: '1200~2000m' }
  ]
})

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let animationId: number

// 存储模型对象
let layerMeshes: THREE.Mesh[] = []
let drillHoleMeshes: THREE.Object3D[] = []
let particleSystems: THREE.Points[] = []
let axesGroup: THREE.Group
let gridGroup: THREE.Group  // 三维网格组

// 默认地质层颜色
const defaultLayerColors = [
  0x4CAF50, 0xFFC107, 0xFF9800, 0xE91E63, 0x9C27B0
]

// 初始化场景
const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // 场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // 相机 - 使用等轴测视角
  camera = new THREE.PerspectiveCamera(50, width / height, 1, 10000)
  camera.position.set(1500, 1200, 1500)
  camera.lookAt(500, -500, 500)

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  containerRef.value.appendChild(renderer.domElement)

  // 控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 500
  controls.maxDistance = 5000
  controls.target.set(500, -500, 500)

  // 光源
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.5)
  scene.add(ambientLight)

  const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.8)
  dirLight1.position.set(1000, 1000, 500)
  scene.add(dirLight1)

  const dirLight2 = new THREE.DirectionalLight(0xffffff, 0.3)
  dirLight2.position.set(-500, 500, -500)
  scene.add(dirLight2)

  // 添加坐标轴
  addAxes()

  // 添加网格
  addGrid()

  animate()
  loading.value = false
}

// 添加坐标轴
const addAxes = () => {
  axesGroup = new THREE.Group()
  const axisLength = 300
  const arrowSize = 40

  // X轴 - 红色 (东向)
  const xMat = new THREE.LineBasicMaterial({ color: 0xff4444, linewidth: 2 })
  const xPoints = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(axisLength, 0, 0)]
  const xLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(xPoints), xMat)
  axesGroup.add(xLine)

  const xArrow = new THREE.Mesh(
    new THREE.ConeGeometry(10, arrowSize, 8),
    new THREE.MeshBasicMaterial({ color: 0xff4444 })
  )
  xArrow.position.set(axisLength, 0, 0)
  xArrow.rotation.z = -Math.PI / 2
  axesGroup.add(xArrow)

  // Y轴 - 蓝色 (深度，向下为正)
  const yMat = new THREE.LineBasicMaterial({ color: 0x4488ff, linewidth: 2 })
  const yPoints = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, -axisLength, 0)]
  const yLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(yPoints), yMat)
  axesGroup.add(yLine)

  const yArrow = new THREE.Mesh(
    new THREE.ConeGeometry(10, arrowSize, 8),
    new THREE.MeshBasicMaterial({ color: 0x4488ff })
  )
  yArrow.position.set(0, -axisLength, 0)
  yArrow.rotation.x = Math.PI
  axesGroup.add(yArrow)

  // Z轴 - 绿色 (北向)
  const zMat = new THREE.LineBasicMaterial({ color: 0x44ff44, linewidth: 2 })
  const zPoints = [new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, axisLength)]
  const zLine = new THREE.Line(new THREE.BufferGeometry().setFromPoints(zPoints), zMat)
  axesGroup.add(zLine)

  const zArrow = new THREE.Mesh(
    new THREE.ConeGeometry(10, arrowSize, 8),
    new THREE.MeshBasicMaterial({ color: 0x44ff44 })
  )
  zArrow.position.set(0, 0, axisLength)
  zArrow.rotation.x = Math.PI / 2
  axesGroup.add(zArrow)

  // 添加坐标轴标签（使用 Sprite）
  addTextSprite('X(西)', axisLength + 50, 0, 0, '#ff4444')
  addTextSprite('Y(深度)', 0, -axisLength - 50, 0, '#4488ff')
  addTextSprite('Z(北)', 0, 0, axisLength + 50, '#44ff44')

  scene.add(axesGroup)
}

// 添加文字精灵
const addTextSprite = (text: string, x: number, y: number, z: number, color: string) => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = 128
  canvas.height = 64

  ctx.fillStyle = 'rgba(0,0,0,0.7)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.font = 'bold 24px Arial'
  ctx.fillStyle = color
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, canvas.width / 2, canvas.height / 2)

  const texture = new THREE.CanvasTexture(canvas)
  const spriteMat = new THREE.SpriteMaterial({ map: texture })
  const sprite = new THREE.Sprite(spriteMat)
  sprite.position.set(x, y, z)
  sprite.scale.set(100, 50, 1)
  axesGroup.add(sprite)
}

// 添加网格
const addGrid = () => {
  const { xMax, zMax } = props.extent
  const size = Math.max(xMax, zMax) * 2
  
  // 水平网格 (XZ平面，在 y=0 处)
  const grid = new THREE.GridHelper(size, 10, 0x666666, 0x444444)
  grid.position.set((xMax) / 2, 0, (zMax) / 2)
  scene.add(grid)
}

// 创建三维网格
const create3DGrid = () => {
  // 移除旧网格
  if (gridGroup) {
    scene.remove(gridGroup)
    gridGroup.traverse((child) => {
      if (child instanceof THREE.Line) {
        child.geometry.dispose()
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose())
        } else {
          child.material.dispose()
        }
      }
    })
  }
  
  if (!showGrid.value) return
  
  gridGroup = new THREE.Group()
  
  const { nx, ny, nz, dx, dy, xMin, yMin, zMin, zMax, xMax, yMax } = gridInfo.value
  
  // 网格线材质
  const lineMaterial = new THREE.LineBasicMaterial({ 
    color: 0x409eff, 
    transparent: true, 
    opacity: 0.4 
  })
  
  // 计算深度范围（Y轴，向下为负）
  const depthMin = zMin  // 例如 -2000
  const depthMax = zMax  // 例如 0
  const depthRange = Math.abs(depthMin - depthMax)
  const depthStep = depthRange / nz
  
  // X 方向网格线（沿Y-Z平面，即沿深度和Z轴方向）
  for (let i = 0; i <= nx; i++) {
    for (let k = 0; k <= nz; k++) {
      const points = [
        new THREE.Vector3(xMin + i * dx, depthMax, yMin + k * dy),
        new THREE.Vector3(xMin + i * dx, depthMin, yMin + k * dy)
      ]
      const geometry = new THREE.BufferGeometry().setFromPoints(points)
      const line = new THREE.Line(geometry, lineMaterial)
      gridGroup.add(line)
    }
  }
  
  // Y 方向网格线（沿X-Z平面，即沿X轴和Z轴方向）- 深度方向
  for (let j = 0; j <= nz; j++) {
    for (let k = 0; k <= ny; k++) {
      const depthY = depthMax - j * depthStep  // 从 0 向下到 zMin
      const points = [
        new THREE.Vector3(xMin, depthY, yMin + k * dy),
        new THREE.Vector3(xMax, depthY, yMin + k * dy)
      ]
      const geometry = new THREE.BufferGeometry().setFromPoints(points)
      const line = new THREE.Line(geometry, lineMaterial)
      gridGroup.add(line)
    }
  }
  
  // Z 方向网格线（沿X-Y平面，即沿X轴和深度方向）
  for (let j = 0; j <= nz; j++) {
    for (let i = 0; i <= nx; i++) {
      const depthY = depthMax - j * depthStep
      const points = [
        new THREE.Vector3(xMin + i * dx, depthY, yMin),
        new THREE.Vector3(xMin + i * dx, depthY, yMax)
      ]
      const geometry = new THREE.BufferGeometry().setFromPoints(points)
      const line = new THREE.Line(geometry, lineMaterial)
      gridGroup.add(line)
    }
  }
  
  // 外边界框
  const boxGeometry = new THREE.BoxGeometry(xMax - xMin, depthRange, yMax - yMin)
  const edges = new THREE.EdgesGeometry(boxGeometry)
  const edgeMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8 })
  const edgeLine = new THREE.LineSegments(edges, edgeMaterial)
  edgeLine.position.set((xMin + xMax) / 2, (depthMin + depthMax) / 2, (yMin + yMax) / 2)
  gridGroup.add(edgeLine)
  
  scene.add(gridGroup)
}

// 切换三维网格显示
const toggleGrid = (visible: boolean) => {
  showGrid.value = visible
  create3DGrid()
}

// 创建地质层
const createLayers = () => {
  layerMeshes.forEach(m => scene.remove(m))
  layerMeshes = []

  const defaultLayers = [
    { name: '地表', depth_top: 0, depth_bottom: 100, color: '#4CAF50' },
    { name: '沉积层', depth_top: 100, depth_bottom: 500, color: '#FFC107' },
    { name: '储层', depth_top: 500, depth_bottom: 1200, color: '#FF9800' },
    { name: '基底', depth_top: 1200, depth_bottom: 2000, color: '#E91E63' }
  ]

  const layersToUse = props.layers.length > 0 ? props.layers : defaultLayers
  const { xMin, xMax, yMin: zMin, yMax: zMax } = props.extent

  layersToUse.forEach((layer: any, index: number) => {
    // 深度值（正数向下）
    let topDepth = layer.depth_top ?? layer.depthTop ?? index * 500
    let bottomDepth = layer.depth_bottom ?? layer.depthBottom ?? (index + 1) * 500
    
    // 确保是正数
    topDepth = Math.abs(topDepth)
    bottomDepth = Math.abs(bottomDepth)
    
    const layerHeight = bottomDepth - topDepth

    // 创建盒子几何体
    const geometry = new THREE.BoxGeometry(
      xMax - xMin,        // 宽度 (X方向)
      layerHeight,        // 高度 (Y方向，即深度)
      zMax - zMin         // 深度 (Z方向)
    )

    // 解析颜色
    let color: number
    if (layer.color && typeof layer.color === 'string') {
      color = parseInt(layer.color.replace('#', ''), 16)
      if (isNaN(color)) color = defaultLayerColors[index % defaultLayerColors.length]
    } else {
      color = defaultLayerColors[index % defaultLayerColors.length]
    }

    const material = new THREE.MeshPhongMaterial({
      color,
      transparent: true,
      opacity: 0.7,
      side: THREE.DoubleSide,
      shininess: 30
    })

    const mesh = new THREE.Mesh(geometry, material)
    
    // 位置：Y轴向下表示深度
    mesh.position.set(
      (xMin + xMax) / 2,
      -(topDepth + bottomDepth) / 2,  // Y轴负方向 = 深度
      (zMin + zMax) / 2
    )

    // 边框
    const edges = new THREE.EdgesGeometry(geometry)
    const wireframe = new THREE.LineSegments(
      edges,
      new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.6, transparent: true })
    )
    mesh.add(wireframe)

    scene.add(mesh)
    layerMeshes.push(mesh)
  })
}

// 创建钻孔
const createDrillHoles = () => {
  drillHoleMeshes.forEach(m => scene.remove(m))
  drillHoleMeshes = []

  const defaultHoles = [
    { name: 'ZK-001', location_x: 200, location_y: 300, depth: 800, temperature: 120 },
    { name: 'ZK-002', location_x: 500, location_y: 600, depth: 1200, temperature: 160 },
    { name: 'ZK-003', location_x: 800, location_y: 400, depth: 600, temperature: 95 },
    { name: 'ZK-004', location_x: 350, location_y: 700, depth: 1000, temperature: 140 },
    { name: 'ZK-005', location_x: 650, location_y: 200, depth: 900, temperature: 135 }
  ]

  const holesToUse = props.drillHoles.length > 0 ? props.drillHoles : defaultHoles

  holesToUse.forEach((hole: any) => {
    const x = hole.location_x ?? 0
    const z = hole.location_y ?? 0  // Y坐标映射到Z轴
    const depth = hole.depth ?? 500

    // 钻孔颜色（根据温度）
    const temp = hole.temperature ?? 100
    const color = temp < 100 ? 0x4CAF50 : temp < 150 ? 0xFFC107 : temp < 200 ? 0xFF9800 : 0xF44336

    // 钻孔圆柱体
    const geometry = new THREE.CylinderGeometry(12, 12, depth, 12)
    const material = new THREE.MeshPhongMaterial({ color, transparent: true, opacity: 0.85 })
    const cylinder = new THREE.Mesh(geometry, material)
    
    // 位置：Y轴负方向表示深度
    cylinder.position.set(x, -depth / 2, z)
    scene.add(cylinder)
    drillHoleMeshes.push(cylinder)

    // 顶部标记球
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(20, 12, 12),
      new THREE.MeshPhongMaterial({ color, shininess: 100 })
    )
    marker.position.set(x, 0, z)
    scene.add(marker)
    drillHoleMeshes.push(marker)

    // 标签（显示名称和坐标）
    const labelSprite = createDrillHoleLabel(hole.name ?? 'ZK', x, z)
    labelSprite.position.set(x, 50, z)
    scene.add(labelSprite)
    drillHoleMeshes.push(labelSprite)
  })
}

// 创建钻孔标签精灵（显示名称和坐标）
const createDrillHoleLabel = (name: string, x: number, z: number): THREE.Sprite => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) return new THREE.Sprite()

  canvas.width = 160
  canvas.height = 72

  // 背景
  ctx.fillStyle = 'rgba(0,0,0,0.85)'
  ctx.roundRect(0, 0, canvas.width, canvas.height, 8)
  ctx.fill()

  // 边框
  ctx.strokeStyle = 'rgba(255,255,255,0.3)'
  ctx.lineWidth = 2
  ctx.roundRect(0, 0, canvas.width, canvas.height, 8)
  ctx.stroke()

  // 名称
  ctx.font = 'bold 22px Arial'
  ctx.fillStyle = '#ffffff'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(name, canvas.width / 2, 22)

  // 坐标
  ctx.font = '16px Arial'
  ctx.fillStyle = '#88ccff'
  ctx.fillText(`X:${x}  Z:${z}`, canvas.width / 2, 50)

  const texture = new THREE.CanvasTexture(canvas)
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({ map: texture }))
  sprite.scale.set(120, 54, 1)
  return sprite
}

// 创建热流粒子
const createHeatParticles = () => {
  particleSystems.forEach(p => scene.remove(p))
  particleSystems = []

  const { xMin, xMax, yMin: zMin, yMax: zMax, zMin: yMin } = props.extent
  
  const count = 200
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)

  for (let i = 0; i < count; i++) {
    positions[i * 3] = xMin + Math.random() * (xMax - xMin)
    positions[i * 3 + 1] = yMin + Math.random() * 200  // Y轴（深度方向）
    positions[i * 3 + 2] = zMin + Math.random() * (zMax - zMin)

    colors[i * 3] = 1.0
    colors[i * 3 + 1] = 0.3 + Math.random() * 0.5
    colors[i * 3 + 2] = 0.1
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  const material = new THREE.PointsMaterial({
    size: 10,
    vertexColors: true,
    transparent: true,
    opacity: 0.7,
    sizeAttenuation: true
  })

  const particles = new THREE.Points(geometry, material)
  scene.add(particles)
  particleSystems.push(particles)
}

// 动画
const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  // 粒子上升动画
  particleSystems.forEach(p => {
    const pos = p.geometry.attributes.position.array as Float32Array
    for (let i = 0; i < pos.length; i += 3) {
      pos[i + 1] += 2  // Y轴向上
      if (pos[i + 1] > 50) pos[i + 1] = props.extent.zMin
    }
    p.geometry.attributes.position.needsUpdate = true
  })
  
  controls.update()
  renderer.render(scene, camera)
}

// 窗口大小变化
const handleResize = () => {
  if (!containerRef.value) return
  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// 重置视图
const resetView = () => {
  camera.position.set(1500, 1200, 1500)
  controls.target.set(500, -500, 500)
  controls.update()
}

// 切换地质层显示
const toggleLayers = (visible: boolean) => {
  layerMeshes.forEach(m => m.visible = visible)
}

// 切换钻孔显示
const toggleDrillHoles = (visible: boolean) => {
  drillHoleMeshes.forEach(m => m.visible = visible)
}

// 监听变化
watch(() => props.extent, () => {
  createLayers()
  createDrillHoles()
  createHeatParticles()
}, { deep: true })

watch(() => props.layers, () => createLayers(), { deep: true })
watch(() => props.drillHoles, () => createDrillHoles(), { deep: true })

onMounted(() => {
  initScene()
  createLayers()
  createDrillHoles()
  createHeatParticles()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)
  renderer?.dispose()
  controls?.dispose()
})

defineExpose({ resetView, toggleLayers, toggleDrillHoles, toggleGrid })
</script>

<template>
  <div class="geothermal-3d-viewer">
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="40" color="#409eff"><Loading /></el-icon>
      <span>加载 3D 场景中...</span>
    </div>
    
    <div ref="containerRef" class="viewer-container"></div>
    
    <!-- 控制面板 -->
    <div class="control-panel">
      <div class="control-group">
        <h4>视图控制</h4>
        <el-button size="small" @click="resetView">
          <el-icon><Refresh /></el-icon> 重置视图
        </el-button>
      </div>
      
      <div class="control-group">
        <h4>三维网格</h4>
        <el-switch v-model="showGrid" active-text="显示" inactive-text="隐藏" @change="toggleGrid" />
        <div v-if="showGrid && showGridInfo" class="grid-info">
          <div class="info-row">
            <span class="info-label">分辨率:</span>
            <span class="info-value">{{ gridInfo.nx }}×{{ gridInfo.ny }}×{{ gridInfo.nz }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">单元尺寸:</span>
            <span class="info-value small">{{ gridInfo.dx.toFixed(0) }}×{{ gridInfo.dy.toFixed(0) }}×{{ Math.abs(gridInfo.dz).toFixed(0) }}m</span>
          </div>
          <div class="info-row highlight">
            <span class="info-label">每格体积:</span>
            <span class="info-value">{{ formatNumber(gridInfo.cellVolume) }} m³</span>
          </div>
          <div class="info-row">
            <span class="info-label">总格数:</span>
            <span class="info-value">{{ formatNumber(gridInfo.totalCells, 0) }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">总体积:</span>
            <span class="info-value">{{ formatNumber(gridInfo.totalVolume) }} m³</span>
          </div>
        </div>
      </div>
      
      <div class="control-group">
        <h4>坐标轴</h4>
        <div class="axis-item"><span class="axis-color" style="background:#ff4444"></span>X轴(西)</div>
        <div class="axis-item"><span class="axis-color" style="background:#4488ff"></span>Y轴(深度↓)</div>
        <div class="axis-item"><span class="axis-color" style="background:#44ff44"></span>Z轴(北)</div>
      </div>
      
      <div class="control-group">
        <h4>地质层</h4>
        <div class="legend-item" v-for="(l, i) in computedLayerLegend" :key="i">
          <span class="color-box" :style="{background:l.color}"></span>
          <span>{{ l.name }}</span>
        </div>
      </div>
      
      <div class="control-group">
        <h4>温度图例</h4>
        <div class="legend-item"><span class="color-box" style="background:#4CAF50"></span>&lt;100°C</div>
        <div class="legend-item"><span class="color-box" style="background:#FFC107"></span>100-150°C</div>
        <div class="legend-item"><span class="color-box" style="background:#FF9800"></span>150-200°C</div>
        <div class="legend-item"><span class="color-box" style="background:#F44336"></span>&gt;200°C</div>
      </div>
      
      <div class="control-group">
        <h4>操作</h4>
        <p>左键: 旋转</p>
        <p>右键: 平移</p>
        <p>滚轮: 缩放</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.geothermal-3d-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 500px;
  background: #1a1a2e;
  border-radius: 8px;
  overflow: hidden;
}

.viewer-container { width: 100%; height: 100%; }

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(26,26,46,0.9);
  z-index: 10;
  color: white;
  gap: 16px;
}

.control-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0,0,0,0.8);
  padding: 16px;
  border-radius: 8px;
  color: white;
  min-width: 160px;
  max-height: calc(100% - 40px);
  overflow-y: auto;
}

.control-group { margin-bottom: 16px; }
.control-group h4 {
  margin: 0 0 8px;
  font-size: 13px;
  color: #909399;
  border-bottom: 1px solid #444;
  padding-bottom: 4px;
}
.control-group p { margin: 4px 0; font-size: 12px; color: #ccc; }

.grid-info {
  margin-top: 10px;
  padding: 8px;
  background: rgba(64, 158, 255, 0.1);
  border-radius: 6px;
  border: 1px solid rgba(64, 158, 255, 0.3);
}

.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 4px 0;
  font-size: 12px;
}

.info-row.highlight {
  background: rgba(64, 158, 255, 0.2);
  padding: 4px 6px;
  border-radius: 4px;
  margin: 6px 0;
}

.info-row.highlight .info-value {
  color: #409eff;
  font-weight: 600;
}

.info-label {
  color: #909399;
}

.info-value {
  color: #ffffff;
  font-weight: 500;
}

.info-value.small {
  font-size: 11px;
}

.axis-item, .legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0;
  font-size: 12px;
}

.axis-color { width: 20px; height: 3px; border-radius: 2px; }
.color-box { width: 18px; height: 18px; border-radius: 4px; border: 1px solid rgba(255,255,255,0.3); }
</style>
