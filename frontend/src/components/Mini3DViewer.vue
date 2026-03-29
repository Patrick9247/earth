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

// 默认地质层颜色
const defaultLayerColors = [
  0x4CAF50, 0xFFC107, 0xFF9800, 0xE91E63, 0x9C27B0
]

const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // 场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // 相机 - 使用等轴测视角
  camera = new THREE.PerspectiveCamera(50, width / height, 1, 5000)
  camera.position.set(800, 600, 800)
  camera.lookAt(500, -400, 500)

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  containerRef.value.appendChild(renderer.domElement)

  // 控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.autoRotate = true
  controls.autoRotateSpeed = 0.5
  controls.target.set(500, -400, 500)

  // 光源
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(500, 500, 500)
  scene.add(directionalLight)

  // 添加坐标轴
  addAxes()

  // 创建模型
  createLayers()
  createDrillHoles()
  createHeatParticles()

  animate()
}

// 添加坐标轴（与 Geothermal3DViewer 一致）
const addAxes = () => {
  axesGroup = new THREE.Group()
  const axisLength = 250
  
  // X 轴 - 红色 (东向)
  const xMat = new THREE.LineBasicMaterial({ color: 0xff4444 })
  const xGeom = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(axisLength, 0, 0)
  ])
  axesGroup.add(new THREE.Line(xGeom, xMat))

  // X轴箭头
  const xArrow = new THREE.Mesh(
    new THREE.ConeGeometry(8, 30, 8),
    new THREE.MeshBasicMaterial({ color: 0xff4444 })
  )
  xArrow.position.set(axisLength, 0, 0)
  xArrow.rotation.z = -Math.PI / 2
  axesGroup.add(xArrow)

  // Y 轴 - 蓝色 (深度，向下为正)
  const yMat = new THREE.LineBasicMaterial({ color: 0x4488ff })
  const yGeom = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, -axisLength, 0)
  ])
  axesGroup.add(new THREE.Line(yGeom, yMat))

  // Y轴箭头
  const yArrow = new THREE.Mesh(
    new THREE.ConeGeometry(8, 30, 8),
    new THREE.MeshBasicMaterial({ color: 0x4488ff })
  )
  yArrow.position.set(0, -axisLength, 0)
  yArrow.rotation.x = Math.PI
  axesGroup.add(yArrow)

  // Z 轴 - 绿色 (北向)
  const zMat = new THREE.LineBasicMaterial({ color: 0x44ff44 })
  const zGeom = new THREE.BufferGeometry().setFromPoints([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, 0, axisLength)
  ])
  axesGroup.add(new THREE.Line(zGeom, zMat))

  // Z轴箭头
  const zArrow = new THREE.Mesh(
    new THREE.ConeGeometry(8, 30, 8),
    new THREE.MeshBasicMaterial({ color: 0x44ff44 })
  )
  zArrow.position.set(0, 0, axisLength)
  zArrow.rotation.x = Math.PI / 2
  axesGroup.add(zArrow)

  // 添加标签
  addTextSprite('X(东)', axisLength + 40, 0, 0, '#ff4444')
  addTextSprite('Y(深)', 0, -axisLength - 40, 0, '#4488ff')
  addTextSprite('Z(北)', 0, 0, axisLength + 40, '#44ff44')

  scene.add(axesGroup)
}

// 添加文字精灵
const addTextSprite = (text: string, x: number, y: number, z: number, color: string) => {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  canvas.width = 96
  canvas.height = 48

  ctx.fillStyle = 'rgba(0,0,0,0.7)'
  ctx.fillRect(0, 0, canvas.width, canvas.height)

  ctx.font = 'bold 18px Arial'
  ctx.fillStyle = color
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(text, canvas.width / 2, canvas.height / 2)

  const texture = new THREE.CanvasTexture(canvas)
  const spriteMat = new THREE.SpriteMaterial({ map: texture })
  const sprite = new THREE.Sprite(spriteMat)
  sprite.position.set(x, y, z)
  sprite.scale.set(80, 40, 1)
  axesGroup.add(sprite)
}

const createLayers = () => {
  layerMeshes.forEach(m => scene.remove(m))
  layerMeshes = []

  const { xMin, xMax, yMin: zMin, yMax: zMax, zMin: yMin } = props.extent

  const layersToUse = props.layers.length > 0 ? props.layers : [
    { name: '地表', depth_top: 0, depth_bottom: 100, color: '#4CAF50' },
    { name: '沉积层', depth_top: 100, depth_bottom: 500, color: '#FFC107' },
    { name: '储层', depth_top: 500, depth_bottom: 1200, color: '#FF9800' },
    { name: '基底', depth_top: 1200, depth_bottom: 2000, color: '#E91E63' }
  ]

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
      opacity: 0.65,
      side: THREE.DoubleSide
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
      new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.4, transparent: true })
    )
    mesh.add(wireframe)

    scene.add(mesh)
    layerMeshes.push(mesh)
  })
}

const createDrillHoles = () => {
  drillHoleMeshes.forEach(m => scene.remove(m))
  drillHoleMeshes = []

  const holesToUse = props.drillHoles.length > 0 ? props.drillHoles : [
    { name: 'ZK-001', location_x: 150, location_y: 150, depth: 800, temperature: 120 },
    { name: 'ZK-002', location_x: -100, location_y: 200, depth: 1200, temperature: 160 },
    { name: 'ZK-003', location_x: 200, location_y: -150, depth: 600, temperature: 95 },
    { name: 'ZK-004', location_x: -200, location_y: -100, depth: 1000, temperature: 140 }
  ]

  holesToUse.forEach((hole: any) => {
    const x = hole.location_x ?? 0
    const z = hole.location_y ?? 0  // Y坐标映射到Z轴
    const depth = hole.depth ?? 500

    // 钻孔颜色（根据温度）
    const temp = hole.temperature ?? 100
    const color = temp < 100 ? 0x4CAF50 : temp < 150 ? 0xFFC107 : temp < 200 ? 0xFF9800 : 0xF44336

    // 钻孔圆柱体
    const geometry = new THREE.CylinderGeometry(8, 8, depth, 12)
    const material = new THREE.MeshPhongMaterial({ color, transparent: true, opacity: 0.8 })
    const cylinder = new THREE.Mesh(geometry, material)
    
    // 位置：Y轴负方向表示深度
    cylinder.position.set(x, -depth / 2, z)
    scene.add(cylinder)
    drillHoleMeshes.push(cylinder)

    // 顶部标记球
    const marker = new THREE.Mesh(
      new THREE.SphereGeometry(12, 12, 12),
      new THREE.MeshPhongMaterial({ color, shininess: 100 })
    )
    marker.position.set(x, 0, z)
    scene.add(marker)
    drillHoleMeshes.push(marker)
  })
}

const createHeatParticles = () => {
  particleSystems.forEach(p => scene.remove(p))
  particleSystems = []

  const { xMin, xMax, yMin: zMin, yMax: zMax, zMin: yMin } = props.extent
  
  const count = 150
  const positions = new Float32Array(count * 3)
  const colors = new Float32Array(count * 3)

  for (let i = 0; i < count; i++) {
    positions[i * 3] = xMin + Math.random() * (xMax - xMin)
    positions[i * 3 + 1] = yMin + Math.random() * 200  // Y轴（深度方向）
    positions[i * 3 + 2] = zMin + Math.random() * (zMax - zMin)

    colors[i * 3] = 1.0
    colors[i * 3 + 1] = 0.3 + Math.random() * 0.4
    colors[i * 3 + 2] = 0.1
  }

  const geometry = new THREE.BufferGeometry()
  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))

  const material = new THREE.PointsMaterial({
    size: 5,
    vertexColors: true,
    transparent: true,
    opacity: 0.6
  })

  const particles = new THREE.Points(geometry, material)
  particles.name = 'particles'
  scene.add(particles)
  particleSystems.push(particles)
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  // 更新粒子位置（向上移动）
  const particles = scene.getObjectByName('particles') as THREE.Points
  if (particles) {
    const positions = particles.geometry.attributes.position.array as Float32Array
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 1] += 2  // Y轴向上
      if (positions[i + 1] > 50) {
        positions[i + 1] = props.extent.zMin
      }
    }
    particles.geometry.attributes.position.needsUpdate = true
  }
  
  controls.update()
  renderer.render(scene, camera)
}

const handleResize = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

// 监听数据变化，更新模型
watch(() => props.extent, () => {
  createLayers()
  createDrillHoles()
  createHeatParticles()
}, { deep: true })

watch(() => props.layers, () => createLayers(), { deep: true })
watch(() => props.drillHoles, () => createDrillHoles(), { deep: true })

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cancelAnimationFrame(animationId)
  if (renderer) renderer.dispose()
  if (controls) controls.dispose()
})
</script>

<template>
  <div class="mini-3d-viewer">
    <div ref="containerRef" class="viewer-container"></div>
    <div class="viewer-label">
      <el-icon><DataAnalysis /></el-icon>
      <span>实时 3D 预览</span>
    </div>
    <div class="axis-hint">
      <span style="color: #ff4444;">X(东)</span>
      <span style="color: #4488ff;">Y(深度↓)</span>
      <span style="color: #44ff44;">Z(北)</span>
    </div>
  </div>
</template>

<style scoped>
.mini-3d-viewer {
  position: relative;
  height: 400px;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.viewer-container {
  width: 100%;
  height: 100%;
}

.viewer-label {
  position: absolute;
  bottom: 16px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 20px;
  color: white;
  font-size: 14px;
}

.axis-hint {
  position: absolute;
  top: 16px;
  right: 16px;
  display: flex;
  gap: 12px;
  padding: 6px 12px;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 12px;
  font-size: 12px;
  font-weight: bold;
}
</style>
