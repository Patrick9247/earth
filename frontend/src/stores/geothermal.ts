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

  // Getters
  const totalLayers = computed(() => layers.value.length)
  const totalDrillHoles = computed(() => drillHoles.value.length)
  const totalPowerPotential = computed(() => 
    calculationResults.value.reduce((sum, r) => sum + (r.power_potential || 0), 0)
  )

  // Actions
  async function fetchLayers() {
    try {
      const res = await layersApi.getAll()
      layers.value = res.data || []
    } catch (error) {
      console.error('Failed to fetch layers:', error)
    }
  }

  async function fetchDrillHoles() {
    try {
      const res = await drillHolesApi.getAll()
      drillHoles.value = res.data || []
    } catch (error) {
      console.error('Failed to fetch drill holes:', error)
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

  return {
    // State
    layers,
    drillHoles,
    calculationResults,
    currentModel,
    loading,
    // Getters
    totalLayers,
    totalDrillHoles,
    totalPowerPotential,
    // Actions
    fetchLayers,
    fetchDrillHoles,
    fetchResults,
    quickCalculate,
  }
})
