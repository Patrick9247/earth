<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const emit = defineEmits(['login-success'])

// 登录/注册切换
const isLogin = ref(true)
const loading = ref(false)

// 登录表单
const loginForm = reactive({
  username: '',
  password: ''
})

// 注册表单
const registerForm = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  superAdminKey: '',
  email: '',
  fullName: '',
  phone: ''
})

// 登录
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  
  loading.value = true
  try {
    const response = await axios.post('/api/users/login', {
      username: loginForm.username,
      password: loginForm.password
    })
    
    const { access_token, user } = response.data
    
    // 保存 token 和用户信息
    localStorage.setItem('token', access_token)
    localStorage.setItem('user', JSON.stringify(user))
    
    ElMessage.success(`欢迎回来，${user.full_name || user.username}！`)
    emit('login-success')
    router.push('/')
  } catch (error: any) {
    const message = error.response?.data?.detail || '登录失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 注册
const handleRegister = async () => {
  if (!registerForm.username || !registerForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }
  
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  
  if (registerForm.password.length < 6) {
    ElMessage.warning('密码长度至少6位')
    return
  }
  
  loading.value = true
  try {
    await axios.post('/api/users/register', {
      username: registerForm.username,
      password: registerForm.password,
      super_admin_key: registerForm.superAdminKey || null,
      email: registerForm.email || null,
      full_name: registerForm.fullName || null,
      phone: registerForm.phone || null
    })
    
    ElMessage.success('注册成功，请登录')
    isLogin.value = true
    loginForm.username = registerForm.username
    registerForm.username = ''
    registerForm.password = ''
    registerForm.confirmPassword = ''
    registerForm.superAdminKey = ''
    registerForm.email = ''
    registerForm.fullName = ''
    registerForm.phone = ''
  } catch (error: any) {
    const message = error.response?.data?.detail || '注册失败'
    ElMessage.error(message)
  } finally {
    loading.value = false
  }
}

// 切换登录/注册
const toggleMode = () => {
  isLogin.value = !isLogin.value
}

// 回车登录
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    if (isLogin.value) {
      handleLogin()
    } else {
      handleRegister()
    }
  }
}
</script>

<template>
  <div class="login-container" @keydown="handleKeydown">
    <div class="login-box">
      <!-- Logo 和标题 -->
      <div class="login-header">
        <div class="logo">
          <svg viewBox="0 0 100 100" width="60" height="60">
            <circle cx="50" cy="50" r="45" fill="#409eff" opacity="0.2"/>
            <circle cx="50" cy="50" r="30" fill="#409eff" opacity="0.4"/>
            <circle cx="50" cy="50" r="15" fill="#409eff"/>
            <path d="M50 20 L50 80 M30 35 L50 50 L70 35 M30 65 L50 50 L70 65" 
                  stroke="white" stroke-width="3" fill="none" stroke-linecap="round"/>
          </svg>
        </div>
        <h1 class="title">地热流体资源建模系统</h1>
        <p class="subtitle">Geothermal Resource Modeling System</p>
      </div>
      
      <!-- 登录表单 -->
      <div v-if="isLogin" class="form-box">
        <h2 class="form-title">用户登录</h2>
        <el-form :model="loginForm" class="login-form">
          <el-form-item>
            <el-input 
              v-model="loginForm.username"
              placeholder="请输入用户名"
              prefix-icon="User"
              size="large"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              :loading="loading" 
              class="submit-btn"
              @click="handleLogin"
            >
              登 录
            </el-button>
          </el-form-item>
        </el-form>
        <div class="toggle-mode">
          还没有账号？<el-link type="primary" @click="toggleMode">立即注册</el-link>
        </div>
      </div>
      
      <!-- 注册表单 -->
      <div v-else class="form-box">
        <h2 class="form-title">用户注册</h2>
        <el-form :model="registerForm" class="login-form">
          <el-form-item>
            <el-input 
              v-model="registerForm.username"
              placeholder="用户名 (3-50位)"
              prefix-icon="User"
              size="large"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="registerForm.password"
              type="password"
              placeholder="密码 (至少6位)"
              prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="registerForm.confirmPassword"
              type="password"
              placeholder="确认密码"
              prefix-icon="Lock"
              size="large"
              show-password
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="registerForm.superAdminKey"
              placeholder="超级管理员密钥 (选填)"
              prefix-icon="Key"
              size="large"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="registerForm.fullName"
              placeholder="姓名 (选填)"
              prefix-icon="UserFilled"
              size="large"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="registerForm.email"
              placeholder="邮箱 (选填)"
              prefix-icon="Message"
              size="large"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-input 
              v-model="registerForm.phone"
              placeholder="联系电话 (选填)"
              prefix-icon="Phone"
              size="large"
              clearable
            />
          </el-form-item>
          <el-form-item>
            <el-button 
              type="primary" 
              size="large" 
              :loading="loading" 
              class="submit-btn"
              @click="handleRegister"
            >
              注 册
            </el-button>
          </el-form-item>
        </el-form>
        <div class="toggle-mode">
          已有账号？<el-link type="primary" @click="toggleMode">返回登录</el-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.login-box {
  width: 100%;
  max-width: 420px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  padding: 40px;
}

.login-header {
  text-align: center;
  margin-bottom: 30px;
}

.logo {
  margin-bottom: 15px;
}

.title {
  font-size: 22px;
  font-weight: 600;
  color: #333;
  margin: 0 0 5px 0;
}

.subtitle {
  font-size: 12px;
  color: #999;
  margin: 0;
}

.form-box {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.form-title {
  font-size: 18px;
  font-weight: 500;
  color: #333;
  text-align: center;
  margin: 0 0 25px 0;
}

.login-form {
  margin: 0;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-input__wrapper) {
  padding: 4px 15px;
}

.submit-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
}

.toggle-mode {
  text-align: center;
  color: #666;
  font-size: 14px;
  margin-top: 10px;
}
</style>
