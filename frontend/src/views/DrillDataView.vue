`<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import { stratigraphicApi } from '@/api/get-api.ts'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
//  页面状态 
const activeTab = ref('stratigraphic')  // 默认显示地层分层数据
//  导入相关 
const importType = ref('stratigraphic')
const uploading = ref(false)
const previewData = ref<any>(null)
const importResult = ref<any>(null)
const fileList = ref<UploadFile[]>([])
const importTypes = [
  { value: 'stratigraphic', label: '地层分层数据', description: '钻孔名称、顶部深度、底部深度、地层类型', icon: 'DataLine' }
]
//  地层分层数据 
const stratigraphicLoading = ref(false)
const stratigraphicLayers = ref<any[]>([])
const stratigraphicHoles = ref<string[]>([])
const selectedHoleFilter = ref<string>('')
const filteredStratigraphicLayers = ref<any[]>([])
const stratigraphicDialogVisible = ref(false)
const stratigraphicForm = ref({
  id: null as number | null,
  hole_name: '',
  depth_top: 0,
  depth_bottom: 0,
  layer_type: '盖层'
})
// 加载地层分层数据
const loadStratigraphicLayers = async () => {
  stratigraphicLoading.value = true
  try {
    const [layersRes, holesRes] = await Promise.all([
      stratigraphicApi.getAll(),
      stratigraphicApi.getHoles()
    ])
    stratigraphicLayers.value = layersRes.data || []
    stratigraphicHoles.value = holesRes.data || []
    filteredStratigraphicLayers.value = stratigraphicLayers.value
  } catch (error) {
    console.error('加载地层分层数据失败:', error)
    ElMessage.error('加载地层分层数据失败')
  } finally {
    stratigraphicLoading.value = false
  }
}
// 筛选地层分层数据
const filterStratigraphicLayers = () => {
  if (selectedHoleFilter.value) {
    filteredStratigraphicLayers.value = stratigraphicLayers.value.filter(
      (layer: any) => layer.hole_name === selectedHoleFilter.value
    )
  } else {
    filteredStratigraphicLayers.value = stratigraphicLayers.value
  }
}
// 获取地层类型标签颜色
const getLayerTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    '盖层': 'info',
    '热储层': 'success',
    '基层': 'warning'
  }
  return typeMap[type] || ''
}
// 添加地层分层
const addStratigraphicLayer = () => {
  stratigraphicForm.value = {
    id: null,
    hole_name: '',
    depth_top: 0,
    depth_bottom: 0,
    layer_type: '盖层'
  }
  stratigraphicDialogVisible.value = true
}
// 编辑地层分层
const editStratigraphicLayer = (row: any) => {
  stratigraphicForm.value = { ...row }
  stratigraphicDialogVisible.value = true
}
// 保存地层分层
const saveStratigraphicLayer = async () => {
  try {
    if (stratigraphicForm.value.id) {
      await stratigraphicApi.update(stratigraphicForm.value.id, stratigraphicForm.value)
      ElMessage.success('更新成功')
    } else {
      await stratigraphicApi.create(stratigraphicForm.value)
      ElMessage.success('添加成功')
    }
    stratigraphicDialogVisible.value = false
    loadStratigraphicLayers()
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  }
}
// 删除地层分层
const deleteStratigraphicLayer = async (row: any) => {
  try {
    await ElMessageBox.confirm('确定删除该地层分层记录吗？', '提示', {
      type: 'warning'
    })
    await stratigraphicApi.delete(row.id)
    ElMessage.success('删除成功')
    loadStratigraphicLayers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}
// 清空地层分层数据
const clearStratigraphicData = async () => {
  try {
    await ElMessageBox.confirm('确定清空所有地层分层数据吗？此操作不可恢复！', '警告', {
      type: 'warning'
    })
    await stratigraphicApi.clearAll()
    ElMessage.success('清空成功')
    loadStratigraphicLayers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空失败:', error)
      ElMessage.error('清空失败')
    }
  }
}
// 下载CSV模板
const downloadStratigraphicTemplate = () => {
  const headers = ['钻孔名称', '顶部深度', '底部深度', '地层类型']
  const csvContent = headers.join(',') + '\n'
  // 添加示例数据行
  const exampleRow = ['ZK001', '0', '23', '盖层']
  const fullContent = csvContent + exampleRow.join(',')
  const blob = new Blob(['\ufeff' + fullContent], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '地层分层数据模板.csv'
  link.click()
  window.URL.revokeObjectURL(url)
  ElMessage.success('模板已下载')
}
// 导入CSV
const handleStratigraphicUpload = async (file: File) => {
  // 返回false阻止自动上传，手动处理
  try {
    const res = await stratigraphicApi.importCsv(file)
    if (res.data.success) {
      ElMessage.success(res.data.message)
      loadStratigraphicLayers()
    } else {
      ElMessage.warning(res.data.message)
    }
  } catch (error: any) {
    console.error('导入失败:', error)
    ElMessage.error(error.response?.data?.detail || '导入失败')
  }
  return false  // 阻止el-upload的自动上传行为
}
// ==================== 导入操作 ====================
const previewColumns = computed(() => {
  if (!previewData.value?.columns) return []
  // 支持 columns 为字符串数组或对象数组
  return previewData.value.columns.map((col: any) => {
    if (typeof col === 'string') {
      return { prop: col, label: col, minWidth: 120 }
    }
    return { prop: col.prop, label: col.label, minWidth: 120 }
  })
})
const handleFileChange = async (file: UploadFile) => {
  if (!file.raw) return
  previewData.value = null
  importResult.value = null
  try {
    // 使用地层分层API导入
    const res = await stratigraphicApi.importCsv(file.raw)
    if (res.data.success) {
      // 构造预览数据 - 使用英文prop匹配后端字段，中文label显示
      previewData.value = {
        success: true,
        total_rows: res.data.count || 0,
        rows: res.data.data || [],
        columns: [
          { prop: 'hole_name', label: '钻孔名称' },
          { prop: 'depth_top', label: '顶部深度' },
          { prop: 'depth_bottom', label: '底部深度' },
          { prop: 'layer_type', label: '地层类型' }
        ]
      }
      ElMessage.success(`成功读取 ${res.data.count || 0} 行数据`)
    } else {
      ElMessage.error(res.data.message || '预览失败')
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || '预览失败')
  }
}
const downloadTemplate = () => {
  const headers = ['钻孔名称', '顶部深度', '底部深度', '地层类型']
  const csvContent = headers.join(',') + '\n'
  // 添加示例数据
  const exampleRows = [
    ['ZK001', '0', '23', '盖层'],
    ['ZK001', '23', '56', '热储层'],
    ['ZK001', '56', '120', '基层']
  ]
  const fullContent = csvContent + exampleRows.map(row => row.join(',')).join('\n')
  const blob = new Blob(['\ufeff' + fullContent], { type: 'text/csv;charset=utf-8;' })
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = '地层分层数据模板.csv'
  link.click()
  window.URL.revokeObjectURL(url)
  ElMessage.success('模板已下载')
}
const executeImport = async () => {
  if (!fileList.value[0]?.raw) {
    ElMessage.warning('请先选择要导入的文件')
    return
  }
  uploading.value = true
  importResult.value = null
  try {
    const file = fileList.value[0].raw
    const res = await stratigraphicApi.importCsv(file)
    if (res.data.success) {
      importResult.value = {
        success: true,
        message: res.data.message,
        total_rows: res.data.count || 0,
        success_rows: res.data.count || 0,
        failed_rows: 0
      }
      ElMessage.success(res.data.message)
      fileList.value = []
      previewData.value = null
      loadStratigraphicLayers()
    } else {
      importResult.value = {
        success: false,
        message: res.data.message,
        total_rows: 0,
        success_rows: 0,
        failed_rows: 0
      }
      ElMessage.error(res.data.message)
    }
  } catch (error: any) {
    importResult.value = {
      success: false,
      message: error.response?.data?.detail || '导入失败',
      total_rows: 0,
      success_rows: 0,
      failed_rows: 1
    }
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
//  图表相关 
// 图表实例
const chartRef = ref<HTMLElement | null>(null)
let myChart: echarts.ECharts | null = null
// 地层类型颜色映射
const layerColors: Record<string, string> = {
  '盖层': '#909399',      // 灰色
  '热储层': '#67C23A',    // 绿色
  '基层': '#E6A23C'       // 橙色
}
// 初始化/更新图表
const initChart = () => {
  if (!chartRef.value) return
  // 确保地层分层数据已加载
  if (stratigraphicHoles.value.length === 0) {
    console.log('等待地层分层数据加载...')
    return
  }
  // 销毁旧实例
  if (myChart) {
    myChart.dispose()
    myChart = null
  }
  // 按钻孔分组数据
  const holesData: Record<string, any[]> = {}
  stratigraphicLayers.value.forEach((layer: any) => {
    if (!holesData[layer.hole_name]) {
      holesData[layer.hole_name] = []
    }
    holesData[layer.hole_name].push(layer)
  })
  // 对每个钻孔的地层按depth_top排序
  Object.keys(holesData).forEach(holeName => {
    holesData[holeName].sort((a, b) => a.depth_top - b.depth_top)
  })
  const holeNames = Object.keys(holesData)
  // 构建图表数据 - 使用堆叠柱状图
  const series: any[] = []
  const layerTypes = ['盖层', '热储层', '基层']
  // 为每种地层类型创建一个系列
  layerTypes.forEach(layerType => {
    const data = holeNames.map(holeName => {
      const layers = holesData[holeName].filter((l: any) => l.layer_type === layerType)
      // 计算该地层的总厚度
      const totalThickness = layers.reduce((sum: number, l: any) => sum + (l.depth_bottom - l.depth_top), 0)
      return totalThickness
    })
    series.push({
      name: layerType,
      type: 'bar',
      stack: 'total',
      data: data,
      itemStyle: { color: layerColors[layerType] },
      emphasis: { focus: 'series' }
    })
  })
  // 初始化图表
  myChart = echarts.init(chartRef.value)
  // 图表配置
  const option = {
    title: {
      text: '地层分层剖面图',
      left: 'center',
      top: 10
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        const holeName = params[0].axisValue
        const layers = holesData[holeName] || []
        let result = `<div style="font-weight:bold;margin-bottom:8px;font-size:14px;">${holeName}</div>`
        result += `<div style="border-top:1px solid #eee;padding-top:8px;">`
        // 按深度排序显示
        layers.forEach((layer: any) => {
          const thickness = (layer.depth_bottom - layer.depth_top).toFixed(2)
          const color = layerColors[layer.layer_type] || '#999'
          result += `<div style="margin:4px 0;display:flex;align-items:center;">`
          result += `<span style="display:inline-block;width:10px;height:10px;background:${color};margin-right:6px;border-radius:2px;"></span>`
          result += `<span>${layer.layer_type}: ${layer.depth_top.toFixed(1)}m - ${layer.depth_bottom.toFixed(1)}m (厚${thickness}m)</span>`
          result += `</div>`
        })
        // 计算总深度
        const maxDepth = Math.max(...layers.map((l: any) => l.depth_bottom))
        result += `<div style="border-top:1px solid #eee;margin-top:6px;padding-top:6px;font-weight:bold;">总深度: ${maxDepth.toFixed(1)}m</div>`
        result += `</div>`
        return result
      }
    },
    legend: {
      data: layerTypes,
      top: 40,
      itemGap: 20
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '100px',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: holeNames,
      axisLabel: {
        interval: 0,
        rotate: 30,
        fontSize: 12
      },
      name: '钻孔名称',
      nameLocation: 'middle',
      nameGap: 50
    },
    yAxis: {
      type: 'value',
      name: '深度 (m)',
      nameLocation: 'middle',
      nameGap: 50,
      inverse: true,  // 反转Y轴，深度向下增加
      axisLabel: {
        formatter: '{value}'
      }
    },
    series: series,
    // 添加标注线显示深度
    graphic: holeNames.flatMap((holeName, index) => {
      const layers = holesData[holeName]
      const points: any[] = []
      layers.forEach((layer: any) => {
        // 在每个地层分界处添加深度标注
        points.push({
          type: 'text',
          left: `${10 + (index * 80 / holeNames.length)}%`,
          top: `${50 + layer.depth_bottom}%`,
          style: {
            text: `${layer.depth_bottom}m`,
            fontSize: 10,
            fill: '#666'
          }
        })
      })
      return points
    })
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
  loadStratigraphicLayers()
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
    <h1 class="page-title">数据管理</h1>
    <el-tabs v-model="activeTab" class="main-tabs">
        <!-- 地层分层数据 -->
        <el-tab-pane label="地层分层" name="stratigraphic">
          <div class="card">
            <div class="toolbar">
              <el-button type="primary" @click="addStratigraphicLayer">
                <el-icon><Plus /></el-icon>
                添加分层
              </el-button>
              <el-upload
                ref="stratigraphicUploadRef"
                :show-file-list="false"
                :before-upload="handleStratigraphicUpload"
                accept=".csv"
                style="display: inline-block; margin-left: 10px;"
              >
                <el-button type="warning">
                  <el-icon><Upload /></el-icon>
                  导入CSV
                </el-button>
              </el-upload>
              <el-button type="info" @click="downloadStratigraphicTemplate">
                <el-icon><Download /></el-icon>
                下载模板
              </el-button>
              <el-button @click="loadStratigraphicLayers">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
              <el-button type="danger" @click="clearStratigraphicData" :disabled="stratigraphicLayers.length === 0">
                <el-icon><Delete /></el-icon>
                清空数据
              </el-button>
            </div>
            <!-- 钻孔筛选 -->
            <div class="filter-section" style="margin-bottom: 16px;">
              <el-select v-model="selectedHoleFilter" placeholder="筛选钻孔" clearable @change="filterStratigraphicLayers" style="width: 200px;">
                <el-option v-for="hole in stratigraphicHoles" :key="hole" :label="hole" :value="hole" />
              </el-select>
            </div>
            <el-table :data="filteredStratigraphicLayers" border stripe v-loading="stratigraphicLoading" max-height="500">
              <el-table-column type="index" label="序号" width="60" />
              <el-table-column prop="hole_name" label="钻孔名称" width="120" />
              <el-table-column prop="depth_top" label="顶部深度(m)" width="120">
                <template #default="{ row }">
                  {{ row.depth_top?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="depth_bottom" label="底部深度(m)" width="120">
                <template #default="{ row }">
                  {{ row.depth_bottom?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column label="厚度(m)" width="100">
                <template #default="{ row }">
                  {{ (row.depth_bottom - row.depth_top)?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="layer_type" label="地层类型" width="100">
                <template #default="{ row }">
                  <el-tag :type="getLayerTypeTag(row.layer_type)" size="small">
                    {{ row.layer_type }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button type="primary" link @click="editStratigraphicLayer(row)">编辑</el-button>
                  <el-button type="danger" link @click="deleteStratigraphicLayer(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        <!-- 数据可视化 -->
        <el-tab-pane label="数据可视化" name="visualization">
          <div class="card">
            <h3 class="card-title">地层分层可视化</h3>
            <div v-if="stratigraphicHoles.length === 0" class="empty-tip">
              <el-empty description="暂无地层分层数据，请先在地层分层标签页添加数据" />
            </div>
            <!-- 柱状图容器 -->
            <div v-else ref="chartRef" class="chart-container" style="height: 600px;"></div>
          </div>
        </el-tab-pane>
        <!-- 数据导入 -->
        <el-tab-pane label="数据导入" name="import">
          <div class="card">
            <h3 class="card-title">选择导入类型</h3>
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
                <h3>上传CSV文件</h3>
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
              <h3>数据预览 (共{{ previewData.total_rows }}行)</h3>
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
    <!-- 地层分层编辑对话框 -->
    <el-dialog v-model="stratigraphicDialogVisible" :title="stratigraphicForm.id ? '编辑地层分层' : '添加地层分层'" width="500px">
      <el-form :model="stratigraphicForm" label-width="100px">
        <el-form-item label="钻孔名称" required>
          <el-input v-model="stratigraphicForm.hole_name" placeholder="如 ZK001" />
        </el-form-item>
        <el-form-item label="顶部深度(m)" required>
          <el-input-number v-model="stratigraphicForm.depth_top" :min="0" :controls="false" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="底部深度(m)" required>
          <el-input-number v-model="stratigraphicForm.depth_bottom" :min="0" :controls="false" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="地层类型" required>
          <el-select v-model="stratigraphicForm.layer_type" style="width: 100%">
            <el-option label="盖层" value="盖层" />
            <el-option label="热储层" value="热储层" />
            <el-option label="基层" value="基层" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="stratigraphicDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStratigraphicLayer">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
<style scoped>
@import "@/styles/drill-data-view.css";
</style>