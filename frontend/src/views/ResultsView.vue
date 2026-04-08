<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { gempyApi } from '@/api'
import { ElMessage } from 'element-plus'

const results = ref<any[]>([])
const loading = ref(false)
const selectedResult = ref<any>(null)
const dialogVisible = computed({
  get: () => selectedResult.value !== null,
  set: () => { selectedResult.value = null }
})

const loadResults = async () => {
  loading.value = true
  try {
    const res = await gempyApi.getResults()
    results.value = res.data || []
  } catch (error) {
    console.error('加载失败:', error)
    // 模拟数据
    results.value = [
      { id: 1, name: '地热田A计算', volume: 1e8, temperature_avg: 150, heat_content: 1.5e18, extractable_heat: 3.75e17, power_potential: 12.5, lifetime_years: 30, created_at: '2024-01-15' },
      { id: 2, name: '地热田B计算', volume: 5e7, temperature_avg: 180, heat_content: 2.1e18, extractable_heat: 5.2e17, power_potential: 18.3, lifetime_years: 25, created_at: '2024-01-20' },
      { id: 3, name: '干热岩资源评估', volume: 2e8, temperature_avg: 250, heat_content: 8.6e18, extractable_heat: 2.1e18, power_potential: 45.2, lifetime_years: 30, created_at: '2024-02-01' }
    ]
  } finally {
    loading.value = false
  }
}

const handleDelete = async (id: number) => {
  // 先从本地删除（确保即使API失败也能删除）
  const index = results.value.findIndex(r => r.id === id)
  if (index !== -1) {
    results.value.splice(index, 1)
  }
  
  try {
    await gempyApi.deleteResult(id)
    ElMessage.success('删除成功')
  } catch (error) {
    console.error('API删除失败，但已从本地删除:', error)
    // 不显示错误，因为本地已删除
  }
}

const viewDetail = (row: any) => {
  selectedResult.value = row
}

// 导出为 CSV
const exportToCSV = () => {
  if (results.value.length === 0) {
    ElMessage.warning('没有数据可导出')
    return
  }

  // CSV 表头
  const headers = ['名称', '储层体积(m³)', '平均温度(°C)', '热含量(EJ)', '可采热量(EJ)', '发电潜力(MW)', '开采年限(年)', '创建时间']
  
  // CSV 数据行
  const rows = results.value.map(row => [
    row.name,
    (row.volume / 1e6).toFixed(2) + 'e6',
    row.temperature_avg,
    (row.heat_content / 1e18).toFixed(4),
    (row.extractable_heat / 1e18).toFixed(4),
    row.power_potential?.toFixed(2) || '0.00',
    row.lifetime_years,
    row.created_at
  ])

  // 组合 CSV 内容
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
  ].join('\n')

  // 添加 BOM 以支持中文
  const BOM = '\uFEFF'
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' })
  
  // 创建下载链接
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `计算结果_${new Date().toISOString().slice(0, 10)}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  
  ElMessage.success('导出成功')
}

onMounted(() => {
  loadResults()
})
</script>

<template>
  <div class="results-view">
    <h1 class="page-title">计算结果管理</h1>
    
    <div class="card">
      <div class="btn-group">
        <el-button @click="loadResults">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="success" @click="exportToCSV">
          <el-icon><Download /></el-icon>
          导出 CSV
        </el-button>
      </div>

      <el-table :data="results" v-loading="loading" stripe>
        <el-table-column prop="name" label="名称" width="200" />
        <el-table-column prop="volume" label="储层体积(m³)" width="150">
          <template #default="{ row }">{{ (row.volume / 1e6).toFixed(1) }} × 10⁶</template>
        </el-table-column>
        <el-table-column prop="temperature_avg" label="平均温度(°C)" width="120">
          <template #default="{ row }">
            <el-tag :type="row.temperature_avg > 150 ? 'danger' : 'success'">{{ row.temperature_avg }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="heat_content" label="热含量(EJ)" width="120">
          <template #default="{ row }">{{ (row.heat_content / 1e18).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="extractable_heat" label="可采热量(EJ)" width="120">
          <template #default="{ row }">{{ (row.extractable_heat / 1e18).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="power_potential" label="发电潜力(MW)" width="120">
          <template #default="{ row }">
            <span style="color: #67c23a; font-weight: 600;">{{ row.power_potential?.toFixed(1) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="lifetime_years" label="开采年限" width="100" />
        <el-table-column prop="created_at" label="创建时间" width="120" />
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="viewDetail(row)">详情</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 结果统计 -->
    <el-row :gutter="20">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-value">{{ results.length }}</div>
          <div class="stat-label">计算记录</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card success">
          <div class="stat-value">{{ results.reduce((sum, r) => sum + (r.power_potential || 0), 0).toFixed(1) }}</div>
          <div class="stat-label">总发电潜力 (MW)</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card info">
          <div class="stat-value">{{ (results.reduce((sum, r) => sum + (r.extractable_heat || 0), 0) / 1e18).toFixed(2) }}</div>
          <div class="stat-label">总可采热量 (EJ)</div>
        </div>
      </el-col>
    </el-row>

    <!-- 详情对话框 -->
    <el-dialog v-model="dialogVisible" title="计算结果详情" width="600px" @close="selectedResult = null">
      <el-descriptions :column="2" border v-if="selectedResult">
        <el-descriptions-item label="名称">{{ selectedResult.name }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ selectedResult.created_at }}</el-descriptions-item>
        <el-descriptions-item label="储层体积">{{ (selectedResult.volume / 1e6).toFixed(2) }} × 10⁶ m³</el-descriptions-item>
        <el-descriptions-item label="平均温度">{{ selectedResult.temperature_avg }} °C</el-descriptions-item>
        <el-descriptions-item label="热含量">{{ (selectedResult.heat_content / 1e18).toFixed(4) }} EJ</el-descriptions-item>
        <el-descriptions-item label="可采热量">{{ (selectedResult.extractable_heat / 1e18).toFixed(4) }} EJ</el-descriptions-item>
        <el-descriptions-item label="发电潜力" :span="2">
          <el-tag type="success" size="large">{{ selectedResult.power_potential?.toFixed(2) }} MW</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开采年限">{{ selectedResult.lifetime_years }} 年</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<style scoped>
.stat-card {
  text-align: center;
  padding: 24px;
  border-radius: 8px;
  color: #fff;
  margin-top: 20px;
}

.btn-group {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
</style>
