<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { resourceApi } from '@/api'
import { useGeothermalStore } from '@/stores/geothermal'
import { ElMessage } from 'element-plus'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

const store = useGeothermalStore()

// 计算状态
const loading = ref(false)
const calculating = ref(false)
const result = ref<any>(null)
const gridCells = ref<any[]>([])

// 网格参数
const gridParams = ref({
  x_min: 0,
  x_max: 1000,
  y_min: 0,
  y_max: 1000,
  z_min: -2000,
  z_max: 0,
  nx: 10,
  ny: 10,
  nz: 20
})

// 物理参数
const physicalParams = ref({
  surface_temperature: 15,
  reference_pressure: 0.101325
})

// 3D 相关
const containerRef = ref<HTMLDivElement | null>(null)
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let controls: OrbitControls
let gridMeshes: THREE.Mesh[] = []

// 相态颜色
const phaseColors = {
  liquid: new THREE.Color(0x4CAF50),      // 绿色 - 液态
  two_phase: new THREE.Color(0xFF5722)    // 橙红色 - 气液共存
}

// 温度颜色映射
const getTemperatureColor = (temp: number): THREE.Color => {
  if (temp < 100) return new THREE.Color(0x4CAF50)  // 绿色
  if (temp < 150) return new THREE.Color(0xFFC107)  // 黄色
  if (temp < 200) return new THREE.Color(0xFF9800)  // 橙色
  if (temp < 250) return new THREE.Color(0xFF5722)  // 橱红
  return new THREE.Color(0xF44336)                   // 红色
}

// 显示模式
const displayMode = ref<'phase' | 'temperature'>('phase')
const showDrillHoles = ref(true)
const showLayers = ref(true)
const sliceX = ref(-1)  // -1 表示不切片
const sliceY = ref(-1)
const sliceZ = ref(-1)

// 初始化3D场景
const initScene = () => {
  if (!containerRef.value) return

  const container = containerRef.value
  const width = container.clientWidth
  const height = container.clientHeight

  // 场景
  scene = new THREE.Scene()
  scene.background = new THREE.Color(0x1a1a2e)

  // 相机
  camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 10000)
  camera.position.set(1500, 1500, 1500)
  camera.lookAt(500, -500, 500)

  // 渲染器
  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(window.devicePixelRatio)
  container.appendChild(renderer.domElement)

  // 控制器
  controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.05
  controls.target.set(500, -500, 500)

  // 添加光源
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6)
  scene.add(ambientLight)

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8)
  directionalLight.position.set(1000, 1000, 1000)
  scene.add(directionalLight)

  // 添加坐标轴辅助
  const axesHelper = new THREE.AxesHelper(500)
  scene.add(axesHelper)

  // 添加网格辅助
  const gridHelper = new THREE.GridHelper(2000, 20, 0x444444, 0x222222)
  gridHelper.position.set(500, 0, 500)
  scene.add(gridHelper)

  // 开始渲染
  animate()
}

// 动画循环
const animate = () => {
  requestAnimationFrame(animate)
  controls.update()
  renderer.render(scene, camera)
}

// 清除网格
const clearGridMeshes = () => {
  gridMeshes.forEach(mesh => {
    scene.remove(mesh)
    mesh.geometry.dispose()
    if (mesh.material instanceof THREE.Material) {
      mesh.material.dispose()
    }
  })
  gridMeshes = []
}

// 渲染网格
const renderGrid = () => {
  clearGridMeshes()
  if (gridCells.value.length === 0) return

  const gp = gridParams.value
  const dx = (gp.x_max - gp.x_min) / gp.nx
  const dy = (gp.y_max - gp.y_min) / gp.ny
  const dz = (gp.z_max - gp.z_min) / gp.nz

  gridCells.value.forEach((cell, index) => {
    // 根据显示模式选择颜色
    let color: THREE.Color
    if (displayMode.value === 'phase') {
      color = cell.phase_state === 'liquid' ? phaseColors.liquid.clone() : phaseColors.two_phase.clone()
    } else {
      color = getTemperatureColor(cell.temperature)
    }

    // 根据切片过滤
    if (sliceX.value >= 0 && Math.abs(cell.x - (gp.x_min + dx * (sliceX.value + 0.5))) > dx) return
    if (sliceY.value >= 0 && Math.abs(cell.y - (gp.y_min + dy * (sliceY.value + 0.5))) > dy) return
    if (sliceZ.value >= 0 && Math.abs(cell.z - (gp.z_min + dz * (sliceZ.value + 0.5))) > dz) return

    // 创建盒子几何体
    const geometry = new THREE.BoxGeometry(dx * 0.95, Math.abs(dz) * 0.95, dy * 0.95)
    const material = new THREE.MeshPhongMaterial({
      color: color,
      transparent: true,
      opacity: 0.7,
      side: THREE.DoubleSide
    })

    const mesh = new THREE.Mesh(geometry, material)
    mesh.position.set(cell.x, cell.z, cell.y)
    mesh.userData = { cell, index }
    scene.add(mesh)
    gridMeshes.push(mesh)
  })
}

// 渲染地层边界
const renderLayers = () => {
  // 移除旧的地层边界
  const oldLayers = scene.getObjectByName('layers')
  if (oldLayers) {
    scene.remove(oldLayers)
  }

  if (!showLayers.value || store.layers.length === 0) return

  const layerGroup = new THREE.Group()
  layerGroup.name = 'layers'

  store.layers.forEach((layer: any) => {
    // 创建地层边界平面
    const geometry = new THREE.PlaneGeometry(
      gridParams.value.x_max - gridParams.value.x_min,
      gridParams.value.y_max - gridParams.value.y_min
    )
    const material = new THREE.MeshBasicMaterial({
      color: layer.color || '#409EFF',
      transparent: true,
      opacity: 0.2,
      side: THREE.DoubleSide
    })
    
    // 顶部边界
    const topPlane = new THREE.Mesh(geometry, material)
    topPlane.rotation.x = Math.PI / 2
    topPlane.position.set(
      (gridParams.value.x_max + gridParams.value.x_min) / 2,
      -layer.depth_top,
      (gridParams.value.y_max + gridParams.value.y_min) / 2
    )
    layerGroup.add(topPlane)
  })

  scene.add(layerGroup)
}

// 渲染钻孔
const renderDrillHoles = () => {
  // 移除旧的钻孔
  const oldDrills = scene.getObjectByName('drillholes')
  if (oldDrills) {
    scene.remove(oldDrills)
  }

  if (!showDrillHoles.value || store.drillHoles.length === 0) return

  const drillGroup = new THREE.Group()
  drillGroup.name = 'drillholes'

  store.drillHoles.forEach((hole: any) => {
    // 钻孔线
    const points = [
      new THREE.Vector3(hole.location_x, 0, hole.location_y),
      new THREE.Vector3(hole.location_x, -hole.depth, hole.location_y)
    ]
    const geometry = new THREE.BufferGeometry().setFromPoints(points)
    const material = new THREE.LineBasicMaterial({ 
      color: getTemperatureColor(hole.temperature).getHex(),
      linewidth: 2
    })
    const line = new THREE.Line(geometry, material)
    drillGroup.add(line)

    // 钻孔顶部标记
    const sphereGeom = new THREE.SphereGeometry(15, 16, 16)
    const sphereMat = new THREE.MeshPhongMaterial({
      color: getTemperatureColor(hole.temperature).getHex()
    })
    const sphere = new THREE.Mesh(sphereGeom, sphereMat)
    sphere.position.set(hole.location_x, 0, hole.location_y)
    drillGroup.add(sphere)
  })

  scene.add(drillGroup)
}

// 计算资源
const calculateResource = async () => {
  calculating.value = true
  loading.value = true
  
  try {
    // 准备请求数据
    const requestData = {
      grid_params: gridParams.value,
      drill_holes: store.drillHoles.map((d: any) => ({
        id: d.id,
        name: d.name,
        location_x: d.location_x,
        location_y: d.location_y,
        location_z: d.location_z || 0,
        depth: d.depth,
        temperature: d.temperature,
        gradient: d.gradient || 6.0
      })),
      layers: store.layers.map((l: any) => ({
        id: l.id,
        name: l.name,
        layer_type: l.layer_type,
        depth_top: l.depth_top,
        depth_bottom: l.depth_bottom,
        porosity: l.porosity,
        permeability: l.permeability || 0,
        thermal_conductivity: l.thermal_conductivity || 2.5,
        color: l.color
      })),
      surface_temperature: physicalParams.value.surface_temperature,
      reference_pressure: physicalParams.value.reference_pressure
    }

    const res = await resourceApi.calculate(requestData)
    
    if (res.data) {
      result.value = res.data.summary
      gridCells.value = res.data.grid_cells
      ElMessage.success('计算完成！')
      
      // 渲染网格
      renderGrid()
      renderDrillHoles()
      renderLayers()
    }
  } catch (error: any) {
    console.error('计算失败:', error)
    ElMessage.error(error.response?.data?.detail || '计算失败')
  } finally {
    calculating.value = false
    loading.value = false
  }
}

// 监听显示模式变化
watch(displayMode, () => {
  renderGrid()
})

watch(showDrillHoles, () => {
  renderDrillHoles()
})

watch(showLayers, () => {
  renderLayers()
})

watch([sliceX, sliceY, sliceZ], () => {
  renderGrid()
})

// 格式化数字
const formatNumber = (num: number, decimals: number = 2): string => {
  if (num >= 1e18) return (num / 1e18).toFixed(decimals) + ' EJ'
  if (num >= 1e15) return (num / 1e15).toFixed(decimals) + ' PJ'
  if (num >= 1e12) return (num / 1e12).toFixed(decimals) + ' TJ'
  if (num >= 1e9) return (num / 1e9).toFixed(decimals) + ' GJ'
  if (num >= 1e6) return (num / 1e6).toFixed(decimals) + ' MJ'
  return num.toFixed(decimals) + ' J'
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

onMounted(() => {
  initScene()
  window.addEventListener('resize', handleResize)
})

// 组件卸载时清理
import { onUnmounted } from 'vue'
onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  renderer?.dispose()
})
</script>

<template>
  <div class="resource-view">
    <h1 class="page-title">地热资源网格计算</h1>
    
    <!-- 计算参数 -->
    <div class="card">
      <h3 class="card-title">📐 网格参数配置</h3>
      <el-form label-width="100px">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-form-item label="X方向范围">
              <el-slider v-model="gridParams.nx" :min="5" :max="30" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="Y方向范围">
              <el-slider v-model="gridParams.ny" :min="5" :max="30" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="Z方向层数">
              <el-slider v-model="gridParams.nz" :min="10" :max="50" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="6">
            <el-form-item label="地表温度">
              <el-input-number v-model="physicalParams.surface_temperature" :min="0" :max="30" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="X范围(m)">
              <el-slider v-model="gridParams.x_max" :min="500" :max="5000" :step="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Y范围(m)">
              <el-slider v-model="gridParams.y_max" :min="500" :max="5000" :step="100" show-input />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="最大深度(m)">
              <el-slider v-model="gridParams.z_min" :min="-5000" :max="-500" :step="100" show-input />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item>
          <el-button type="primary" size="large" @click="calculateResource" :loading="calculating">
            <el-icon><Cpu /></el-icon>
            开始计算资源量
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 3D 可视化 -->
    <div class="card">
      <h3 class="card-title">🌐 三维网格模型</h3>
      
      <!-- 控制面板 -->
      <div class="control-bar">
        <div class="control-group">
          <label>显示模式：</label>
          <el-radio-group v-model="displayMode">
            <el-radio-button value="phase">按相态</el-radio-button>
            <el-radio-button value="temperature">按温度</el-radio-button>
          </el-radio-group>
        </div>
        
        <div class="control-group">
          <el-checkbox v-model="showDrillHoles">显示钻孔</el-checkbox>
          <el-checkbox v-model="showLayers">显示地层</el-checkbox>
        </div>
        
        <div class="control-group" v-if="gridCells.length > 0">
          <label>X切片：</label>
          <el-slider v-model="sliceX" :min="-1" :max="gridParams.nx - 1" :step="1" style="width: 150px" />
        </div>
        
        <div class="control-group" v-if="gridCells.length > 0">
          <label>Y切片：</label>
          <el-slider v-model="sliceY" :min="-1" :max="gridParams.ny - 1" :step="1" style="width: 150px" />
        </div>
        
        <div class="control-group" v-if="gridCells.length > 0">
          <label>Z切片：</label>
          <el-slider v-model="sliceZ" :min="-1" :max="gridParams.nz - 1" :step="1" style="width: 150px" />
        </div>
      </div>

      <!-- 图例 -->
      <div class="legend-bar">
        <div class="legend-item" v-if="displayMode === 'phase'">
          <span class="color-box liquid"></span>
          <span>纯液态</span>
        </div>
        <div class="legend-item" v-if="displayMode === 'phase'">
          <span class="color-box two-phase"></span>
          <span>气液共存</span>
        </div>
        <div class="legend-item" v-if="displayMode === 'temperature'">
          <span class="color-box temp-1"></span>
          <span>&lt;100°C</span>
        </div>
        <div class="legend-item" v-if="displayMode === 'temperature'">
          <span class="color-box temp-2"></span>
          <span>100-150°C</span>
        </div>
        <div class="legend-item" v-if="displayMode === 'temperature'">
          <span class="color-box temp-3"></span>
          <span>150-200°C</span>
        </div>
        <div class="legend-item" v-if="displayMode === 'temperature'">
          <span class="color-box temp-4"></span>
          <span>&gt;200°C</span>
        </div>
      </div>

      <!-- 3D 容器 -->
      <div class="viewer-container" ref="containerRef"></div>
    </div>

    <!-- 计算结果 -->
    <div class="card" v-if="result">
      <h3 class="card-title">📊 资源计算结果</h3>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总资源量" :value="result.total_resource">
            <template #formatter>
              <span class="stat-value">{{ formatNumber(result.total_resource) }}</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="纯液态资源" :value="result.liquid_resource">
            <template #formatter>
              <span class="stat-value liquid">{{ formatNumber(result.liquid_resource) }}</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="气液共存资源" :value="result.two_phase_resource">
            <template #formatter>
              <span class="stat-value two-phase">{{ formatNumber(result.two_phase_resource) }}</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="孔隙体积" :value="result.pore_volume">
            <template #formatter>
              <span class="stat-value">{{ (result.pore_volume / 1e6).toFixed(2) }} × 10⁶ m³</span>
            </template>
          </el-statistic>
        </el-col>
      </el-row>

      <el-divider />

      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总网格数" :value="gridCells.length" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="液态网格" :value="result.liquid_cells">
            <template #suffix>
              <span class="stat-suffix liquid">({{ (result.liquid_cells / gridCells.length * 100).toFixed(1) }}%)</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="气液共存网格" :value="result.two_phase_cells">
            <template #suffix>
              <span class="stat-suffix two-phase">({{ (result.two_phase_cells / gridCells.length * 100).toFixed(1) }}%)</span>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="总体积" :value="result.total_volume">
            <template #formatter>
              <span class="stat-value">{{ (result.total_volume / 1e6).toFixed(2) }} × 10⁶ m³</span>
            </template>
          </el-statistic>
        </el-col>
      </el-row>
    </div>

    <!-- 公式说明 -->
    <div class="card">
      <h3 class="card-title">📖 计算方法说明</h3>
      <div class="formula-content">
        <el-collapse>
          <el-collapse-item title="1. 建立三维网格模型" name="1">
            <div class="formula">
              <p>将研究区域划分为 nx × ny × nz 个小网格单元，每个网格单元的体积：</p>
              <p class="equation">ΔV = Δx × Δy × Δz</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="2. 计算网格参数" name="2">
            <div class="formula">
              <p><strong>孔隙度 φᵢ：</strong>根据地层深度插值确定</p>
              <p><strong>压力 Pᵢ：</strong>基于静水压力计算</p>
              <p class="equation">Pᵢ = P₀ + ρ·g·h = 0.101325 + 0.00981 × h (MPa)</p>
              <p><strong>温度 Tᵢ：</strong>基于钻孔数据三维插值</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="3. 相态判定" name="3">
            <div class="formula">
              <p><strong>沸点温度计算：</strong></p>
              <p class="equation">T<sub>boiling</sub> = f(P) （基于水蒸气表）</p>
              <p><strong>相态判断：</strong></p>
              <ul>
                <li>Tᵢ < T<sub>boiling</sub> → 纯液态（绿色）</li>
                <li>Tᵢ ≥ T<sub>boiling</sub> → 气液共存（橙红色）</li>
              </ul>
            </div>
          </el-collapse-item>
          <el-collapse-item title="4. 密度计算" name="4">
            <div class="formula">
              <p><strong>纯液态：</strong>ρ = ρ<sub>water</sub>(T, P)</p>
              <p><strong>气液共存：</strong></p>
              <p class="equation">ρ<sub>mixture</sub> = 1 / (x/ρ<sub>g</sub> + (1-x)/ρ<sub>l</sub>)</p>
              <p>其中 x 为蒸汽质量分数（干度）</p>
            </div>
          </el-collapse-item>
          <el-collapse-item title="5. 资源量计算" name="5">
            <div class="formula">
              <p><strong>单网格资源量：</strong></p>
              <p class="equation">Qᵢ = Vᵢ × φᵢ × ρᵢ × C<sub>p</sub> × (Tᵢ - T₀)</p>
              <p><strong>总资源量：</strong></p>
              <p class="equation">Q<sub>total</sub> = Σ Qᵢ</p>
              <p><strong>分相态汇总：</strong></p>
              <ul>
                <li>Q<sub>liquid</sub> = Σ(液态网格的Qᵢ)</li>
                <li>Q<sub>two_phase</sub> = Σ(气液共存网格的Qᵢ)</li>
              </ul>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>
  </div>
</template>

<style scoped>
.resource-view {
  padding: 0;
}

.control-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group label {
  color: #aaa;
  font-size: 14px;
}

.legend-bar {
  display: flex;
  gap: 24px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 8px;
  margin-bottom: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #ccc;
  font-size: 13px;
}

.color-box {
  width: 20px;
  height: 20px;
  border-radius: 4px;
}

.color-box.liquid { background: #4CAF50; }
.color-box.two-phase { background: #FF5722; }
.color-box.temp-1 { background: #4CAF50; }
.color-box.temp-2 { background: #FFC107; }
.color-box.temp-3 { background: #FF9800; }
.color-box.temp-4 { background: #F44336; }

.viewer-container {
  width: 100%;
  height: 600px;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a2e;
}

.stat-value {
  font-size: 18px;
  font-weight: 600;
}

.stat-value.liquid {
  color: #4CAF50;
}

.stat-value.two-phase {
  color: #FF5722;
}

.stat-suffix.liquid {
  color: #4CAF50;
  font-size: 14px;
}

.stat-suffix.two-phase {
  color: #FF5722;
  font-size: 14px;
}

.formula-content {
  padding: 8px 0;
}

.formula {
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
  line-height: 1.8;
}

.formula p {
  margin: 6px 0;
}

.formula .equation {
  font-family: 'Times New Roman', serif;
  font-size: 16px;
  color: #409eff;
  padding: 8px 16px;
  background: #ecf5ff;
  border-radius: 4px;
  margin: 8px 0;
}

.formula ul {
  margin: 8px 0;
  padding-left: 24px;
}

.formula li {
  margin: 6px 0;
}
</style>
