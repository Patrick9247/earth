<script setup lang="ts">
import { ref, computed } from 'vue'
import { importApi } from '@/api'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'

// 当前导入类型
const importType = ref('drill_info')

// 导入类型配置
const importTypes = [
  {
    value: 'drill_info',
    label: '钻孔空间信息',
    description: '钻孔编号、坐标、深度等基本信息',
    icon: 'Aim'
  },
  {
    value: 'layers',
    label: '热储层分层数据',
    description: '地层分层、岩性、厚度等信息',
    icon: 'DataLine'
  },
  {
    value: 'temperature',
    label: '钻孔测温曲线',
    description: '不同深度的温度测量数据',
    icon: 'TrendCharts'
  },
  {
    value: 'pressure',
    label: '孔口压力数据',
    description: '井口压力、储层压力等数据',
    icon: 'Odometer'
  },
  {
    value: 'porosity',
    label: '岩石孔隙度数据',
    description: '岩石物性、孔隙度、渗透率数据',
    icon: 'Grid'
  }
]

// 上传状态
const uploading = ref(false)
const previewData = ref<any>(null)
const importResult = ref<any>(null)

// 文件列表
const fileList = ref<UploadFile[]>([])

// 预览表格数据
const previewColumns = computed(() => {
  if (!previewData.value?.columns) return []
  return previewData.value.columns.map((col: string) => ({
    prop: col,
    label: col,
    minWidth: 120
  }))
})

// 处理文件变化
const handleFileChange = async (file: UploadFile) => {
  if (!file.raw) return
  
  // 清空之前的数据
  previewData.value = null
  importResult.value = null
  
  // 预览文件
  try {
    const res = await importApi.preview(file.raw)
    if (res.data.success) {
      previewData.value = res.data
      ElMessage.success(`成功读取 ${res.data.total_rows} 行数据`)
    } else {
      ElMessage.error(res.data.message || '预览失败')
    }
  } catch (error: any) {
    console.error('预览失败:', error)
    ElMessage.error(error.response?.data?.detail || '预览失败')
  }
}

// 下载模板
const downloadTemplate = () => {
  const url = importApi.downloadTemplate(importType.value)
  window.open(url, '_blank')
}

// 执行导入
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
      case 'drill_info':
        res = await importApi.importDrillInfo(file)
        break
      case 'layers':
        res = await importApi.importLayers(file)
        break
      case 'temperature':
        res = await importApi.importTemperature(file)
        break
      case 'pressure':
        res = await importApi.importPressure(file)
        break
      case 'porosity':
        res = await importApi.importPorosity(file)
        break
      default:
        throw new Error('未知的导入类型')
    }
    
    if (res.data.success) {
      importResult.value = res.data
      ElMessage.success(res.data.message)
      // 清空文件
      fileList.value = []
      previewData.value = null
    } else {
      importResult.value = res.data
      ElMessage.error(res.data.message)
    }
  } catch (error: any) {
    console.error('导入失败:', error)
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    uploading.value = false
  }
}

// 清空数据
const clearData = () => {
  fileList.value = []
  previewData.value = null
  importResult.value = null
}

// 上传前验证
const beforeUpload = (file: File) => {
  const isCSV = file.name.endsWith('.csv')
  if (!isCSV) {
    ElMessage.error('只能上传CSV文件')
    return false
  }
  return true
}
</script>

<template>
  <div class="import-view">
    <h1 class="page-title">数据导入</h1>
    
    <!-- 导入类型选择 -->
    <div class="card">
      <h3 class="card-title">📂 选择导入类型</h3>
      
      <el-radio-group v-model="importType" class="type-radio-group" @change="clearData">
        <el-radio-button 
          v-for="type in importTypes" 
          :key="type.value" 
          :value="type.value"
        >
          <div class="type-option">
            <el-icon><component :is="type.icon" /></el-icon>
            <span class="type-label">{{ type.label }}</span>
          </div>
        </el-radio-button>
      </el-radio-group>
      
      <div class="type-description">
        <el-alert 
          :title="importTypes.find(t => t.value === importType)?.description" 
          type="info" 
          show-icon 
          :closable="false"
        />
      </div>
    </div>
    
    <!-- 上传区域 -->
    <div class="card">
      <div class="upload-header">
        <h3 class="card-title">📤 上传CSV文件</h3>
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
        <div class="el-upload__text">
          拖拽CSV文件到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传CSV格式文件，建议使用UTF-8编码
          </div>
        </template>
      </el-upload>
    </div>
    
    <!-- 数据预览 -->
    <div class="card" v-if="previewData?.success">
      <h3 class="card-title">👀 数据预览</h3>
      <p class="preview-info">共 {{ previewData.total_rows }} 行数据，显示前20行</p>
      
      <el-table 
        :data="previewData.rows" 
        border 
        stripe 
        max-height="400"
        style="width: 100%"
      >
        <el-table-column 
          v-for="col in previewColumns" 
          :key="col.prop"
          :prop="col.prop"
          :label="col.label"
          :min-width="col.minWidth"
          show-overflow-tooltip
        />
      </el-table>
      
      <div class="action-buttons">
        <el-button type="primary" size="large" @click="executeImport" :loading="uploading">
          <el-icon><Upload /></el-icon>
          开始导入
        </el-button>
        <el-button size="large" @click="clearData">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>
    
    <!-- 导入结果 -->
    <div class="card" v-if="importResult">
      <h3 class="card-title">📊 导入结果</h3>
      
      <el-result
        :icon="importResult.success ? 'success' : 'warning'"
        :title="importResult.success ? '导入完成' : '部分导入成功'"
        :sub-title="importResult.message"
      >
        <template #extra>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="总行数">
              {{ importResult.total_rows }}
            </el-descriptions-item>
            <el-descriptions-item label="成功行数">
              <el-tag type="success">{{ importResult.success_rows }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="失败行数">
              <el-tag :type="importResult.failed_rows > 0 ? 'danger' : 'success'">
                {{ importResult.failed_rows }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <!-- 错误详情 -->
          <div v-if="importResult.errors?.length" class="error-details">
            <h4>错误详情（前20条）：</h4>
            <el-table :data="importResult.errors" border size="small" max-height="300">
              <el-table-column prop="row" label="行号" width="80" />
              <el-table-column prop="error" label="错误信息" />
            </el-table>
          </div>
        </template>
      </el-result>
    </div>
    
    <!-- 字段说明 -->
    <div class="card">
      <h3 class="card-title">📋 字段说明</h3>
      
      <el-collapse v-model="activeCollapse">
        <!-- 钻孔空间信息字段 -->
        <el-collapse-item title="钻孔空间信息字段" name="drill_info">
          <el-table :data="drillInfoFields" border size="small">
            <el-table-column prop="field" label="字段名" width="180" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
        </el-collapse-item>
        
        <!-- 热储层分层数据字段 -->
        <el-collapse-item title="热储层分层数据字段" name="layers">
          <el-table :data="layerFields" border size="small">
            <el-table-column prop="field" label="字段名" width="180" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
        </el-collapse-item>
        
        <!-- 测温曲线字段 -->
        <el-collapse-item title="钻孔测温曲线字段" name="temperature">
          <el-table :data="temperatureFields" border size="small">
            <el-table-column prop="field" label="字段名" width="180" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
        </el-collapse-item>
        
        <!-- 压力数据字段 -->
        <el-collapse-item title="孔口压力数据字段" name="pressure">
          <el-table :data="pressureFields" border size="small">
            <el-table-column prop="field" label="字段名" width="180" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
        </el-collapse-item>
        
        <!-- 孔隙度数据字段 -->
        <el-collapse-item title="岩石孔隙度数据字段" name="porosity">
          <el-table :data="porosityFields" border size="small">
            <el-table-column prop="field" label="字段名" width="180" />
            <el-table-column prop="required" label="必填" width="80">
              <template #default="{ row }">
                <el-tag :type="row.required ? 'danger' : 'info'" size="small">
                  {{ row.required ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="说明" />
          </el-table>
        </el-collapse-item>
      </el-collapse>
    </div>
  </div>
</template>

<script lang="ts">
// 字段说明数据
const drillInfoFields = [
  { field: '钻孔编号', required: true, description: '钻孔唯一标识符' },
  { field: '钻孔名称', required: false, description: '钻孔的名称' },
  { field: 'X坐标(m)', required: true, description: '钻孔X坐标（米）' },
  { field: 'Y坐标(m)', required: true, description: '钻孔Y坐标（米）' },
  { field: '地面高程(m)', required: false, description: '钻孔地面高程' },
  { field: '钻孔总深度(m)', required: false, description: '钻孔总深度' },
  { field: '终孔深度(m)', required: false, description: '最终钻孔深度' },
  { field: '孔径(mm)', required: false, description: '钻孔直径' },
  { field: '施工单位', required: false, description: '施工钻探单位' },
  { field: '开孔日期', required: false, description: '开始钻探日期' },
  { field: '终孔日期', required: false, description: '结束钻探日期' },
  { field: '钻孔状态', required: false, description: '钻孔当前状态' },
  { field: '备注说明', required: false, description: '其他说明信息' }
]

const layerFields = [
  { field: '钻孔编号', required: true, description: '关联的钻孔编号' },
  { field: '层序号', required: false, description: '地层序号' },
  { field: '地层名称', required: false, description: '地层名称' },
  { field: '地层类型', required: false, description: '如：储层、盖层、基底' },
  { field: '层顶深度(m)', required: true, description: '地层顶部深度' },
  { field: '层底深度(m)', required: true, description: '地层底部深度' },
  { field: '层厚度(m)', required: false, description: '地层厚度' },
  { field: '岩性描述', required: false, description: '岩石性质描述' },
  { field: '岩石类型', required: false, description: '岩石分类' },
  { field: '孔隙度', required: false, description: '岩石孔隙度（0-1）' },
  { field: '渗透率(mD)', required: false, description: '渗透率（毫达西）' },
  { field: '热导率(W/m·K)', required: false, description: '热导率' }
]

const temperatureFields = [
  { field: '钻孔编号', required: true, description: '关联的钻孔编号' },
  { field: '测点序号', required: false, description: '测点编号' },
  { field: '测量日期', required: false, description: '测量日期' },
  { field: '测量类型', required: false, description: '稳态测温/非稳态测温' },
  { field: '测量深度(m)', required: true, description: '测量点的深度' },
  { field: '测量温度(°C)', required: true, description: '测量的温度值' },
  { field: '校正后温度(°C)', required: false, description: '校正后的温度' },
  { field: '地温梯度(°C/100m)', required: false, description: '地温梯度' },
  { field: '测量仪器', required: false, description: '使用的测量仪器' }
]

const pressureFields = [
  { field: '钻孔编号', required: true, description: '关联的钻孔编号' },
  { field: '测量日期', required: false, description: '测量日期' },
  { field: '测量时间', required: false, description: '测量时间' },
  { field: '井口压力(MPa)', required: false, description: '井口压力' },
  { field: '储层压力(MPa)', required: false, description: '储层压力' },
  { field: '流动压力(MPa)', required: false, description: '流动压力' },
  { field: '关井压力(MPa)', required: false, description: '关井压力' },
  { field: '压力梯度(MPa/100m)', required: false, description: '压力梯度' },
  { field: '测量深度(m)', required: false, description: '测量深度' },
  { field: '流量(m³/h)', required: false, description: '流体流量' },
  { field: '动水位(m)', required: false, description: '动水位深度' }
]

const porosityFields = [
  { field: '钻孔编号', required: true, description: '关联的钻孔编号' },
  { field: '样品编号', required: false, description: '样品唯一编号' },
  { field: '采样日期', required: false, description: '采样日期' },
  { field: '取样深度(m)', required: false, description: '取样深度' },
  { field: '岩性描述', required: false, description: '岩性描述' },
  { field: '总孔隙度(%)', required: false, description: '总孔隙度百分比' },
  { field: '有效孔隙度(%)', required: false, description: '有效孔隙度百分比' },
  { field: '渗透率(mD)', required: false, description: '渗透率' },
  { field: '体密度(g/cm³)', required: false, description: '体密度' },
  { field: '含水饱和度(%)', required: false, description: '含水饱和度' },
  { field: '测试方法', required: false, description: '测试方法' },
  { field: '测试单位', required: false, description: '测试单位' }
]

export default {
  data() {
    return {
      activeCollapse: ['drill_info']
    }
  }
}
</script>

<style scoped>
.import-view {
  padding: 0;
}

.type-radio-group {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.type-radio-group :deep(.el-radio-button__inner) {
  padding: 16px 24px;
  border-radius: 8px !important;
  border: 1px solid #dcdfe6 !important;
}

.type-radio-group :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  box-shadow: none;
}

.type-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.type-option .el-icon {
  font-size: 24px;
}

.type-label {
  font-size: 14px;
}

.type-description {
  margin-top: 16px;
}

.upload-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.upload-header .card-title {
  margin-bottom: 0;
}

.upload-area {
  width: 100%;
}

.upload-area :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.preview-info {
  color: #909399;
  margin-bottom: 16px;
}

.action-buttons {
  display: flex;
  gap: 16px;
  margin-top: 24px;
  justify-content: center;
}

.error-details {
  margin-top: 20px;
  text-align: left;
}

.error-details h4 {
  margin-bottom: 12px;
  color: #606266;
}
</style>
