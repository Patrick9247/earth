<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 用户信息
interface User {
  id: number
  username: string
  role: string
  email?: string
  full_name?: string
  phone?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

const users = ref<User[]>([])
const loading = ref(false)
const currentUser = ref<User | null>(null)

// 判断是否为超级管理员
const isSuperAdmin = computed(() => currentUser.value?.role === 'SUPER')

// 获取当前用户
const getCurrentUser = (): User | null => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  }
  return null
}

// 获取请求头
const getAuthHeaders = () => {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// 获取用户列表
const fetchUsers = async () => {
  if (!isSuperAdmin.value) {
    ElMessage.warning('只有超级管理员可以查看用户列表')
    return
  }
  
  loading.value = true
  try {
    const response = await axios.get('/api/users/', {
      headers: getAuthHeaders()
    })
    users.value = response.data
  } catch (error: any) {
    const message = error.response?.data?.detail || '获取用户列表失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 创建用户对话框
const dialogVisible = ref(false)
const dialogTitle = ref('创建用户')
const isEdit = ref(false)

const userForm = reactive({
  id: 0,
  username: '',
  password: '',
  role: 'ADMIN',
  email: '',
  full_name: '',
  phone: ''
})

const userFormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }]
}

// 打开创建用户对话框
const openCreateDialog = () => {
  dialogTitle.value = '创建用户'
  isEdit.value = false
  Object.assign(userForm, {
    id: 0,
    username: '',
    password: '',
    role: 'ADMIN',
    email: '',
    full_name: '',
    phone: ''
  })
  dialogVisible.value = true
}

// 打开编辑用户对话框
const openEditDialog = (user: User) => {
  dialogTitle.value = '编辑用户'
  isEdit.value = true
  Object.assign(userForm, {
    id: user.id,
    username: user.username,
    password: '',
    role: user.role,
    email: user.email || '',
    full_name: user.full_name || '',
    phone: user.phone || ''
  })
  dialogVisible.value = true
}

// 打开编辑自己信息的对话框
const openSelfEditDialog = () => {
  if (!currentUser.value) return
  dialogTitle.value = '编辑个人信息'
  isEdit.value = true
  Object.assign(userForm, {
    id: currentUser.value.id,
    username: currentUser.value.username,
    password: '',
    role: currentUser.value.role,
    email: currentUser.value.email || '',
    full_name: currentUser.value.full_name || '',
    phone: currentUser.value.phone || ''
  })
  dialogVisible.value = true
}

// 提交表单
const submitForm = async () => {
  if (!userForm.username || (!isEdit.value && !userForm.password)) {
    ElMessage.warning('请填写必填项')
    return
  }
  
  if (!isEdit.value && userForm.password.length < 6) {
    ElMessage.warning('密码长度至少6位')
    return
  }
  
  loading.value = true
  try {
    const data: any = {
      username: userForm.username,
      role: userForm.role,
      email: userForm.email || null,
      full_name: userForm.full_name || null,
      phone: userForm.phone || null
    }
    
    if (userForm.password) {
      data.password = userForm.password
    }
    
    if (isEdit.value) {
      await axios.put(`/api/users/${userForm.id}`, data, {
        headers: getAuthHeaders()
      })
      ElMessage.success('更新成功')
    } else {
      await axios.post('/api/users/', data, {
        headers: getAuthHeaders()
      })
      ElMessage.success('创建成功')
    }
    
    dialogVisible.value = false
    fetchUsers()
    
    // 如果更新的是当前用户，更新本地存储
    if (isEdit.value && userForm.id === currentUser.value?.id) {
      const response = await axios.get('/api/users/me', {
        headers: getAuthHeaders()
      })
      localStorage.setItem('user', JSON.stringify(response.data))
      currentUser.value = response.data
    }
  } catch (error: any) {
    const message = error.response?.data?.detail || '操作失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 删除用户
const deleteUser = async (user: User) => {
  if (user.id === currentUser.value?.id) {
    ElMessage.warning('不能删除当前登录用户')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除用户「${user.full_name || user.username}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await axios.delete(`/api/users/${user.id}`, {
      headers: getAuthHeaders()
    })
    ElMessage.success('删除成功')
    fetchUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      const message = error.response?.data?.detail || '删除失败'
      ElMessage.error(message)
    }
  }
}

// 切换用户启用状态
const toggleUserActive = async (user: User) => {
  if (user.id === currentUser.value?.id) {
    ElMessage.warning('不能修改当前登录用户的启用状态')
    return
  }
  
  try {
    await axios.patch(`/api/users/${user.id}/toggle-active`, {}, {
      headers: getAuthHeaders()
    })
    ElMessage.success(user.is_active ? '已禁用' : '已启用')
    fetchUsers()
  } catch (error: any) {
    const message = error.response?.data?.detail || '操作失败'
    ElMessage.error(message)
  }
}

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN')
}

// 获取角色标签类型
const getRoleType = (role: string) => {
  return role === 'SUPER' ? 'danger' : 'primary'
}

// 获取角色标签文本
const getRoleText = (role: string) => {
  return role === 'SUPER' ? '超级管理员' : '普通管理员'
}

// 初始化
onMounted(() => {
  currentUser.value = getCurrentUser()
  if (isSuperAdmin.value) {
    fetchUsers()
  }
})
</script>

<template>
  <div class="user-management">
    <div class="page-header">
      <h1 class="page-title">用户管理</h1>
      <div class="header-actions">
        <el-button type="primary" @click="openSelfEditDialog">
          <el-icon><Edit /></el-icon>
          编辑个人信息
        </el-button>
        <el-button v-if="isSuperAdmin" type="success" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建用户
        </el-button>
        <el-button @click="fetchUsers" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <!-- 当前用户信息 -->
    <el-card v-if="currentUser" class="current-user-card">
      <template #header>
        <div class="card-header">
          <span>当前登录用户</span>
        </div>
      </template>
      <div class="user-info-row">
        <div class="user-info-item">
          <span class="label">用户名：</span>
          <span class="value">{{ currentUser.username }}</span>
        </div>
        <div class="user-info-item">
          <span class="label">姓名：</span>
          <span class="value">{{ currentUser.full_name || '-' }}</span>
        </div>
        <div class="user-info-item">
          <span class="label">角色：</span>
          <el-tag :type="getRoleType(currentUser.role)" size="small">
            {{ getRoleText(currentUser.role) }}
          </el-tag>
        </div>
        <div class="user-info-item">
          <span class="label">邮箱：</span>
          <span class="value">{{ currentUser.email || '-' }}</span>
        </div>
        <div class="user-info-item">
          <span class="label">电话：</span>
          <span class="value">{{ currentUser.phone || '-' }}</span>
        </div>
      </div>
    </el-card>
    
    <!-- 用户列表 -->
    <el-card v-if="isSuperAdmin" class="user-list-card">
      <template #header>
        <div class="card-header">
          <span>用户列表</span>
          <span class="user-count">共 {{ users.length }} 个用户</span>
        </div>
      </template>
      
      <el-table 
        :data="users" 
        v-loading="loading"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="full_name" label="姓名" min-width="100">
          <template #default="{ row }">
            {{ row.full_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="role" label="角色" width="120" align="center">
          <template #default="{ row }">
            <el-tag :type="getRoleType(row.role)" size="small">
              {{ getRoleText(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="160">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="phone" label="电话" width="130">
          <template #default="{ row }">
            {{ row.phone || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button 
              type="primary" 
              size="small" 
              text
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button 
              :type="row.is_active ? 'warning' : 'success'" 
              size="small" 
              text
              :disabled="row.id === currentUser?.id"
              @click="toggleUserActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              text
              :disabled="row.id === currentUser?.id"
              @click="deleteUser(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- 非管理员提示 -->
    <el-card v-else class="info-card">
      <el-empty description="普通管理员只能编辑个人信息，无法管理其他用户">
        <el-button type="primary" @click="openSelfEditDialog">
          编辑个人信息
        </el-button>
      </el-empty>
    </el-card>
    
    <!-- 创建/编辑用户对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form 
        ref="formRef"
        :model="userForm" 
        :rules="userFormRules" 
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input 
            v-model="userForm.username" 
            :disabled="isEdit"
            placeholder="请输入用户名"
          />
        </el-form-item>
        
        <el-form-item label="密码" :prop="isEdit ? '' : 'password'">
          <el-input 
            v-model="userForm.password" 
            type="password"
            show-password
            :placeholder="isEdit ? '留空则不修改密码' : '请输入密码'"
          />
        </el-form-item>
        
        <el-form-item label="角色" prop="role" v-if="isSuperAdmin && !isEdit">
          <el-select v-model="userForm.role" style="width: 100%">
            <el-option label="普通管理员" value="ADMIN" />
            <el-option label="超级管理员" value="SUPER" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="角色" v-else-if="isSuperAdmin && isEdit">
          <el-select v-model="userForm.role" style="width: 100%">
            <el-option label="普通管理员" value="ADMIN" />
            <el-option label="超级管理员" value="SUPER" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="姓名">
          <el-input v-model="userForm.full_name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="邮箱">
          <el-input v-model="userForm.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="电话">
          <el-input v-model="userForm.phone" placeholder="请输入联系电话" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="submitForm">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.user-management {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 22px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.current-user-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.user-count {
  font-size: 12px;
  color: #909399;
}

.user-info-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

.user-info-item {
  display: flex;
  align-items: center;
  min-width: 150px;
}

.user-info-item .label {
  color: #909399;
  font-size: 14px;
}

.user-info-item .value {
  color: #303133;
  font-size: 14px;
}

.user-list-card {
  margin-bottom: 20px;
}

.info-card {
  margin-bottom: 20px;
}
</style>
