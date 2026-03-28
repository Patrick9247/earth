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

const containerRef = ref<HTMLDivElement | null>(null)
const loading = ref(true)

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

// 存储模型对象，方便后续操作
let layerMeshes: THREE.Mesh[] = []
let drillHoleMeshes: THREE.Mesh[] = []
let particleSystems: THREE.Points[] = []

// 默认地质层颜色（彩色且鲜明）
const defaultLayerColors = [
  0x4CAF50, // 绿色 - 表层
  0xFFC107, // 黄色 - 第一层
  0xFF9800, // 橙色 - 第二层
  0xE91E63, // 粉红色 - 第三层
  0x9C27B0  // 紫色 - 基岩
]

// 初始化 Three.js 场景
const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // 创建场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // 创建相机
  camera = new THREE.PerspectiveCamera(60, width / height, 1, 10000)
  camera.position.set(1500, 1500, 1000)

  // 创建渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  renderer.shadowMap.enabled = true
  containerRef.value.appendChild(renderer.domElement)

  // 创建控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.minDistance = 500
  controls.maxDistance = 5000

  // 添加光源
  addLights()

  // 添加坐标轴辅助
  const axesHelper = new THREE.AxesHelper(500)
  scene.add(axesHelper)

  // 添加网格辅助
  addGrid()

  // 开始动画
  animate()
  loading.value = false
}

// 添加光源
const addLights = () => {
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  ambientLight.name = 'ambientLight'
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(1000, 1000, 500)
  directionalLight.castShadow = true
  directionalLight.name = 'directionalLight1'
  scene.add(directionalLight)

  const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4)
  directionalLight2.position.set(-500, -500, 250)
  directionalLight2.name = 'directionalLight2'
  scene.add(directionalLight2)
}

// 添加网格
const addGrid = () => {
  const gridHelper = new THREE.GridHelper(2000, 20, 0x444444, 0x333333)
  gridHelper.position.y = props.extent.zMax
  gridHelper.name = 'gridHelper'
  scene.add(gridHelper)
}

// 创建地质层
const createLayers = () => {
  // 清除旧的地质层
  layerMeshes.forEach(mesh => scene.remove(mesh))
  layerMeshes = []

  const defaultLayers = [
    { name: '地表', depth_top: 0, depth_bottom: -100, color: '#4CAF50' },
    { name: '沉积层', depth_top: -100, depth_bottom: -500, color: '#FFC107' },
    { name: '储层', depth_top: -500, depth_bottom: -1200, color: '#FF9800' },
    { name: '基底', depth_top: -1200, depth_bottom: -2000, color: '#E91E63' }
  ]

  const layersToUse = props.layers.length > 0 ? props.layers : defaultLayers
  const { xMin, xMax, yMin, yMax } = props.extent

  layersToUse.forEach((layer: any, index: number) => {
    // 处理深度值：如果是正数（深度），转为负数（Z坐标）
    let topDepth = layer.depth_top ?? layer.depthTop ?? -(index * 500)
    let bottomDepth = layer.depth_bottom ?? layer.depthBottom ?? -((index + 1) * 500)
    
    // 如果是正数深度值，转换为负的Z坐标
    if (topDepth > 0) topDepth = -topDepth
    if (bottomDepth > 0) bottomDepth = -bottomDepth
    
    const geometry = new THREE.BoxGeometry(
      xMax - xMin,
      yMax - yMin,
      Math.abs(bottomDepth - topDepth)
    )

    // 解析颜色
    let color: number
    if (layer.color && typeof layer.color === 'string') {
      // 处理 #RRGGBB 格式
      color = parseInt(layer.color.replace('#', ''), 16)
      if (isNaN(color)) {
        color = defaultLayerColors[index % defaultLayerColors.length]
      }
    } else {
      color = defaultLayerColors[index % defaultLayerColors.length]
    }

    const material = new THREE.MeshPhongMaterial({
      color: color,
      transparent: true,
      opacity: 0.75,
      side: THREE.DoubleSide,
      shininess: 30
    })

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(
      (xMin + xMax) / 2,
      (yMin + yMax) / 2,
      (topDepth + bottomDepth) / 2
    )
    mesh.receiveShadow = true
    mesh.castShadow = true
    mesh.name = `layer_${index}_${layer.name || 'unnamed'}`

    // 添加边框
    const edges = new THREE.EdgesGeometry(geometry)
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.8, transparent: true })
    const wireframe = new THREE.LineSegments(edges, lineMaterial)
    mesh.add(wireframe)

    scene.add(mesh)
    layerMeshes.push(mesh)
  })
}

// 创建钻孔
const createDrillHoles = () => {
  // 清除旧的钻孔
  drillHoleMeshes.forEach(mesh => scene.remove(mesh))
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
    const x = hole.location_x ?? hole.locationX ?? 0
    const y = hole.location_y ?? hole.locationY ?? 0
    const depth = hole.depth ?? 500

    // 创建钻孔主体（圆柱体）
    const radius = 15
    const geometry = new THREE.CylinderGeometry(radius, radius, depth, 16)
    
    // 根据温度设置颜色
    const temp = hole.temperature ?? 100
    const color = getTemperatureColor(temp)
    
    const material = new THREE.MeshPhongMaterial({
      color: color,
      transparent: true,
      opacity: 0.9,
      shininess: 50
    })

    const cylinder = new THREE.Mesh(geometry, material)
    cylinder.position.set(x, y, -depth / 2)
    cylinder.castShadow = true
    cylinder.name = `drillhole_${hole.name || 'unnamed'}`
    scene.add(cylinder)
    drillHoleMeshes.push(cylinder)

    // 创建钻孔顶部标记（球体）
    const markerGeometry = new THREE.SphereGeometry(25, 16, 16)
    const markerMaterial = new THREE.MeshPhongMaterial({ 
      color: color,
      shininess: 100
    })
    const marker = new THREE.Mesh(markerGeometry, markerMaterial)
    marker.position.set(x, y, 0)
    marker.castShadow = true
    marker.name = `drillhole_marker_${hole.name || 'unnamed'}`
    scene.add(marker)
    drillHoleMeshes.push(marker)

    // 创建标签
    createLabel(hole.name ?? 'ZK', x, y, 50)
  })
}

// 根据温度获取颜色（返回 THREE.Color）
const getTemperatureColor = (temp: number): number => {
  if (temp < 100) return 0x4CAF50  // 绿色 - 低温
  if (temp < 150) return 0xFFC107  // 黄色 - 中温
  if (temp < 200) return 0xFF9800  // 橙色 - 高温
  return 0xF44336                   // 红色 - 超高温
}

// 创建文字标签（使用精灵）
const createLabel = (text: string, x: number, y: number, z: number) => {
  const canvas = document.createElement('canvas')
  const context = canvas.getContext('2d')
  if (!context) return

  canvas.width = 256
  canvas.height = 64

  context.fillStyle = 'rgba(0, 0, 0, 0.7)'
  context.fillRect(0, 0, canvas.width, canvas.height)

  context.font = 'bold 32px Arial'
  context.fillStyle = 'white'
  context.textAlign = 'center'
  context.textBaseline = 'middle'
  context.fillText(text, canvas.width / 2, canvas.height / 2)

  const texture = new THREE.CanvasTexture(canvas)
  const spriteMaterial = new THREE.SpriteMaterial({ map: texture })
  const sprite = new THREE.Sprite(spriteMaterial)
  
  sprite.position.set(x, y, z)
  sprite.scale.set(100, 25, 1)
  sprite.name = `label_${text}`
  
  scene.add(sprite)
  drillHoleMeshes.push(sprite as any)
}

// 创建热流粒子效果
const createHeatParticles = () => {
  // 清除旧的粒子系统
  particleSystems.forEach(p => scene.remove(p))
  particleSystems = []

  const { xMin, xMax, yMin, yMax, zMin } = props.extent
  
  // 创建热流粒子
  const particleCount = 500
  const positions = new Float32Array(particleCount * 3)
  const colors = new Float32Array(particleCount * 3)

  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = xMin + Math.random() * (xMax - xMin)
    positions[i * 3 + 1] = yMin + Math.random() * (yMax - yMin)
    positions[i * 3 + 2] = zMin + Math.random() * 200

    // 颜色从黄色到红色渐变
    const t = Math.random()
    colors[i * 3] = 1.0          // R
    colors[i * 3 + 1] = 0.3 + t * 0.5  // G
    colors[i * 3 + 2] = 0.0      // B
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  const material = new THREE.PointsMaterial({
    size: 15,
    vertexColors: true,
    transparent: true,
    opacity: 0.8,
    sizeAttenuation: true
  })

  const particles = new THREE.Points(geometry, material)
  particles.name = 'heatParticles'
  scene.add(particles)
  particleSystems.push(particles)
}

// 动画循环
const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  // 更新粒子动画
  particleSystems.forEach(particles => {
    const positions = particles.geometry.attributes.position.array as Float32Array
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 2] += 2 // 向上移动
      if (positions[i + 2] > 0) {
        positions[i + 2] = props.extent.zMin
      }
    }
    particles.geometry.attributes.position.needsUpdate = true
  })
  
  controls.update()
  renderer.render(scene, camera)
}

// 处理窗口大小变化
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
  camera.position.set(1500, 1500, 1000)
  controls.reset()
}

// 切换地质层显示
const toggleLayers = (visible: boolean) => {
  layerMeshes.forEach(mesh => {
    mesh.visible = visible
  })
}

// 切换钻孔显示
const toggleDrillHoles = (visible: boolean) => {
  drillHoleMeshes.forEach(mesh => {
    mesh.visible = visible
  })
}

// 重建整个场景模型
const rebuildScene = () => {
  // 清除所有模型对象
  layerMeshes.forEach(mesh => scene.remove(mesh))
  drillHoleMeshes.forEach(mesh => scene.remove(mesh))
  particleSystems.forEach(p => scene.remove(p))
  layerMeshes = []
  drillHoleMeshes = []
  particleSystems = []
  
  // 清除标签精灵
  const spritesToRemove = scene.children.filter(child => 
    child instanceof THREE.Sprite && child.name.startsWith('label_')
  )
  spritesToRemove.forEach(sprite => scene.remove(sprite))
  
  // 清除网格并重新添加
  const oldGrid = scene.getObjectByName('gridHelper')
  if (oldGrid) scene.remove(oldGrid)
  addGrid()
  
  // 重新创建模型
  createLayers()
  createDrillHoles()
  createHeatParticles()
}

// 监听数据变化 - 监听 extent 变化
watch(() => props.extent, () => {
  rebuildScene()
}, { deep: true })

// 监听 layers 变化
watch(() => props.layers, () => {
  createLayers()
}, { deep: true })

// 监听 drillHoles 变化
watch(() => props.drillHoles, () => {
  createDrillHoles()
}, { deep: true })

onMounted(async () => {
  initScene()
  createLayers()
  createDrillHoles()
  createHeatParticles()
  
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)
  
  if (renderer) {
    renderer.dispose()
  }
  if (controls) {
    controls.dispose()
  }
})

// 暴露方法给父组件
defineExpose({
  resetView,
  toggleLayers,
  toggleDrillHoles
})
</script>

<template>
  <div class="geothermal-3d-viewer">
    <div v-if="loading" class="loading-overlay">
      <el-icon class="is-loading" :size="40" color="#409eff">
        <Loading />
      </el-icon>
      <span>加载 3D 场景中...</span>
    </div>
    
    <div ref="containerRef" class="viewer-container"></div>
    
    <!-- 控制面板 -->
    <div class="control-panel">
      <div class="control-group">
        <h4>视图控制</h4>
        <el-button size="small" @click="resetView">
          <el-icon><Refresh /></el-icon>
          重置视图
        </el-button>
      </div>
      
      <div class="control-group">
        <h4>地质层颜色</h4>
        <div class="legend-item" v-for="(layer, index) in computedLayerLegend" :key="index">
          <span class="color-box" :style="{ background: layer.color }"></span>
          <span>{{ layer.name }} ({{ layer.depthRange }})</span>
        </div>
      </div>
      
      <div class="control-group">
        <h4>温度图例</h4>
        <div class="legend-item">
          <span class="color-box temp-low"></span>
          <span>低温 (&lt;100°C)</span>
        </div>
        <div class="legend-item">
          <span class="color-box temp-mid"></span>
          <span>中温 (100-150°C)</span>
        </div>
        <div class="legend-item">
          <span class="color-box temp-high"></span>
          <span>高温 (150-200°C)</span>
        </div>
        <div class="legend-item">
          <span class="color-box temp-very-high"></span>
          <span>超高温 (&gt;200°C)</span>
        </div>
      </div>
      
      <div class="control-group">
        <h4>操作提示</h4>
        <p>🖱️ 左键拖动：旋转</p>
        <p>🖱️ 右键拖动：平移</p>
        <p>🖱️ 滚轮：缩放</p>
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

.viewer-container {
  width: 100%;
  height: 100%;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(26, 26, 46, 0.9);
  z-index: 10;
  color: white;
  gap: 16px;
}

.control-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(0, 0, 0, 0.8);
  padding: 16px;
  border-radius: 8px;
  color: white;
  min-width: 180px;
  max-height: calc(100% - 40px);
  overflow-y: auto;
}

.control-group {
  margin-bottom: 16px;
}

.control-group h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #909399;
  border-bottom: 1px solid #444;
  padding-bottom: 4px;
}

.control-group p {
  margin: 4px 0;
  font-size: 12px;
  color: #ccc;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 6px 0;
  font-size: 12px;
}

.color-box {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.temp-low {
  background: #4CAF50;
}

.temp-mid {
  background: #FFC107;
}

.temp-high {
  background: #FF9800;
}

.temp-very-high {
  background: #F44336;
}
</style>
