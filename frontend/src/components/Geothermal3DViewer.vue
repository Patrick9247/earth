<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
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

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let animationId: number

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
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(1000, 1000, 500)
  directionalLight.castShadow = true
  scene.add(directionalLight)

  const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.4)
  directionalLight2.position.set(-500, -500, 250)
  scene.add(directionalLight2)

  // 添加坐标轴辅助
  const axesHelper = new THREE.AxesHelper(500)
  scene.add(axesHelper)

  // 添加网格辅助
  const gridHelper = new THREE.GridHelper(2000, 20, 0x444444, 0x333333)
  gridHelper.position.y = props.extent.zMax
  scene.add(gridHelper)

  // 开始动画
  animate()
  loading.value = false
}

// 创建地质层
const createLayers = () => {
  const layerColors = [
    0x4CAF50, // 绿色 - 表层
    0xFFC107, // 黄色 - 第一层
    0xFF9800, // 橙色 - 第二层
    0xF44336, // 红色 - 第三层
    0x9C27B0  // 紫色 - 基岩
  ]

  const defaultLayers = [
    { name: '地表', depthTop: 0, depthBottom: -100 },
    { name: '沉积层', depthTop: -100, depthBottom: -500 },
    { name: '储层', depthTop: -500, depthBottom: -1200 },
    { name: '基底', depthTop: -1200, depthBottom: -2000 }
  ]

  const layersToUse = props.layers.length > 0 ? props.layers : defaultLayers
  const { xMin, xMax, yMin, yMax } = props.extent

  layersToUse.forEach((layer: any, index: number) => {
    const topDepth = layer.depth_top ?? layer.depthTop ?? -(index * 500)
    const bottomDepth = layer.depth_bottom ?? layer.depthBottom ?? -((index + 1) * 500)
    
    const geometry = new THREE.BoxGeometry(
      xMax - xMin,
      yMax - yMin,
      Math.abs(bottomDepth - topDepth)
    )

    const material = new THREE.MeshPhongMaterial({
      color: layer.color ? parseInt(layer.color.replace('#', '0x')) : layerColors[index % layerColors.length],
      transparent: true,
      opacity: 0.7,
      side: THREE.DoubleSide
    })

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(
      (xMin + xMax) / 2,
      (yMin + yMax) / 2,
      (topDepth + bottomDepth) / 2
    )
    mesh.receiveShadow = true
    mesh.castShadow = true

    // 添加边框
    const edges = new THREE.EdgesGeometry(geometry)
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.5, transparent: true })
    const wireframe = new THREE.LineSegments(edges, lineMaterial)
    mesh.add(wireframe)

    scene.add(mesh)
  })
}

// 创建钻孔
const createDrillHoles = () => {
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
      opacity: 0.9
    })

    const cylinder = new THREE.Mesh(geometry, material)
    cylinder.position.set(x, y, -depth / 2)
    cylinder.castShadow = true
    scene.add(cylinder)

    // 创建钻孔顶部标记（球体）
    const markerGeometry = new THREE.SphereGeometry(25, 16, 16)
    const markerMaterial = new THREE.MeshPhongMaterial({ color: color })
    const marker = new THREE.Mesh(markerGeometry, markerMaterial)
    marker.position.set(x, y, 0)
    marker.castShadow = true
    scene.add(marker)

    // 创建标签
    createLabel(hole.name ?? 'ZK', x, y, 50)
  })
}

// 根据温度获取颜色
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
  
  scene.add(sprite)
}

// 创建温度场可视化
const createTemperatureField = () => {
  const { xMin, xMax, yMin, yMax, zMin } = props.extent
  
  // 创建等温面
  const points: THREE.Vector3[] = []
  const gridSize = 50
  
  for (let x = xMin; x <= xMax; x += gridSize) {
    for (let y = yMin; y <= yMax; y += gridSize) {
      // 模拟温度随深度增加
      const z = zMin + Math.random() * 100
      points.push(new THREE.Vector3(x, y, z))
    }
  }
  
  // 创建粒子系统表示温度分布
  const geometry = new THREE.BufferGeometry().setFromPoints(points)
  const material = new THREE.PointsMaterial({
    color: 0xff6600,
    size: 10,
    transparent: true,
    opacity: 0.6
  })
  
  const pointsMesh = new THREE.Points(geometry, material)
  scene.add(pointsMesh)
}

// 动画循环
const animate = () => {
  animationId = requestAnimationFrame(animate)
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
  scene.children.forEach((child) => {
    if (child instanceof THREE.Mesh && child.geometry instanceof THREE.BoxGeometry) {
      child.visible = visible
    }
  })
}

// 切换钻孔显示
const toggleDrillHoles = (visible: boolean) => {
  scene.children.forEach((child) => {
    if (child instanceof THREE.Mesh && child.geometry instanceof THREE.CylinderGeometry) {
      child.visible = visible
    }
  })
}

// 监听数据变化
watch(() => [props.layers, props.drillHoles], () => {
  // 清除旧的模型
  while (scene.children.length > 0) {
    scene.remove(scene.children[0])
  }
  // 重新创建
  createLayers()
  createDrillHoles()
}, { deep: true })

onMounted(() => {
  initScene()
  createLayers()
  createDrillHoles()
  createTemperatureField()
  
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
        <h4>图例</h4>
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
  background: rgba(0, 0, 0, 0.7);
  padding: 16px;
  border-radius: 8px;
  color: white;
  min-width: 180px;
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
  width: 16px;
  height: 16px;
  border-radius: 3px;
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
