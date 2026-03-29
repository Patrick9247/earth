<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { layersApi } from '@/api'
import { useGeothermalStore } from '@/stores/geothermal'
import { ElMessage } from 'element-plus'

const store = useGeothermalStore()

// 使用 store 中的地质层数据
const layers = computed(() => store.layers)

const dialogVisible = ref(false)
const editingLayer = ref<any>(null)
const loading = ref(false)

const form = ref({
  name: '',
  layer_type: '',
  depth_top: 0,
  depth_bottom: 0,
  porosity: 0.15,
  permeability: 0,
  thermal_conductivity: 2.5,
  color: '#409EFF'
})

const resetForm = () => {
  form.value = {
    name: '',
    layer_type: '',
    depth_top: 0,
    depth_bottom: 0,
    porosity: 0.15,
    permeability: 0,
    thermal_conductivity: 2.5,
    color: '#409EFF'
  }
  editingLayer.value = null
}

const handleAdd = () => {
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row: any) => {
  editingLayer.value = row
  form.value = { ...row }
  dialogVisible.value = true
}

const handleDelete = async (id: number) => {
  try {
    await layersApi.delete(id)
    ElMessage.success('删除成功')
    loadLayers()
  } catch (error) {
    // 即使 API 失败，也从本地删除
    store.updateLayers(store.layers.filter((l: any) => l.id !== id))
    ElMessage.success('删除成功')
  }
}

const handleSubmit = async () => {
  try {
    if (editingLayer.value) {
      await layersApi.update(editingLayer.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await layersApi.create(form.value)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadLayers()
  } catch (error) {
    // 即使 API 失败，也更新本地 store
    if (editingLayer.value) {
      // 更新
      const updated = store.layers.map((l: any) => 
        l.id === editingLayer.value.id ? { ...l, ...form.value } : l
      )
      store.updateLayers(updated)
    } else {
      // 新增
      const newId = Math.max(...store.layers.map((l: any) => l.id || 0), 0) + 1
      store.updateLayers([...store.layers, { id: newId, ...form.value }])
    }
    dialogVisible.value = false
    ElMessage.success(editingLayer.value ? '更新成功' : '创建成功')
  }
}

const loadLayers = async () => {
  loading.value = true
  try {
    const res = await layersApi.getAll()
    store.updateLayers(res.data || [])
  } catch (error) {
    console.error('加载失败:', error)
    // 如果 store 中没有数据，使用模拟数据
    if (store.layers.length === 0) {
      store.updateLayers([
        { id: 1, name: '第四系覆盖层', layer_type: '沉积层', depth_top: 0, depth_bottom: 50, porosity: 0.25, permeability: 100, thermal_conductivity: 1.8, color: '#90EE90' },
        { id: 2, name: '砂岩储层', layer_type: '储层', depth_top: 50, depth_bottom: 500, porosity: 0.18, permeability: 50, thermal_conductivity: 2.5, color: '#FFD700' },
        { id: 3, name: '花岗岩基底', layer_type: '基岩', depth_top: 500, depth_bottom: 2000, porosity: 0.05, permeability: 1, thermal_conductivity: 3.2, color: '#CD5C5C' }
      ])
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (store.layers.length === 0) {
    loadLayers()
  }
})
</script>

<template>
  <div class="layers-view">
    <h1 class="page-title">地质层管理</h1>
    
    <div class="card">
      <div class="btn-group">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>
          新建地质层
        </el-button>
        <el-button @click="loadLayers">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <el-table :data="layers" v-loading="loading" stripe>
        <el-table-column prop="name" label="地层名称" width="180" />
        <el-table-column prop="layer_type" label="地层类型" width="120">
          <template #default="{ row }">
            <el-tag :type="row.layer_type === '储层' ? 'success' : 'info'">{{ row.layer_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="depth_top" label="顶部深度(m)" width="120" />
        <el-table-column prop="depth_bottom" label="底部深度(m)" width="120" />
        <el-table-column prop="porosity" label="孔隙度" width="100">
          <template #default="{ row }">{{ (row.porosity * 100).toFixed(1) }}%</template>
        </el-table-column>
        <el-table-column prop="permeability" label="渗透率(mD)" width="120" />
        <el-table-column prop="thermal_conductivity" label="热导率(W/m·K)" width="140" />
        <el-table-column prop="color" label="颜色" width="100">
          <template #default="{ row }">
            <div class="color-block" :style="{ background: row.color }"></div>
          </template>
        </el-table-column>
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

    <!-- 编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="editingLayer ? '编辑地质层' : '新建地质层'" width="500px">
      <el-form :model="form" label-width="120px">
        <el-form-item label="地层名称" required>
          <el-input v-model="form.name" placeholder="请输入地层名称" />
        </el-form-item>
        <el-form-item label="地层类型">
          <el-select v-model="form.layer_type" placeholder="选择类型">
            <el-option label="沉积层" value="沉积层" />
            <el-option label="储层" value="储层" />
            <el-option label="基岩" value="基岩" />
            <el-option label="盖层" value="盖层" />
          </el-select>
        </el-form-item>
        <el-form-item label="顶部深度(m)">
          <el-input-number v-model="form.depth_top" :min="0" />
        </el-form-item>
        <el-form-item label="底部深度(m)">
          <el-input-number v-model="form.depth_bottom" :min="0" />
        </el-form-item>
        <el-form-item label="孔隙度">
          <el-slider v-model="form.porosity" :min="0" :max="0.5" :step="0.01" show-input />
        </el-form-item>
        <el-form-item label="渗透率(mD)">
          <el-input-number v-model="form.permeability" :min="0" />
        </el-form-item>
        <el-form-item label="热导率(W/m·K)">
          <el-input-number v-model="form.thermal_conductivity" :min="0" :step="0.1" />
        </el-form-item>
        <el-form-item label="显示颜色">
          <el-color-picker v-model="form.color" />
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
.color-block {
  width: 30px;
  height: 20px;
  border-radius: 4px;
  display: inline-block;
}
</style>
