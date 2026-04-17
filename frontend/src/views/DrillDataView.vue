<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { drillHolesApi, importApi, drillHoleDetailApi } from '@/api/get-api.ts'
import { useGeothermalStore } from '@/stores/geothermal'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'

const store = useGeothermalStore()

// ==================== 页面状态 ====================
const loading = ref(false)
const activeTab = ref('list')
const drillHoles = ref<any[]>([])
const selectedDrillHole = ref<any>(null)
const detailData = ref<any>(null)

// 分页状态
const currentPage = ref(1)
const pageSize = ref(10)
const pageSizes = [5, 10, 20, 50]

// ==================== 导入相关 ====================
const importType = ref('drill_info')
const uploading = ref(false)
const previewData = ref<any>(null)
const importResult = ref<any>(null)
const fileList = ref<UploadFile[]>([])

const importTypes = [
  { value: 'drill_info', label: '钻孔空间信息', description: '钻孔编号、坐标、深度等基本信息', icon: 'Aim' }
]

// ==================== 手动输入表单 ====================
const dialogVisible = ref(false)
const editingItem = ref<any>(null)
const form = ref({
  activeTab: 'basic',
  // 钻孔基本信息
  hole_id: '',
  hole_name: '',
  location_x: 0,
  location_y: 0,
  elevation: 0,
  total_depth: 0,
  final_depth: null as number | null,
  diameter: null as number | null,
  drill_company: '',
  drill_start_date: '',
  drill_end_date: '',
  status: '完成',
  description: '',
  // 关联数据
  layers: [] as any[],
  temperature_curves: [] as any[],
  pressure_data: [] as any[],
  porosity_data: [] as any[]
})

// 测温数据手动输入
const tempDialogVisible = ref(false)
const tempForm = ref({
  id: null as number | null,
  drill_hole_id: 0,
  depth: 0,
  temperature: 0,
  gradient: null as number | null,
  measure_date: '',
  measure_type: '稳态测温'
})

// 分层数据手动输入
const layerDialogVisible = ref(false)
const layerForm = ref({
  id: null as number | null,
  drill_hole_id: 0,
  layer_no: 1,
  layer_name: '',
  layer_type: '',
  depth_top: 0,
  depth_bottom: 0,
  lithology: '',
  porosity: null as number | null,
  permeability: null as number | null
})

// 压力数据手动输入
const pressureDialogVisible = ref(false)
const pressureForm = ref({
  id: null as number | null,
  drill_hole_id: 0,
  measure_date: '',
  measure_time: '',
  wellhead_pressure: null as number | null,
  reservoir_pressure: null as number | null,
  flowing_pressure: null as number | null,
  shut_in_pressure: null as number | null,
  pressure_gradient: null as number | null,
  measure_depth: null as number | null,
  flow_rate: null as number | null,
  water_level: null as number | null,
  instrument: '',
  description: ''
})

// 孔隙度数据手动输入
const porosityDialogVisible = ref(false)
const porosityForm = ref({
  id: null as number | null,
  drill_hole_id: 0,
  sample_no: '',
  sample_date: '',
  depth_top: null as number | null,
  depth_bottom: null as number | null,
  depth: null as number | null,
  lithology: '',
  rock_type: '',
  porosity_total: null as number | null,
  porosity_effective: null as number | null,
  permeability: null as number | null,
  permeability_horizontal: null as number | null,
  permeability_vertical: null as number | null,
  density_bulk: null as number | null,
  density_grain: null as number | null,
  water_saturation: null as number | null,
  test_method: '',
  laboratory: '',
  description: ''
})

// ==================== 数据加载 ====================
const loadDrillHoles = async () => {
  loading.value = true
  try {
    const res = await drillHolesApi.getAll()
    drillHoles.value = res.data || []
    // 同步到store
    store.updateDrillHoles(drillHoles.value.map((d: any) => ({
      id: d.id,
      name: d.hole_name || d.hole_id,
      location_x: d.location_x,
      location_y: d.location_y,
      location_z: d.elevation,
      depth: d.total_depth,
      temperature: 0,
      gradient: 6.0,
      description: d.description
    })))
  } catch (error) {
    console.error('加载失败:', error)
    // 使用模拟数据
    drillHoles.value = [
      { id: 1, hole_id: 'ZK-001', hole_name: '钻孔001', location_x: 374.5, location_y: 20.6, elevation: 42.4, total_depth: 1150.7, final_depth: 1150.7, diameter: 150, drill_company: '地质勘探一队', drill_start_date: '2023-03-01', drill_end_date: '2023-06-15', status: '完成', description: '合成钻孔数据 #1' },
      { id: 2, hole_id: 'ZK-002', hole_name: '钻孔002', location_x: 950.7, location_y: 969.9, elevation: 49.9, total_depth: 725.5, final_depth: 725.5, diameter: 150, drill_company: '地质勘探一队', drill_start_date: '2023-04-01', drill_end_date: '2023-07-01', status: '完成', description: '合成钻孔数据 #2' },
      { id: 3, hole_id: 'ZK-003', hole_name: '钻孔003', location_x: 732.0, location_y: 832.4, elevation: 40.7, total_depth: 862.9, final_depth: 862.9, diameter: 150, drill_company: '地质勘探二队', drill_start_date: '2023-05-01', drill_end_date: '2023-08-15', status: '完成', description: '合成钻孔数据 #3' },
      { id: 4, hole_id: 'ZK-004', hole_name: '钻孔004', location_x: 598.7, location_y: 212.3, elevation: 58.2, total_depth: 929.7, final_depth: 929.7, diameter: 150, drill_company: '地质勘探二队', drill_start_date: '2023-06-01', drill_end_date: '2023-09-01', status: '完成', description: '合成钻孔数据 #4' },
      { id: 5, hole_id: 'ZK-005', hole_name: '钻孔005', location_x: 156.0, location_y: 181.8, elevation: 45.2, total_depth: 1010.5, final_depth: 1010.5, diameter: 150, drill_company: '地质勘探三队', drill_start_date: '2023-07-01', drill_end_date: '2023-10-15', status: '完成', description: '合成钻孔数据 #5' }
    ]
    store.updateDrillHoles(drillHoles.value.map((d: any) => ({
      id: d.id,
      name: d.hole_name || d.hole_id,
      location_x: d.location_x,
      location_y: d.location_y,
      location_z: d.elevation,
      depth: d.total_depth,
      temperature: 0,
      gradient: 6.0,
      description: ''
    })))
  } finally {
    loading.value = false
  }
}

const loadDrillHoleDetail = async (id: number) => {
  try {
    const res = await drillHoleDetailApi.getDetail(id)
    detailData.value = res.data
    selectedDrillHole.value = res.data.drill_hole
    
    // 计算平均温度和梯度
    const tempCurves = res.data.temperature_curves || []
    if (tempCurves.length > 0) {
      const avgTemp = tempCurves.reduce((sum: number, t: any) => sum + t.temperature, 0) / tempCurves.length
      const avgGradient = tempCurves.reduce((sum: number, t: any) => sum + (t.gradient || 0), 0) / tempCurves.length
      
      // 更新store中的钻孔数据
      store.updateDrillHoles(store.drillHoles.map((d: any) => 
        d.id === id ? { ...d, temperature: avgTemp, gradient: avgGradient || 6.0 } : d
      ))
    }
  } catch (error) {
    console.error('加载详情失败:', error)
    ElMessage.warning('加载钻孔详情失败')
  }
}

// ==================== 手动输入操作 ====================
// 添加分层数据
const addLayer = () => {
  form.value.layers.push({
    layer_no: form.value.layers.length + 1,
    layer_name: '',
    layer_type: '',
    depth_top: 0,
    depth_bottom: 0,
    lithology: '',
    porosity: null,
    permeability: null
  })
}

// 移除分层数据
const removeLayer = (index: number) => {
  form.value.layers.splice(index, 1)
  // 重新编号
  form.value.layers.forEach((layer, idx) => {
    layer.layer_no = idx + 1
  })
}

// 添加测温数据
const addTemperature = () => {
  form.value.temperature_curves.push({
    depth: 0,
    temperature: 0,
    gradient: null,
    measure_date: '',
    measure_type: '稳态测温'
  })
}

// 移除测温数据
const removeTemperature = (index: number) => {
  form.value.temperature_curves.splice(index, 1)
}

// 添加压力数据
const addPressure = () => {
  form.value.pressure_data.push({
    measure_date: '',
    wellhead_pressure: null,
    reservoir_pressure: null,
    flow_rate: null,
    water_level: null
  })
}

// 移除压力数据
const removePressure = (index: number) => {
  form.value.pressure_data.splice(index, 1)
}

// 添加孔隙度数据
const addPorosity = () => {
  form.value.porosity_data.push({
    sample_no: '',
    depth: 0,
    lithology: '',
    porosity_total: null,
    permeability: null
  })
}

// 移除孔隙度数据
const removePorosity = (index: number) => {
  form.value.porosity_data.splice(index, 1)
}

const handleAdd = () => {
  editingItem.value = null
  form.value = {
    activeTab: 'basic',
    hole_id: '',
    hole_name: '',
    location_x: 0,
    location_y: 0,
    elevation: 0,
    total_depth: 0,
    final_depth: null,
    diameter: null,
    drill_company: '',
    drill_start_date: '',
    drill_end_date: '',
    status: '完成',
    description: '',
    layers: [],
    temperature_curves: [],
    pressure_data: [],
    porosity_data: []
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  editingItem.value = row
  form.value = {
    ...row,
    activeTab: 'basic',
    layers: [],
    temperature_curves: [],
    pressure_data: [],
    porosity_data: []
  }
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  try {
    await drillHolesApi.delete(id)
    ElMessage.success('删除成功')
    loadDrillHoles()
  } catch (error) {
    // 本地删除
    drillHoles.value = drillHoles.value.filter(d => d.id !== id)
    store.updateDrillHoles(store.drillHoles.filter((d: any) => d.id !== id))
    ElMessage.success('删除成功')
  }
}

const handleSubmit = async () => {
  try {
    // 新建钻孔时提交完整数据
    if (!editingItem.value) {
      // 准备提交数据
      const submitData = {
        drill_hole: {
          hole_id: form.value.hole_id,
          hole_name: form.value.hole_name,
          location_x: form.value.location_x,
          location_y: form.value.location_y,
          elevation: form.value.elevation,
          total_depth: form.value.total_depth,
          final_depth: form.value.final_depth,
          diameter: form.value.diameter,
          drill_company: form.value.drill_company,
          drill_start_date: form.value.drill_start_date,
          drill_end_date: form.value.drill_end_date,
          status: form.value.status,
          description: form.value.description
        },
        layers: form.value.layers.length > 0 ? form.value.layers : undefined,
        temperature_curves: form.value.temperature_curves.length > 0 ? form.value.temperature_curves : undefined,
        pressure_data: form.value.pressure_data.length > 0 ? form.value.pressure_data : undefined,
        porosity_data: form.value.porosity_data.length > 0 ? form.value.porosity_data : undefined
      }
      
      // 提交到新 API 端点
      const response = await fetch('http://localhost:5000/api/drill-holes/with-details', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData)
      })
      
      if (response.ok) {
        ElMessage.success('钻孔及其关联数据创建成功')
        dialogVisible.value = false
        loadDrillHoles()
      } else {
        throw new Error('创建失败')
      }
    } else {
      // 编辑钻孔只更新基本信息
      await drillHolesApi.update(editingItem.value.id, form.value)
      ElMessage.success('更新成功')
      dialogVisible.value = false
      loadDrillHoles()
    }
  } catch (error) {
    // 本地添加
    const newId = Math.max(...drillHoles.value.map(d => d.id || 0), 0) + 1
    const newHole = { id: newId, ...form.value }
    drillHoles.value.push(newHole)
    store.updateDrillHoles([...store.drillHoles, {
      id: newId,
      name: form.value.hole_name || form.value.hole_id,
      location_x: form.value.location_x,
      location_y: form.value.location_y,
      location_z: form.value.elevation,
      depth: form.value.total_depth,
      temperature: 0,
      gradient: 6.0,
      description: form.value.description
    }])
    dialogVisible.value = false
    ElMessage.success(editingItem.value ? '更新成功' : '创建成功')
  }
}

// 添加测温数据
const handleAddTemperature = (drillHoleId: number) => {
  tempForm.value = {
    id: null,
    drill_hole_id: drillHoleId,
    depth: 0,
    temperature: 0,
    gradient: null,
    measure_date: '',
    measure_type: '稳态测温'
  }
  tempDialogVisible.value = true
}

const handleSubmitTemperature = async () => {
  // 简化处理：直接更新本地数据
  if (detailData.value) {
    const index = detailData.value.temperature_curves.findIndex((t: any) => t.id === tempForm.value.id)
    if (index >= 0) {
      // 编辑模式：更新现有数据
      detailData.value.temperature_curves[index] = {
        id: tempForm.value.id,
        drill_hole_id: tempForm.value.drill_hole_id,
        depth: tempForm.value.depth,
        temperature: tempForm.value.temperature,
        gradient: tempForm.value.gradient || 0,
        measure_type: tempForm.value.measure_type,
        measure_date: tempForm.value.measure_date
      }
    } else {
      // 新增模式
      const newTemp = {
        id: Date.now(),
        drill_hole_id: tempForm.value.drill_hole_id,
        depth: tempForm.value.depth,
        temperature: tempForm.value.temperature,
        gradient: tempForm.value.gradient || 0,
        measure_type: tempForm.value.measure_type,
        measure_date: tempForm.value.measure_date,
        created_at: new Date().toISOString()
      }
      detailData.value.temperature_curves.push(newTemp)
    }

    // 更新store中的温度数据
    const avgTemp = detailData.value.temperature_curves.reduce((sum: number, t: any) => sum + t.temperature, 0) / detailData.value.temperature_curves.length
    store.updateDrillHoles(store.drillHoles.map((d: any) =>
      d.id === tempForm.value.drill_hole_id ? { ...d, temperature: avgTemp } : d
    ))
  }
  tempDialogVisible.value = false
  ElMessage.success('保存成功')
}

// 添加分层数据
const handleAddLayer = (drillHoleId: number) => {
  layerForm.value = {
    id: null,
    drill_hole_id: drillHoleId,
    layer_no: (detailData.value?.layers?.length || 0) + 1,
    layer_name: '',
    layer_type: '',
    depth_top: 0,
    depth_bottom: 0,
    lithology: '',
    porosity: null,
    permeability: null
  }
  layerDialogVisible.value = true
}

const handleSubmitLayer = async () => {
  if (detailData.value) {
    const index = detailData.value.layers.findIndex((l: any) => l.id === layerForm.value.id)
    if (index >= 0) {
      // 编辑模式：更新现有数据
      detailData.value.layers[index] = {
        id: layerForm.value.id,
        drill_hole_id: layerForm.value.drill_hole_id,
        layer_no: layerForm.value.layer_no,
        layer_name: layerForm.value.layer_name,
        layer_type: layerForm.value.layer_type,
        depth_top: layerForm.value.depth_top,
        depth_bottom: layerForm.value.depth_bottom,
        lithology: layerForm.value.lithology,
        porosity: layerForm.value.porosity,
        permeability: layerForm.value.permeability,
        thickness: layerForm.value.depth_bottom - layerForm.value.depth_top
      }
    } else {
      // 新增模式
      const newLayer = {
        id: Date.now(),
        drill_hole_id: layerForm.value.drill_hole_id,
        layer_no: layerForm.value.layer_no,
        layer_name: layerForm.value.layer_name,
        layer_type: layerForm.value.layer_type,
        depth_top: layerForm.value.depth_top,
        depth_bottom: layerForm.value.depth_bottom,
        lithology: layerForm.value.lithology,
        porosity: layerForm.value.porosity,
        permeability: layerForm.value.permeability,
        thickness: layerForm.value.depth_bottom - layerForm.value.depth_top,
        created_at: new Date().toISOString()
      }
      detailData.value.layers.push(newLayer)

      // 同步到地质层store
      if (layerForm.value.porosity) {
        const existingLayer = store.layers.find((l: any) => l.name === layerForm.value.layer_name)
        if (!existingLayer) {
          store.updateLayers([...store.layers, {
            id: Date.now(),
            name: layerForm.value.layer_name,
            layer_type: layerForm.value.layer_type,
            depth_top: layerForm.value.depth_top,
            depth_bottom: layerForm.value.depth_bottom,
            porosity: layerForm.value.porosity / 100,
            permeability: layerForm.value.permeability || 0,
            thermal_conductivity: 2.5,
            color: '#FFD700'
          }])
        }
      }
    }
  }
  layerDialogVisible.value = false
  ElMessage.success('保存成功')
}

// 编辑分层数据
const handleEditLayer = (row: any) => {
  layerForm.value = { ...row }
  layerDialogVisible.value = true
}

// 删除分层数据
const handleDeleteLayer = (id: number) => {
  if (detailData.value) {
    const index = detailData.value.layers.findIndex((l: any) => l.id === id)
    if (index >= 0) {
      detailData.value.layers.splice(index, 1)
      // 重新排序层号
      detailData.value.layers.forEach((layer: any, idx: number) => {
        layer.layer_no = idx + 1
      })
      ElMessage.success('删除成功')
    }
  }
}

// 添加压力数据
const handleAddPressure = (drillHoleId: number) => {
  pressureForm.value = {
    id: null,
    drill_hole_id: drillHoleId,
    measure_date: '',
    measure_time: '',
    wellhead_pressure: null,
    reservoir_pressure: null,
    flowing_pressure: null,
    shut_in_pressure: null,
    pressure_gradient: null,
    measure_depth: null,
    flow_rate: null,
    water_level: null,
    instrument: '',
    description: ''
  }
  pressureDialogVisible.value = true
}

const handleSubmitPressure = async () => {
  if (detailData.value) {
    const index = detailData.value.pressure_data.findIndex((p: any) => p.id === pressureForm.value.id)
    if (index >= 0) {
      // 编辑模式：更新现有数据
      detailData.value.pressure_data[index] = {
        id: pressureForm.value.id,
        drill_hole_id: pressureForm.value.drill_hole_id,
        measure_date: pressureForm.value.measure_date,
        measure_time: pressureForm.value.measure_time,
        wellhead_pressure: pressureForm.value.wellhead_pressure,
        reservoir_pressure: pressureForm.value.reservoir_pressure,
        flowing_pressure: pressureForm.value.flowing_pressure,
        shut_in_pressure: pressureForm.value.shut_in_pressure,
        pressure_gradient: pressureForm.value.pressure_gradient,
        measure_depth: pressureForm.value.measure_depth,
        flow_rate: pressureForm.value.flow_rate,
        water_level: pressureForm.value.water_level,
        instrument: pressureForm.value.instrument,
        description: pressureForm.value.description
      }
    } else {
      // 新增模式
      const newPressure = {
        id: Date.now(),
        drill_hole_id: pressureForm.value.drill_hole_id,
        measure_date: pressureForm.value.measure_date,
        measure_time: pressureForm.value.measure_time,
        wellhead_pressure: pressureForm.value.wellhead_pressure,
        reservoir_pressure: pressureForm.value.reservoir_pressure,
        flowing_pressure: pressureForm.value.flowing_pressure,
        shut_in_pressure: pressureForm.value.shut_in_pressure,
        pressure_gradient: pressureForm.value.pressure_gradient,
        measure_depth: pressureForm.value.measure_depth,
        flow_rate: pressureForm.value.flow_rate,
        water_level: pressureForm.value.water_level,
        instrument: pressureForm.value.instrument,
        description: pressureForm.value.description,
        created_at: new Date().toISOString()
      }
      detailData.value.pressure_data.push(newPressure)
    }
  }
  pressureDialogVisible.value = false
  ElMessage.success('保存成功')
}

// 添加孔隙度数据
const handleAddPorosity = (drillHoleId: number) => {
  porosityForm.value = {
    id: null,
    drill_hole_id: drillHoleId,
    sample_no: '',
    sample_date: '',
    depth_top: null,
    depth_bottom: null,
    depth: null,
    lithology: '',
    rock_type: '',
    porosity_total: null,
    porosity_effective: null,
    permeability: null,
    permeability_horizontal: null,
    permeability_vertical: null,
    density_bulk: null,
    density_grain: null,
    water_saturation: null,
    test_method: '',
    laboratory: '',
    description: ''
  }
  porosityDialogVisible.value = true
}

const handleSubmitPorosity = async () => {
  if (detailData.value) {
    const index = detailData.value.porosity_data.findIndex((p: any) => p.id === porosityForm.value.id)
    if (index >= 0) {
      // 编辑模式：更新现有数据
      detailData.value.porosity_data[index] = {
        id: porosityForm.value.id,
        drill_hole_id: porosityForm.value.drill_hole_id,
        sample_no: porosityForm.value.sample_no,
        sample_date: porosityForm.value.sample_date,
        depth_top: porosityForm.value.depth_top,
        depth_bottom: porosityForm.value.depth_bottom,
        depth: porosityForm.value.depth,
        lithology: porosityForm.value.lithology,
        rock_type: porosityForm.value.rock_type,
        porosity_total: porosityForm.value.porosity_total,
        porosity_effective: porosityForm.value.porosity_effective,
        permeability: porosityForm.value.permeability,
        permeability_horizontal: porosityForm.value.permeability_horizontal,
        permeability_vertical: porosityForm.value.permeability_vertical,
        density_bulk: porosityForm.value.density_bulk,
        density_grain: porosityForm.value.density_grain,
        water_saturation: porosityForm.value.water_saturation,
        test_method: porosityForm.value.test_method,
        laboratory: porosityForm.value.laboratory,
        description: porosityForm.value.description
      }
    } else {
      // 新增模式
      const newPorosity = {
        id: Date.now(),
        drill_hole_id: porosityForm.value.drill_hole_id,
        sample_no: porosityForm.value.sample_no,
        sample_date: porosityForm.value.sample_date,
        depth_top: porosityForm.value.depth_top,
        depth_bottom: porosityForm.value.depth_bottom,
        depth: porosityForm.value.depth,
        lithology: porosityForm.value.lithology,
        rock_type: porosityForm.value.rock_type,
        porosity_total: porosityForm.value.porosity_total,
        porosity_effective: porosityForm.value.porosity_effective,
        permeability: porosityForm.value.permeability,
        permeability_horizontal: porosityForm.value.permeability_horizontal,
        permeability_vertical: porosityForm.value.permeability_vertical,
        density_bulk: porosityForm.value.density_bulk,
        density_grain: porosityForm.value.density_grain,
        water_saturation: porosityForm.value.water_saturation,
        test_method: porosityForm.value.test_method,
        laboratory: porosityForm.value.laboratory,
        description: porosityForm.value.description,
        created_at: new Date().toISOString()
      }
      detailData.value.porosity_data.push(newPorosity)
    }
  }
  porosityDialogVisible.value = false
  ElMessage.success('保存成功')
}

// 编辑压力数据
const handleEditPressure = (row: any) => {
  pressureForm.value = { ...row }
  pressureDialogVisible.value = true
}

// 删除压力数据
const handleDeletePressure = (id: number) => {
  if (detailData.value) {
    detailData.value.pressure_data = detailData.value.pressure_data.filter((p: any) => p.id !== id)
    ElMessage.success('删除成功')
  }
}

// 编辑孔隙度数据
const handleEditPorosity = (row: any) => {
  porosityForm.value = { ...row }
  porosityDialogVisible.value = true
}

// 删除孔隙度数据
const handleDeletePorosity = (id: number) => {
  if (detailData.value) {
    detailData.value.porosity_data = detailData.value.porosity_data.filter((p: any) => p.id !== id)
    ElMessage.success('删除成功')
  }
}

// 编辑测温数据
const handleEditTemperature = (row: any) => {
  tempForm.value = {
    id: row.id,
    drill_hole_id: row.drill_hole_id,
    depth: row.depth,
    temperature: row.temperature,
    gradient: row.gradient || 0,
    measure_type: row.measure_type || '稳态测温',
    measure_date: row.measure_date || new Date().toISOString().split('T')[0]
  }
  tempDialogVisible.value = true
}

// 删除测温数据
const handleDeleteTemperature = (id: number) => {
  if (detailData.value) {
    detailData.value.temperature_curves = detailData.value.temperature_curves.filter((t: any) => t.id !== id)
    ElMessage.success('删除成功')
  }
}

// ==================== 导入操作 ====================
const previewColumns = computed(() => {
  if (!previewData.value?.columns) return []
  return previewData.value.columns.map((col: string) => ({
    prop: col,
    label: col,
    minWidth: 120
  }))
})

const handleFileChange = async (file: UploadFile) => {
  if (!file.raw) return
  previewData.value = null
  importResult.value = null
  
  try {
    const res = await importApi.preview(file.raw)
    if (res.data.success) {
      previewData.value = res.data
      ElMessage.success(`成功读取 ${res.data.total_rows} 行数据`)
    } else {
      ElMessage.error(res.data.message || '预览失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '预览失败')
  }
}

const downloadTemplate = () => {
  const url = importApi.downloadTemplate(importType.value)
  window.open(url, '_blank')
}

const executeImport = async () => {
  if (!fileList.value[0]?.raw) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }
  
  uploading.value = true
  importResult.value = null
  
  try {
    let res
    const file = fileList.value[0].raw
    
    switch (importType.value) {
      case 'drill_info': res = await importApi.importDrillInfo(file); break
      case 'layers': res = await importApi.importLayers(file); break
      case 'temperature': res = await importApi.importTemperature(file); break
      case 'pressure': res = await importApi.importPressure(file); break
      case 'porosity': res = await importApi.importPorosity(file); break
      default: throw new Error('未知的导入类型')
    }
    
    if (res.data.success) {
      importResult.value = res.data
      ElMessage.success(res.data.message)
      fileList.value = []
      previewData.value = null
      loadDrillHoles()
    } else {
      importResult.value = res.data
      ElMessage.error(res.data.message)
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    uploading.value = false
  }
}

const clearImportData = () => {
  fileList.value = []
  previewData.value = null
  importResult.value = null
}

const beforeUpload = (file: File) => {
  if (!file.name.endsWith('.csv')) {
    ElMessage.error('只能上传CSV文件')
    return false
  }
  return true
}

// ==================== 选择钻孔 ====================
const selectDrillHole = (row: any) => {
  selectedDrillHole.value = row
  loadDrillHoleDetail(row.id)
}

const goBack = () => {
  selectedDrillHole.value = null
  detailData.value = null
}

// ==================== 分页计算 ====================
const paginatedDrillHoles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return drillHoles.value.slice(start, end)
})

const handlePageChange = (page: number) => {
  currentPage.value = page
}

const handleSizeChange = (size: number) => {
  pageSize.value = size
  currentPage.value = 1
}

// ==================== 图表相关 ====================
// 图表实例
const chartRef = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null

// 初始化/更新图表
const initChart = () => {
  if (!chartRef.value) return
  
  // 确保钻孔数据已加载
  if (drillHoles.value.length === 0) {
    console.log('等待钻孔数据加载...')
    return
  }
  
  // 销毁旧实例
  if (myChart) {
    myChart.dispose()
    myChart = null
  }
  
  // 从 drillHoles 获取动态数据
  const xData = drillHoles.value.map((d: any) => d.hole_name || d.hole_id)
  const yData = drillHoles.value.map((d: any) => d.total_depth || 0)
  const yData2 = drillHoles.value.map((d: any) => d.elevation || 0)

  // 初始化图表
  myChart = echarts.init(chartRef.value)

  // 多图表配置
  const option = {
    title: {
      text: '钻孔数据可视化',
      left: 'center'
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const idx = params[0].dataIndex
        const hole = drillHoles.value[idx]
        let result = `<div style="font-weight:bold;margin-bottom:5px;">${params[0].axisValue}</div>`
        result += `<div style="color:#909399;margin:2px 0;">X坐标: <b>${hole?.location_x ?? '-'}</b> m</div>`
        result += `<div style="color:#909399;margin:2px 0;">Y坐标: <b>${hole?.location_y ?? '-'}</b> m</div>`
        result += `<div style="border-top:1px solid #eee;margin-top:5px;padding-top:5px;">`
        params.forEach((param: any) => {
          result += `<div style="margin:2px 0;">${param.marker} ${param.seriesName}: <b>${param.value}</b> m</div>`
        })
        result += `</div>`
        return result
      }
    },
    legend: {
      data: ['钻孔深度', '地面高程'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '80px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: xData,
      axisLabel: {
        interval: 0,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      name: '数值'
    },
    series: [
      {
        name: '钻孔深度',
        type: 'bar',
        data: yData,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '地面高程',
        type: 'bar',
        data: yData2,
        itemStyle: { color: '#67C23A' }
      }
    ]
  }

  myChart.setOption(option)
}

// 监听 activeTab，切换到可视化时初始化图表
watch(activeTab, (newTab) => {
  if (newTab === 'visualization') {
    // 等待 DOM 更新后再初始化图表
    setTimeout(() => {
      initChart()
    }, 100)
  }
})

// 窗口变化自适应
const resizeChart = () => {
  myChart?.resize()
}

onMounted(() => {
  loadDrillHoles()
  window.addEventListener('resize', resizeChart)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeChart)
  if (myChart) {
    myChart.dispose()
    myChart = null
  }
})
</script>

<template>
  <div class="drill-data-view">
    <h1 class="page-title">钻孔数据管理</h1>
    
    <!-- 钻孔列表视图 -->
    <template v-if="!selectedDrillHole">
      <el-tabs v-model="activeTab" class="main-tabs">
        <!-- 钻孔列表 -->
        <el-tab-pane label="钻孔列表" name="list">
          <div class="card">
            <div class="toolbar">
              <el-button type="primary" @click="handleAdd">
                <el-icon><Plus /></el-icon>
                新建钻孔
              </el-button>
              <el-button @click="loadDrillHoles">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>

            <el-table :data="paginatedDrillHoles" v-loading="loading" stripe @row-click="selectDrillHole">
              <el-table-column prop="hole_id" label="钻孔编号" width="100" fixed />
              <el-table-column prop="hole_name" label="钻孔名称" width="120" />
              <el-table-column label="空间坐标" align="center">
                <el-table-column prop="location_x" label="X(m)" width="90" />
                <el-table-column prop="location_y" label="Y(m)" width="90" />
                <el-table-column prop="elevation" label="高程(m)" width="90" />
              </el-table-column>
              <el-table-column label="深度信息" align="center">
                <el-table-column prop="total_depth" label="总深(m)" width="90" />
                <el-table-column prop="final_depth" label="终孔深(m)" width="95" />
                <el-table-column prop="diameter" label="孔径(mm)" width="90" />
              </el-table-column>
              <el-table-column label="施工信息" align="center">
                <el-table-column prop="drill_company" label="施工单位" width="130" show-overflow-tooltip />
                <el-table-column prop="drill_start_date" label="开孔日期" width="100" />
                <el-table-column prop="drill_end_date" label="终孔日期" width="100" />
              </el-table-column>
              <el-table-column prop="status" label="状态" width="80">
                <template #default="{ row }">
                  <el-tag :type="row.status === '完成' ? 'success' : 'warning'">{{ row.status }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" fixed="right" width="150">
                <template #default="{ row }">
                  <el-button type="primary" link @click.stop="selectDrillHole(row)">详情</el-button>
                  <el-button type="primary" link @click.stop="handleEdit(row)">编辑</el-button>
                  <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
                    <template #reference>
                      <el-button type="danger" link @click.stop>删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页组件 -->
            <div class="pagination-container">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="pageSizes"
                :total="drillHoles.length"
                layout="total, sizes, prev, pager, next, jumper"
                @current-change="handlePageChange"
                @size-change="handleSizeChange"
              />
            </div>

            <!-- 钻孔位置图 -->
            <div class="map-section">
              <h3>钻孔位置分布</h3>
              <div class="map-container">
                <div 
                  v-for="dh in drillHoles" 
                  :key="dh.id"
                  class="drill-marker"
                  :style="{ 
                    left: `${(dh.location_x / Math.max(...drillHoles.map(d => d.location_x || 1))) * 90 + 5}%`,
                    top: `${(dh.location_y / Math.max(...drillHoles.map(d => d.location_y || 1))) * 90 + 5}%`
                  }"
                  @click="selectDrillHole(dh)"
                >
                  <el-tooltip :content="`${dh.hole_id}: ${dh.hole_name}`">
                    <el-icon :size="28" color="#409eff"><Aim /></el-icon>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 数据导入 -->
        <el-tab-pane label="数据导入" name="import">
          <div class="card">
            <h3 class="card-title">📂 选择导入类型</h3>
            <el-radio-group v-model="importType" class="type-radio-group" @change="clearImportData">
              <el-radio-button v-for="type in importTypes" :key="type.value" :value="type.value">
                <div class="type-option">
                  <el-icon><component :is="type.icon" /></el-icon>
                  <span>{{ type.label }}</span>
                </div>
              </el-radio-button>
            </el-radio-group>

            <div class="upload-section">
              <div class="upload-header">
                <h3>📤 上传CSV文件</h3>
                <el-button type="primary" plain @click="downloadTemplate">
                  <el-icon><Download /></el-icon>
                  下载模板
                </el-button>
              </div>
              
              <el-upload
                v-model:file-list="fileList"
                class="upload-area"
                drag
                :auto-upload="false"
                :limit="1"
                accept=".csv"
                :before-upload="beforeUpload"
                @change="handleFileChange"
              >
                <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                <div class="el-upload__text">拖拽CSV文件到此处，或<em>点击上传</em></div>
              </el-upload>
            </div>

            <!-- 数据预览 -->
            <div v-if="previewData?.success" class="preview-section">
              <h3>👀 数据预览 (共{{ previewData.total_rows }}行)</h3>
              <el-table :data="previewData.rows" border stripe max-height="300">
                <el-table-column v-for="col in previewColumns" :key="col.prop" :prop="col.prop" :label="col.label" :min-width="col.minWidth" show-overflow-tooltip />
              </el-table>
              
              <div class="action-buttons">
                <el-button type="primary" size="large" @click="executeImport" :loading="uploading">
                  <el-icon><Upload /></el-icon>
                  开始导入
                </el-button>
                <el-button size="large" @click="clearImportData">清空</el-button>
              </div>
            </div>

            <!-- 导入结果 -->
            <div v-if="importResult" class="result-section">
              <el-result :icon="importResult.success ? 'success' : 'warning'" :title="importResult.success ? '导入完成' : '部分导入成功'" :sub-title="importResult.message">
                <template #extra>
                  <el-descriptions :column="3" border>
                    <el-descriptions-item label="总行数">{{ importResult.total_rows }}</el-descriptions-item>
                    <el-descriptions-item label="成功"><el-tag type="success">{{ importResult.success_rows }}</el-tag></el-descriptions-item>
                    <el-descriptions-item label="失败"><el-tag :type="importResult.failed_rows > 0 ? 'danger' : 'success'">{{ importResult.failed_rows }}</el-tag></el-descriptions-item>
                  </el-descriptions>
                </template>
              </el-result>
            </div>
          </div>
        </el-tab-pane>

        <!-- 数据可视化 -->
        <el-tab-pane label="数据可视化" name="visualization">
          <div class="card">
            <h3 class="card-title">钻孔数据可视化</h3>
            <!-- 柱状图容器 -->
           <div ref="chartRef" class="chart-container"></div>
          </div>
        </el-tab-pane>
      </el-tabs>


    </template>

    <!-- 钻孔详情视图 -->
    <template v-else>
      <div class="card detail-card">
        <div class="detail-header">
          <el-button @click="goBack" circle>
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          <h2>{{ selectedDrillHole.hole_id }} - {{ selectedDrillHole.hole_name }}</h2>
        </div>

        <el-descriptions :column="4" border>
          <el-descriptions-item label="钻孔编号">{{ selectedDrillHole.hole_id }}</el-descriptions-item>
          <el-descriptions-item label="钻孔名称">{{ selectedDrillHole.hole_name }}</el-descriptions-item>
          <el-descriptions-item label="X坐标">{{ selectedDrillHole.location_x }} m</el-descriptions-item>
          <el-descriptions-item label="Y坐标">{{ selectedDrillHole.location_y }} m</el-descriptions-item>
          <el-descriptions-item label="地面高程">{{ selectedDrillHole.elevation }} m</el-descriptions-item>
          <el-descriptions-item label="钻孔总深">{{ selectedDrillHole.total_depth }} m</el-descriptions-item>
          <el-descriptions-item label="终孔深度">{{ selectedDrillHole.final_depth || '-' }} m</el-descriptions-item>
          <el-descriptions-item label="孔径">{{ selectedDrillHole.diameter || '-' }} mm</el-descriptions-item>
          <el-descriptions-item label="施工单位">{{ selectedDrillHole.drill_company || '-' }}</el-descriptions-item>
          <el-descriptions-item label="开孔日期">{{ selectedDrillHole.drill_start_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="终孔日期">{{ selectedDrillHole.drill_end_date || '-' }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="selectedDrillHole.status === '完成' ? 'success' : 'warning'">{{ selectedDrillHole.status }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="备注" :span="4">{{ selectedDrillHole.description || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 子数据表 -->
        <el-tabs class="detail-tabs">
          <!-- 测温曲线 -->
          <el-tab-pane>
            <template #label>
              <span><el-icon><TrendCharts /></el-icon> 测温曲线 ({{ detailData?.temperature_curves?.length || 0 }})</span>
            </template>
            <div class="sub-toolbar">
              <el-button type="primary" size="small" @click="handleAddTemperature(selectedDrillHole.id)">
                <el-icon><Plus /></el-icon>
                添加测温数据
              </el-button>
            </div>
            <el-table :data="detailData?.temperature_curves || []" border stripe size="small">
              <el-table-column prop="depth" label="深度(m)" width="100" />
              <el-table-column prop="temperature" label="温度(°C)" width="100" />
              <el-table-column prop="gradient" label="梯度(°C/100m)" width="140" />
              <el-table-column prop="measure_type" label="测量类型" width="120" />
              <el-table-column prop="measure_date" label="测量日期" width="120" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="handleEditTemperature(row)">编辑</el-button>
                  <el-popconfirm title="确定删除？" @confirm="handleDeleteTemperature(row.id)">
                    <template #reference>
                      <el-button type="danger" link size="small">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 热储层分层 -->
          <el-tab-pane>
            <template #label>
              <span><el-icon><DataLine /></el-icon> 地层分层 ({{ detailData?.layers?.length || 0 }})</span>
            </template>
            <div class="sub-toolbar">
              <el-button type="primary" size="small" @click="handleAddLayer(selectedDrillHole.id)">
                <el-icon><Plus /></el-icon>
                添加分层
              </el-button>
            </div>
            <el-table :data="detailData?.layers || []" border stripe size="small">
              <el-table-column prop="layer_no" label="层号" width="80" />
              <el-table-column prop="layer_name" label="地层名称" width="150" />
              <el-table-column prop="layer_type" label="类型" width="100" />
              <el-table-column prop="depth_top" label="顶深(m)" width="100" />
              <el-table-column prop="depth_bottom" label="底深(m)" width="100" />
              <el-table-column prop="thickness" label="厚度(m)" width="100" />
              <el-table-column prop="lithology" label="岩性" min-width="150" />
              <el-table-column prop="porosity" label="孔隙度" width="100">
                <template #default="{ row }">{{ row.porosity ? (row.porosity * 100).toFixed(1) + '%' : '-' }}</template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="handleEditLayer(row)">编辑</el-button>
                  <el-popconfirm title="确定删除？" @confirm="handleDeleteLayer(row.id)">
                    <template #reference>
                      <el-button type="danger" link size="small">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 压力数据 -->
          <el-tab-pane>
            <template #label>
              <span><el-icon><Odometer /></el-icon> 压力数据 ({{ detailData?.pressure_data?.length || 0 }})</span>
            </template>
            <div class="sub-toolbar">
              <el-button type="primary" size="small" @click="handleAddPressure(selectedDrillHole.id)">
                <el-icon><Plus /></el-icon>
                添加压力数据
              </el-button>
            </div>
            <el-table :data="detailData?.pressure_data || []" border stripe size="small">
              <el-table-column prop="measure_date" label="日期" width="120" />
              <el-table-column prop="measure_time" label="时间" width="100" />
              <el-table-column prop="wellhead_pressure" label="井口压力(MPa)" width="130" />
              <el-table-column prop="reservoir_pressure" label="储层压力(MPa)" width="130" />
              <el-table-column prop="flow_rate" label="流量(m³/h)" width="110" />
              <el-table-column prop="water_level" label="动水位(m)" width="110" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="handleEditPressure(row)">编辑</el-button>
                  <el-popconfirm title="确定删除？" @confirm="handleDeletePressure(row.id)">
                    <template #reference>
                      <el-button type="danger" link size="small">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 孔隙度数据 -->
          <el-tab-pane>
            <template #label>
              <span><el-icon><Grid /></el-icon> 孔隙度数据 ({{ detailData?.porosity_data?.length || 0 }})</span>
            </template>
            <div class="sub-toolbar">
              <el-button type="primary" size="small" @click="handleAddPorosity(selectedDrillHole.id)">
                <el-icon><Plus /></el-icon>
                添加孔隙度数据
              </el-button>
            </div>
            <el-table :data="detailData?.porosity_data || []" border stripe size="small">
              <el-table-column prop="sample_no" label="样品编号" width="110" />
              <el-table-column prop="depth" label="深度(m)" width="90" />
              <el-table-column prop="lithology" label="岩性" width="130" />
              <el-table-column prop="porosity_total" label="总孔隙度(%)" width="110" />
              <el-table-column prop="porosity_effective" label="有效孔隙度(%)" width="120" />
              <el-table-column prop="permeability" label="渗透率(mD)" width="110" />
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link size="small" @click="handleEditPorosity(row)">编辑</el-button>
                  <el-popconfirm title="确定删除？" @confirm="handleDeletePorosity(row.id)">
                    <template #reference>
                      <el-button type="danger" link size="small">删除</el-button>
                    </template>
                  </el-popconfirm>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>

    <!-- 新建/编辑钻孔对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑钻孔' : '新建钻孔'" width="900px" top="5vh">
      <el-form :model="form" label-width="120px">
        <el-tabs v-model="form.activeTab" class="form-tabs">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="basic">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="钻孔编号" required>
                  <el-input v-model="form.hole_id" placeholder="如 ZK-001" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="钻孔名称">
                  <el-input v-model="form.hole_name" placeholder="如 主探孔" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-divider content-position="left">空间坐标信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="X坐标(m)" required>
                  <el-input-number v-model="form.location_x" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="Y坐标(m)" required>
                  <el-input-number v-model="form.location_y" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="地面高程(m)">
                  <el-input-number v-model="form.elevation" :controls="false" :precision="4" size="large" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-divider content-position="left">钻孔深度信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="总深度(m)">
                  <el-input-number v-model="form.total_depth" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="终孔深度(m)">
                  <el-input-number v-model="form.final_depth" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="孔径(mm)">
                  <el-input-number v-model="form.diameter" :min="0" :controls="false" :precision="1" size="large" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-divider content-position="left">施工信息</el-divider>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="施工单位">
                  <el-input v-model="form.drill_company" placeholder="如 地质勘探一队" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="状态">
                  <el-select v-model="form.status" style="width: 100%">
                    <el-option label="完成" value="完成" />
                    <el-option label="施工中" value="施工中" />
                    <el-option label="暂停" value="暂停" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="开孔日期">
                  <el-date-picker v-model="form.drill_start_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="终孔日期">
                  <el-date-picker v-model="form.drill_end_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="备注">
              <el-input v-model="form.description" type="textarea" :rows="2" />
            </el-form-item>
          </el-tab-pane>

          <!-- 分层数据 -->
          <el-tab-pane label="地层分层" name="layers" v-if="!editingItem">
            <div class="tab-toolbar">
              <el-button type="primary" size="small" @click="addLayer">
                <el-icon><Plus /></el-icon>
                添加分层
              </el-button>
            </div>
            <el-table :data="form.layers" border stripe size="small" max-height="400">
              <el-table-column prop="layer_no" label="层号" width="60" />
              <el-table-column label="地层名称" width="140">
                <template #default="{ row }">
                  <el-input v-model="row.layer_name" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="类型" width="100">
                <template #default="{ row }">
                  <el-select v-model="row.layer_type" size="small" style="width: 100%">
                    <el-option label="储层" value="储层" />
                    <el-option label="盖层" value="盖层" />
                    <el-option label="基底" value="基底" />
                    <el-option label="沉积层" value="沉积层" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="顶深(m)" width="90">
                <template #default="{ row }">
                  <el-input-number v-model="row.depth_top" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="底深(m)" width="90">
                <template #default="{ row }">
                  <el-input-number v-model="row.depth_bottom" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="岩性" width="120">
                <template #default="{ row }">
                  <el-input v-model="row.lithology" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="孔隙度" width="90">
                <template #default="{ row }">
                  <el-input-number v-model="row.porosity" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="渗透率" width="90">
                <template #default="{ row }">
                  <el-input-number v-model="row.permeability" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70">
                <template #default="{ $index }">
                  <el-button type="danger" link @click="removeLayer($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 测温数据 -->
          <el-tab-pane label="测温曲线" name="temperature" v-if="!editingItem">
            <div class="tab-toolbar">
              <el-button type="primary" size="small" @click="addTemperature">
                <el-icon><Plus /></el-icon>
                添加测温数据
              </el-button>
            </div>
            <el-table :data="form.temperature_curves" border stripe size="small" max-height="400">
              <el-table-column label="深度(m)" width="100">
                <template #default="{ row }">
                  <el-input-number v-model="row.depth" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="温度(°C)" width="100">
                <template #default="{ row }">
                  <el-input-number v-model="row.temperature" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="梯度" width="100">
                <template #default="{ row }">
                  <el-input-number v-model="row.gradient" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="测量类型" width="120">
                <template #default="{ row }">
                  <el-select v-model="row.measure_type" size="small" style="width: 100%">
                    <el-option label="稳态测温" value="稳态测温" />
                    <el-option label="非稳态测温" value="非稳态测温" />
                  </el-select>
                </template>
              </el-table-column>
              <el-table-column label="测量日期" width="130">
                <template #default="{ row }">
                  <el-date-picker v-model="row.measure_date" type="date" value-format="YYYY-MM-DD" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70">
                <template #default="{ $index }">
                  <el-button type="danger" link @click="removeTemperature($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 压力数据 -->
          <el-tab-pane label="压力数据" name="pressure" v-if="!editingItem">
            <div class="tab-toolbar">
              <el-button type="primary" size="small" @click="addPressure">
                <el-icon><Plus /></el-icon>
                添加压力数据
              </el-button>
            </div>
            <el-table :data="form.pressure_data" border stripe size="small" max-height="400">
              <el-table-column label="测量日期" width="130">
                <template #default="{ row }">
                  <el-date-picker v-model="row.measure_date" type="date" value-format="YYYY-MM-DD" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="井口压力" width="120">
                <template #default="{ row }">
                  <el-input-number v-model="row.wellhead_pressure" :controls="false" :precision="3" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="储层压力" width="120">
                <template #default="{ row }">
                  <el-input-number v-model="row.reservoir_pressure" :controls="false" :precision="3" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="流量" width="100">
                <template #default="{ row }">
                  <el-input-number v-model="row.flow_rate" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="动水位" width="100">
                <template #default="{ row }">
                  <el-input-number v-model="row.water_level" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70">
                <template #default="{ $index }">
                  <el-button type="danger" link @click="removePressure($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 孔隙度数据 -->
          <el-tab-pane label="孔隙度数据" name="porosity" v-if="!editingItem">
            <div class="tab-toolbar">
              <el-button type="primary" size="small" @click="addPorosity">
                <el-icon><Plus /></el-icon>
                添加孔隙度数据
              </el-button>
            </div>
            <el-table :data="form.porosity_data" border stripe size="small" max-height="400">
              <el-table-column label="样品编号" width="120">
                <template #default="{ row }">
                  <el-input v-model="row.sample_no" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="深度(m)" width="90">
                <template #default="{ row }">
                  <el-input-number v-model="row.depth" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="岩性" width="120">
                <template #default="{ row }">
                  <el-input v-model="row.lithology" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="总孔隙度(%)" width="110">
                <template #default="{ row }">
                  <el-input-number v-model="row.porosity_total" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="渗透率" width="100">
                <template #default="{ row }">
                  <el-input-number v-model="row.permeability" :controls="false" :precision="4" size="small" style="width: 100%" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70">
                <template #default="{ $index }">
                  <el-button type="danger" link @click="removePorosity($index)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加测温数据对话框 -->
    <el-dialog v-model="tempDialogVisible" title="添加测温数据" width="450px">
      <el-form :model="tempForm" label-width="100px">
        <el-form-item label="深度(m)">
          <el-input-number v-model="tempForm.depth" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
        </el-form-item>
        <el-form-item label="温度(°C)">
          <el-input-number v-model="tempForm.temperature" :min="0" :max="400" :controls="false" :precision="4" size="large" style="width: 100%" />
        </el-form-item>
        <el-form-item label="地温梯度">
          <el-input-number v-model="tempForm.gradient" :min="0" :max="20" :precision="1" :controls="false" size="large" style="width: 100%" />
        </el-form-item>
        <el-form-item label="测量类型">
          <el-select v-model="tempForm.measure_type" style="width: 100%">
            <el-option label="稳态测温" value="稳态测温" />
            <el-option label="非稳态测温" value="非稳态测温" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="tempDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitTemperature">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加分层对话框 -->
    <el-dialog v-model="layerDialogVisible" title="添加地层分层" width="500px">
      <el-form :model="layerForm" label-width="100px">
        <el-form-item label="层序号">
          <el-input-number v-model="layerForm.layer_no" :min="1" :controls="false" size="large" style="width: 100%" />
        </el-form-item>
        <el-form-item label="地层名称">
          <el-input v-model="layerForm.layer_name" placeholder="如 第四系覆盖层" />
        </el-form-item>
        <el-form-item label="地层类型">
          <el-select v-model="layerForm.layer_type" style="width: 100%">
            <el-option label="储层" value="储层" />
            <el-option label="盖层" value="盖层" />
            <el-option label="基底" value="基底" />
            <el-option label="沉积层" value="沉积层" />
          </el-select>
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="顶深(m)">
              <el-input-number v-model="layerForm.depth_top" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="底深(m)">
              <el-input-number v-model="layerForm.depth_bottom" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="岩性描述">
          <el-input v-model="layerForm.lithology" placeholder="如 砂岩、花岗岩" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="孔隙度(%)">
              <el-input-number v-model="layerForm.porosity" :min="0" :max="50" :controls="false" :precision="1" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="渗透率(mD)">
              <el-input-number v-model="layerForm.permeability" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="layerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitLayer">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑压力数据对话框 -->
    <el-dialog v-model="pressureDialogVisible" title="压力数据" width="550px">
      <el-form :model="pressureForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="测量日期">
              <el-date-picker v-model="pressureForm.measure_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="测量时间">
              <el-input v-model="pressureForm.measure_time" placeholder="如 10:30:00" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="井口压力">
              <el-input-number v-model="pressureForm.wellhead_pressure" :controls="false" :precision="3" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="储层压力">
              <el-input-number v-model="pressureForm.reservoir_pressure" :controls="false" :precision="3" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="流动压力">
              <el-input-number v-model="pressureForm.flowing_pressure" :controls="false" :precision="3" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="关井压力">
              <el-input-number v-model="pressureForm.shut_in_pressure" :controls="false" :precision="3" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="流量(m³/h)">
              <el-input-number v-model="pressureForm.flow_rate" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="动水位(m)">
              <el-input-number v-model="pressureForm.water_level" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="测量仪器">
          <el-input v-model="pressureForm.instrument" placeholder="如 压力计型号" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="pressureForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pressureDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitPressure">确定</el-button>
      </template>
    </el-dialog>

    <!-- 添加/编辑孔隙度数据对话框 -->
    <el-dialog v-model="porosityDialogVisible" title="孔隙度数据" width="600px">
      <el-form :model="porosityForm" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="样品编号">
              <el-input v-model="porosityForm.sample_no" placeholder="如 S-001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="采样日期">
              <el-date-picker v-model="porosityForm.sample_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="取样深度(m)">
              <el-input-number v-model="porosityForm.depth" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="总孔隙度(%)">
              <el-input-number v-model="porosityForm.porosity_total" :min="0" :max="100" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="有效孔隙度(%)">
              <el-input-number v-model="porosityForm.porosity_effective" :min="0" :max="100" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="渗透率(mD)">
              <el-input-number v-model="porosityForm.permeability" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="水平渗透率(mD)">
              <el-input-number v-model="porosityForm.permeability_horizontal" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="垂直渗透率(mD)">
              <el-input-number v-model="porosityForm.permeability_vertical" :min="0" :controls="false" :precision="4" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="岩性描述">
          <el-input v-model="porosityForm.lithology" placeholder="如 砂岩、花岗岩" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="测试方法">
              <el-input v-model="porosityForm.test_method" placeholder="如 气测法" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="测试单位">
              <el-input v-model="porosityForm.laboratory" placeholder="测试实验室" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="备注">
          <el-input v-model="porosityForm.description" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="porosityDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitPorosity">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
@import "@/styles/drill-data-view.css";
</style>
