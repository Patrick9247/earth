import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { layersApi, drillHolesApi, gempyApi } from '@/api'

export const useGeothermalStore = defineStore('geothermal', () => {
  // State
  const layers = ref<any[]>([])
  const drillHoles = ref<any[]>([])
  const calculationResults = ref<any[]>([])
  const currentModel = ref<any>(null)
  const loading = ref(false)

  // 模型配置
  const modelConfig = ref({
    grid_resolution: 50,
    extent_x_min: 0,
    extent_x_max: 1000,
    extent_y_min: 0,
    extent_y_max: 1000,
    extent_z_min: -2000,
    extent_z_max: 0
  })

  // 模型是否已创建
  const modelCreated = ref(false)

  // Getters
  const totalLayers = computed(() => layers.value.length)
  const totalDrillHoles = computed(() => drillHoles.value.length)
  const totalPowerPotential = computed(() => 
    calculationResults.value.reduce((sum, r) => sum + (r.power_potential || 0), 0)
  )

  // Extent 计算属性
  const extent = computed(() => ({
    xMin: modelConfig.value.extent_x_min,
    xMax: modelConfig.value.extent_x_max,
    yMin: modelConfig.value.extent_y_min,
    yMax: modelConfig.value.extent_y_max,
    zMin: modelConfig.value.extent_z_min,
    zMax: modelConfig.value.extent_z_max
  }))

  // 默认模拟数据
  const defaultLayers = [
    { id: 1, name: '第四系覆盖层', layer_type: '沉积层', depth_top: 0, depth_bottom: 100, porosity: 0.25, color: '#90EE90' },
    { id: 2, name: '砂岩储层', layer_type: '储层', depth_top: 100, depth_bottom: 500, porosity: 0.18, color: '#FFD700' },
    { id: 3, name: '泥岩盖层', layer_type: '盖层', depth_top: 500, depth_bottom: 1200, porosity: 0.08, color: '#87CEEB' },
    { id: 4, name: '花岗岩基底', layer_type: '基岩', depth_top: 1200, depth_bottom: 2000, porosity: 0.05, color: '#CD5C5C' }
  ]

  const defaultDrillHoles = [
    { id: 1, name: 'ZK-001', location_x: 200, location_y: 300, depth: 800, temperature: 120 },
    { id: 2, name: 'ZK-002', location_x: 500, location_y: 600, depth: 1200, temperature: 160 },
    { id: 3, name: 'ZK-003', location_x: 800, location_y: 400, depth: 600, temperature: 95 },
    { id: 4, name: 'ZK-004', location_x: 350, location_y: 700, depth: 1000, temperature: 140 },
    { id: 5, name: 'ZK-005', location_x: 650, location_y: 200, depth: 900, temperature: 135 }
  ]

  // Actions
  async function fetchLayers() {
    try {
      const res = await layersApi.getAll()
      layers.value = res.data && res.data.length > 0 ? res.data : defaultLayers
    } catch (error) {
      console.error('Failed to fetch layers:', error)
      layers.value = defaultLayers
    }
  }

  async function fetchDrillHoles() {
    try {
      const res = await drillHolesApi.getAll()
      drillHoles.value = res.data && res.data.length > 0 ? res.data : defaultDrillHoles
    } catch (error) {
      console.error('Failed to fetch drill holes:', error)
      drillHoles.value = defaultDrillHoles
    }
  }

  async function fetchResults() {
    try {
      const res = await gempyApi.getResults()
      calculationResults.value = res.data || []
    } catch (error) {
      console.error('Failed to fetch results:', error)
    }
  }

  async function quickCalculate(params: {
    reservoir_volume: number
    avg_temperature: number
    porosity?: number
    recovery_factor?: number
  }) {
    loading.value = true
    try {
      const res = await gempyApi.quickCalc(params)
      return res.data
    } finally {
      loading.value = false
    }
  }

  // 初始化数据（用于首页和建模页面）
  async function initializeData() {
    // 每次都从 API 获取最新数据，确保数据同步
    await Promise.all([fetchLayers(), fetchDrillHoles()])
  }

  // 更新模型配置
  function updateModelConfig(config: Partial<typeof modelConfig.value>) {
    modelConfig.value = { ...modelConfig.value, ...config }
  }

  // 更新地质层
  function updateLayers(newLayers: any[]) {
    layers.value = newLayers
  }

  // 更新钻孔
  function updateDrillHoles(newDrillHoles: any[]) {
    drillHoles.value = newDrillHoles
  }

  // 设置模型已创建
  function setModelCreated(created: boolean) {
    modelCreated.value = created
  }

  return {
    // State
    layers,
    drillHoles,
    calculationResults,
    currentModel,
    loading,
    modelConfig,
    modelCreated,
    // Getters
    totalLayers,
    totalDrillHoles,
    totalPowerPotential,
    extent,
    // Actions
    fetchLayers,
    fetchDrillHoles,
    fetchResults,
    quickCalculate,
    initializeData,
    updateModelConfig,
    updateLayers,
    updateDrillHoles,
    setModelCreated,
  }
})
