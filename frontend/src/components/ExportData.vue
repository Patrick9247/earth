<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const exporting = ref(false)

const handleExport = async (type: string) => {
  exporting.value = true
  try {
    const baseUrl = '/api/export'
    
    switch (type) {
      case 'layers-csv':
        window.open(`${baseUrl}/layers/csv`, '_blank')
        break
      case 'drillholes-csv':
        window.open(`${baseUrl}/drill-holes/csv`, '_blank')
        break
      case 'results-csv':
        window.open(`${baseUrl}/results/csv`, '_blank')
        break
      case 'all-json':
        window.open(`${baseUrl}/all/json`, '_blank')
        break
      case 'report':
        window.open(`${baseUrl}/report`, '_blank')
        break
    }
    
    ElMessage.success('导出成功')
  } catch (error) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

const exportOptions = [
  {
    title: '地质层数据',
    description: '导出所有地质层信息（CSV格式）',
    icon: 'Document',
    type: 'layers-csv',
    color: '#409eff'
  },
  {
    title: '钻孔数据',
    description: '导出所有钻孔勘探数据（CSV格式）',
    icon: 'Aim',
    type: 'drillholes-csv',
    color: '#67c23a'
  },
  {
    title: '计算结果',
    description: '导出所有资源计算结果（CSV格式）',
    icon: 'TrendCharts',
    type: 'results-csv',
    color: '#e6a23c'
  },
  {
    title: '完整数据',
    description: '导出所有数据（JSON格式）',
    icon: 'Download',
    type: 'all-json',
    color: '#909399'
  },
  {
    title: '汇总报告',
    description: '生成系统汇总报告',
    icon: 'DocumentCopy',
    type: 'report',
    color: '#f56c6c'
  }
]
</script>

<template>
  <div class="export-component">
    <h3 class="section-title">数据导出</h3>
    <el-row :gutter="16">
      <el-col :span="8" v-for="option in exportOptions" :key="option.type">
        <el-card 
          shadow="hover" 
          class="export-card"
          @click="handleExport(option.type)"
        >
          <div class="card-content">
            <el-icon :size="40" :color="option.color">
              <component :is="option.icon" />
            </el-icon>
            <h4>{{ option.title }}</h4>
            <p>{{ option.description }}</p>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
@import "@/styles/export-data.css";
</style>
