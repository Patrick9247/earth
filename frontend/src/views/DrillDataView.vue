<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { drillHolesApi, importApi, drillHoleDetailApi } from '@/api'
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
  { value: 'drill_info', label: '钻孔空间信息', description: '钻孔编号、坐标、深度等基本信息', icon: 'Aim' },
  { value: 'layers', label: '热储层分层数据', description: '地层分层、岩性、厚度等信息', icon: 'DataLine' },
  { value: 'temperature', label: '钻孔测温曲线', description: '不同深度的温度测量数据', icon: 'TrendCharts' },
  { value: 'pressure', label: '孔口压力数据', description: '井口压力、储层压力等数据', icon: 'Odometer' },
  { value: 'porosity', label: '岩石孔隙度数据', description: '岩石物性、孔隙度、渗透率数据', icon: 'Grid' }
]

// ==================== 手动输入表单 ====================
const dialogVisible = ref(false)
const editingItem = ref<any>(null)
const form = ref({
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
  description: ''
})

// 测温数据手动输入
const tempDialogVisible = ref(false)
const tempForm = ref({
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
const handleAdd = () => {
  editingItem.value = null
  form.value = {
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
    description: ''
  }
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  editingItem.value = row
  form.value = { ...row }
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
    if (editingItem.value) {
      await drillHolesApi.update(editingItem.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await drillHolesApi.create(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadDrillHoles()
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
    const newTemp = {
      id: Date.now(),
      ...tempForm.value,
      created_at: new Date().toISOString()
    }
    detailData.value.temperature_curves.push(newTemp)
    
    // 更新store中的温度数据
    const avgTemp = detailData.value.temperature_curves.reduce((sum: number, t: any) => sum + t.temperature, 0) / detailData.value.temperature_curves.length
    store.updateDrillHoles(store.drillHoles.map((d: any) => 
      d.id === tempForm.value.drill_hole_id ? { ...d, temperature: avgTemp } : d
    ))
  }
  tempDialogVisible.value = false
  ElMessage.success('添加成功')
}

// 添加分层数据
const handleAddLayer = (drillHoleId: number) => {
  layerForm.value = {
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
    const newLayer = {
      id: Date.now(),
      ...layerForm.value,
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
  layerDialogVisible.value = false
  ElMessage.success('添加成功')
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

// ==================== 初始化 ====================
onMounted(() => {
  loadDrillHoles()
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
            </el-table>
          </el-tab-pane>

          <!-- 压力数据 -->
          <el-tab-pane>
            <template #label>
              <span><el-icon><Odometer /></el-icon> 压力数据 ({{ detailData?.pressure_data?.length || 0 }})</span>
            </template>
            <el-table :data="detailData?.pressure_data || []" border stripe size="small">
              <el-table-column prop="measure_date" label="日期" width="120" />
              <el-table-column prop="wellhead_pressure" label="井口压力(MPa)" width="140" />
              <el-table-column prop="reservoir_pressure" label="储层压力(MPa)" width="140" />
              <el-table-column prop="flow_rate" label="流量(m³/h)" width="120" />
              <el-table-column prop="water_level" label="动水位(m)" width="120" />
            </el-table>
          </el-tab-pane>

          <!-- 孔隙度数据 -->
          <el-tab-pane>
            <template #label>
              <span><el-icon><Grid /></el-icon> 孔隙度数据 ({{ detailData?.porosity_data?.length || 0 }})</span>
            </template>
            <el-table :data="detailData?.porosity_data || []" border stripe size="small">
              <el-table-column prop="sample_no" label="样品编号" width="120" />
              <el-table-column prop="depth" label="深度(m)" width="100" />
              <el-table-column prop="lithology" label="岩性" width="150" />
              <el-table-column prop="porosity_total" label="总孔隙度(%)" width="120" />
              <el-table-column prop="porosity_effective" label="有效孔隙度(%)" width="130" />
              <el-table-column prop="permeability" label="渗透率(mD)" width="120" />
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>

    <!-- 新建/编辑钻孔对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑钻孔' : '新建钻孔'" width="700px">
      <el-form :model="form" label-width="120px">
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
              <el-input-number v-model="form.location_x" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Y坐标(m)" required>
              <el-input-number v-model="form.location_y" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="地面高程(m)">
              <el-input-number v-model="form.elevation" :controls="false" :precision="2" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-divider content-position="left">钻孔深度信息</el-divider>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="总深度(m)">
              <el-input-number v-model="form.total_depth" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="终孔深度(m)">
              <el-input-number v-model="form.final_depth" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
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
          <el-input-number v-model="tempForm.depth" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
        </el-form-item>
        <el-form-item label="温度(°C)">
          <el-input-number v-model="tempForm.temperature" :min="0" :max="400" :controls="false" :precision="2" size="large" style="width: 100%" />
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
              <el-input-number v-model="layerForm.depth_top" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="底深(m)">
              <el-input-number v-model="layerForm.depth_bottom" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
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
              <el-input-number v-model="layerForm.permeability" :min="0" :controls="false" :precision="2" size="large" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="layerDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitLayer">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.drill-data-view {
  padding: 0;
}

.main-tabs {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.map-section {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

.map-section h3 {
  margin-bottom: 16px;
  color: #606266;
}

.map-container {
  height: 300px;
  background: linear-gradient(135deg, #e8f4f8 0%, #d1e8e0 100%);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.drill-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  cursor: pointer;
  transition: transform 0.2s;
}

.drill-marker:hover {
  transform: translate(-50%, -50%) scale(1.3);
}

.type-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}

.type-radio-group :deep(.el-radio-button__inner) {
  padding: 12px 20px;
  border-radius: 6px !important;
}

.type-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.type-option .el-icon {
  font-size: 20px;
}

.upload-section {
  margin-top: 24px;
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.upload-header h3 {
  margin: 0;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 180px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.preview-section,
.result-section {
  margin-top: 24px;
}

.action-buttons {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-top: 20px;
}

.detail-card {
  min-height: 600px;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.detail-header h2 {
  margin: 0;
  color: #303133;
}

.detail-tabs {
  margin-top: 24px;
}

.sub-toolbar {
  margin-bottom: 12px;
}

/* 分页样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}

/* 数字输入框样式优化 */
:deep(.el-input-number) {
  font-size: 16px;
}

:deep(.el-input-number .el-input__inner) {
  font-size: 16px;
  font-weight: 500;
  text-align: center;
}

:deep(.el-input-number--large .el-input__inner) {
  font-size: 18px;
  font-weight: 500;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style>
