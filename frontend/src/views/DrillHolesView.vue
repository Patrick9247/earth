<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { drillHolesApi } from '@/api'
import { ElMessage } from 'element-plus'

const drillHoles = ref<any[]>([])
const dialogVisible = ref(false)
const editingItem = ref<any>(null)
const loading = ref(false)

const form = ref({
  name: '',
  location_x: 0,
  location_y: 0,
  location_z: 0,
  depth: 0,
  temperature: 0,
  gradient: 0,
  description: ''
})

const resetForm = () => {
  form.value = {
    name: '',
    location_x: 0,
    location_y: 0,
    location_z: 0,
    depth: 0,
    temperature: 0,
    gradient: 0,
    description: ''
  }
  editingItem.value = null
}

const handleAdd = () => {
  resetForm()
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
    ElMessage.error('删除失败')
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
    ElMessage.error('操作失败')
  }
}

const loadDrillHoles = async () => {
  loading.value = true
  try {
    const res = await drillHolesApi.getAll()
    drillHoles.value = res.data || []
  } catch (error) {
    console.error('加载失败:', error)
    // 模拟数据
    drillHoles.value = [
      { id: 1, name: 'ZK-001', location_x: 100, location_y: 200, location_z: 50, depth: 800, temperature: 120, gradient: 6.5, description: '主探孔' },
      { id: 2, name: 'ZK-002', location_x: 300, location_y: 400, location_z: 45, depth: 1200, temperature: 160, gradient: 7.2, description: '深部探孔' },
      { id: 3, name: 'ZK-003', location_x: 500, location_y: 150, location_z: 55, depth: 600, temperature: 95, gradient: 5.8, description: '边缘探孔' },
      { id: 4, name: 'ZK-004', location_x: 200, location_y: 350, location_z: 48, depth: 1000, temperature: 145, gradient: 6.8, description: '验证孔' }
    ]
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDrillHoles()
})
</script>

<template>
  <div class="drill-holes-view">
    <h1 class="page-title">钻孔数据管理</h1>
    
    <div class="card">
      <div class="btn-group">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新建钻孔
        </el-button>
        <el-button @click="loadDrillHoles">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <el-table :data="drillHoles" v-loading="loading" stripe>
        <el-table-column prop="name" label="钻孔编号" width="120" />
        <el-table-column prop="location_x" label="X坐标" width="100" />
        <el-table-column prop="location_y" label="Y坐标" width="100" />
        <el-table-column prop="location_z" label="地面高程(m)" width="120" />
        <el-table-column prop="depth" label="钻孔深度(m)" width="120" />
        <el-table-column prop="temperature" label="测量温度(°C)" width="120">
          <template #default="{ row }">
            <span :style="{ color: row.temperature > 150 ? '#f56c6c' : '#67c23a' }">
              {{ row.temperature }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="gradient" label="地温梯度(°C/100m)" width="150">
          <template #default="{ row }">{{ row.gradient?.toFixed(1) }}</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="150" />
        <el-table-column label="操作" fixed="right" width="150">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除？" @confirm="handleDelete(row.id)">
              <template #reference>
                <el-button type="danger" link>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 钻孔位置图 -->
    <div class="card">
      <h3 class="card-title">钻孔位置分布</h3>
      <div class="map-placeholder">
        <div class="map-grid">
          <div 
            v-for="dh in drillHoles" 
            :key="dh.id"
            class="drill-marker"
            :style="{ 
              left: `${(dh.location_x / 600) * 100}%`,
              top: `${(dh.location_y / 500) * 100}%`
            }"
          >
            <el-tooltip :content="`${dh.name}: ${dh.temperature}°C`">
              <el-icon :size="24" color="#f56c6c"><Aim /></el-icon>
            </el-tooltip>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingItem ? '编辑钻孔' : '新建钻孔'" width="500px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="钻孔编号" required>
          <el-input v-model="form.name" placeholder="如 ZK-001" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="X坐标">
              <el-input-number v-model="form.location_x" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Y坐标">
              <el-input-number v-model="form.location_y" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="地面高程">
              <el-input-number v-model="form.location_z" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="钻孔深度(m)">
          <el-input-number v-model="form.depth" :min="0" />
        </el-form-item>
        <el-form-item label="测量温度(°C)">
          <el-input-number v-model="form.temperature" :min="0" />
        </el-form-item>
        <el-form-item label="地温梯度">
          <el-input-number v-model="form.gradient" :min="0" :step="0.1" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.map-placeholder {
  height: 400px;
  background: linear-gradient(135deg, #e8f4f8 0%, #d1e8e0 100%);
  border-radius: 8px;
  position: relative;
  overflow: hidden;
}

.map-grid {
  position: absolute;
  inset: 20px;
  border: 1px dashed #909399;
}

.drill-marker {
  position: absolute;
  transform: translate(-50%, -50%);
  cursor: pointer;
  transition: transform 0.2s;
}

.drill-marker:hover {
  transform: translate(-50%, -50%) scale(1.2);
}
</style>
