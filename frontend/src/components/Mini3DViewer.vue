<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const containerRef = ref<HTMLDivElement | null>(null)

let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let animationId: number

const initScene = () => {
  if (!containerRef.value) return

  const width = containerRef.value.clientWidth
  const height = containerRef.value.clientHeight

  // 场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // 相机
  camera = new THREE.PerspectiveCamera(50, width / height, 1, 5000)
  camera.position.set(800, 800, 600)

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

  // 光源
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(500, 500, 300)
  scene.add(directionalLight)

  // 创建地质层
  createLayers()

  // 创建钻孔
  createDrillHoles()

  // 创建热流粒子
  createHeatParticles()

  animate()
}

const createLayers = () => {
  const colors = [0x4CAF50, 0xFFC107, 0xFF9800, 0xF44336]
  const depths = [0, -100, -500, -1200, -2000]
  
  for (let i = 0; i < 4; i++) {
    const thickness = Math.abs(depths[i + 1] - depths[i])
    const geometry = new THREE.BoxGeometry(800, 800, thickness)
    const material = new THREE.MeshPhongMaterial({
      color: colors[i],
      transparent: true,
      opacity: 0.6,
      side: THREE.DoubleSide
    })
    
    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(0, 0, (depths[i] + depths[i + 1]) / 2)
    
    // 边框
    const edges = new THREE.EdgesGeometry(geometry)
    const lineMaterial = new THREE.LineBasicMaterial({ color: 0xffffff, opacity: 0.3, transparent: true })
    const wireframe = new THREE.LineSegments(edges, lineMaterial)
    mesh.add(wireframe)
    
    scene.add(mesh)
  }
}

const createDrillHoles = () => {
  const positions = [
    { x: 150, y: 150, depth: 800, temp: 120 },
    { x: -100, y: 200, depth: 1200, temp: 160 },
    { x: 200, y: -150, depth: 600, temp: 95 },
    { x: -200, y: -100, depth: 1000, temp: 140 }
  ]

  positions.forEach(pos => {
    // 钻孔主体
    const geometry = new THREE.CylinderGeometry(10, 10, pos.depth, 12)
    const color = pos.temp > 150 ? 0xF44336 : pos.temp > 100 ? 0xFF9800 : 0x4CAF50
    const material = new THREE.MeshPhongMaterial({ color, transparent: true, opacity: 0.8 })
    const cylinder = new THREE.Mesh(geometry, material)
    cylinder.position.set(pos.x, pos.y, -pos.depth / 2)
    scene.add(cylinder)

    // 顶部标记
    const markerGeometry = new THREE.SphereGeometry(15, 12, 12)
    const markerMaterial = new THREE.MeshPhongMaterial({ color })
    const marker = new THREE.Mesh(markerGeometry, markerMaterial)
    marker.position.set(pos.x, pos.y, 0)
    scene.add(marker)
  })
}

const createHeatParticles = () => {
  const particleCount = 500
  const positions = new Float32Array(particleCount * 3)
  const colors = new Float32Array(particleCount * 3)

  for (let i = 0; i < particleCount; i++) {
    positions[i * 3] = (Math.random() - 0.5) * 600
    positions[i * 3 + 1] = (Math.random() - 0.5) * 600
    positions[i * 3 + 2] = -Math.random() * 1500 - 200

    // 橙红色渐变
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
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  
  // 更新粒子位置（上升动画）
  const particles = scene.getObjectByName('particles') as THREE.Points
  if (particles) {
    const positions = particles.geometry.attributes.position.array as Float32Array
    for (let i = 0; i < positions.length; i += 3) {
      positions[i + 2] += 0.5
      if (positions[i + 2] > 0) {
        positions[i + 2] = -1500
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
</style>
