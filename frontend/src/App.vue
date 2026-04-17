<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import AppHeader from './components/AppHeader.vue'
import AppSidebar from './components/AppSidebar.vue'

const router = useRouter()

// 用户信息
interface User {
  id: number
  username: string
  role: string
  full_name?: string
  email?: string
  phone?: string
}

const currentUser = ref<User | null>(null)
const isLoggedIn = computed(() => !!currentUser.value)

// 加载用户信息
const loadUser = () => {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      currentUser.value = JSON.parse(userStr)
    } catch {
      currentUser.value = null
    }
  }
}

// 登出
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('确定要退出登录吗？', '退出确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    currentUser.value = null
    router.push('/login')
  } catch {
    // 用户取消
  }
}

// 跳转到用户管理
const goToUserManagement = () => {
  router.push('/users')
}

onMounted(() => {
  loadUser()
})

// 监听登录状态变化
window.addEventListener('storage', (e) => {
  if (e.key === 'user') {
    loadUser()
  }
})
</script>

<template>
  <div class="app-container" v-if="isLoggedIn">
    <AppHeader 
      :user="currentUser" 
      @logout="handleLogout"
      @go-to-users="goToUserManagement"
    />
    <div class="main-wrapper">
      <AppSidebar />
      <main class="content-area">
        <RouterView />
      </main>
    </div>
  </div>
  <div v-else class="app-container app-container--login">
    <RouterView @login-success="loadUser" />
  </div>
</template>

<style scoped>
@import "@/styles/app.css";

.app-container--login {
  min-height: 100vh;
}
</style>
